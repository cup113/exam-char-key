from pathlib import Path

from sqlalchemy import Column, Integer, String, Text, create_engine, text
from sqlalchemy import Index
from sqlalchemy.orm import declarative_base

from config import settings

_db_path = Path(settings.DB_PATH).resolve().as_posix()
engine = create_engine(f"sqlite:///{_db_path}")
Base = declarative_base()


class DictCache(Base):
    __tablename__ = "dict_cache"

    word = Column(String, primary_key=True)
    structured_data = Column(Text, nullable=True)


class DailyUsage(Base):
    __tablename__ = "daily_usage"

    identifier = Column(String, primary_key=True)
    date = Column(String, primary_key=True)
    used_count = Column(Integer)


class QueryHistory(Base):
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    word = Column(String, nullable=False)
    context = Column(String, default="")
    mode = Column(String, default="quick")
    quick_answer = Column(String, default="")
    dict_result = Column(String, default="")
    deep_think = Column(String, default="")
    created_at = Column(String, server_default=text("(datetime('now','localtime'))"))


class UsageLog(Base):
    __tablename__ = "usage_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    identifier = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    created_at = Column(String, server_default=text("(datetime('now','localtime'))"))


class Corpus(Base):
    __tablename__ = "corpus"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, nullable=False)
    context = Column(String, default="")
    word = Column(String, nullable=False)
    answer = Column(String, default="")

    __table_args__ = (Index("idx_corpus_word", "word"),)


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    title = Column(String, nullable=False, default="")
    source_text = Column(String, nullable=False)
    tracked_words = Column(String, nullable=False)
    is_public = Column(Integer, nullable=False, default=0)
    public_uuid = Column(String, unique=True, nullable=True)
    created_at = Column(String, server_default=text("(datetime('now','localtime'))"))
    updated_at = Column(String, server_default=text("(datetime('now','localtime'))"))


def init_db(db_path: str | None = None):
    if db_path is not None:
        _p = Path(db_path).resolve().as_posix()
        e = create_engine(f"sqlite:///{_p}")
        Base.metadata.create_all(e)
        with e.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL;"))
            conn.commit()
        e.dispose()
    else:
        Base.metadata.create_all(engine)
        with engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL;"))
            conn.commit()
