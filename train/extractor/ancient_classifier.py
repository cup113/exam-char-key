from dotenv import load_dotenv
from os import getenv
from openai import OpenAI
from json import loads, dumps
from typing import TypedDict
from tqdm import tqdm
from train.models import Passage

load_dotenv(".env")

client = OpenAI(
    api_key=getenv("API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

with open("./train/result/textbook-passages.jsonl", "r", encoding="utf-8") as f:
    passages = [Passage.from_dict(loads(line)) for line in f]

SYSTEM_PROMPT = "你要判断一篇文章是不是一篇文言文（包括古诗文），主要依据为其中语言是否可能包含一些文言词汇，因此近代诗文可能也包含在内。你需要先简单思考判断，然后给出判断结果。以 json 格式输出：{'thought': string, 'is_ancient': boolean}，不要包含其它内容。"

class Result(TypedDict):
    title: str
    thought: str
    is_ancient: bool

results: list[Result] = []
tokens = { "prompt": 0, "completion": 0 }

for passage in tqdm(passages):
    prompt = f"""
{{
    'title': {passage.title},
    'author': {passage.author},
    'excerpt': \n{passage.content[:128]}
}}\n按要求输出你对这篇文章的判断。"""

    completion = client.chat.completions.create(
        model="qwen2.5-14b-instruct",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={ "type": "json_object" },
    )

    completion_info = loads(completion.model_dump_json())
    content = completion_info["choices"][0]["message"]["content"]
    tokens["prompt"] += completion_info["usage"]["prompt_tokens"]
    tokens["completion"] += completion_info["usage"]["completion_tokens"]
    try:
        result = loads(content)
    except Exception as e:
        print(f"Error: {e}")
        continue
    result["title"] = passage.title
    results.append(result)
    with open("./train/result/textbook-is-ancient.jsonl", "w", encoding="utf-8") as f:
        for result in results:
            f.write(dumps(result, ensure_ascii=False) + "\n")
