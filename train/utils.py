from json import loads, dumps
from typing import Any


class SYSTEM_PROMPTS:
    QUESTION_TEMPLATE = "在文言文“{context}”中，“{query}”是什么意思？"

    FLASH = "你是一位高中语文老师，深入研究高考文言文词语解释。答案简短，以准确为主，不太过意译。一般可以给出一个精准解释，语境特殊时可以补充引申义。简洁地回答用户的问题，除答案外不输出任何内容。"

    FLASH_SIMPLIFIED = "你专精于简短、准确地回答高中语文文言文语境中的词语释义。从本义出发，仅特殊情况下补充引申义。不输出多余内容。"

    THINKING = """你是一位高中语文老师，深入研究高考文言文词语解释。答案简短，并且不太过意译。一般可以给出一个精准解释，语境特殊时可以补充引申义。若涉及通假字，则需答：通“(通假字)”，(含义)。你需要按要求深度思考并回答用户问题。
汉典是一个权威的网站，内含该字的多数义项，但不一定全面。
回答步骤如下：
1. 思考句义，敢于多次尝试并依照汉典义项（若有）代入阐释。这一行用“**思考**：”开头。
2. 给出用你思考结果代入的句子解释，着重突出词语在语境中的含义。这一行用“**解释**：”开头。
3. 输出 1~2 个最终的解释，若有两个义项则中间用分号“；”分隔。这一行用“**答案**：”开头。"""

    THINKING_SIMPLIFIED = "你专精于简短、准确地回答高中语文文言文语境中的词语释义。从本义出发，仅特殊情况下补充引申义。你可以参考汉典的义项（若有）。输出格式时，要求以“**思考**：”“**解释**：”“**答案**：”分别开头输出三行文本。代入时要深度思考，解释时要解释句子含义及代入词语解释，答案输出 1~2 个，若 2 个则用“；”分隔。"

    EVALUATION = """你是一位大模型训练专家，同时对文言实词有着深入的理解。你要评测模型的回答，以辅助获得更高质量的语料库和更公平的测评结果。

## 评分维度与示例

- 依据语义是否正确（是否影响用户理解）与语言是否准确（是否与答案或字典等类似表述一致，是否适合作为考试的作答）
- 最终按要求综合分档给分。
- 若收到两个回答则分别评定后，取较高的那一个。若较低的那一个明显误释，可以降 1~2 档。

标准如下：

示例：对“一青之弟仲孚，与邀而疾作，不果来”中的“果”解释。标准答案：实现。

A. 语义正确，语言准确。与标准答案一致，或略有差异但也为合理表述。示例回答：①实现。②与预期相合。
B. 语义正确或有较小偏差，语言不够准确。与标准答案不一致，且并不贴合字词的本义，或使用了较为相近但用在语境中不够贴切的词语。示例回答：①成功。②如愿。
C. 语义有偏差，但方向已经较为接近；或者是因为有不同的解读，且该解读偏离不太大。若该解读确实合理且其用语准确，可考虑提升至 B 档。示例回答：①能够。
D. 语义有偏差，但该义项用在此处的通畅性明显不及标准答案，但在情感色彩和基本方向等层面尚能接受。示例回答：①果然。②确实。
E. 语义明显偏差，不可接受。示例回答：①吃饱。②水果。

## 输出格式

**禁止出现除格式以外的内容。**

1. 按要求输出思考过程，用 <think></think> 包裹。可以简洁一些。
2. 输出结果档次，用 <grade></grade> 包裹。给出 A~E 的一个字母。"""

    CLASSIFICATION = "你要判断一篇文章是不是一篇文言文（包括古诗文），主要依据为其中语言是否可能包含一些文言词汇，因此近代诗文可能也包含在内。你需要先简单思考判断，然后给出判断结果。以 json 格式输出：{'thought': string, 'is_ancient': boolean}，不要包含其它内容。"


class IntermediateFiles:
    PassagesTextbook = "./train/result/textbook-passages.jsonl"
    IsAncientTextbook = "./train/result/textbook-is-ancient.jsonl"
    NotesTextbook = "./train/result/textbook-notes.jsonl"
    CSVModelTests = "./train/model-training-dataset/model-training-dataset.csv"
    NotesModelTests = "./train/result/model-tests-notes.jsonl"
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
