"""
*** Please open dev server first! ***
Should take 10s * 1080 notes = 10800s = 3h without cache
"""

from json import loads
from time import sleep, time
from tqdm import tqdm
from httpx import Client
from train.models import Note, PromptRaw
from train.utils import SYSTEM_PROMPTS, IntermediateFiles, JsonlReader, JsonlWriter
from random import shuffle

(TEXTBOOK_SAMPLE_INTERVAL, TEXTBOOK_SAMPLE_START) = (4, 1)
CRAWL_INTERVAL = 10
CRAWL_MIN_INTERVAL = 1

client = Client()
notes: list[Note] = []


def get_completion(note: Note, i: int):
    original_text = note.get_original_text()

    response = client.get(
        f"http://localhost:4122/api/zdic?q={original_text}", timeout=20
    )
    if response.status_code == 200:
        response_json = loads(response.text)
        zdic_prompt: str = response_json["zdic_prompt"]
        cached: bool = response_json["cached"]

    else:
        zdic_prompt = ""
        cached = True

    template = SYSTEM_PROMPTS.QUESTION_TEMPLATE + "请按要求仔细思考后回答。"
    user_prompt = (
        template.format(context=note.context, query=original_text) + zdic_prompt
    )
    completion: PromptRaw = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPTS.THINKING},
            {"role": "user", "content": user_prompt},
        ],
        "note": note.to_dict(),
    }
    return completion, cached


with JsonlReader(IntermediateFiles.NotesFiltered) as f:
    textbook_acc = TEXTBOOK_SAMPLE_INTERVAL
    for i, line in enumerate(f):
        note = Note.from_dict(line)
        is_textbook = len(note.name_passage) >= 1
        if is_textbook:
            textbook_acc += 1
            textbook_acc %= TEXTBOOK_SAMPLE_INTERVAL
            if textbook_acc != TEXTBOOK_SAMPLE_START:
                continue
        notes.append(note)


shuffle(notes)


with JsonlWriter(IntermediateFiles.DatasetThinkingRaw) as f:
    for i, note in enumerate(tqdm(notes, unit="note")):
        start_time = time()
        completion, cached = get_completion(note, i)

        f.write_line(completion)

        if not cached:
            sleep(max(start_time + CRAWL_INTERVAL - time(), CRAWL_MIN_INTERVAL))
