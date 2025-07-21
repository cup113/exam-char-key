from json import dumps, loads
from typing import TypedDict, Literal
from random import shuffle


class BatchRequestMessage(TypedDict):
    role: Literal["user", "system"]
    content: str


class BatchRequestBody(TypedDict):
    model: str
    messages: list[BatchRequestMessage]
    temperature: float
    top_p: float


class BatchRequest(TypedDict):
    custom_id: str
    method: Literal["POST"]
    url: Literal["/v1/chat/completions"]
    body: BatchRequestBody


class PromptRaw(TypedDict):
    messages: list[BatchRequestMessage]


def convert(prompt_raw: PromptRaw, i: int, model: str) -> BatchRequest:
    return {
        "custom_id": f"request-tb-{i:04d}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": model,
            "messages": prompt_raw["messages"],
            "temperature": 0.5,
            "top_p": 0.95,
        },
    }

batch_requests_1: list[BatchRequest] = []
batch_requests_2: list[BatchRequest] = []


with open("./train/result/dataset-thinking-raw.jsonl", "r", encoding="utf-8") as fr:
    for i, line in enumerate(fr):
        prompt_raw = loads(line)
        batch_requests_1.append(convert(prompt_raw, i + 1, "qwen-plus"))
        batch_requests_2.append(convert(prompt_raw, i + 5001, "deepseek-v3"))

shuffle(batch_requests_1)

with open(
    "./train/result/dataset-thinking-prompt-1.jsonl", "w", encoding="utf-8"
) as fw:
    for batch_request in batch_requests_1:
        fw.write(dumps(batch_request, ensure_ascii=False) + "\n")

with open(
    "./train/result/dataset-thinking-prompt-2.jsonl", "w", encoding="utf-8"
) as fw:
    for batch_request in batch_requests_2:
        fw.write(dumps(batch_request, ensure_ascii=False) + "\n")
