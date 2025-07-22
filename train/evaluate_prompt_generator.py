from models import BatchRequest, Note, PromptRaw
from json import loads, dumps
from re import match
from warnings import warn

SYSTEM_PROMPT = """你是一位高中语文文言文实词解释阅卷员，你将要对学生的回答进行批改。
你会收到原句、需要解释的字、标准答案、学生答案。

## 评分标准

> 以“一青之弟仲孚，与邀而疾作，不果来”中的“果”（答案：实现）为例：

1. 定档：按照考生给出的第一个解释标定档次。
   - A 档（10 分）：与标准答案完全贴合。示例回答：实现、与预期相合。
   - B 档（7 分）：与标准答案基本贴合，词性正确，用词可能不太规范，在考试中很可能得分。示例回答：成功。
   - C 档（3 分）：与标准答案有所差异，但总体方向正确，词性可能错误，不影响整体理解但在考试中一般不得分。示例回答：果然、终究。
   - D 档（0 分）：与标准答案完全无关，总体方向错误，影响了整体理解，具有误导性。示例回答：吃饱、结果。
2. 细节：对于 ABC 档的回答，按照考生给出的补充解释（第二、三个解释）决定具体分数。若考生的补充解释只是回答用法（如“作动词”），对分数无影响。
   - 若考生只给出了一个解释，则按照上述档次给分。例如：
     - 答“实现”，给满 10 分。
     - 答“果然”，给 3 分。
   - 若考生给出了两个解释，则根据第二个解释的档次适当调整分数（每高一档加 1 分，每低一档减 1 分）。例如：
     - 答“实现；成功”，在 A 档基础上扣 1 分（补充解释为 B 档），给 9 分；
     - 答“成功；结果”，在 B 档基础上扣 2 分（补充解释为 D 档），给 5 分；
     - 答“成功；实现”，在 B 档基础上加 1 分（补充解释为 A 档），给 8 分。
   - 若考生给出了三个解释，则根据第二、三个解释的档次适当调整分数（第二解释同上，第三解释可适当缩小分差）。例如：
     - 答“实现；终究；果然”，在 A 档基础上扣 3 分（两补充解释均为 C 档，第二解释 -2，第三解释 -1），给 7 分。
     - 答“果然；成功；结果”，在 C 档基础上加 1 分（第二解释为 B 档，第三解释为 D 档，以第二解释 +1 为主），给 4 分。

## 输出格式

**禁止出现除格式以外的内容。**

1. 输出思考过程，用 <think></think> 包裹。因为你的评分要尽可能准确，所以思考过程可以详细。结束后换行。
2. 输出结果分数，用 <score></score> 包裹。内部只包含一个 0~10 的数字。
"""


def get_evaluation_prompt(answer_stu: str, note: Note, i: int) -> BatchRequest:
    user_prompt = f"上下文：{note.context}。\n需解释的词语：{note.get_original_text()}。\n标准答案：{note.core_detail}。\n学生答案：{answer_stu}。\n请按要求评分并按格式输出。"

    return {
        "custom_id": f"request-ef-{i+1}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "qwen-turbo",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "top_p": 0.95,
        },
    }


raw_data: dict[str, Note] = {}


with open("./train/result/dataset-thinking-raw.jsonl", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        prompt_raw: PromptRaw = loads(line)
        note = Note.from_dict(prompt_raw["note"])
        raw_data.update(
            [(f"request-tb-{i + 1}", note), (f"request-tb-{i + 5001}", note)]
        )


with open(
    "./train/result/dataset-thinking-evaluation-prompt-1", "w", encoding="utf-8"
) as fw:
    FILENAMES = [
        "./train/result/dataset-thinking-batch-completion-1.jsonl",
        "./train/result/dataset-thinking-batch-completion-2.jsonl",
    ]

    for filename in FILENAMES:
        with open(filename, "r", encoding="utf-8") as fr:
            for i, line in enumerate(fr):
                completion = loads(line)
                raw_answer = completion["response"]["body"]["choices"][0]["message"][
                    "content"
                ]
                raw_match = match(r"<answer>([\s\S]+)</answer>", raw_answer)
                if raw_match is None:
                    warn(f"Answer unmatched: {raw_answer}")
                    continue
                answer = raw_match.groups()[1]
                note = raw_data[completion["custom_id"]]
                fw.write(
                    dumps(get_evaluation_prompt(answer, note, i), ensure_ascii=False)
                    + "\n"
                )
