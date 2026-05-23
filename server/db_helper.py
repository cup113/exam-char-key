import json
import sqlite3
from collections.abc import Iterable
from datetime import date
from uuid import uuid4

from config import settings
from schema import init_db as schema_init_db


class Database:
    def __init__(self, db_path: str | None = None):
        self._db_path = db_path or settings.DB_PATH

    def init_db(self):
        schema_init_db(self._db_path)

    def check_and_decrease_quota(
        self, identifier: str, limit: int, count: int = 1
    ) -> bool:
        today = date.today().isoformat()
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT used_count FROM daily_usage WHERE identifier=? AND date=?",
                (identifier, today),
            )
            row = cursor.fetchone()
            current = row[0] if row else 0
            if current + count > limit:
                return False
            cursor.execute(
                """INSERT INTO daily_usage (identifier, date, used_count)
                   VALUES (?, ?, ?)
                   ON CONFLICT(identifier, date) DO UPDATE
                   SET used_count = used_count + ?""",
                (identifier, today, count, count),
            )
            conn.commit()
            return True

    def get_quota_usage(self, identifier: str) -> int:
        today = date.today().isoformat()
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT used_count FROM daily_usage WHERE identifier=? AND date=?",
                (identifier, today),
            )
            row = cursor.fetchone()
            return row[0] if row else 0

    def get_dict_cache(self, word: str):
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT structured_data FROM dict_cache WHERE word=?", (word,)
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def set_dict_cache(self, word: str, data: str):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO dict_cache (word, structured_data) VALUES (?, ?)",
                (word, data),
            )

    # --- Document CRUD ---

    def save_document(
        self,
        user_id: str,
        title: str,
        source_text: str,
        tracked_words: list,
        is_public: bool = False,
    ) -> int:
        uuid_str = str(uuid4()) if is_public else None
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO documents (user_id, title, source_text, tracked_words, is_public, public_uuid) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    title,
                    source_text,
                    json.dumps(tracked_words),
                    int(is_public),
                    uuid_str,
                ),
            )
            conn.commit()
            assert cursor.lastrowid is not None
            return cursor.lastrowid

    def get_documents(self, user_id: str, limit: int = 50, offset: int = 0):
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM documents WHERE user_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (user_id, limit, offset),
            )
            return [self._doc_row(row) for row in cursor.fetchall()]

    def get_document(self, doc_id: int, user_id: str):
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM documents WHERE id=? AND user_id=?",
                (doc_id, user_id),
            )
            row = cursor.fetchone()
            return self._doc_row(row) if row else None

    def get_public_document(self, uuid: str):
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM documents WHERE public_uuid=?",
                (uuid,),
            )
            row = cursor.fetchone()
            return self._doc_row(row) if row else None

    def update_document(self, doc_id: int, user_id: str, **kwargs):
        allowed = {"title", "is_public", "public_uuid"}
        sets, vals = [], []
        for k, v in kwargs.items():
            if k in allowed:
                sets.append(f"{k}=?")
                vals.append(v)
        if not sets:
            return
        vals.extend([doc_id, user_id])
        with sqlite3.connect(self._db_path) as conn:
            cur = conn.execute(
                f"UPDATE documents SET {', '.join(sets)}, updated_at=datetime('now','localtime') "
                "WHERE id=? AND user_id=?",
                vals,
            )
            conn.commit()
        return cur.rowcount > 0

    def delete_document(self, doc_id: int, user_id: str) -> bool:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM documents WHERE id=? AND user_id=?",
                (doc_id, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def _doc_row(row: sqlite3.Row) -> dict:
        d = dict(row)
        d["tracked_words"] = json.loads(d["tracked_words"])
        return d

    def save_query_history(
        self,
        user_id: str,
        word: str,
        context: str = "",
        mode: str = "quick",
        quick_answer: str = "",
        dict_result: str = "",
        deep_think: str = "",
        created_at: str | None = None,
    ) -> int:
        with sqlite3.connect(self._db_path) as conn:
            if created_at:
                cursor = conn.execute(
                    """INSERT INTO query_history
                       (user_id, word, context, mode, quick_answer, dict_result, deep_think, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        user_id,
                        word,
                        context,
                        mode,
                        quick_answer,
                        dict_result,
                        deep_think,
                        created_at,
                    ),
                )
            else:
                cursor = conn.execute(
                    """INSERT INTO query_history
                       (user_id, word, context, mode, quick_answer, dict_result, deep_think)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        user_id,
                        word,
                        context,
                        mode,
                        quick_answer,
                        dict_result,
                        deep_think,
                    ),
                )
            conn.commit()
            assert cursor.lastrowid is not None
            return cursor.lastrowid

    def log_api_usage(self, identifier: str, endpoint: str):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO usage_log (identifier, endpoint) VALUES (?, ?)",
                (identifier, endpoint),
            )

    def get_query_history(self, user_id: str, limit: int = 50, offset: int = 0):
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """SELECT * FROM query_history WHERE user_id = ?
                   ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                (user_id, limit, offset),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_all_query_history(self, user_id: str):
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """SELECT * FROM query_history WHERE user_id = ?
                   ORDER BY created_at DESC""",
                (user_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_query_history_by_ids(self, user_id: str, ids: list[int]):
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            placeholders = ",".join("?" for _ in ids)
            cursor = conn.execute(
                f"SELECT * FROM query_history WHERE id IN ({placeholders}) AND user_id = ? ORDER BY created_at DESC",
                (*ids, user_id),
            )
            return [dict(row) for row in cursor.fetchall()]

    def delete_query_history(self, user_id: str, record_id: int) -> bool:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM query_history WHERE id = ? AND user_id = ?",
                (record_id, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_query_history_batch(self, user_id: str, ids: list[int]):
        with sqlite3.connect(self._db_path) as conn:
            placeholders = ",".join("?" for _ in ids)
            conn.execute(
                f"DELETE FROM query_history WHERE id IN ({placeholders}) AND user_id = ?",
                (*ids, user_id),
            )
            conn.commit()

    def save_corpus(self, type_: str, context: str, word: str, answer: str) -> int:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO corpus (type, context, word, answer) VALUES (?, ?, ?, ?)",
                (type_, context, word, answer),
            )
            conn.commit()
            return cursor.lastrowid

    def get_corpus_by_word(self, word: str):
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM corpus WHERE word LIKE '%' || ? || '%' ORDER BY id",
                (word,),
            )
            return [dict(row) for row in cursor.fetchall()]


_db = Database()

check_and_decrease_quota = _db.check_and_decrease_quota
get_quota_usage = _db.get_quota_usage
get_dict_cache = _db.get_dict_cache
set_dict_cache = _db.set_dict_cache
save_document = _db.save_document
get_documents = _db.get_documents
get_document = _db.get_document
get_public_document = _db.get_public_document
update_document = _db.update_document
delete_document = _db.delete_document
save_query_history = _db.save_query_history
log_api_usage = _db.log_api_usage
get_query_history = _db.get_query_history
get_all_query_history = _db.get_all_query_history
get_query_history_by_ids = _db.get_query_history_by_ids
delete_query_history = _db.delete_query_history
delete_query_history_batch = _db.delete_query_history_batch
save_corpus = _db.save_corpus
get_corpus_by_word = _db.get_corpus_by_word
init_db = _db.init_db


def ingest_corpus_lines(lines: Iterable[str]) -> int:
    count = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        word = entry.get("word", "")
        for note in entry.get("notes", []):
            name_passage = note.get("name_passage", "").strip()
            type_ = "textbook" if name_passage else "mock_exam"
            save_corpus(
                type_=type_,
                context=note.get("context", ""),
                word=word,
                answer=note.get("detail", ""),
            )
            count += 1
    return count
