from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI
from openai import AsyncStream
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionChunk
from json import load, dumps
from os import getenv
from httpx import AsyncClient
from bs4 import BeautifulSoup
from urllib.parse import quote
from typing import TypedDict


# 常量定义
class Config:
    API_KEY = getenv("API_KEY")
    MODEL = "qwen-plus-2025-01-25"
    MODEL_INPUT_PRICE = 8  # 1e-7 yuan/token
    MODEL_OUTPUT_PRICE = 20  # 1e-7 yuan/token
    AI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ZDIC_URL = "https://www.zdic.net/hans/"
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


def prompt_ai_instant():
    return """<prompt>
你是一位高中语文老师，对高考文言文词语解释与句子翻译有着深入研究。高考的词语解释答案常常在 6 字以内，不能太过意译。一般地可以给出一个精准解释，若语境确实特殊可以表示为：(原义)，这里指(引申义)。若涉及通假字，则需答：通“(通假字)”，(含义)。
汉典是一个权威的网站，你可以由此获得了该字的基本义项，但不一定全面。
你要做的事情如下：
- 对句义进行简单思考。用<think></think>标签包裹。
- 给出用你思考结果代入的句子解释。用<explain></explain>标签包裹。
- 输出你认为最好的 1 个可以写在高考试卷上的词语解释，用<answer></answer>包裹。
- 输出的最外层不需要做任何修饰，每步需要换行，每步内部可以换行。
</prompt>"""


def prompt_ai_thought():
    return """<prompt>
你是一位高中语文老师，对高考文言文词语解释与句子翻译有着深入研究。高考的词语解释答案常常在 6 字以内，不能太过意译，一般地可以给出一个精准解释，若语境确实特殊可以表示为：(原义)，这里指(引申义)。若涉及通假字，则需答：通“(通假字)”，(含义)。
汉典是一个权威的网站，你可以由此获得了该字的基本义项，但不一定全面。
你要做的事情如下：
- 对句义进行详细而有深度的思考，敢于多次尝试并依照汉典义项（若有）代入阐释。用<think></think>标签包裹。
- 给出用你思考结果代入的句子解释。用<explain></explain>标签包裹。
- 输出 1~3 个可以写在高考试卷上的词语解释，用<answers></answers>包裹，每个义项之间用分号“；”分隔。
- 输出的最外层不需要做任何修饰，每步需要换行，每步内部可以换行。
</prompt>"""


class CompletionService:
    def __init__(self, client: AsyncOpenAI):
        self.client = client

    async def _send_request(
        self,
        messages: list[ChatCompletionMessageParam],
        temperature: float,
        top_p: float,
    ):
        return await self.client.chat.completions.create(
            model=Config.MODEL,
            messages=messages,
            stream=True,
            temperature=temperature,
            top_p=top_p,
            stream_options={"include_usage": True},
        )

    async def _process_response(
        self, response: AsyncStream[ChatCompletionChunk], response_type: str
    ):
        async for answer in response:
            if answer.usage:
                yield dumps(
                    {
                        "type": "ai-usage",
                        "result": {
                            "prompt_tokens": answer.usage.prompt_tokens,
                            "completion_tokens": answer.usage.completion_tokens,
                            "input_unit_price": Config.MODEL_INPUT_PRICE,
                            "output_unit_price": Config.MODEL_OUTPUT_PRICE,
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
            messages=[
                {"role": "system", "content": prompt_ai_instant()},
                {"role": "user", "content": f"语境: {context}\n需要解释的字: {q}"},
            ],
            temperature=0.5,
            top_p=0.9,
        )
        async for chunk in self._process_response(response, "ai-instant"):
            yield chunk

    async def generate_thought_response(self, context: str, q: str, zdic_prompt: str):
        response = await self._send_request(
            messages=[
                {"role": "system", "content": prompt_ai_thought()},
                {
                    "role": "user",
                    "content": f"语境: {context}\n需要解释的字: {q}{zdic_prompt}",
                },
            ],
            temperature=0.6,
            top_p=0.9,
        )
        async for chunk in self._process_response(response, "ai-thought"):
            yield chunk


completion_service = CompletionService(client)


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


class ZDicResult(TypedDict):
    basic_explanations: list[str]
    detailed_explanations: list[str]
    phrase_explanations: list[str]
    zdic_prompt: str


class ZDicService:
    def __init__(self):
        self.zdic_url = Config.ZDIC_URL

    async def request_zdic(self, word: str):
        async with AsyncClient() as client:
            response = await client.get(self.zdic_url + quote(word), timeout=10)
            if response.status_code == 200:
                return response.text
            return f"Error {response.status_code}: {response.text}"

    def parse_zdic_result(self, zdic_result: str) -> ZDicResult:
        soup = BeautifulSoup(zdic_result, "html.parser")
        basic_explanations = [
            li.get_text()
            for li in soup.select(".zdict div.content.definitions.jnr>ol>li")
        ]
        detailed_explanations_prettified = [
            p.prettify(formatter="html5")
            for p in soup.select("#xxjs div.content.definitions.xnr>p")
        ]
        detailed_explanations = [
            p.get_text() for p in soup.select("#xxjs div.content.definitions.xnr>p")
        ]
        phrase_explanations = [
            p.get_text() for p in soup.select(".nr-box div.content.definitions .jnr>p")
        ]

        prompt_basic = (
            (
                "【基本解释】\n"
                + "\n".join(
                    f"{i + 1}. {exp}" for i, exp in enumerate(basic_explanations)
                )
                + "\n"
            )
            if basic_explanations
            else ""
        )
        prompt_detailed = (
            (
                "【详细解释】\n"
                + "\n".join(
                    f"{i + 1}. {exp}" for i, exp in enumerate(detailed_explanations)
                )
                + "\n"
            )
            if detailed_explanations
            else ""
        )
        prompt_phrase = (
            (
                "【词语解释】\n"
                + "\n".join(
                    f"{i + 1}. {exp}" for i, exp in enumerate(phrase_explanations)
                )
                + "\n"
            )
            if phrase_explanations
            else ""
        )

        zdic_prompt = prompt_basic + prompt_detailed + prompt_phrase
        zdic_prompt = (
            f"\n汉典给出的解释有：\n{zdic_prompt}"
            if zdic_prompt.strip()
            else "汉典未给出解释"
        )

        return {
            "basic_explanations": basic_explanations,
            "detailed_explanations": detailed_explanations_prettified,
            "phrase_explanations": phrase_explanations,
            "zdic_prompt": zdic_prompt,
        }


zdic_service = ZDicService()


async def thought_query_generator(q: str, context: str):
    try:
        zdic_result = await zdic_service.request_zdic(q)
        zdic_data = zdic_service.parse_zdic_result(zdic_result)

        yield dumps(
            {
                "type": "zdic",
                "result": {
                    "basic_explanations": zdic_data["basic_explanations"],
                    "detailed_explanations": zdic_data["detailed_explanations"],
                    "phrase_explanations": zdic_data["phrase_explanations"],
                },
            }
        ) + "\n"
        zdic_prompt = zdic_data["zdic_prompt"]
    except Exception as err:
        print(err)
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
    q: str = Query(..., description="The query word"),
    context: str = Query(..., description="The context word"),
    instant: bool = Query(True, description="Whether to use instant mode"),
):
    generator = instant_query_generator if instant else thought_query_generator
    return StreamingResponse(generator(q, context), media_type="application/json")


@app.get("/")
async def root():
    return RedirectResponse("/index.html")


app.mount("/", StaticFiles(directory="client/dist"), name="static")
