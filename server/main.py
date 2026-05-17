import json
import re
from datetime import date
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import Scope
import httpx
from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import ChatCompletionChunk
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Coroutine

from config import settings
from log_helper import get_logger
from prompt import QUICK_PROMPT, DEEP_PROMPT
from db_helper import (
    init_db,
    check_and_decrease_quota,
    get_quota_usage,
    save_document,
    get_documents,
    get_document,
    get_public_document,
    update_document,
    delete_document,
    save_query_history,
    save_corpus,
    get_query_history,
    get_all_query_history,
    get_query_history_by_ids,
    delete_query_history,
    delete_query_history_batch,
    get_corpus_by_word,
    log_api_usage,
    get_dict_cache,
    ingest_corpus_lines,
)
from spider import get_dict_entry, format_dict_for_prompt
from export_service import build_export_document, ANKI_API_URL, ANKI_BASE_URL
from auth import router as auth_router, callback_router, decode_jwt
from admin import setup_admin
from config import get_admin_users

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting server ...")
    init_db()
    logger.info("Database initialized")
    yield
    logger.info("Server shutting down")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def trust_forwarded_proto(request: Request, call_next):
    if request.headers.get("x-forwarded-proto") == "https":
        request.scope["scheme"] = "https"
    return await call_next(request)


setup_admin(app)

app.include_router(auth_router, prefix="/api")
app.include_router(callback_router, prefix="/api")

client = AsyncOpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)


@app.get("/health")
async def health():
    return {"status": "ok"}


def get_identifier_and_limit(request: Request):
    token = request.cookies.get("auth_token")
    if token:
        try:
            payload = decode_jwt(token)
            return f"user:{payload['sub']}", settings.QUOTA_USER_DAILY, payload["sub"]
        except Exception:
            pass
    return "ip:guest", settings.QUOTA_GUEST_DAILY, None


# --- 限流 ---
def consume_quota(request: Request, count: int = 1) -> str:
    identifier, limit, _ = get_identifier_and_limit(request)
    if not check_and_decrease_quota(identifier, limit, count):
        logger.warning("额度耗尽 | %s", identifier)
        raise HTTPException(status_code=429, detail="今日额度已耗尽")
    log_api_usage(identifier, request.url.path)
    logger.debug("额度扣除成功 | %s | count=%d", identifier, count)
    return identifier


def verify_quota(count: int = 1):
    def _verify(request: Request):
        return consume_quota(request, count)

    return _verify


# --- SSE 流式辅助 ---
async def stream_llm_sse(
    llm_coro: Coroutine[Any, Any, AsyncStream[ChatCompletionChunk]],
):
    """将 LLM 流式输出包装为 SSE data chunk 事件"""
    try:
        stream = await llm_coro
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield f"data: {json.dumps({'chunk': content})}\n\n"
    except Exception:
        logger.exception("LLM 流式异常")
    finally:
        yield "data: [DONE]\n\n"


# --- 分拆为独立端点 ---


@app.get("/api/query/quick")
async def query_quick(word: str, context: str, _: str = Depends(verify_quota(1))):
    logger.info("快速查询 | word=%s | context_len=%d", word, len(context))
    llm_coro = client.chat.completions.create(
        model=settings.MODEL_QUICK_ANSWER,
        messages=[
            {"role": "system", "content": QUICK_PROMPT},
            {"role": "user", "content": f"“{context}”中，【{word}】是什么意思？"},
        ],
        reasoning_effort="none",
        stream=True,
    )
    return StreamingResponse(stream_llm_sse(llm_coro), media_type="text/event-stream")


@app.get("/api/query/corpus")
async def query_corpus(word: str):
    entries = get_corpus_by_word(word)
    logger.debug("语料库查询 | word=%s | count=%d", word, len(entries))
    return {"entries": entries}


@app.get("/api/query/dictionary")
async def query_dictionary(word: str, request: Request) -> dict[str, Any]:
    cached = get_dict_cache(word)
    if cached:
        logger.debug("字典缓存命中 | word=%s", word)
        return {"result": cached, "cached": True}

    consume_quota(request, 1)

    result = await get_dict_entry(word)
    logger.info("字典查询完成 | word=%s | data_len=%d", word, len(result))
    return {"result": result, "cached": False}


@app.get("/api/query/deep")
async def query_deep(word: str, context: str, _: str = Depends(verify_quota(2))):
    dict_data = get_dict_cache(word)
    if not dict_data:
        raise HTTPException(status_code=400, detail="请先查询汉典释义")

    formatted = format_dict_for_prompt(dict_data)
    logger.info("深度分析 | word=%s | context_len=%d", word, len(context))

    llm_coro = client.chat.completions.create(
        model=settings.MODEL_DEEP_THINK,
        messages=[
            {"role": "system", "content": DEEP_PROMPT},
            {
                "role": "user",
                "content": f"【字典数据】\n{formatted}\n\n“{context}”中，【{word}】是什么意思？",
            },
        ],
        stream=True,
        reasoning_effort="low",
    )
    return StreamingResponse(stream_llm_sse(llm_coro), media_type="text/event-stream")


@app.get("/api/quota")
async def get_quota(request: Request):
    identifier, limit, _ = get_identifier_and_limit(request)
    used = get_quota_usage(identifier)
    return {"used": used, "limit": limit, "remaining": limit - used}


@app.get("/api/history")
async def list_history(request: Request, limit: int = 50, offset: int = 0):
    _, _, user_id = get_identifier_and_limit(request)
    if not user_id:
        raise HTTPException(401, "请先登录")
    records = get_query_history(user_id, limit, offset)
    return {"records": records}


@app.post("/api/history")
async def save_history(request: Request) -> dict[str, int | str]:
    _, _, user_id = get_identifier_and_limit(request)
    if not user_id:
        raise HTTPException(401, "请先登录")

    data = await request.json()
    word = data.get("word")
    if not word:
        raise HTTPException(400, "word 不能为空")

    history_id = save_query_history(
        user_id=user_id,
        word=word,
        context=data.get("context", ""),
        mode=data.get("mode", "quick"),
        quick_answer=data.get("quick_answer", ""),
        dict_result=data.get("dict_result", ""),
        deep_think=data.get("deep_think", ""),
    )
    save_corpus(
        type_="user_query",
        context=data.get("context", ""),
        word=word,
        answer=data.get("quick_answer", ""),
    )
    logger.info("历史记录已保存 | id=%d | user=%s | word=%s", history_id, user_id, word)
    return {"id": history_id, "message": "保存成功"}


@app.delete("/api/history/{record_id}")
async def delete_history(record_id: int, request: Request):
    _, _, user_id = get_identifier_and_limit(request)
    if not user_id:
        raise HTTPException(401, "请先登录")
    if not delete_query_history(user_id, record_id):
        raise HTTPException(404, "记录不存在")
    return {"message": "删除成功"}


@app.post("/api/history/delete")
async def delete_history_batch(request: Request):
    _, _, user_id = get_identifier_and_limit(request)
    if not user_id:
        raise HTTPException(401, "请先登录")
    body = await request.json()
    ids = body.get("ids", [])
    if not ids:
        raise HTTPException(400, "ids 不能为空")
    delete_query_history_batch(user_id, ids)
    return {"message": f"已删除 {len(ids)} 条记录"}


# --- 数据迁移（旧版 localStorage EC_history → query_history）---
@app.post("/api/migrate")
async def migrate_legacy_data(request: Request) -> dict[str, Any]:
    _, _, user_id = get_identifier_and_limit(request)
    if not user_id:
        raise HTTPException(401, "请先登录")

    body = await request.json()
    entries = body.get("entries", [])
    if not entries:
        raise HTTPException(400, "entries 不能为空")

    count = 0
    for entry in entries:
        front = entry.get("front", "")
        match = re.search(r"<strong>(.*?)</strong>", front)
        word = match.group(1) if match else front
        context = re.sub(r"<[^>]+>", "", front)

        created_at_raw = entry.get("createdAt", "")
        created_at = None
        if created_at_raw:
            try:
                _ = date.fromisoformat(created_at_raw.split(" ")[0])
                created_at = created_at_raw
            except ValueError:
                pass

        save_query_history(
            user_id=user_id,
            word=word,
            context=context,
            mode="quick",
            quick_answer=entry.get("back", ""),
            created_at=created_at,
        )
        count += 1

    logger.info("数据迁移完成 | user=%s | count=%d", user_id, count)
    return {"migrated": count, "message": f"成功迁移 {count} 条数据"}


# --- 导出（query_history → JSON / Word / Anki）---
# TODO: extract format dispatch + external HTTP calls into export_service.py


@app.post("/api/export")
async def export_history(request: Request):
    _, _, user_id = get_identifier_and_limit(request)
    if not user_id:
        raise HTTPException(401, "请先登录")

    body = await request.json()
    fmt = body.get("format", "json")
    ids = body.get("ids")

    if ids:
        records = get_query_history_by_ids(user_id, ids)
    else:
        records = get_all_query_history(user_id)
    if not records:
        raise HTTPException(400, "暂无历史记录可导出")

    doc = build_export_document(records)

    if fmt == "json":
        title = doc["title"]
        return JSONResponse(
            content=doc,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{title}.json"'},
        )

    if fmt in ("word", "apkg"):
        async with httpx.AsyncClient() as client:
            resp = await client.post(ANKI_API_URL, json=doc, timeout=60)
            if resp.status_code != 200:
                logger.error(
                    "外部导出服务异常 | status=%d | body=%s",
                    resp.status_code,
                    resp.text,
                )
                raise HTTPException(502, "外部导出服务异常")
            result = resp.json()
            fmt_suffix = "docx" if fmt == "word" else fmt
            filename = result.get(f"{fmt_suffix}_filename")
            if not filename:
                raise HTTPException(502, "外部服务返回异常: 缺少文件名")
            file_resp = await client.get(
                f"{ANKI_BASE_URL}/api/download/{fmt_suffix}/{filename}", timeout=60
            )
            if file_resp.status_code != 200:
                logger.error(
                    "文件下载失败 | filename=%s | status=%d",
                    filename,
                    file_resp.status_code,
                )
                raise HTTPException(502, "导出文件下载失败")
            return Response(
                content=file_resp.content,
                media_type="application/octet-stream",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

    raise HTTPException(400, f"不支持的导出格式: {fmt}")


# --- 文档接口 ---


class CreateDocumentRequest(BaseModel):
    title: str
    source_text: str
    tracked_words: list
    is_public: bool = False


class UpdateDocumentRequest(BaseModel):
    title: str | None = None
    is_public: bool | None = None


@app.post("/api/documents")
async def create_document(req: CreateDocumentRequest, request: Request):
    _, _, user_id = get_identifier_and_limit(request)
    if not user_id:
        raise HTTPException(401, "请先登录")
    doc_id = save_document(
        user_id=user_id,
        title=req.title,
        source_text=req.source_text,
        tracked_words=req.tracked_words,
        is_public=req.is_public,
    )
    return {"id": doc_id, "title": req.title, "message": "保存成功"}


@app.get("/api/documents")
async def list_documents(request: Request, limit: int = 50, offset: int = 0):
    _, _, user_id = get_identifier_and_limit(request)
    if not user_id:
        raise HTTPException(401, "请先登录")
    docs = get_documents(user_id, limit, offset)
    return {"documents": docs}


@app.get("/api/documents/{doc_id}")
async def read_document(doc_id: int, request: Request):
    _, _, user_id = get_identifier_and_limit(request)
    if not user_id:
        raise HTTPException(401, "请先登录")
    doc = get_document(doc_id, user_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    return doc


@app.patch("/api/documents/{doc_id}")
async def update_document_route(
    doc_id: int, req: UpdateDocumentRequest, request: Request
):
    _, _, user_id = get_identifier_and_limit(request)
    if not user_id:
        raise HTTPException(401, "请先登录")
    kwargs = {}
    if req.title is not None:
        kwargs["title"] = req.title
    if req.is_public is not None:
        import uuid

        kwargs["is_public"] = int(req.is_public)
        kwargs["public_uuid"] = str(uuid.uuid4()) if req.is_public else None
    update_document(doc_id, user_id, **kwargs)
    return {"message": "更新成功"}


@app.delete("/api/documents/{doc_id}")
async def delete_document_route(doc_id: int, request: Request):
    _, _, user_id = get_identifier_and_limit(request)
    if not user_id:
        raise HTTPException(401, "请先登录")
    if not delete_document(doc_id, user_id):
        raise HTTPException(404, "文档不存在")
    return {"message": "删除成功"}


@app.get("/api/documents/public/{uuid}")
async def read_public_document(uuid: str):
    doc = get_public_document(uuid)
    if not doc:
        raise HTTPException(404, "文档不存在或未公开")
    return doc


# --- 管理员接口 ---


def verify_admin(request: Request):
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(401, "未登录")
    payload = decode_jwt(token)
    if payload["sub"] not in get_admin_users():
        raise HTTPException(403, "非管理员")
    return payload["sub"]


@app.get("/api/admin/check")
async def admin_check(request: Request):
    try:
        verify_admin(request)
        return {"admin": True}
    except HTTPException:
        return {"admin": False}


@app.post("/api/admin/import-corpus")
async def admin_import_corpus(request: Request):
    verify_admin(request)
    form = await request.form()
    file = form.get("file")
    if not file or not file.filename:
        raise HTTPException(400, "请选择 JSONL 文件")
    try:
        content = (await file.read()).decode("utf-8")
    except Exception:
        raise HTTPException(400, "文件读取失败")

    count = ingest_corpus_lines(content.splitlines())
    return {"success": True, "count": count, "filename": file.filename}


# --- 旧版 PWA 自注销（vite-plugin-pwa 默认路径 /sw.js）---
# 当旧 Service Worker 检查更新时拉取此脚本，会立即激活、清除缓存、注销自身，并刷新页面
SW_SELF_DESTRUCT = (
    "self.addEventListener('install',()=>self.skipWaiting());"
    "self.addEventListener('activate',e=>{"
    "e.waitUntil("
    "caches.keys().then(ks=>Promise.all(ks.map(k=>caches.delete(k))))"
    ".then(()=>self.registration.unregister())"
    ".then(()=>clients.matchAll({type:'window'}))"
    ".then(cl=>cl.forEach(c=>c.navigate(c.url)))"
    ")})"
)


@app.get("/sw.js")
@app.get("/service-worker.js")
async def sw_self_destruct():
    return Response(
        content=SW_SELF_DESTRUCT,
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache, must-revalidate"},
    )


class SPAStaticFiles(StaticFiles):
    """SPA fallback: 对于 404 文件请求，返回 index.html（支持 Vue Router 的 history 模式）"""

    async def get_response(self, path: str, scope: Scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as e:
            if e.status_code == 404:
                return await super().get_response("index.html", scope)
            raise


STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/", SPAStaticFiles(directory=str(STATIC_DIR), html=True), name="static")
