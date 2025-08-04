from typing import Literal
from openai import AsyncOpenAI
from openai import AsyncStream
from openai.types.chat import ChatCompletionChunk

from server.config import Config
from server.models import (
    AiModel,
    AiUsage,
    ServerResponseType,
    CompletionChunkResponse,
    ServerResponseAiUsage,
    ServerResponseAi,
    ServerResponseAiFlash,
)
from server.services.pocketbase_service import PocketBaseService


class CompletionService:
    def __init__(self, client: AsyncOpenAI, pb: PocketBaseService):
        self.client = client
        self.pb = pb

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
        else:
            extra_body["enable_thinking"] = False
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
        completion_type: str,
    ):
        reasoning = False
        async for answer in response:
            if answer.usage:
                usage = AiUsage(
                    model=model,
                    prompt_tokens=answer.usage.prompt_tokens,
                    completion_tokens=answer.usage.completion_tokens,
                )
                await self.pb.users_spend_coins(
                    usage.calc_cost(), reason=f"AI {completion_type}"
                )
                yield ServerResponseAiUsage.create(usage)
                break
            delta = answer.choices[0].delta
            try:
                reasoning_content: str | None = delta.reasoning_content  # type: ignore
                assert reasoning_content is None or isinstance(reasoning_content, str)
            except AttributeError:
                reasoning_content = None

            # Special in Qwen3
            if reasoning_content is not None:
                if not reasoning:
                    content = "**思考**：" + reasoning_content
                    reasoning = True
                else:
                    content = reasoning_content
            else:
                if reasoning:
                    content = "\n" + (delta.content or "")
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
        # Unnecessary for streaming response, using regular completion instead.
        model = Config.WYW_FLASH_MODEL
        response = await self.client.chat.completions.create(
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
        usage = AiUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            model=model,
        )

        await self.pb.users_spend_coins(coins=usage.calc_cost(), reason=f"AI 快速回答")

        yield ServerResponseAiUsage.create(usage)

        yield ServerResponseAiFlash.create(data=content)

    async def generate_thought_response(self, context: str, q: str, zdic_prompt: str, deep: bool):
        model = Config.WYW_THINKING_MODEL_DEEP if deep else Config.WYW_THINKING_MODEL
        response = await self._send_request(
            model=model,
            system_prompt=Config.PROMPT_AI_THOUGHT,
            user_prompt=f"请解释古文“{context}”中，“{q}”的含义。{zdic_prompt}",
            temperature=0.5,
            search="no",
        )

        async for chunk in self._process_response(
            response, ServerResponseType.AiThinking, model, "深度思考"
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
            response,
            ServerResponseType.SearchOriginal,
            Config.GENERAL_MODEL,
            "搜索原文",
        ):
            yield chunk.to_jsonl_str()

    async def extract_model_test(self, prompt: str):
        response = await self._send_request(
            model=Config.LONG_MODEL,
            system_prompt=Config.PROMPT_AI_EXTRACT_MODEL_TEST,
            user_prompt=prompt,
            temperature=0.5,
            search="no",
        )

        async for chunk in self._process_response(
            response, ServerResponseType.AiExtract, Config.LONG_MODEL, "提取模卷"
        ):
            yield chunk.to_jsonl_str()
