import sqlite3
from datetime import date

from config import settings

DB_PATH = settings.DB_PATH


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dict_cache (
                word TEXT PRIMARY KEY,
                structured_data TEXT
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_usage (
                identifier TEXT,
                date TEXT,
                used_count INTEGER,
                PRIMARY KEY (identifier, date)
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                word TEXT NOT NULL,
                context TEXT DEFAULT '',
                mode TEXT DEFAULT 'quick',
                quick_answer TEXT DEFAULT '',
                dict_result TEXT DEFAULT '',
                deep_think TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS corpus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                context TEXT DEFAULT '',
                word TEXT NOT NULL,
                answer TEXT DEFAULT ''
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_corpus_word ON corpus(word)")
        conn.execute("PRAGMA journal_mode=WAL;")


def check_and_decrease_quota(identifier: str, limit: int, count: int = 1) -> bool:
    today = date.today().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO daily_usage (identifier, date, used_count)
               VALUES (?, ?, ?)
               ON CONFLICT(identifier, date) DO UPDATE
               SET used_count = used_count + ?
               WHERE used_count + ? <= ?""",
            (identifier, today, count, count, count, limit),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_quota_usage(identifier: str) -> int:
    today = date.today().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT used_count FROM daily_usage WHERE identifier=? AND date=?",
            (identifier, today),
        )
        row = cursor.fetchone()
        return row[0] if row else 0


def get_dict_cache(word: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT structured_data FROM dict_cache WHERE word=?", (word,))
        row = cursor.fetchone()
        return row[0] if row else None


def set_dict_cache(word: str, data: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO dict_cache (word, structured_data) VALUES (?, ?)",
            (word, data),
        )


def save_query_history(
    user_id: str,
    word: str,
    context: str = "",
    mode: str = "quick",
    quick_answer: str = "",
    dict_result: str = "",
    deep_think: str = "",
    created_at: str | None = None,
) -> int:
    with sqlite3.connect(DB_PATH) as conn:
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
                (user_id, word, context, mode, quick_answer, dict_result, deep_think),
            )
        conn.commit()
        assert cursor.lastrowid is not None
        return cursor.lastrowid


def log_api_usage(identifier: str, endpoint: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO usage_log (identifier, endpoint) VALUES (?, ?)",
            (identifier, endpoint),
        )


def get_query_history(user_id: str, limit: int = 50, offset: int = 0):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """SELECT * FROM query_history WHERE user_id = ?
               ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (user_id, limit, offset),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_all_query_history(user_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """SELECT * FROM query_history WHERE user_id = ?
               ORDER BY created_at DESC""",
            (user_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_query_history_by_ids(user_id: str, ids: list[int]):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        placeholders = ",".join("?" for _ in ids)
        cursor = conn.execute(
            f"SELECT * FROM query_history WHERE id IN ({placeholders}) AND user_id = ? ORDER BY created_at DESC",
            (*ids, user_id),
        )
        return [dict(row) for row in cursor.fetchall()]


def delete_query_history(user_id: str, record_id: int) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "DELETE FROM query_history WHERE id = ? AND user_id = ?",
            (record_id, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_query_history_batch(user_id: str, ids: list[int]):
    with sqlite3.connect(DB_PATH) as conn:
        placeholders = ",".join("?" for _ in ids)
        conn.execute(
            f"DELETE FROM query_history WHERE id IN ({placeholders}) AND user_id = ?",
            (*ids, user_id),
        )
        conn.commit()


def save_corpus(type_: str, context: str, word: str, answer: str) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "INSERT INTO corpus (type, context, word, answer) VALUES (?, ?, ?, ?)",
            (type_, context, word, answer),
        )
        conn.commit()
        return cursor.lastrowid


def get_corpus_by_word(word: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM corpus WHERE word LIKE '%' || ? || '%' ORDER BY id",
            (word,),
        )
        return [dict(row) for row in cursor.fetchall()]
