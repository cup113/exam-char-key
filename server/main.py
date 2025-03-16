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
    return """你是一位高中语文老师，对高考文言文词语解释与句子翻译有着深入研究。
高考的词语解释答案常常在 5 字以内，且首先要回答出原义，如果语境中需要另外解释再回答衍生义。
现在，用户会提供一个短句，并指定一个字。
请你输出两行，第一行直接按高考要求回答该字的词语解释。
第二行为一个 0~10 的数字表示置信度。
不要输出其他多余内容。"""


def prompt_ai_thought():
    return """你是一位高中语文老师，对高考文言文词语解释与句子翻译有着深入研究。
高考的词语解释答案常常在 6 字以内，且首先要回答出原义，如果语境中需要另外解释再回答衍生义。
现在，用户会提供一个短句，并指定一个字。对你的回答要求如下：
1. 分析句子，可以用多行和列表，分析完成后用输出分隔线---。
2. 输出一行，表示你能想到的义项。
3. 输出多行无序列表。每一行，针对你能想到的一个义项进行逐个分析，形如 "<义项>/<分析>"，然后输出分隔线。
4. 用有序列表输出你认为最可能的 1~3 个答案，形如"1. <符合高考要求的词语解释>/<置信度(0~10)>"。
尖括号仅表示占位符，不要出现在输出内容中。敢于分析，但不要输出多余内容。"""


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
        temperature=0.6,
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
        temperature=0.8,
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
