"""
Please also turn on server when running this script.
Should take about 2 hours to complete.
"""

from dotenv import load_dotenv
from os import getenv
from openai import AsyncOpenAI
from httpx import AsyncClient
from train.utils import SYSTEM_PROMPTS
from tqdm import tqdm
from typing import TypedDict, Coroutine, Any
from dataclasses import dataclass
from csv import DictReader, DictWriter
from re import match, DOTALL
from asyncio import run, gather

load_dotenv(".env")

client = AsyncOpenAI(
    api_key=getenv("API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

httpx_client = AsyncClient()


class EvaluationData(TypedDict):
    type: str
    context: str
    query: str
    answer: str


class AiSubject:
    model_code: str
    model_name: str

    def __init__(self):
        pass

    async def get_flash_completion(self, context: str, query: str) -> str:
        supplement_prompt = (
            "不要输出除答案外的无关文字。" if "ft" not in self.model_code else ""
        )
        content = await self.get_ali_completion(
            system_prompt=SYSTEM_PROMPTS.FLASH,
            user_prompt=f"请解释古文“{context}”中，“{query}”的含义。请迅速回答。{supplement_prompt}",
            enable_search=False,
        )
        return content

    async def get_online_completion(self, context: str, query: str) -> str:
        response = await httpx_client.get(f"http://localhost:4122/api/zdic?q={query}")
        zdic_prompt = response.json()["zdic_prompt"]
        content = await self.get_ali_completion(
            system_prompt=SYSTEM_PROMPTS.THINKING,
            user_prompt=f"请解释古文“{context}”中，“{query}”的含义。请按要求仔细思考后回答。\n{zdic_prompt}",
            enable_search=False,
        )
        match_content = match(
            r"(.*?)\<answers\>(.*?)\<\/answers\>", content.strip(), DOTALL
        )
        if not match_content:
            return ""
        return match_content.group(2).strip()

    async def get_search_completion(self, context: str, query: str) -> str:
        content = await self.get_ali_completion(
            system_prompt=SYSTEM_PROMPTS.THINKING,
            user_prompt=f"请解释古文“{context}”中，“{query}”的含义。请按要求仔细思考后回答。",
            enable_search=True,
        )
        match_content = match(
            r"(.*?)\<answers\>(.*?)\<\/answers\>", content.strip(), DOTALL
        )
        if not match_content:
            return ""
        return match_content.group(2)

    async def get_offline_completion(self, context: str, query: str) -> str:
        content = await self.get_ali_completion(
            system_prompt=SYSTEM_PROMPTS.THINKING,
            user_prompt=f"请解释古文“{context}”中，“{query}”的含义。请按要求仔细思考后回答。\n汉典未给出解释。",
            enable_search=False,
        )
        match_content = match(
            r"(.*?)\<answers\>(.*?)\<\/answers\>", content.strip(), DOTALL
        )
        if not match_content:
            return ""
        return match_content.group(2)

    async def get_ali_completion(
        self, system_prompt: str, user_prompt: str, enable_search: bool
    ) -> str:
        completion = await client.chat.completions.create(
            model=self.model_code,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            extra_body={"enable_search": enable_search, "enable_thinking": False},
            temperature=0,
            top_p=0.95,
        )
        return completion.choices[0].message.content or ""

    async def ask(self, context: str, query: str) -> str:
        raise NotImplementedError


@dataclass
class ScoredAnswer:
    answer: str
    scores: dict[str, int]

    def get_average_score(self) -> float:
        return sum(self.scores.values()) / max(len(self.scores), 1)


@dataclass
class EvaluationResult:
    base: EvaluationData
    results: dict[str, ScoredAnswer]

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.base["type"],
            "context": self.base["context"],
            "query": self.base["query"],
            "answer": self.base["answer"],
            **{
                f"{subject}-avg": scored_answer.get_average_score()
                for subject, scored_answer in self.results.items()
            },
            **{
                f"{subject}-ans": scored_answer.answer
                for subject, scored_answer in self.results.items()
            },
            # **{
            #     f"{subject}-{evaluator}": score
            #     for subject, scored_answer in self.results.items()
            #     for evaluator, score in scored_answer.scores.items()
            # },
        }


class AiEvaluator:
    model_code: str
    model_name: str

    def __init__(self):
        pass

    async def evaluate(self, data: EvaluationData, subject_answer: str) -> int | None:
        answer = data["answer"]
        context = data["context"]
        query = data["query"]

        completion = await client.chat.completions.create(
            model=self.model_code,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPTS.EVALUATION},
                {
                    "role": "user",
                    "content": f"上下文：{context}\n需解释的词语：{query}\n标准答案：{answer}\n学生答案：{subject_answer}\n请按要求评分并按格式输出。",
                },
            ],
            temperature=0,
            top_p=0.95,
        )

        content = completion.choices[0].message.content or ""
        match_content = match(
            r"(.*?)\<score\>(.*?)\<\/score\>", content.strip(), DOTALL
        )
        if not match_content:
            return None

        score = match_content.group(2)
        return min(int(score), 3)


class EckFlashSubject(AiSubject):
    model_code = "qwen3-14b-ft-202507221614-8d95"
    model_name = "eck-flash"

    def __init__(self):
        super().__init__()

    async def ask(self, context: str, query: str) -> str:
        content = await self.get_ali_completion(
            system_prompt=SYSTEM_PROMPTS.FLASH,
            user_prompt=f"请解释古文“{context}”中，“{query}”的含义。请快速回答。",
            enable_search=False,
        )
        return content


class EckThinkingSubject(AiSubject):
    model_code = "qwen3-8b-ft-202507231002-7aeb"
    model_name = "eck-thinking"

    def __init__(self):
        super().__init__()

    async def ask(self, context: str, query: str) -> str:
        return await self.get_online_completion(context, query)


class AiTaiyanSubject(AiSubject):
    model_code = "taiyan"
    model_name = "taiyan"

    async def ask(self, context: str, query: str) -> str:
        content = await httpx_client.post(
            "https://t.shenshen.wiki/shiyi",
            headers={
                "Origin": "https://t.shenshen.wiki",
                "Referer": "https://t.shenshen.wiki/",
            },
            json={"mission": "shiyi", "text": f"{context}@@@@@{query}"},
        )
        return content.text


class Qwen8BSubject(AiSubject):
    model_code = "qwen3-8b"
    model_name = "qwen3-8b"

    async def ask(self, context: str, query: str) -> str:
        return await self.get_online_completion(context, query)


class Qwen8BFlashSubject(AiSubject):
    model_code = "qwen3-8b"
    model_name = "qwen3-8b-flash"

    async def ask(self, context: str, query: str) -> str:
        return await self.get_flash_completion(context, query)


class QwenTurboSubject(AiSubject):
    model_code = "qwen-turbo-latest"
    model_name = "qwen-turbo"

    async def ask(self, context: str, query: str) -> str:
        return await self.get_online_completion(context, query)


class QwenTurboFlashSubject(AiSubject):
    model_code = "qwen-turbo-flash-latest"
    model_name = "qwen-turbo-flash"

    async def ask(self, context: str, query: str) -> str:
        return await self.get_flash_completion(context, query)


class QwenMaxSubject(AiSubject):
    model_code = "qwen-max-latest"
    model_name = "qwen-max"

    async def ask(self, context: str, query: str) -> str:
        return await self.get_online_completion(context, query)


class DeepSeekV3Subject(AiSubject):
    model_code = "deepseek-v3"
    model_name = "deepseek-v3"

    async def ask(self, context: str, query: str) -> str:
        return await self.get_online_completion(context, query)


class QwenLongEvaluator(AiEvaluator):
    model_code = "qwen-long-latest"
    model_name = "ql"


class QwenPlusEvaluator(AiEvaluator):
    model_code = "qwen-plus-latest"
    model_name = "qp"


subjects: list[AiSubject] = [
    EckFlashSubject(),
    EckThinkingSubject(),
    AiTaiyanSubject(),
    QwenMaxSubject(),
    DeepSeekV3Subject(),
    Qwen8BSubject(),
    Qwen8BFlashSubject(),
]

evaluators: list[AiEvaluator] = [QwenLongEvaluator(), QwenPlusEvaluator()]


async def answer_and_score(
    data: EvaluationData, subject: AiSubject
) -> tuple[str, ScoredAnswer] | None:
    try:
        subject_answer = (await subject.ask(data["context"], data["query"])).strip()
        scored_answer = ScoredAnswer(answer=subject_answer, scores={})
        for evaluator in evaluators:
            score = await evaluator.evaluate(data, subject_answer)
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
            # for evaluator in evaluators:
            #     fields.append(f"{subject.model_name}-{evaluator.model_name}")

        writer = DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for data in tqdm(dataset):
            query = data["query"]
            tasks: list[Coroutine[Any, Any, tuple[str, ScoredAnswer] | None]] = []
            await httpx_client.get(f"http://localhost:4122/api/zdic?q={query}")
            for subject in subjects:
                tasks.append(answer_and_score(data, subject))

            scored_answers = await gather(*tasks)
            evaluation_result = EvaluationResult(base=data, results={})
            for scored_answer_ in scored_answers:
                if scored_answer_ is not None:
                    model_name, scored_answer = scored_answer_
                    evaluation_result.results[model_name] = scored_answer

            writer.writerow(evaluation_result.to_dict())
            f.flush()


if __name__ == "__main__":
    run(main())
