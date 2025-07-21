from models import ChineseGswPassage
from json import loads, dumps
from tqdm import tqdm

PATHS = [
    "train/chinese-gushiwen/guwen/guwen0-1000.jsonl",
    "train/chinese-gushiwen/guwen/guwen1001-2000.jsonl",
]

with open("train/result/guwen-notes.jsonl", "w", encoding="utf-8") as f_out:
    for path in PATHS:
        with open(path, "r", encoding="utf-8") as f:
            passages: list[ChineseGswPassage] = []
            for line in tqdm(f, desc="Extracting", unit="Passage"):
                raw_passage: dict[str, str] = loads(line)
                if "remark" not in raw_passage:
                    continue
                passages.append(ChineseGswPassage.from_dict(loads(line)))
            for passage in passages:
                notes = passage.extract_notes()
                for note in notes:
                    f_out.write(dumps(note.to_dict(), ensure_ascii=False) + "\n")
