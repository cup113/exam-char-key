from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI
from json import load, dumps
from os import getenv
from httpx import AsyncClient
from bs4 import BeautifulSoup

app = FastAPI()

client = AsyncOpenAI(
    api_key=getenv("API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

with open("server/textbook.json", "r", encoding="utf-8") as f:
    textbook_data = load(f)
    tender_dict: dict[str, set[int]] = dict()
    for i, record in enumerate(textbook_data):
        word = record["context"][record["index_range"][0] : record["index_range"][1]]
        for ch in word:
            if ch not in tender_dict:
                tender_dict[ch] = set()
            tender_dict[ch].add(i)


def prompt_ai_instant():
    return """你是一位高中语文老师，对高考文言文词语解释与句子翻译有着深入研究。高考的词语解释答案常常在 6 字以内，不能太过意译，若语境确实特殊可以表示为：(原义)，这里指(引申义)。若涉及通假字，则需答：同“(通假字)”，(含义)。
现在，你的学生会提供一个短句，并指定一个字。你要先简短地思考，然后给出能够写在高考试卷上的答题解释，简短地解释原因，并给出置信度(0~10)。你的输出格式遵循 YAML，不要输出其他多余内容，格式如下：
```yaml
think: 思考过程
answer: 答案
explain: 解释
conf: 置信度（数字）
```"""


def prompt_ai_thought():
    return """你是一位高中语文老师，对高考文言文词语解释与句子翻译有着深入研究。高考的词语解释答案常常在 6 字以内，不能太过意译，，若语境确实特殊可以表示为：(原义)，这里指(引申义)。若涉及通假字，则需答：同“(通假字)”，(含义)。
汉典是一个权威的网站，你可以由此获得了该字的基本义项，但不一定全面。
现在，你的学生会提供一个短句，并指定一个字。你要先分析句子，包括句子大意和成分分析，然后给出你猜测的义项范围，接着逐个分析，最后给出 1~3 个能够写在高考试卷上的答题解释，并对每一个给出置信度(0~10)。你的输出格式遵循 YAML，不要输出其他多余内容，格式如下：
```yaml
analysis: 句意分析
candidates: [多个候选项]
filter:
  '候选项': 具体分析
answers:
  -
    answer: 答案
    conf: 置信度（数字）
```"""


async def request_zdic(word: str):
    async with AsyncClient() as client:
        response = await client.get("https://www.zdic.net/hans/" + word, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            return "Error: " + response.text


async def instant_query_generator(q: str, context: str):
    if not q:
        return
    possible_set = tender_dict.get(q[0]) or set()
    for ch in q[1:]:
        possible_set = possible_set & (tender_dict.get(ch) or set())
    result = [textbook_data[i] for i in possible_set]
    yield dumps({"type": "text", "result": result}) + "\n"

    response = await client.chat.completions.create(
        model="qwen-plus-2025-01-25",
        messages=[
            {
                "role": "system",
                "content": prompt_ai_instant(),
            },
            {"role": "user", "content": f"语境: {context}\n需要解释的字: {q}"},
        ],
        stream=True,
        temperature=0.5,
        top_p=0.9,
    )

    async for answer in response:
        yield dumps(
            {
                "type": "ai-instant",
                "result": {
                    "content": answer.choices[0].delta.content,
                    "stopped": bool(answer.choices[0].finish_reason),
                },
            }
        ) + "\n"


async def thought_query_generator(q: str, context: str):
    try:
        zdic_result = await request_zdic(q)
        soup = BeautifulSoup(zdic_result, "html.parser")
        basic_explanations = [li.get_text() for li in soup.select("div.content.definitions.jnr>ol>li")]
        zdic_prompt = "\n汉典给出的解释有：\n" + "\n".join(f"{i + 1}. {exp}" for i, exp in enumerate(basic_explanations))
        yield dumps({"type": "zdic", "result": { "basic_explanations": basic_explanations }}) + "\n"
    except:
        zdic_prompt = ""
        yield dumps({"type": "zdic", "result": { "basic_explanations": [] }}) + "\n"


    response = await client.chat.completions.create(
        model="qwen-plus-2025-01-25",
        messages=[
            {
                "role": "system",
                "content": prompt_ai_thought(),
            },
            {"role": "user", "content": f"语境: {context}\n需要解释的字: {q}{zdic_prompt}"},
        ],
        stream=True,
        temperature=0.7,
        top_p=0.9,
    )

    async for answer in response:
        yield dumps(
            {
                "type": "ai-thought",
                "result": {
                    "content": answer.choices[0].delta.content,
                    "stopped": bool(answer.choices[0].finish_reason),
                },
            }
        ) + "\n"


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
