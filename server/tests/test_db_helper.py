import sqlite3

import pytest

from db_helper import Database


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    database = Database(db_path)
    database.init_db()
    return database


class TestInitDB:
    def test_tables_created(self, db):
        tables = ["dict_cache", "daily_usage", "query_history", "usage_log", "corpus"]
        for tbl in tables:
            with sqlite3.connect(db._db_path) as conn:
                row = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (tbl,),
                ).fetchone()
                assert row is not None, f"Table {tbl} not created"


class TestQuota:
    def test_decrease_quota_returns_true_when_within_limit(self, db):
        assert db.check_and_decrease_quota("user:1", 5, 3) is True

    def test_decrease_quota_exceeds_limit_from_start(self, db):
        assert db.check_and_decrease_quota("user:1", 5, 6) is False

    def test_decrease_quota_accumulates_correctly(self, db):
        assert db.check_and_decrease_quota("user:1", 10, 3) is True
        assert db.check_and_decrease_quota("user:1", 10, 4) is True
        assert db.check_and_decrease_quota("user:1", 10, 4) is False
        assert db.check_and_decrease_quota("user:1", 10, 3) is True
        assert db.check_and_decrease_quota("user:1", 10, 1) is False

    def test_get_quota_usage_returns_zero_when_none(self, db):
        assert db.get_quota_usage("user:1") == 0

    def test_get_quota_usage_after_decrease(self, db):
        db.check_and_decrease_quota("user:1", 10, 3)
        db.check_and_decrease_quota("user:1", 10, 2)
        assert db.get_quota_usage("user:1") == 5

    def test_quota_is_per_identifier(self, db):
        db.check_and_decrease_quota("user:a", 10, 5)
        assert db.get_quota_usage("user:a") == 5
        assert db.get_quota_usage("user:b") == 0

    def test_quota_at_exact_limit(self, db):
        assert db.check_and_decrease_quota("user:1", 5, 5) is True
        assert db.check_and_decrease_quota("user:1", 5, 1) is False


class TestDictCache:
    def test_get_miss(self, db):
        assert db.get_dict_cache("nonexistent") is None

    def test_set_and_get(self, db):
        db.set_dict_cache("之", '{"data": "test"}')
        assert db.get_dict_cache("之") == '{"data": "test"}'

    def test_overwrite(self, db):
        db.set_dict_cache("之", "old")
        db.set_dict_cache("之", "new")
        assert db.get_dict_cache("之") == "new"

    def test_multiple_words(self, db):
        db.set_dict_cache("之", "data1")
        db.set_dict_cache("乎", "data2")
        assert db.get_dict_cache("之") == "data1"
        assert db.get_dict_cache("乎") == "data2"


class TestQueryHistory:
    def test_save_and_get(self, db):
        db.save_query_history("user:1", "之", "知之者", "quick", "代词")
        records = db.get_query_history("user:1")
        assert len(records) == 1
        assert records[0]["word"] == "之"
        assert records[0]["quick_answer"] == "代词"
        assert records[0]["context"] == "知之者"

    def test_get_empty(self, db):
        assert db.get_query_history("user:1") == []

    def test_all_fields(self, db):
        db.save_query_history(
            user_id="user:1",
            word="乎",
            context="不亦说乎",
            mode="deep",
            quick_answer="语气词",
            dict_result="{}",
            deep_think="详细分析",
        )
        records = db.get_query_history("user:1")
        r = records[0]
        assert r["word"] == "乎"
        assert r["mode"] == "deep"
        assert r["quick_answer"] == "语气词"
        assert r["dict_result"] == "{}"
        assert r["deep_think"] == "详细分析"
        assert r["created_at"] is not None

    def test_get_all_query_history(self, db):
        db.save_query_history("user:1", "a")
        db.save_query_history("user:1", "b")
        db.save_query_history("user:1", "c")
        all_records = db.get_all_query_history("user:1")
        assert len(all_records) == 3

    def test_per_user_isolation(self, db):
        db.save_query_history("user:a", "word1")
        db.save_query_history("user:b", "word2")
        assert len(db.get_query_history("user:a")) == 1
        assert len(db.get_query_history("user:b")) == 1

    def test_limit_and_offset(self, db):
        for i in range(10):
            db.save_query_history("user:1", f"word{i}")
        assert len(db.get_query_history("user:1", limit=3)) == 3

    def test_save_with_custom_created_at(self, db):
        db.save_query_history("user:1", "之", created_at="2024-01-01 12:00:00")
        records = db.get_query_history("user:1")
        assert records[0]["created_at"] == "2024-01-01 12:00:00"

    def test_get_query_history_by_ids(self, db):
        id1 = db.save_query_history("user:1", "a")
        id2 = db.save_query_history("user:1", "b")
        db.save_query_history("user:1", "c")
        records = db.get_query_history_by_ids("user:1", [id1, id2])
        assert len(records) == 2

    def test_get_query_history_by_ids_respects_user(self, db):
        id1 = db.save_query_history("user:a", "word")
        records = db.get_query_history_by_ids("user:b", [id1])
        assert len(records) == 0

    def test_delete_query_history(self, db):
        rid = db.save_query_history("user:1", "word")
        assert db.delete_query_history("user:1", rid) is True
        assert len(db.get_query_history("user:1")) == 0

    def test_delete_query_history_wrong_user(self, db):
        rid = db.save_query_history("user:a", "word")
        assert db.delete_query_history("user:b", rid) is False
        assert len(db.get_query_history("user:a")) == 1

    def test_delete_query_history_batch(self, db):
        id1 = db.save_query_history("user:1", "a")
        _ = db.save_query_history("user:1", "b")
        id3 = db.save_query_history("user:1", "c")
        db.delete_query_history_batch("user:1", [id1, id3])
        records = db.get_query_history("user:1")
        assert len(records) == 1
        assert records[0]["word"] == "b"


class TestCorpus:
    def test_save_and_get_by_word(self, db):
        db.save_corpus("textbook", "学而时习之", "之", "代词")
        entries = db.get_corpus_by_word("之")
        assert len(entries) == 1
        assert entries[0]["type"] == "textbook"
        assert entries[0]["answer"] == "代词"

    def test_get_corpus_empty(self, db):
        assert db.get_corpus_by_word("nonexistent") == []

    def test_get_corpus_partial_match(self, db):
        db.save_corpus("mock_exam", "不亦说乎", "乎", "语气词")
        entries = db.get_corpus_by_word("乎")
        assert len(entries) == 1

    def test_multiple_entries_same_word(self, db):
        db.save_corpus("textbook", "学而时习之", "之", "代词")
        db.save_corpus("mock_exam", "知之者", "之", "助词")
        entries = db.get_corpus_by_word("之")
        assert len(entries) == 2


class TestUsageLog:
    def test_log_api_usage(self, db):
        db.log_api_usage("user:1", "/api/query/quick")
        with sqlite3.connect(db._db_path) as conn:
            rows = conn.execute("SELECT * FROM usage_log").fetchall()
        assert len(rows) == 1
        assert rows[0][1] == "user:1"
        assert rows[0][2] == "/api/query/quick"


class TestDocument:
    def test_save_and_get(self, db):
        doc_id = db.save_document("user:1", "论语", "学而时习之", [])
        doc = db.get_document(doc_id, "user:1")
        assert doc["title"] == "论语"
        assert doc["source_text"] == "学而时习之"

    def test_update_source_text(self, db):
        doc_id = db.save_document("user:1", "t", "原文", [])
        db.update_document(doc_id, "user:1", source_text="更新后")
        doc = db.get_document(doc_id, "user:1")
        assert doc["source_text"] == "更新后"
        assert doc["title"] == "t"

    def test_update_tracked_words(self, db):
        doc_id = db.save_document("user:1", "t", "s", [{"word": "之"}])
        new_words = [{"word": "乎", "quickAnswer": "语气词"}]
        db.update_document(doc_id, "user:1", tracked_words=new_words)
        doc = db.get_document(doc_id, "user:1")
        assert len(doc["tracked_words"]) == 1
        assert doc["tracked_words"][0]["word"] == "乎"
        assert doc["tracked_words"][0]["quickAnswer"] == "语气词"

    def test_update_respects_user_id(self, db):
        doc_id = db.save_document("user:a", "t", "s", [])
        result = db.update_document(doc_id, "user:b", source_text="hack")
        assert result is False
        doc = db.get_document(doc_id, "user:a")
        assert doc["source_text"] == "s"


class TestMultipleDatabases:
    def test_isolated_instances(self, tmp_path):
        d1 = Database(str(tmp_path / "db1.db"))
        d2 = Database(str(tmp_path / "db2.db"))
        d1.init_db()
        d2.init_db()

        d1.save_corpus("textbook", "context", "word1", "answer1")
        d2.save_corpus("textbook", "context", "word2", "answer2")

        assert len(d1.get_corpus_by_word("word1")) == 1
        assert len(d2.get_corpus_by_word("word2")) == 1
        assert len(d2.get_corpus_by_word("word1")) == 0
