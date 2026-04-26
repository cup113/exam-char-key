import sqlite3
from datetime import date

DB_PATH = "../db/data.db"


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
        conn.execute("PRAGMA journal_mode=WAL;")


def check_and_decrease_quota(identifier: str, limit: int) -> bool:
    today = date.today().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT used_count FROM daily_usage WHERE identifier=? AND date=?",
            (identifier, today),
        )
        row = cursor.fetchone()

        used_count = row[0] if row else 0
        if used_count >= limit:
            return False

        if row:
            cursor.execute(
                "UPDATE daily_usage SET used_count = used_count + 1 WHERE identifier=? AND date=?",
                (identifier, today),
            )
        else:
            cursor.execute(
                "INSERT INTO daily_usage (identifier, date, used_count) VALUES (?, ?, ?)",
                (identifier, today, 1),
            )
        conn.commit()
        return True


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
) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """INSERT INTO query_history
               (user_id, word, context, mode, quick_answer, dict_result, deep_think)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, word, context, mode, quick_answer, dict_result, deep_think),
        )
        conn.commit()
        return cursor.lastrowid


def get_query_history(user_id: str, limit: int = 50, offset: int = 0):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """SELECT * FROM query_history WHERE user_id = ?
               ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (user_id, limit, offset),
        )
        return [dict(row) for row in cursor.fetchall()]
