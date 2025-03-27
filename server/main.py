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
    return """你是一位高中语文老师，对高考文言文词语解释与句子翻译有着深入研究。高考的词语解释答案常常在 6 字以内，不能太过意译，若语境确实特殊可以表示为：(原义)，这里指(引申义)。若涉及通假字，则需答：通“(通假字)”，(含义)。
现在，你的学生会提供一个短句，并指定一个字。你要先简短地思考，然后给出能够写在高考试卷上的答题解释，简短地解释原因，并给出置信度(1~5)。请不要输出其他多余内容。例如：
问：“举类迩而见义远”的“迩”的意思是什么？
回答示例：
think/句中的“迩”应该是形容词，和“远”形成对照，应该表示“近”之类的意思。结合“举类”即举例，可以很确定为浅近之义。
answer/浅近
explain/与“远”形成对照，表示举的例子很浅近。
conf/5"""


def prompt_ai_thought():
    return """你是一位高中语文老师，对高考文言文词语解释与句子翻译有着深入研究。高考的词语解释答案常常在 6 字以内，不能太过意译，，若语境确实特殊可以表示为：(原义)，这里指(引申义)。若涉及通假字，则需答：通“(通假字)”，(含义)。
汉典是一个权威的网站，你可以由此获得了该字的基本义项，但不一定全面。
现在，你的学生会提供一个短句，并指定一个字。你要先分析句子，包括句子大意和成分分析，然后按照你猜测的义项和汉典的义项逐个分析，最后给出 1~3 个能够写在高考试卷上的答题解释，并对每一个给出置信度(1~5)。请不要输出其他多余内容，遵循如下格式输出：
问：“其称文小而其指极大”的“指”的意思是什么？汉典的意思有：
1. 手伸出的支体（脚趾亦作“脚指”）：手～。巨～（大拇指）。～甲。～纹。～印。屈～可数。
2. 量词，一个手指的宽度：下了三～雨。
3. （手指或物体尖端）对着，向着：～着。～画。～南针。～手画脚。
4. 点明，告知：～导。～引。～正。～责。～控（指名控告）。～摘。～挥。～日可待。
5. 直立，竖起：令人发（fà）～（形容极为愤怒）。
6. 意向针对：～标。～定。
7. 古同“旨”，意义，目的。
回答示例：
think/句意为文章的表述虽然简短，但其“指”却很深远。句中“指”为主语，表示一种抽象的概念。
candidates/
手指/身体部位，显然不符。
意向/虽然接近，但过于宽泛，未完全符合文言文中的精确含义。
目的/古同“旨”，意义、目的，在此语境下恰当。
点明/动作，不符合成分。
answers/
同“旨”，意义/4
意向/2"""


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
        stream_options={"include_usage": True},
    )

    async for answer in response:
        if answer.usage:
            # usage info
            yield dumps(
                {
                    "type": "ai-usage",
                    "result": {
                        "prompt_tokens": answer.usage.prompt_tokens,
                        "completion_tokens": answer.usage.completion_tokens,
                    },
                }
            )
            break
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
        basic_explanations = [
            li.get_text() for li in soup.select("div.content.definitions.jnr>ol>li")
        ]
        detailed_explanations = [
            p.prettify(formatter="html5")
            for p in soup.select("div.content.definitions.xnr>p")
        ]

        zdic_prompt = "\n汉典给出的解释有：\n" + "\n".join(
            f"{i + 1}. {exp}" for i, exp in enumerate(basic_explanations)
        )
        yield dumps(
            {
                "type": "zdic",
                "result": {
                    "basic_explanations": basic_explanations,
                    "detailed_explanations": detailed_explanations,
                },
            }
        ) + "\n"
    except Exception as err:
        print(err)
        zdic_prompt = ""
        yield dumps(
            {
                "type": "zdic",
                "result": {
                    "basic_explanations": ["无"],
                    "detailed_explanations": ["无"],
                },
            }
        ) + "\n"

    response = await client.chat.completions.create(
        model="qwen-plus-2025-01-25",
        messages=[
            {
                "role": "system",
                "content": prompt_ai_thought(),
            },
            {
                "role": "user",
                "content": f"语境: {context}\n需要解释的字: {q}{zdic_prompt}",
            },
        ],
        stream=True,
        temperature=0.6,
        top_p=0.9,
        stream_options={"include_usage": True},
    )

    async for answer in response:
        if answer.usage:
            # usage info
            yield dumps(
                {
                    "type": "ai-usage",
                    "result": {
                        "prompt_tokens": answer.usage.prompt_tokens,
                        "completion_tokens": answer.usage.completion_tokens,
                    },
                }
            )
            break
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
