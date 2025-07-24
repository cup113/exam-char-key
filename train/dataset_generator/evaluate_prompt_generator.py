from train.models import BatchRequest, Note, PromptRaw, CompletionApiResponse
from train.utils import SYSTEM_PROMPTS, JsonlReader, JsonlWriter, IntermediateFiles
from typing import TypedDict
from re import match, DOTALL
from warnings import warn


def get_evaluation_prompt(
    answer_stu: str,
    note: Note,
    completion_custom_id: str,
    model_index_id: int,
    model: str,
) -> BatchRequest:
    user_prompt = f"上下文：{note.context}\n需解释的词语：{note.get_original_text()}\n标准答案：{note.core_detail}\n学生答案：{answer_stu}\n请按要求评分并按格式输出。"

    return {
        "custom_id": f"{completion_custom_id}-ev-{model_index_id}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": model,
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
        raw_data.update([(f"request-tb-{i + 1:04d}", note)])


class EvaluationFiles(TypedDict):
    filename: str
    model: str


EVALUATION_FILES: list[EvaluationFiles] = [
    {
        "filename": IntermediateFiles.PromptEvaluationThinkingDataset1,
        "model": "qwen-plus-latest",
    },
    {
        "filename": IntermediateFiles.PromptEvaluationThinkingDataset2,
        "model": "qwen-long-latest",
    },
]

BATCH_FILENAMES = [
    IntermediateFiles.CompletionBatchThinking1,
    IntermediateFiles.CompletionBatchThinking2,
]


for out_no, evaluation_file in enumerate(EVALUATION_FILES):
    with JsonlWriter(evaluation_file["filename"]) as writer:
        for filename in BATCH_FILENAMES:
            with JsonlReader(filename) as fr:
                for i, line in enumerate(fr):
                    completion: CompletionApiResponse = line
                    raw_answer = completion["response"]["body"]["choices"][0][
                        "message"
                    ]["content"]
                    raw_match = match(
                        r"(.*?)\<answers\>(.*?)\<\/answers\>(.*?)", raw_answer, DOTALL
                    )
                    note = raw_data[completion["custom_id"]]

                    if raw_match is None:
                        if "<answers>" in raw_answer:
                            print(f"{completion['custom_id']} lack end tag </answers>")
                        else:
                            warn(f"Answer to {note.to_dict()} unmatched: {raw_answer}")
                        continue

                    answer = raw_match.groups()[1].strip()
                    writer.write_line(
                        get_evaluation_prompt(
                            answer,
                            note,
                            completion["custom_id"],
                            out_no,
                            evaluation_file["model"],
                        )
                    )
