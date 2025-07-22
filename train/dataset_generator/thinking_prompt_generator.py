"""
*** Please open dev server first! ***
Should take ~4h unless cached
"""

from json import loads
from time import sleep, time
from tqdm import tqdm
from httpx import Client
from train.models import Note, PromptRaw
from train.utils import sample_question_template, SYSTEM_PROMPTS, IntermediateFiles, JsonlReader, JsonlWriter

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

    template = sample_question_template(i) + "请按要求仔细思考后回答。"
    user_prompt = (
        template.format(context=note.context, character=original_text) + zdic_prompt
    )
    completion: PromptRaw = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPTS.THINKING},
            {"role": "user", "content": user_prompt},
        ],
        "note": note.to_dict(),
    }
    return completion, cached

with JsonlReader(IntermediateFiles.NotesTextbook) as f:
    for i, line in enumerate(f):
        if i % TEXT_SAMPLE_INTERVAL == SAMPLE_START:
            note = Note.from_dict(loads(line))
            if note.is_short_note():
                notes.append(note)

with JsonlReader(IntermediateFiles.NotesGuwen) as f:
    for i, line in enumerate(f):
        if i % GUWEN_SAMPLE_INTERVAL == SAMPLE_START:
            note = Note.from_dict(loads(line))
            if note.is_short_note():
                notes.append(note)

with JsonlWriter(IntermediateFiles.DatasetThinkingRaw) as f:
    for i, note in enumerate(tqdm(notes, unit="note")):
        start_time = time()
        completion, cached = get_completion(note, i)

        if completion is None:
            continue

        f.write_line(completion)

        if not cached:
            sleep(max(start_time + CRAWL_INTERVAL - time(), CRAWL_MIN_INTERVAL))
