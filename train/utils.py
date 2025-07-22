from json import loads, dumps
from typing import Any

# Common prompt templates
QUESTION_TEMPLATES = [
    "请解释古文“{context}”中，“{character}”一字的含义。",
    "关于古文“{context}”，我想确认一下，“{character}”在这里具体指什么？",
    "读到“{context}”，我不明白这里的“{character}”是什么意思，能帮我解释一下吗？",
    "请给出古文“{context}”中，“{character}”在当前语境下的准确解释。",
    "对于古文“{context}”，“{character}”的最佳翻译或解释是什么？",
]


def sample_question_template(index: int):
    return QUESTION_TEMPLATES[index % len(QUESTION_TEMPLATES)]


class SYSTEM_PROMPTS:
    FLASH = "你是一位高中语文老师，深入研究高考文言文词语解释。答案简短，以准确为主，不太过意译。一般可以给出一个精准解释，语境特殊时可以补充引申义。简洁地回答用户的问题，除答案外不输出任何内容。"

    THINKING = """你是一位高中语文老师，深入研究高考文言文词语解释。答案简短，并且不太过意译。一般可以给出一个精准解释，语境特殊时可以补充引申义。若涉及通假字，则需答：通“(通假字)”，(含义)。你需要按要求深度思考并回答用户问题。
汉典是一个权威的网站，内含该字的多数义项，但不一定全面。
回答步骤如下：
1. 思考句义，敢于多次尝试并依照汉典义项（若有）代入阐释。用<think></think>标签包裹。换行。
2. 给出用你思考结果代入的句子解释。用<explain></explain>标签包裹。换行。
3. 输出 1~3 个最终的解释，用<answers></answers>包裹，每个义项之间用分号“；”分隔。"""

    EVALUATION = """你是一位高中语文文言文实词解释阅卷员，你将要对学生的回答进行批改。
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

1. 输出思考过程，用 <think></think> 包裹。为使评分尽量准确，要充分思考，不过可以使用较为简洁的语言。结束后换行。
2. 输出结果分数，用 <score></score> 包裹。内部只包含一个 0~10 的数字。
"""

    CLASSIFICATION = "你要判断一篇文章是不是一篇文言文（包括古诗文），主要依据为其中语言是否可能包含一些文言词汇，因此近代诗文可能也包含在内。你需要先简单思考判断，然后给出判断结果。以 json 格式输出：{'thought': string, 'is_ancient': boolean}，不要包含其它内容。"

    QUESTION_TEMPLATES_GENERATION = """你是一位文言文翻译方向的 LLM 微调研究人员，现要生成多样化的微调模板以辅助进行模型微调。你的任务是：生成提问模板
要求：生成的微调模板应是一条通顺的语句，包含 {context} 和 {character}。
样例：在古文“{context}”中，{character}是什么意思？
请你生成类似这样的 5 个提问模板，尽量模仿各类人可能的提问语气。"""


class IntermediateFiles:
    PassagesTextbook = "./train/data/textbook-passages.jsonl"
    IsAncientTextbook = "./train/data/textbook-is-ancient.jsonl"
    NotesTextbook = "./train/result/textbook-notes.jsonl"
    NotesGuwen = "./train/result/guwen-notes.jsonl"
    StatFrequency = "./train/result/word-frequency.jsonl"
    DatasetFlash = "./train/result/dataset-flash.jsonl"
    DatasetThinking = "./train/result/dataset-thinking.jsonl"
    DatasetThinkingRaw = "./train/result/dataset-thinking-raw.jsonl"
    PromptDatasetThinking1 = "./train/result/dataset-thinking-prompt-1.jsonl"
    PromptDatasetThinking2 = "./train/result/dataset-thinking-prompt-2.jsonl"
    PromptEvaluationThinkingDataset1 = (
        "./train/result/dataset-thinking-evaluation-prompt-1.jsonl"
    )
    PromptEvaluationThinkingDataset2 = (
        "./train/result/dataset-thinking-evaluation-prompt-2.jsonl"
    )
    CompletionBatchThinking1 = (
        "./train/result/dataset-thinking-batch-completion-1.jsonl"
    )
    CompletionBatchThinking2 = (
        "./train/result/dataset-thinking-batch-completion-2.jsonl"
    )
    CompletionBatchEvaluationThinking1 = (
        "./train/result/dataset-evaluation-thinking-batch-completion-1.jsonl"
    )
    CompletionBatchEvaluationThinking2 = (
        "./train/result/dataset-evaluation-thinking-batch-completion-2.jsonl"
    )


class JsonlReader:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def __enter__(self):
        self.file = open(self.file_path, "r", encoding="utf-8")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        self.file.close()

    def __iter__(self):
        return self

    def __next__(self) -> Any:
        line = self.file.readline()
        if not line:
            raise StopIteration
        return loads(line)


class JsonlWriter:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def __enter__(self):
        self.file = open(self.file_path, "w", encoding="utf-8")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        self.file.close()

    def write_line(self, data: Any) -> None:
        self.file.write(dumps(data, ensure_ascii=False) + "\n")
