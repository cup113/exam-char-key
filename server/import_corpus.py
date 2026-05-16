import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server.db_helper import init_db, ingest_corpus_lines


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_corpus.py <jsonl_path>")
        sys.exit(1)

    jsonl_path = Path(sys.argv[1])
    if not jsonl_path.exists():
        print(f"File not found: {jsonl_path}")
        sys.exit(1)

    init_db()

    with jsonl_path.open("r", encoding="utf-8") as f:
        count = ingest_corpus_lines(f)

    print(f"Imported {count} corpus entries from {jsonl_path}")


if __name__ == "__main__":
    main()
