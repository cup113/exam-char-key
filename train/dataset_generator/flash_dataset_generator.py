from train.models import Note
from train.utils import JsonlReader, JsonlWriter, SYSTEM_PROMPTS, IntermediateFiles
from random import shuffle
from csv import DictReader

# 读取课本数据
with JsonlReader(IntermediateFiles.NotesTextbook) as f:
    notes = [Note.from_dict(d) for d in f]

with open(IntermediateFiles.ModelTests, "r", encoding="utf-8") as csv_file:
    reader = DictReader(csv_file)
    for i, row in enumerate(reader):
        model_test_note = Note.from_dict(
            {
                "name_passage": "",
                "context": row["context"],
                "query": row["query"],
                "detail": row["answer"],
                "core_detail": row["answer"],
                "index_range": [
                    row["context"].find(row["query"]),
                    row["context"].find(row["query"]) + len(row["query"]),
                ],
            }
        )
        notes.append(model_test_note)

shuffle(notes)

with JsonlWriter(IntermediateFiles.DatasetFlash) as f:
    for i, note in enumerate(notes):
        original_text = note.get_original_text()
        if original_text == note.context:
            continue  # it's probably a note to the title
        if len(note.core_detail) >= 15 or len(original_text) >= 4:
            continue  # Too long
        template = SYSTEM_PROMPTS.QUESTION_TEMPLATE + "请快速回答。"
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
