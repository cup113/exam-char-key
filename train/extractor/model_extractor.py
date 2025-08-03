from train.utils import IntermediateFiles, JsonlWriter
from train.models import Note
from csv import DictReader

notes: list[Note] = []

with open(IntermediateFiles.CSVModelTests, "r", encoding="utf-8") as csv_file:
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

with JsonlWriter(IntermediateFiles.NotesModelTests) as jsonl_writer:
    for note in notes:
        jsonl_writer.write_line(note.to_dict())
