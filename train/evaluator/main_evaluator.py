"""
Please also turn on server when running this script.
Should take about 2 hours to complete.
"""

from dotenv import load_dotenv
from os import getenv
from openai import AsyncOpenAI
from httpx import AsyncClient
from tqdm import tqdm
from typing import Coroutine, Any
from csv import DictReader, DictWriter
from asyncio import run, gather
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
    ScoredAnswer,
    EvaluationResult,
    AiEvaluator,
    AiSubject,
    CacheHandler,
    CompletionSourcePack,
)
from time import sleep, time

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


async def answer_and_score(
    data: EvaluationData, subject: AiSubject, zdic_prompt: str
) -> tuple[str, ScoredAnswer] | None:
    try:
        pack = CompletionSourcePack(
            context=data["context"],
            query=data["query"],
            zdic_prompt=zdic_prompt,
            client=client,
            cache_handler=cache_handler,
        )
        subject_answer = (await subject.ask(pack)).strip().replace("\n", "")
        scored_answer = ScoredAnswer(answer=subject_answer, scores={})
        for evaluator in evaluators:
            score = await evaluator.evaluate(
                data, subject_answer, client, cache_handler
            )
            if score is not None:
                scored_answer.scores[evaluator.model_name] = score
        return subject.model_name, scored_answer
    except Exception as e:
        print(f"Error evaluating {data['type']} {data['context']} {data['query']}: {e}")
        return None


async def main():
    dataset: list[EvaluationData] = []
    with open("./train/evaluation-dataset/dataset.csv", "r", encoding="utf-8") as f:
        reader = DictReader(f)
        for row in reader:
            dataset.append(row)  # type: ignore

    with open(
        "./train/result/evaluation-results.csv", "w", encoding="gbk", newline=""
    ) as f:
        fields = ["type", "context", "query", "answer"]
        for subject in subjects:
            fields.append(f"{subject.model_name}-ans")
            fields.append(f"{subject.model_name}-avg")

        writer = DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for data in tqdm(dataset):
            start_time = time()
            query = data["query"]
            tasks: list[Coroutine[Any, Any, tuple[str, ScoredAnswer] | None]] = []
            zdic_response = await httpx_client.get(
                f"http://localhost:4122/api/zdic?q={query}"
            )
            if zdic_response.status_code == 200:
                zdic_prompt = zdic_response.json()["zdic_prompt"]
            else:
                zdic_prompt = "汉典未给出解释。"

            for subject in subjects:
                tasks.append(answer_and_score(data, subject, zdic_prompt))

            scored_answers = await gather(*tasks)
            evaluation_result = EvaluationResult(base=data, results={})
            for scored_answer_ in scored_answers:
                if scored_answer_ is not None:
                    model_name, scored_answer = scored_answer_
                    evaluation_result.results[model_name] = scored_answer

            writer.writerow(evaluation_result.to_dict())
            f.flush()
            sleep(
                max(0, min(32 - (time() - start_time), time() - start_time))
            )  # If it's too fast, it's probably cached.


if __name__ == "__main__":
    run(main())
