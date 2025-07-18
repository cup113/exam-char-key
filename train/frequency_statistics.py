from models import Note
from json import loads, dumps
from dataclasses import dataclass
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class FreqInfo:
    word: str
    textbook_freq: int
    guwen_freq: int
    query_freq: int
    notes: list[Note]

    def get_total_freq(self) -> int:
        return self.textbook_freq * 6 + self.guwen_freq + self.query_freq * 3

    @classmethod
    def create(cls, word: str) -> "FreqInfo":
        return FreqInfo(word=word, textbook_freq=0, guwen_freq=0, query_freq=0, notes=[])

    def to_dict(self): ...


with open("./train/result/textbook-notes.jsonl", "r", encoding="utf-8") as f:
    notes_textbook = [Note.from_dict(loads(line)) for line in f]


with open("./train/result/guwen-notes.jsonl", "r", encoding="utf-8") as f:
    notes_guwen = [Note.from_dict(loads(line)) for line in f]


raw: "dict[str, FreqInfo]" = {}
for note in notes_textbook:
    original_text = note.get_original_text()
    if original_text not in raw:
        raw[original_text] = FreqInfo.create(original_text)
    raw[original_text].textbook_freq += 1
    raw[original_text].notes.append(note)

for note in notes_guwen:
    original_text = note.get_original_text()
    if original_text not in raw:
        raw[original_text] = FreqInfo.create(original_text)
    raw[original_text].guwen_freq += 1
    raw[original_text].notes.append(note)

del raw[""] # Delete empty string
result = sorted([r for r in raw.values()], key=lambda r: r.get_total_freq(), reverse=True)

with open("./train/result/word-frequency.jsonl", "w", encoding="utf-8") as f:
    for r in result:
        f.write(dumps(r.to_dict(), ensure_ascii=False) + "\n")
