from train.models import Note
from train.utils import JsonlReader, JsonlWriter, sample_question_template, SYSTEM_PROMPTS
from random import shuffle

GUWEN_SAMPLE_INTERVAL = 5

with JsonlReader("./train/result/textbook-notes.jsonl") as f:
    notes = [Note.from_dict(d) for d in f]

with JsonlReader("./train/result/guwen-notes.jsonl") as f:
    for i, d in enumerate(f):
        if i % GUWEN_SAMPLE_INTERVAL == 0:
            note = Note.from_dict(d)
            if "\n" in note.core_detail or note.is_title_note() or not note.is_short_note():
                continue  # It's probably an error / unsuitable for training
            notes.append(note)

shuffle(notes)

with JsonlWriter("./train/result/dataset-flash.jsonl") as f:
    for i, note in enumerate(notes):
        original_text = note.get_original_text()
        if original_text == note.context:
            continue  # it's probably a note to the title
        template = sample_question_template(i) + "请快速回答。"
        completion = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPTS.FLASH},
                {
                    "role": "user",
                    "content": template.format(
                        context=note.context, character=original_text
                    ),
                },
                {"role": "assistant", "content": note.detail},
            ]
        }
        f.write_line(completion)
