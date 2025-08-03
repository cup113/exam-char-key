from train.models import Note
from train.utils import IntermediateFiles, JsonlReader, JsonlWriter
from dataclasses import dataclass
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class FreqInfo:
    word: str
    textbook_freq: int
    dataset_freq: int
    query_freq: int
    notes: list[Note]

    def get_total_freq(self) -> int:
        return self.textbook_freq * 3 + self.dataset_freq + self.query_freq * 2

    @classmethod
    def create(cls, word: str) -> "FreqInfo":
        return FreqInfo(word=word, textbook_freq=0, dataset_freq=0, query_freq=0, notes=[])

    @staticmethod
    def from_dict(d: dict[str, str | int | list[Note]]) -> "FreqInfo": ...

    def to_dict(self): ...


with JsonlReader(IntermediateFiles.NotesTextbook) as f:
    notes_textbook = [Note.from_dict(line) for line in f]


with JsonlReader(IntermediateFiles.NotesModelTests) as f:
    notes_model_tests = [Note.from_dict(line) for line in f]


raw: "dict[str, FreqInfo]" = {}
for note in notes_textbook:
    original_text = note.get_original_text()
    if original_text not in raw:
        raw[original_text] = FreqInfo.create(original_text)
    raw[original_text].textbook_freq += 1
    raw[original_text].notes.append(note)

for note in notes_model_tests:
    original_text = note.get_original_text()
    if original_text not in raw:
        raw[original_text] = FreqInfo.create(original_text)
    raw[original_text].dataset_freq += 1
    raw[original_text].notes.append(note)

del raw[""] # Delete empty string
result = sorted([r for r in raw.values()], key=lambda r: r.get_total_freq(), reverse=True)

with JsonlWriter(IntermediateFiles.StatFrequency) as f:
    for r in result:
        f.write_line(r.to_dict())
