import sqlite3
from datetime import date

DB_PATH = "../db/data.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        # 字典缓存表
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dict_cache (
                word TEXT PRIMARY KEY,
                structured_data TEXT
            )
        """
        )
        # 每日限流表
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
        # 开启 WAL 模式提升并发读写性能
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
