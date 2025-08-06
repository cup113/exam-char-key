from train.models import BatchRequest, Note, PromptRaw, CompletionApiResponse
from train.utils import SYSTEM_PROMPTS, JsonlReader, JsonlWriter, IntermediateFiles
from typing import TypedDict
from re import match, DOTALL
from warnings import warn


def get_evaluation_prompt(
    answer_stu: str,
    note: Note,
    completion_custom_id: str,
) -> BatchRequest:
    user_prompt = f"题目：“{note.context}”中“{note.get_original_text()}”的含义。\n标准答案为：{note.core_detail}\n学生答案为：{answer_stu}\n请按要求评分并按格式输出。"

    return {
        "custom_id": f"{completion_custom_id}-ev",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "qwen-long-latest",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPTS.EVALUATION},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "top_p": 0.95,
        },
    }


raw_data: dict[str, Note] = {}


with JsonlReader(IntermediateFiles.DatasetThinkingRaw) as reader:
    for i, line in enumerate(reader):
        prompt_raw: PromptRaw = line
        note = Note.from_dict(prompt_raw["note"])
        raw_data.update([(f"request-tb-{i:04d}", note)])


class EvaluationFiles(TypedDict):
    filename: str
    model: str


with JsonlWriter(IntermediateFiles.PromptEvaluationThinkingDataset) as writer:
    with JsonlReader(IntermediateFiles.CompletionBatchThinking) as fr:
        for i, line in enumerate(fr):
            completion: CompletionApiResponse = line
            raw_answer = completion["response"]["body"]["choices"][0]["message"][
                "content"
            ]
            raw_match = match(r".*?\*\*答案\*\*[:：]\s*(.*)", raw_answer, DOTALL)
            note = raw_data[completion["custom_id"]]

            if raw_match is None:
                warn(f"Answer to {note.to_dict()} unmatched: {raw_answer}")
                continue

            answer = raw_match.group(1).strip()
            writer.write_line(
                get_evaluation_prompt(
                    answer,
                    note,
                    completion["custom_id"],
                )
            )
