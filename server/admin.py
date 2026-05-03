from pathlib import Path

from fastapi import Request
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import Column, Integer, String, Text, create_engine, text
from sqlalchemy.orm import declarative_base

from auth import decode_jwt
from config import settings, get_admin_users

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


class DictCacheAdmin(ModelView, model=DictCache):
    name = "Dict Cache"
    name_plural = "Dict Caches"
    icon = "fa-solid fa-database"
    column_list = [DictCache.word, DictCache.structured_data]
    column_details_list = [DictCache.word, DictCache.structured_data]
    can_create = False
    can_edit = True
    can_delete = True
    column_searchable_list = [DictCache.word]
    column_sortable_list = [DictCache.word]
    column_formatters = {
        DictCache.structured_data: lambda m, a: (
            (m.structured_data[:200] + "...")
            if m.structured_data and len(m.structured_data) > 200
            else m.structured_data
        ),
    }


class DailyUsageAdmin(ModelView, model=DailyUsage):
    name = "Daily Usage"
    name_plural = "Daily Usage"
    icon = "fa-solid fa-chart-bar"
    column_list = [DailyUsage.identifier, DailyUsage.date, DailyUsage.used_count]
    can_create = False
    can_edit = True
    can_delete = False
    column_searchable_list = [DailyUsage.identifier]
    column_sortable_list = [DailyUsage.date, DailyUsage.used_count]


class QueryHistoryAdmin(ModelView, model=QueryHistory):
    name = "Query History"
    name_plural = "Query History"
    icon = "fa-solid fa-clock"
    column_list = [
        QueryHistory.id,
        QueryHistory.user_id,
        QueryHistory.word,
        QueryHistory.mode,
        QueryHistory.created_at,
    ]
    column_details_list = [
        QueryHistory.id,
        QueryHistory.user_id,
        QueryHistory.word,
        QueryHistory.context,
        QueryHistory.mode,
        QueryHistory.quick_answer,
        QueryHistory.dict_result,
        QueryHistory.deep_think,
        QueryHistory.created_at,
    ]
    can_create = False
    can_edit = True
    can_delete = True
    column_searchable_list = [QueryHistory.word, QueryHistory.user_id]
    column_sortable_list = [QueryHistory.created_at, QueryHistory.id]
    column_default_sort = [(QueryHistory.created_at, True)]


class UsageLogAdmin(ModelView, model=UsageLog):
    name = "Usage Log"
    name_plural = "Usage Log"
    icon = "fa-solid fa-list"
    column_list = [
        UsageLog.id,
        UsageLog.identifier,
        UsageLog.endpoint,
        UsageLog.created_at,
    ]
    can_create = False
    can_edit = False
    can_delete = True
    column_searchable_list = [UsageLog.identifier, UsageLog.endpoint]
    column_sortable_list = [UsageLog.created_at, UsageLog.id]
    column_default_sort = [(UsageLog.created_at, True)]


class CorpusAdmin(ModelView, model=Corpus):
    name = "Corpus"
    name_plural = "Corpus"
    icon = "fa-solid fa-book"
    column_list = [Corpus.id, Corpus.type, Corpus.word, Corpus.context, Corpus.answer]
    can_create = False
    can_edit = True
    can_delete = True
    column_searchable_list = [Corpus.word, Corpus.type]
    column_sortable_list = [Corpus.word, Corpus.type]


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        token = request.cookies.get("auth_token")
        if not token:
            return False
        try:
            payload = decode_jwt(token)
            return payload["sub"] in get_admin_users()
        except Exception:
            return False

    async def authenticate(self, request: Request) -> bool:
        return await self.login(request)

    async def logout(self, request: Request) -> bool:
        return True


def setup_admin(app):
    auth_backend = AdminAuth(secret_key=settings.JWT_SECRET or "opencode-fallback")
    admin = Admin(app, engine, authentication_backend=auth_backend)

    admin.add_view(DictCacheAdmin)
    admin.add_view(DailyUsageAdmin)
    admin.add_view(QueryHistoryAdmin)
    admin.add_view(UsageLogAdmin)
    admin.add_view(CorpusAdmin)

    return admin
