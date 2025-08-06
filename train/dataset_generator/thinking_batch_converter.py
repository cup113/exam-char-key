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
            "temperature": 0.7,
            "top_p": 0.95,
        },
    }


batch_requests: list[BatchRequest] = []
with JsonlReader(IntermediateFiles.DatasetThinkingRaw) as fr:
    for i, prompt_raw in enumerate(fr):
        batch_requests.append(convert(prompt_raw, i, "qwen-long-latest"))

shuffle(batch_requests)

with JsonlWriter(IntermediateFiles.PromptDatasetThinking) as fw:
    for batch_request in batch_requests:
        fw.write_line(batch_request)
