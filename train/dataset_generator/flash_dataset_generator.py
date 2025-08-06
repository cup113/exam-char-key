from train.models import Note
from train.utils import JsonlReader, JsonlWriter, SYSTEM_PROMPTS, IntermediateFiles
from random import shuffle

with JsonlReader(IntermediateFiles.NotesFiltered) as f:
    notes = [Note.from_dict(d) for d in f]

shuffle(notes)

with JsonlWriter(IntermediateFiles.DatasetFlash) as f:
    for i, note in enumerate(notes):
        original_text = note.get_original_text()
        template = SYSTEM_PROMPTS.QUESTION_TEMPLATE
        completion = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPTS.FLASH_SIMPLIFIED},
                {
                    "role": "user",
                    "content": template.format(
                        context=note.context, query=original_text
                    ),
                },
                {"role": "assistant", "content": note.detail},
            ]
        }
        f.write_line(completion)
