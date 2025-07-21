"""
*** Please open dev server first! ***
Should take ~4h unless cached
"""

from json import loads, dumps
from time import sleep, time
from tqdm import tqdm
from httpx import Client
from models import Note
from instant_dataset_generator import question_templates

SYSTEM_PROMPT_THINKING = """你是一位高中语文老师，深入研究高考文言文词语解释。答案简短，并且不太过意译。一般可以给出一个精准解释，语境特殊时可以补充引申义。若涉及通假字，则需答：通“(通假字)”，(含义)。你需要按要求深度思考并回答用户问题。
汉典是一个权威的网站，内含该字的多数义项，但不一定全面。
回答步骤如下：
1. 思考句义，敢于多次尝试并依照汉典义项（若有）代入阐释。用<think></think>标签包裹。换行。
2. 给出用你思考结果代入的句子解释。用<explain></explain>标签包裹。换行。
3. 输出 1~3 个最终的解释，用<answers></answers>包裹，每个义项之间用分号“；”分隔。"""

TEXT_SAMPLE_INTERVAL = 5
GUWEN_SAMPLE_INTERVAL = 25
SAMPLE_START = (
    2  # (0~4) To ensure dataset diversity, avoiding overlapping with Instant.
)

CRAWL_INTERVAL = 10
CRAWL_MIN_INTERVAL = 1

client = Client()
notes: list[Note] = []


def get_completion(note: Note, i: int):
    original_text = note.get_original_text()
    if original_text == note.context:
        return None, True  # it's probably a note to the title

    response = client.get(f"http://localhost:4122/api/zdic?q={original_text}")
    if response.status_code == 200:
        response_json = loads(response.text)
        zdic_prompt: str = response_json["zdic_prompt"]
        cached: bool = response_json["cached"]

    else:
        zdic_prompt = ""
        cached = True

    template = (
        question_templates[i % len(question_templates)] + "请按要求仔细思考后回答。"
    )
    user_prompt = (
        template.format(context=note.context, character=original_text) + zdic_prompt
    )
    completion = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_THINKING},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": note.detail},
        ]
    }
    return completion, cached


def is_short_note(note: Note) -> bool:
    """If a note is too long, then it's probably not a 'character explanation' task."""
    MAX_CHARACTERS_ALLOWED = 4
    return len(note.get_original_text()) <= MAX_CHARACTERS_ALLOWED


with open("./train/result/textbook-notes.jsonl", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i % TEXT_SAMPLE_INTERVAL == SAMPLE_START:
            note = Note.from_dict(loads(line))
            if is_short_note(note):
                notes.append(note)

with open("./train/result/guwen-notes.jsonl", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i % GUWEN_SAMPLE_INTERVAL == SAMPLE_START:
            note = Note.from_dict(loads(line))
            if is_short_note(note):
                notes.append(note)

with open("./train/result/dataset-thinking-raw.jsonl", "w", encoding="utf-8") as f:
    for i, note in enumerate(tqdm(notes, unit="note")):
        start_time = time()
        completion, cached = get_completion(note, i)

        if completion is None:
            continue

        f.write(dumps(completion, ensure_ascii=False) + "\n")
        f.flush()

        if not cached:
            sleep(max(start_time + CRAWL_INTERVAL - time(), CRAWL_MIN_INTERVAL))
