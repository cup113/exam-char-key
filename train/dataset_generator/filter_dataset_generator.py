from train.utils import JsonlReader, JsonlWriter, IntermediateFiles
from train.models import Note, CompletionApiResponse

def process_completion(response: CompletionApiResponse) -> bool:
    content = response["response"]["body"]["choices"][0]["message"]["content"]
    return "<answer>适合</answer>" in content

with JsonlReader(IntermediateFiles.NotesTextbook) as f:
    notes = [Note.from_dict(line) for line in f]

with JsonlReader(IntermediateFiles.NotesModelTests) as f:
    notes.extend(Note.from_dict(line) for line in f)

filtered_out_indices: list[int] = []

with JsonlReader(IntermediateFiles.CompletionFilter) as f:
    for i, line in enumerate(f):
        accepted = process_completion(line)
        if not accepted:
            filtered_out_indices.append(i)

filtered_notes = [note for i, note in enumerate(notes) if i not in filtered_out_indices and note.is_short_note() and len(note.core_detail) < 15]

with JsonlWriter(IntermediateFiles.NotesFiltered) as f:
    for note in filtered_notes:
        f.write_line(note.to_dict())
