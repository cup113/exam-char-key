"""
Please also turn on server when running this script.
Should take 2h unless cached.
"""

from dotenv import load_dotenv
from os import getenv
from openai import AsyncOpenAI
from httpx import AsyncClient
from tqdm import tqdm
from typing import Coroutine, Any
from asyncio import run, gather
from csv import DictReader
from train.evaluator.subjects import (
    EckFlashSubject,
    EckThinkingSubject,
    AiTaiyanSubject,
    Qwen8BSubject,
    Qwen8BFlashSubject,
    QwenPlusSubject,
    QwenPlusFlashSubject,
    QwenLongSubject,
    DeepSeekV3Subject,
)
from train.evaluator.evaluators import QwenLongEvaluator, QwenPlusEvaluator
from train.models import (
    EvaluationData,
    AiEvaluator,
    AiSubject,
    CacheHandler,
    CompletionSourcePack,
    BatchRequest,
)
from train.utils import IntermediateFiles, JsonlWriter
from hashlib import sha256

load_dotenv(".env")

client = AsyncOpenAI(
    api_key=getenv("API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

httpx_client = AsyncClient()
cache_handler = CacheHandler("train/result/cache")

subjects: list[AiSubject] = [
    EckFlashSubject(),
    EckThinkingSubject(),
    AiTaiyanSubject(),
    QwenPlusSubject(),
    QwenPlusFlashSubject(),
    QwenLongSubject(),
    DeepSeekV3Subject(),
    Qwen8BSubject(),
    Qwen8BFlashSubject(),
]

evaluators: list[AiEvaluator] = [QwenLongEvaluator(), QwenPlusEvaluator()]


async def subject_answer(
    data: EvaluationData, subject: AiSubject, zdic_prompt: str, index: int
) -> list[BatchRequest]:
    try:
        pack = CompletionSourcePack(
            context=data["context"],
            query=data["query"],
            zdic_prompt=zdic_prompt,
            client=client,
            cache_handler=cache_handler,
        )
        subject_answer = (await subject.ask(pack)).strip().replace("\n", "")
        hashed_id = sha256(subject_answer.encode()).hexdigest()

        result = [
            evaluator.get_request(
                data=data,
                subject_answer=subject_answer,
                cache_handler=cache_handler,
                id_prefix=f"final-{index:03d}-{hashed_id}",
            )
            for evaluator in evaluators
        ]

        return [r for r in result if r is not None]
    except Exception as e:
        print(f"Error evaluating {data['type']} {data['context']} {data['query']}: {e}")
        return []


async def main():
    dataset: list[EvaluationData] = []

    with open("./train/evaluation-dataset/dataset.csv", "r", encoding="utf-8") as f:
        reader = DictReader(f)
        for row in reader:
            dataset.append(row)  # type: ignore

    with JsonlWriter(IntermediateFiles.PromptEvaluationFinal1) as f1, JsonlWriter(
        IntermediateFiles.PromptEvaluationFinal2
    ) as f2:
        for index, data in enumerate(tqdm(dataset)):
            query = data["query"]
            tasks: list[Coroutine[Any, Any, list[BatchRequest]]] = []
            zdic_response = await httpx_client.get(
                f"http://localhost:4122/api/zdic?q={query}"
            )
            if zdic_response.status_code == 200:
                zdic_prompt = zdic_response.json()["zdic_prompt"]
            else:
                zdic_prompt = "汉典未给出解释。"

            for subject in subjects:
                tasks.append(subject_answer(data, subject, zdic_prompt, index))
            requests = await gather(*tasks)

            total_len = sum(len(request) for request in requests)
            if total_len == 0:
                continue # Cached, skip.

            existing_ids: set[str] = set()
            duplicated_count = 0
            for request in requests:
                for batch_request in request:
                    if batch_request["custom_id"] in existing_ids:
                        duplicated_count += 1
                        continue
                    model = batch_request["body"]["model"]
                    if model == "qwen-plus-latest":
                        f1.write_line(batch_request)
                        existing_ids.add(batch_request["custom_id"])
                    elif model == "qwen-long-latest":
                        f2.write_line(batch_request)
                    else:
                        raise ValueError(f"Unknown model: {model}")
            if duplicated_count != 0:
                tqdm.write(f"Saved {duplicated_count} duplicated requests in note {index:03d}")


if __name__ == "__main__":
    run(main())
