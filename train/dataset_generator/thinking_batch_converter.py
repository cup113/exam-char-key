from train.models import BatchRequest, PromptRaw
from train.utils import JsonlReader, JsonlWriter, IntermediateFiles
from random import shuffle


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
with JsonlReader(IntermediateFiles.DatasetThinkingRaw) as fr:
    for i, prompt_raw in enumerate(fr):
        batch_requests_1.append(convert(prompt_raw, i + 1, "qwen-max-latest"))
        batch_requests_2.append(convert(prompt_raw, i + 5001, "deepseek-v3"))

shuffle(batch_requests_1)

with JsonlWriter(IntermediateFiles.PromptDatasetThinking1) as fw:
    for batch_request in batch_requests_1:
        fw.write_line(batch_request)

with JsonlWriter(IntermediateFiles.PromptDatasetThinking2) as fw:
    for batch_request in batch_requests_2:
        fw.write_line(batch_request)
