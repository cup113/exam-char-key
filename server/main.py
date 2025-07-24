from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI
from openai import AsyncStream
from openai.types.chat import ChatCompletionChunk
from typing import Literal
from httpx import ConnectTimeout

from server.services.zdic_service import ZdicService
from server.services.logging_service import main_logger
from server.config import Config
from server.models import (
    AiModel,
    AiUsage,
    FreqInfo,
    ZdicResult,
    ServerResponseType,
    CompletionChunkResponse,
    ServerResponseAiUsage,
    ServerResponseAi,
    ServerResponseAiFlash,
    ServerResponseZdic,
    ServerResponseFreqInfo,
)


def init_ai_client():
    if not Config.API_KEY:
        raise ValueError("API_KEY is not set")
    return AsyncOpenAI(
        api_key=Config.API_KEY,
        base_url=Config.AI_BASE_URL,
    )


def load_frequency_data():
    with open(Config.FREQUENCY_PATH, "r", encoding="utf-8") as f:
        data: dict[str, FreqInfo] = {}
        for line in f:
            record = FreqInfo.model_validate_json(line)
            data[record.word] = record
        return data


app = FastAPI()
client = init_ai_client()
frequency_data = load_frequency_data()


class CompletionService:
    def __init__(self, client: AsyncOpenAI):
        self.client = client

    async def _send_request(
        self,
        model: AiModel,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        search: Literal["no", "optional", "force"],
    ):
        if search == "no":
            extra_body = {"enable_search": False}
        elif search == "optional":
            extra_body = {"enable_search": True}
        elif search == "force":
            extra_body: "dict[str, bool | dict[str, bool]]" = {
                "enable_search": True,
                "search_options": {"forced_search": True},
            }
        if model.thinking:
            extra_body["enable_thinking"] = True
        return await self.client.chat.completions.create(
            model=model.id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
            temperature=temperature,
            stream_options={"include_usage": True},
            extra_body=extra_body,
        )

    async def _process_response(
        self,
        response: AsyncStream[ChatCompletionChunk],
        response_type: ServerResponseType,
        model: AiModel,
    ):
        reasoning = False
        async for answer in response:
            if answer.usage:
                yield ServerResponseAiUsage.create(
                    AiUsage(
                        model=model,
                        prompt_tokens=answer.usage.prompt_tokens,
                        completion_tokens=answer.usage.completion_tokens,
                    )
                )
                break
            delta = answer.choices[0].delta
            reasoning_content = delta.reasoning_content  # type: ignore
            if not isinstance(reasoning_content, str):
                reasoning_content = None

            # Special in Qwen3
            if reasoning_content is not None:
                if not reasoning:
                    content = "<think>" + reasoning_content
                    reasoning = True
                else:
                    content = reasoning_content
            else:
                if reasoning:
                    content = "</think>\n" + (delta.content or "")
                    reasoning = False
                else:
                    content = delta.content or ""

            yield ServerResponseAi.create(
                type=response_type,
                data=CompletionChunkResponse(
                    stopped=bool(answer.choices[0].finish_reason),
                    content=content,
                ),
            )

    async def generate_flash_response(self, context: str, q: str):
        model = Config.WYW_FLASH_MODEL
        response = await client.chat.completions.create(
            model=model.id,
            messages=[
                {"role": "system", "content": Config.PROMPT_FLASH},
                {"role": "user", "content": f"请解释古文“{context}”中，“{q}”的含义。"},
            ],
            temperature=0.3,
            top_p=0.95,
            max_tokens=100,
            extra_body={"enable_thinking": False},
        )
        content = response.choices[0].message.content

        if not content:
            raise ValueError("Empty response from ai flash model")

        assert response.usage is not None

        yield ServerResponseAiUsage.create(
            AiUsage(
                model=model,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
            )
        )

        yield ServerResponseAiFlash.create(data=content)

    async def generate_thought_response(self, context: str, q: str, zdic_prompt: str):
        model = Config.WYW_THINKING_MODEL
        response = await self._send_request(
            model=model,
            system_prompt=Config.PROMPT_AI_THOUGHT,
            user_prompt=f"请解释古文“{context}”中，“{q}”的含义。{zdic_prompt}",
            temperature=0.5,
            search="no",
        )

        async for chunk in self._process_response(
            response, ServerResponseType.AiThinking, model
        ):
            yield chunk

    async def search_original_text(
        self, excerpt: str, target: Literal["sentence", "paragraph", "full-text"]
    ):
        PROMPT_MAP = {
            "sentence": "请给出原文所在的句子，若有同段内的前后句更好。",
            "paragraph": "请给出原文所在的段落，若段落太短可扩充上下段。",
            "full-text": "请给出原文所在的全文。若全文过长，可以选择经典（出现在课文中或文言文练习中）的节选。千字以内建议全文输出。",
        }

        response = await self._send_request(
            model=Config.GENERAL_MODEL,
            system_prompt=Config.PROMPT_AI_SEARCH_ORIGINAL,
            user_prompt=f"原文内容节选: {excerpt}\n{PROMPT_MAP[target]}",
            temperature=0,
            search="force",
        )
        async for chunk in self._process_response(
            response, ServerResponseType.SearchOriginal, Config.GENERAL_MODEL
        ):
            yield chunk.to_jsonl_str()


completion_service = CompletionService(client)
zdic_service = ZdicService()


async def query_flash_core(context: str, q: str):
    async for chunk in completion_service.generate_flash_response(context, q):
        yield chunk.to_jsonl_str()


async def query_thinking_core(context: str, q: str):
    if q in frequency_data:
        yield ServerResponseFreqInfo.create(frequency_data[q]).to_jsonl_str()

    try:
        zdic_result = await zdic_service.get_result(q)

        if zdic_result is None:
            raise ValueError("Zdic unavailable.")

        yield ServerResponseZdic.create(zdic_result).to_jsonl_str()
        zdic_prompt = zdic_result.zdic_prompt
    except Exception as err:
        main_logger.warning(err)
        zdic_prompt = ""
        yield ServerResponseZdic.create(ZdicResult.empty()).to_jsonl_str()

    async for chunk in completion_service.generate_thought_response(
        context, q, zdic_prompt
    ):
        yield chunk.to_jsonl_str()


@app.get("/api/query/thinking")
async def query_thinking(
    q: str = Query(..., description="The query word", min_length=1, max_length=100),
    context: str = Query(..., description="The context sentence", max_length=1000),
):
    return StreamingResponse(
        query_thinking_core(context=context, q=q), media_type="application/json"
    )


@app.get("/api/query/flash")
async def query_flash(
    q: str = Query(..., description="The query word", min_length=1, max_length=100),
    context: str = Query(..., description="The context sentence", max_length=1000),
):
    return StreamingResponse(
        query_flash_core(context=context, q=q), media_type="application/json"
    )


@app.get("/api/search-original")
async def search_original(
    excerpt: str = Query(..., description="Excerpt to search in", max_length=10000),
    target: Literal["sentence", "paragraph", "full-text"] = Query(
        "sentence", description="Target level of detail"
    ),
):
    return StreamingResponse(
        completion_service.search_original_text(excerpt, target),
        media_type="application/json",
    )


@app.get("/api/zdic")
async def get_zdic_only(
    q: str = Query(..., description="The query word", max_length=100)
):
    try:
        result = await zdic_service.get_result(q)
    except ConnectTimeout:
        raise HTTPException(503, "Connection Timeout from zdic")
    if result is None:
        raise HTTPException(404, "Empty Response from zdic")
    return JSONResponse(result.model_dump_json())


@app.get("/")
async def root():
    return RedirectResponse("/index.html")


app.mount("/", StaticFiles(directory="client/dist"), name="static")
