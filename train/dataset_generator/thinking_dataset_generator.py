from re import match, DOTALL
from train.utils import JsonlReader, JsonlWriter, IntermediateFiles, SYSTEM_PROMPTS
from train.models import (
    CompletionApiResponse,
    Note,
    PromptRaw,
    CacheHandler,
    BatchRequest,
    BatchRequestMessage,
)
from warnings import warn
from dataclasses import dataclass
from openai import AsyncOpenAI
from asyncio import run
from json import loads, dumps
from dotenv import load_dotenv
from os import getenv
from typing import Literal


@dataclass
class ScoredResponse:
    answer: str
    model: str
    model_full: str
    messages: list[BatchRequestMessage]
    scores: list[float]

    def get_average(self) -> float | None:
        if len(self.scores) == 0:
            return None
        return sum(self.scores) / len(self.scores)


@dataclass
class ScoredNote:
    base: Note
    prompt: str
    responses: dict[str, ScoredResponse]


def parse_grade(message: str) -> str | None:
    grade_match = match(r"(.*?)\<grade\>([ABCDE])\<\/grade\>", message.strip(), DOTALL)

    if grade_match:
        return str(grade_match.group(2))
    else:
        return None


def grade_to_score(grade: str | None) -> float | None:
    if grade is None:
        return None
    return {
        "A": 1.0,
        "B": 0.8,
        "C": 0.5,
        "D": 0.2,
        "E": 0.0,
    }.get(grade)


def get_answer(message: str) -> str | None:
    pattern = r"\*\*思考\*\*[\:：].*?\n\*\*解释\*\*[\:：].*?\n\*\*答案\*\*[\:：](.*)"
    result = match(pattern, message.strip(), DOTALL)
    if result is None:
        return None
    return result.group(1)


# 初始化缓存处理器
cache_handler = CacheHandler("./train/result/cache")

# TODO Reflection


async def reflect_on_response(
    model_code: str,
    messages: list[BatchRequestMessage],
    correct_answer: str,
    score: float,
) -> str | None | Literal[False]:

    reflection_prompt = f"""然而标准答案是：{correct_answer}，因此在评估过程中你只获得了 {score:.2f} 分。你需要反思你的回答，以便更好地训练学生。

请按以下步骤进行：
1. 分析你的回答与标准答案的差异
2. 判断你的回答是否正确，标准答案是否合理
3. 决定是坚持你的原始回答还是接受标准答案

请以以下格式输出，分为三行：
第一行：**分析**：[你的分析过程]
第二行：**接受**：[接受/拒绝]
第三行：**重新回答**：[如果你接受标准答案，则重新按原有格式（即：“**思考**：”“**解释**：”“**答案**：”开头）组织回答；如果拒绝，则此行为空。注意，不要在这一回答中展现出你知道标准答案，而是重新从头推理，以便更好地教育学生。]"""

    cache_key = f"reflect_{dumps(messages, ensure_ascii=False)}_{model_code}_{reflection_prompt}"
    cached_result = cache_handler.query_cache(cache_key)

    if not cached_result:
        load_dotenv()
        client = AsyncOpenAI(
            api_key=getenv("API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

        try:
            print(messages)
            print(reflection_prompt)
            response = await client.chat.completions.create(
                model=model_code,
                messages=messages + [{"role": "user", "content": reflection_prompt}],  # type: ignore
                temperature=0.3,
                top_p=0.95,
            )

            content = response.choices[0].message.content
            print(content)
            if content:
                # 解析结果
                try:
                    accept_standard = "拒绝" not in content

                    if accept_standard:
                        content_match = match(
                            r".*?\*\*重新回答\*\*[\:：]\s*(.*)", content, DOTALL
                        )
                        if content_match is None:
                            warn(f"Model illegal response: {content}")
                            return None

                        result = content_match.group(1).strip()
                        cache_handler.save_cache(cache_key, dumps(result))
                        return result

                    elif not accept_standard:
                        cache_handler.save_cache(cache_key, dumps(None))
                        return None

                except Exception as e:
                    warn(f"Failed to parse reflection result: {e}")
                    return False
        except Exception as e:
            warn(f"Reflection failed: {e}")
            return False
    else:
        return loads(cached_result)


data: dict[int, ScoredNote] = {}


def add_data(api_response: CompletionApiResponse) -> None:
    if api_response["error"] is not None:
        warn(f"Error in response: {api_response['error']}")
        return
    content = api_response["response"]["body"]["choices"][0]["message"]["content"]
    id_match = match(r"request-tb-(\d{4})-([a-zA-Z]+)", api_response["custom_id"])
    if not id_match:
        return
    note_id = int(id_match.group(1).lstrip("0") or "0")
    model = id_match.group(2)

    if not get_answer(content):
        single_line_content = content.replace("\n", "")
        warn(f"Response is incomplete: {single_line_content}")
        return
    if model not in data[note_id].responses:
        data[note_id].responses[model] = ScoredResponse(
            answer=content,
            model=model,
            model_full={
                "ds": "deepseek-v3",
                "qp": "qwen-plus-latest",
                "ql": "qwen-long-latest",
            }[model],
            messages=[{"role": "assistant", "content": content}],
            scores=[],
        )


def add_message(batch_request: BatchRequest):
    custom_id_match = match(r"request-tb-(\d+)-([a-z]+)", batch_request["custom_id"])
    assert custom_id_match is not None, "Invalid custom_id"
    messages = batch_request["body"]["messages"]
    note_id = int(custom_id_match.group(1).lstrip("0") or "0")
    model_short = custom_id_match.group(2)
    data[note_id].responses[model_short].messages.extend(reversed(messages))
    data[note_id].responses[model_short].messages.reverse()


def add_score(api_response: CompletionApiResponse) -> None:
    if api_response["error"] is not None:
        warn(f"Error in response: {api_response['error']}")
        return
    content = api_response["response"]["body"]["choices"][0]["message"]["content"]
    grade = parse_grade(content)
    score = grade_to_score(grade)
    if score is None:
        single_line_content = content.replace("\n", "")
        warn(f"No score found in response: {single_line_content}")
        return
    id_match = match(
        r"request-tb-(\d{4})-([a-zA-Z]+)-ev-(.*)", api_response["custom_id"]
    )
    if not id_match:
        return

    note_id = int(id_match.group(1).lstrip("0") or "0")
    model = id_match.group(2)
    if note_id not in data:
        warn(f"Note {note_id} not found in dataset")
        return

    if model not in data[note_id].responses:
        warn(f"Model {model} not found in note {note_id}")
        return
    data[note_id].responses[model].scores.append(score)


with JsonlReader(IntermediateFiles.DatasetThinkingRaw) as reader:
    for i, line in enumerate(reader):
        prompt_raw: PromptRaw = line
        user_prompt = prompt_raw["messages"][1]["content"]
        data[i] = ScoredNote(Note.from_dict(prompt_raw["note"]), user_prompt, {})


with JsonlReader(IntermediateFiles.CompletionBatchThinking1) as reader:
    for line in reader:
        add_data(line)

with JsonlReader(IntermediateFiles.CompletionBatchThinking2) as reader:
    for line in reader:
        add_data(line)

with JsonlReader(IntermediateFiles.CompletionBatchThinking3) as reader:
    for line in reader:
        add_data(line)


with JsonlReader(IntermediateFiles.CompletionBatchEvaluationThinking1) as reader:
    for line in reader:
        add_score(line)

with JsonlReader(IntermediateFiles.CompletionBatchEvaluationThinking2) as reader:
    for line in reader:
        add_score(line)

with JsonlReader(IntermediateFiles.PromptDatasetThinking1) as reader:
    for line in reader:
        add_message(line)

with JsonlReader(IntermediateFiles.PromptDatasetThinking2) as reader:
    for line in reader:
        add_message(line)

with JsonlReader(IntermediateFiles.PromptDatasetThinking3) as reader:
    for line in reader:
        add_message(line)


async def main():
    with JsonlWriter(IntermediateFiles.DatasetThinking) as writer, open(
        "./train/result/dataset-thinking-evaluation-scores.txt", "w", encoding="utf-8"
    ) as score_file:
        ACCEPT_THRESHOLD = 0.74
        for note_id, note in data.items():
            score_file.write(f"{note.base.get_original_text()}\t")
            responses = list(note.responses.items())
            scores: list[float] = []
            for model, response in responses:
                score = response.get_average()
                if score is None:
                    warn(f"No score found for {model} in note {note_id}")
                    continue
                if score < ACCEPT_THRESHOLD:
                    final_answer = await reflect_on_response(
                        model_code=response.model_full,
                        messages=response.messages,
                        correct_answer=note.base.core_detail,
                        score=score,
                    )
                    if final_answer == False:
                        continue # Error
                    if final_answer is not None:
                        response.answer = final_answer
                scores.append(score)
                scores_display = ";".join(f"{s}" for s in response.scores)
                score_file.write(f"{model}:{score:.2f}:{scores_display}\t")

            score_file.write(f"{len(responses)}\n")

            for model, response in responses:
                completion = {
                    "messages": [
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPTS.THINKING_SIMPLIFIED,
                        },
                        {"role": "user", "content": note.prompt},
                        {"role": "assistant", "content": response.answer},
                    ]
                }
                writer.write_line(completion)


if __name__ == "__main__":
    run(main())
