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
    QwenFlashSubject,
    QwenLongSubject,
    QwenLongFlashSubject,
    DeepSeekV3Subject,
)
from train.evaluator.evaluators import QwenLongEvaluator
from train.models import (
    EvaluationData,
    AiEvaluator,
    AiSubject,
    CacheHandler,
    CompletionSourcePack,
    BatchRequest,
)
from train.utils import IntermediateFiles, JsonlWriter

load_dotenv(".env")

client = AsyncOpenAI(
    api_key=getenv("API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

httpx_client = AsyncClient()
cache_handler = CacheHandler("train/result/cache")

subjects: list[AiSubject] = [
    EckFlashSubject(),
    Qwen8BFlashSubject(),
    AiTaiyanSubject(),
    QwenFlashSubject(),
    QwenLongFlashSubject(),
    EckThinkingSubject(),
    Qwen8BSubject(),
    QwenLongSubject(),
    DeepSeekV3Subject(),
]

evaluators: list[AiEvaluator] = [QwenLongEvaluator()]


async def subject_answer(
    data: EvaluationData,
    subject: AiSubject,
    zdic_prompt: str,
    index: int,
    ff: JsonlWriter,
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
        answer_hex = subject.answer_to_hex(subject_answer)
        ff.write_line(
            {
                "index": index,
                "answer": subject_answer,
                "hex": answer_hex,
                "model": subject.model_name,
            }
        )

        result = [
            evaluator.get_request(
                data=data,
                subject_answer=subject_answer,
                cache_handler=cache_handler,
                id_prefix=f"final-{index:03d}-{answer_hex}",
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

    with JsonlWriter(IntermediateFiles.PromptEvaluationFinal) as f, JsonlWriter(
        IntermediateFiles.CompletionFinals
    ) as ff:
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
                tasks.append(subject_answer(data, subject, zdic_prompt, index, ff))
            requests = await gather(*tasks)

            total_len = sum(len(request) for request in requests)
            if total_len == 0:
                continue  # Cached, skip.

            existing_ids: set[str] = set()
            duplicated_count = 0
            for request in requests:
                for batch_request in request:
                    if batch_request["custom_id"] in existing_ids:
                        duplicated_count += 1
                        continue
                    f.write_line(batch_request)
                    existing_ids.add(batch_request["custom_id"])
            if duplicated_count != 0:
                tqdm.write(
                    f"Saved {duplicated_count} duplicated requests in note {index:03d}"
                )


if __name__ == "__main__":
    run(main())
