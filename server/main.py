from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI
from openai import AsyncStream
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionChunk
from json import load, dumps
from os import getenv
from typing import Literal
from dataclasses import dataclass
from .services.zdic_service import ZDicService
from .services.logging_service import main_logger


@dataclass
class AiModel:
    id: str
    prompt_price: int  # 1e-7 RMB/token
    completion_price: int  # 1e-7 RMB/token
    thinking: bool


# 常量定义
class Config:
    API_KEY = getenv("API_KEY")
    GENERAL_MODEL = AiModel("qwen-plus", 8, 20, False)
    GENERAL_MODEL_THINKING = AiModel("qwen-plus", 8, 80, True)
    TURBO_MODEL = AiModel("qwen-turbo", 3, 6, False)
    WYW_MODEL = AiModel("qwen3-14b-ft-202506272014-8e62", 10, 40, False)

    MODEL_INPUT_PRICE = 8  # 1e-7 yuan/token
    MODEL_OUTPUT_PRICE = 20  # 1e-7 yuan/token
    AI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    TEXTBOOK_PATH = "server/textbook.json"


def init_ai_client():
    if not Config.API_KEY:
        raise ValueError("API_KEY is not set")
    return AsyncOpenAI(
        api_key=Config.API_KEY,
        base_url=Config.AI_BASE_URL,
    )


# 加载教材数据
def load_textbook_data():
    with open(Config.TEXTBOOK_PATH, "r", encoding="utf-8") as f:
        textbook_data = load(f)
        tender_dict: dict[str, set[int]] = {}
        for i, record in enumerate(textbook_data):
            word = record["context"][
                record["index_range"][0] : record["index_range"][1]
            ]
            for ch in word:
                if ch not in tender_dict:
                    tender_dict[ch] = set()
                tender_dict[ch].add(i)
        return textbook_data, tender_dict


app = FastAPI()
client = init_ai_client()
textbook_data, tender_dict = load_textbook_data()


PROMPT_AI_INSTANT = """你是一位高中语文老师，深入研究高考文言文词语解释。答案简短，并且不太过意译。一般可以给出一个精准解释，语境特殊时可以补充引申义。若涉及通假字，则需答：通“(通假字)”，(含义)。你需要简洁地回答用户的问题，除答案外不输出任何内容。"""


PROMPT_AI_THOUGHT = """<prompt>
你是一位高中语文老师，对高考文言文词语解释与句子翻译有着深入研究。高考的词语解释答案常常在 6 字以内，不能太过意译，一般地可以给出一个精准解释，若语境确实特殊可以表示为：(原义)，这里指(引申义)。若涉及通假字，则需答：通“(通假字)”，(含义)。
汉典是一个权威的网站，内含该字的基本义项，但不一定全面。
你要做的事情如下：
- 对句义进行详细而有深度的思考，敢于多次尝试并依照汉典义项（若有）代入阐释。用<think></think>标签包裹。
- 给出用你思考结果代入的句子解释。用<explain></explain>标签包裹。
- 输出 1~3 个可以写在高考试卷上的词语解释，用<answers></answers>包裹，每个义项之间用分号“；”分隔。
- 输出的最外层不需要做任何修饰，每步需要换行，每步内部可以换行。
</prompt>"""

PROMPT_AI_SEARCH_ORIGINAL = """你是一位助手，要根据节选的内容，【搜索文言文原文】并输出。请不要输出任何其他格式类和互动类信息，仅仅给出原文内容。"""


class CompletionService:
    def __init__(self, client: AsyncOpenAI):
        self.client = client

    async def _send_request(
        self,
        model: AiModel,
        messages: list[ChatCompletionMessageParam],
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
            messages=messages,
            stream=True,
            temperature=temperature,
            stream_options={"include_usage": True},
            extra_body=extra_body,
        )

    async def _process_response(
        self,
        response: AsyncStream[ChatCompletionChunk],
        response_type: str,
        model: AiModel,
    ):
        async for answer in response:
            if answer.usage:
                yield dumps(
                    {
                        "type": "ai-usage",
                        "result": {
                            "prompt_tokens": answer.usage.prompt_tokens,
                            "completion_tokens": answer.usage.completion_tokens,
                            "input_unit_price": model.prompt_price,
                            "output_unit_price": model.completion_price,
                        },
                    }
                )
                break
            yield dumps(
                {
                    "type": response_type,
                    "result": {
                        "content": answer.choices[0].delta.content,
                        "stopped": bool(answer.choices[0].finish_reason),
                    },
                }
            ) + "\n"

    async def generate_instant_response(self, context: str, q: str):
        response = await self._send_request(
            model=Config.WYW_MODEL,
            messages=[
                {"role": "system", "content": PROMPT_AI_INSTANT},
                {"role": "user", "content": f"请解释古文“{context}”中，“{q}”的含义。"},
            ],
            temperature=0.4,
            search="no",
        )
        async for chunk in self._process_response(
            response, "ai-instant", Config.WYW_MODEL
        ):
            yield chunk

    async def generate_thought_response(self, context: str, q: str, zdic_prompt: str):
        response = await self._send_request(
            model=Config.GENERAL_MODEL,
            messages=[
                {"role": "system", "content": PROMPT_AI_THOUGHT},
                {
                    "role": "user",
                    "content": f"语境: {context}\n需要解释的字: {q}{zdic_prompt}",
                },
            ],
            temperature=0.4,
            search="optional",
        )
        async for chunk in self._process_response(
            response, "ai-thought", Config.GENERAL_MODEL
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
            messages=[
                {"role": "system", "content": PROMPT_AI_SEARCH_ORIGINAL},
                {
                    "role": "user",
                    "content": f"原文内容节选: {excerpt}\n{PROMPT_MAP[target]}",
                },
            ],
            temperature=0,
            search="force",
        )

        async for chunk in self._process_response(
            response, "search-original", Config.GENERAL_MODEL
        ):
            yield chunk


completion_service = CompletionService(client)
zdic_service = ZDicService()


async def instant_query_generator(q: str, context: str):
    if not q:
        return
    possible_set = tender_dict.get(q[0]) or set()
    for ch in q[1:]:
        possible_set = possible_set & (tender_dict.get(ch) or set())
    result = [textbook_data[i] for i in possible_set]
    yield dumps({"type": "text", "result": result}) + "\n"

    async for chunk in completion_service.generate_instant_response(context, q):
        yield chunk


async def thought_query_generator(q: str, context: str):
    try:
        zdic_result = await zdic_service.get_result(q)

        if zdic_result is None:
            raise ValueError("Zdic unavailable.")

        yield dumps(
            {
                "type": "zdic",
                "result": {
                    "basic_explanations": zdic_result.basic_explanations,
                    "detailed_explanations": zdic_result.detailed_explanations,
                    "phrase_explanations": zdic_result.phrase_explanations,
                },
            }
        ) + "\n"
        zdic_prompt = zdic_result.zdic_prompt
    except Exception as err:
        main_logger.warning(err)
        zdic_prompt = ""
        yield dumps(
            {
                "type": "zdic",
                "result": {
                    "basic_explanations": [],
                    "detailed_explanations": [],
                    "phrase_explanations": [],
                },
            }
        ) + "\n"

    async for chunk in completion_service.generate_thought_response(
        context, q, zdic_prompt
    ):
        yield chunk


@app.get("/api/query")
async def query(
    q: str = Query(..., description="The query word", max_length=100),
    context: str = Query(..., description="The context sentence", max_length=1000),
    instant: bool = Query(True, description="Whether to use instant mode"),
):
    # TODO separate API
    generator = instant_query_generator if instant else thought_query_generator
    return StreamingResponse(generator(q, context), media_type="application/json")


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
async def get_zdic_only(q: str = Query(..., description="The query word", max_length=100)):
    result = await zdic_service.get_result(q)
    if result is None:
        raise HTTPException(404, "Empty Response from zdic")
    return JSONResponse(result.to_dict())


@app.get("/")
async def root():
    return RedirectResponse("/index.html")


app.mount("/", StaticFiles(directory="client/dist"), name="static")
