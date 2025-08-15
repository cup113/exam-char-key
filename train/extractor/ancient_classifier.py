from dotenv import load_dotenv
from os import getenv
from openai import OpenAI
from json import loads
from typing import TypedDict
from tqdm import tqdm
from train.models import Passage
from train.utils import SYSTEM_PROMPTS, JsonlReader, JsonlWriter, IntermediateFiles

load_dotenv(".env")

client = OpenAI(
    api_key=getenv("API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

with JsonlReader("./train/result/textbook-passages.jsonl") as f:
    passages = [Passage.from_dict(line) for line in f]


class Result(TypedDict):
    title: str
    thought: str
    is_ancient: bool


results: list[Result] = []
tokens = {"prompt": 0, "completion": 0}

for passage in tqdm(passages):
    prompt = f"""
{{
    'title': '{passage.title}',
    'author': '{passage.author}',
    'excerpt': '{passage.content[:128]}',
    'task': '按要求输出你对这篇文章的判断。'
}}"""

    completion = client.chat.completions.create(
        model="qwen2.5-14b-instruct",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPTS.CLASSIFICATION},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        top_p=0.95,
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
    with JsonlWriter(IntermediateFiles.IsAncientTextbook) as f:
        for result in results:
            f.write_line(result)

print(tokens)
