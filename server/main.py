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


def query_generator(q: str, context: str):
    if not q:
        return
    possible_set = tender_dict.get(q[0]) or set()
    for ch in q[1:]:
        possible_set = possible_set & (tender_dict.get(ch) or set())
    result = [textbook_data[i] for i in possible_set]
    yield dumps({"type": "text", "result": result})

    completion = client.chat.completions.create(
        model="qwen-plus-2025-01-25",
        messages=[
            {
                "role": "system",
                "content": """你是一位高中语文老师，对高考文言文词语解释与句子翻译有着深入研究。
高考的词语解释答案常常在 5 字以内，且首先要回答出原义，如果语境中需要另外解释再回答衍生义。
现在，用户会提供一个短句，并指定一个字。请你直接按高考要求回答该字的词语解释，并给出一个 0~10 的数字表示置信度。
除最终释义和置信度外，不要输出其他内容。""",
            },
            {"role": "user", "content": f"语境: {context}\n需要解释的字: {q}"},
        ],
        stream=True,
        temperature=0.8,
        top_p=0.9,
    )

    for answer in completion:
        yield dumps(
            {
                "type": "ai-instant",
                "result": {
                    "content": answer.choices[0].delta.content,
                    "stopped": bool(answer.choices[0].finish_reason),
                },
            }
        )


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
