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
    messages: list[BatchRequestMessage]
    score: float


@dataclass
class ScoredNote:
    base: Note
    prompt: str
    response: ScoredResponse


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
    id_match = match(r"request-tb-(\d{4})", api_response["custom_id"])
    if not id_match:
        return
    note_id = int(id_match.group(1).lstrip("0") or "0")

    if not get_answer(content):
        single_line_content = content.replace("\n", "")
        warn(f"Response is incomplete: {single_line_content}")
        return

    data[note_id].response = ScoredResponse(
        answer=content,
        messages=[{"role": "assistant", "content": content}],
        score=0.88,
    )


def add_message(batch_request: BatchRequest):
    custom_id_match = match(r"request-tb-(\d+)", batch_request["custom_id"])
    assert custom_id_match is not None, "Invalid custom_id"
    messages = batch_request["body"]["messages"]
    note_id = int(custom_id_match.group(1).lstrip("0") or "0")
    data[note_id].response.messages.extend(reversed(messages))
    data[note_id].response.messages.reverse()


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
    id_match = match(r"request-tb-(\d{4})-ev", api_response["custom_id"])
    if not id_match:
        return

    note_id = int(id_match.group(1).lstrip("0") or "0")
    if note_id not in data:
        warn(f"Note {note_id} not found in dataset")
        return

    data[note_id].response.score = score


with JsonlReader(IntermediateFiles.DatasetThinkingRaw) as reader:
    for i, line in enumerate(reader):
        prompt_raw: PromptRaw = line
        user_prompt = prompt_raw["messages"][1]["content"]
        data[i] = ScoredNote(
            Note.from_dict(prompt_raw["note"]),
            user_prompt,
            ScoredResponse("", [], 0.88),
        )


with JsonlReader(IntermediateFiles.CompletionBatchThinking) as reader:
    for line in reader:
        add_data(line)


with JsonlReader(IntermediateFiles.CompletionBatchEvaluationThinking) as reader:
    for line in reader:
        add_score(line)

with JsonlReader(IntermediateFiles.PromptDatasetThinking) as reader:
    for line in reader:
        add_message(line)


async def main():
    with JsonlWriter(IntermediateFiles.DatasetThinking) as writer, open(
        "./train/result/dataset-thinking-evaluation-scores.txt", "w", encoding="utf-8"
    ) as score_file:
        QUALITY_THRESHOLD = 0.89
        for note_id, note in tqdm(data.items()):
            score_file.write(f"{note.base.get_original_text()}\t")
            response = data[note_id].response
            score = response.score
            if score < QUALITY_THRESHOLD:
                response.answer = ""
            score_file.write(f"{score:.2f}\t")

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
