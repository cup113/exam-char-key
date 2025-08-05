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
from asyncio import run
from tqdm import tqdm


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
        QUALITY_THRESHOLD = 0.89
        for note_id, note in tqdm(data.items()):
            score_file.write(f"{note.base.get_original_text()}\t")
            responses = list(note.responses.items())
            scores: list[float] = []
            for model, response in responses:
                score = response.get_average()
                if score is None:
                    warn(f"No score found for {model} in note {note_id}")
                    continue
                if score < QUALITY_THRESHOLD:
                    response.answer = ""
                scores.append(score)
                scores_display = ";".join(f"{s}" for s in response.scores)
                score_file.write(f"{model}:{score:.2f}:{scores_display}\t")

            score_file.write(f"{len(responses)}\n")

            for model, response in responses:
                if response.answer == "":
                    continue
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
