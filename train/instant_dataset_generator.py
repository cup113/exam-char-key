from json import loads, dumps
from models import Note

"""
PROMPT:
你是一位文言文翻译方向的 LLM 微调研究人员，现要生成多样化的微调模板以辅助进行模型微调。你的任务是：生成提问模板
要求：生成的微调模板应是一条通顺的语句，包含 {context} 和 {character}。
样例：在古文“{context}”中，{character}是什么意思？
请你生成类似这样的 5 个提问模板，尽量模仿各类人可能的提问语气。
"""

question_templates = [
    "请解释古文“{context}”中，“{character}”一字的含义。",
    "关于古文“{context}”，我想确认一下，“{character}”在这里具体指什么？",
    "读到“{context}”，我不明白这里的“{character}”是什么意思，能帮我解释一下吗？",
    "请给出古文“{context}”中，“{character}”在当前语境下的准确解释。",
    "对于古文“{context}”，“{character}”的最佳翻译或解释是什么？",
]

SYSTEM_PROMPT_FLASH = """你是一位高中语文老师，深入研究高考文言文词语解释。答案简短，并且不太过意译。一般可以给出一个精准解释，语境特殊时可以补充引申义。若涉及通假字，则需答：通“(通假字)”，(含义)。你需要简洁地回答用户的问题，除答案外不输出任何内容。"""
GUWEN_SAMPLE_INTERVAL = 10

with open("./train/result/textbook-notes.jsonl", "r", encoding="utf-8") as f:
    notes = [Note.from_dict(loads(line)) for line in f]

with open("./train/result/guwen-notes.jsonl", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i % GUWEN_SAMPLE_INTERVAL == 0:
            note = Note.from_dict(loads(line))
            if "\n" in note.core_detail:
                continue  # It's probably an error
            notes.append(Note.from_dict(loads(line)))

with open("./train/result/dataset-flash.jsonl", "w", encoding="utf-8") as f:
    for i, note in enumerate(notes):
        original_text = note.get_original_text()
        if original_text == note.context:
            continue  # it's probably a note to the title
        template = question_templates[i % len(question_templates)] + "请快速回答。"
        completion = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_FLASH},
                {
                    "role": "user",
                    "content": template.format(
                        context=note.context, character=original_text
                    ),
                },
                {"role": "assistant", "content": note.detail},
            ]
        }
        f.write(dumps(completion, ensure_ascii=False) + "\n")
