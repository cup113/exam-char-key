import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server.db_helper import init_db, save_corpus


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_corpus.py <jsonl_path>")
        sys.exit(1)

    jsonl_path = Path(sys.argv[1])
    if not jsonl_path.exists():
        print(f"File not found: {jsonl_path}")
        sys.exit(1)

    init_db()

    count = 0
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            word = entry.get("word", "")
            notes = entry.get("notes", [])
            for note in notes:
                name_passage = note.get("name_passage", "").strip()
                context = note.get("context", "")
                detail = note.get("detail", "")
                if name_passage:
                    type_ = "textbook"
                else:
                    type_ = "mock_exam"
                save_corpus(type_=type_, context=context, word=word, answer=detail)
                count += 1

    print(f"Imported {count} corpus entries from {jsonl_path}")


if __name__ == "__main__":
    main()
