from train.models import ChineseGswPassage
from train.utils import JsonlReader, JsonlWriter
from tqdm import tqdm

PATHS = [
    "train/chinese-gushiwen/guwen/guwen0-1000.jsonl",
    "train/chinese-gushiwen/guwen/guwen1001-2000.jsonl",
]

with JsonlWriter("train/result/guwen-notes.jsonl") as f_out:
    for path in PATHS:
        with JsonlReader(path) as f:
            passages: list[ChineseGswPassage] = []
            for raw_passage in tqdm(f, desc="Extracting", unit="Passage"):
                if "remark" not in raw_passage:
                    continue
                passages.append(ChineseGswPassage.from_dict(raw_passage))
            for passage in passages:
                notes = passage.extract_notes()
                for note in notes:
                    f_out.write_line(note.to_dict())
