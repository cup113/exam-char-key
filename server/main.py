from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from json import load, dumps
from os import getenv

app = FastAPI()

client = OpenAI(
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
    return """你是一位高中语文老师，对高考文言文词语解释与句子翻译有着深入研究。高考的词语解释答案常常在 6 字以内，不能太过意译，若语境确实特殊可以表示为：(原义)，这里指(引申义)。若涉及通假字，则需答：同“(通假字)”，(含义)。现在，你的学生会提供一个短句，并指定一个字。你要先思考，然后给出能够写在高考试卷上的答题解释，简短地解释原因，并给出置信度(0~10)。你的输出格式要求如下：
思考：...
答案：...
解释：...
置信度：..."""


def prompt_ai_thought():
    return """是一位高中语文老师，对高考文言文词语解释与句子翻译有着深入研究。高考的词语解释答案常常在 6 字以内，不能太过意译，，若语境确实特殊可以表示为：(原义)，这里指(引申义)。若涉及通假字，则需答：同“(通假字)”，(含义)。现在，你的学生会提供一个短句，并指定一个字。你要先分析句子，包括句子大意和成分分析，然后给出你猜测的义项范围，接着逐个分析，最后给出 1~3 个能够写在高考试卷上的答题解释，并对每一个给出置信度(0~10)。你的输出格式要求如下：
句意分析：...
初步义项：...
义项分析：...
最终答案：[答案1/置信度1,答案2/置信度2,答案3/置信度3](若置信度低于 5，则不输出)"""


def query_generator(q: str, context: str):
    if not q:
        return
    possible_set = tender_dict.get(q[0]) or set()
    for ch in q[1:]:
        possible_set = possible_set & (tender_dict.get(ch) or set())
    result = [textbook_data[i] for i in possible_set]
    yield dumps({"type": "text", "result": result}) + "\n"

    instant_completion = client.chat.completions.create(
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

    thought_completion = client.chat.completions.create(
        model="qwen-plus-2025-01-25",
        messages=[
            {
                "role": "system",
                "content": prompt_ai_thought(),
            },
            {"role": "user", "content": f"语境: {context}\n需要解释的字: {q}"},
        ],
        stream=True,
        temperature=0.7,
        top_p=0.9,
    )

    for answer in instant_completion:
        yield dumps(
            {
                "type": "ai-instant",
                "result": {
                    "content": answer.choices[0].delta.content,
                    "stopped": bool(answer.choices[0].finish_reason),
                },
            }
        ) + "\n"

    for answer in thought_completion:
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
):
    return StreamingResponse(query_generator(q, context), media_type="application/json")


@app.get("/")
async def root():
    return RedirectResponse("/index.html")


app.mount("/", StaticFiles(directory="client/dist"), name="static")
