from datetime import date
from typing import Any

ANKI_API_URL = "https://anki.cup11.top/api/generate"
ANKI_BASE_URL = "https://anki.cup11.top"


def build_export_document(records: list[dict[str, Any]]) -> dict[str, Any]:
    today = date.today().isoformat()
    now = f"{date.today().isoformat()} 00:00:00"

    doc_records: list[dict[str, Any]] = []
    for r in records:
        context = r.get("context", "")
        word = r.get("word", "")
        front = context
        if word and word in front:
            front = front.replace(word, f"<strong>{word}</strong>")
        front = f"<p>{front}</p>"
        back = f"<p>{r.get('quick_answer', '')}</p>"

        doc_records.append(
            {
                "id": str(r["id"]),
                "level": "-",
                "front": front,
                "back": back,
                "additions": [],
            }
        )

    return {
        "version": 4,
        "title": f"Chinese Ancient {today}",
        "records": doc_records,
        "sections": [],
        "footer": "",
        "deckType": "one-side",
        "createdAt": now,
        "modifiedAt": now,
    }
