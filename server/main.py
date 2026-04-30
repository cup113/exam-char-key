import json
import re
from datetime import date
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import httpx
from openai import AsyncOpenAI
from time import time
from contextlib import asynccontextmanager
from pathlib import Path

from config import settings
from log_helper import get_logger
from prompt import QUICK_PROMPT, DEEP_PROMPT
from typing import Any

logger = get_logger("main")
from db_helper import (
    init_db,
    check_and_decrease_quota,
    get_quota_usage,
    save_query_history,
    save_corpus,
    get_query_history,
    get_all_query_history,
    get_corpus_by_word,
    log_api_usage,
)
from spider import get_dict_entry
from auth import router as auth_router, callback_router, decode_jwt


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
    return f"ip:guest", settings.QUOTA_GUEST_DAILY, None


# --- 依赖注入：限流 ---
def verify_quota(request: Request):
    identifier, limit, _ = get_identifier_and_limit(request)
    mode = request.query_params.get("mode", "quick")
    count = 3 if mode == "deep" else 1
    if not check_and_decrease_quota(identifier, limit, count):
        logger.warning("额度耗尽 | %s | mode=%s", identifier, mode)
        raise HTTPException(status_code=429, detail="今日额度已耗尽")
    log_api_usage(identifier, request.url.path)
    logger.debug("额度扣除成功 | %s | mode=%s | count=%d", identifier, mode, count)
    return identifier


# --- SSE 流水线 ---
async def query_pipeline(word: str, context: str, mode: str):
    logger.info(
        "查询开始 | word=%s | mode=%s | context_len=%d", word, mode, len(context)
    )
    try:
        yield f"data: {json.dumps({'step': 'quick_answer', 'status': 'start'})}\n\n"
        start = time()
        quick_stream = await client.chat.completions.create(
            model=settings.MODEL_QUICK_ANSWER,
            messages=[
                {
                    "role": "system",
                    "content": QUICK_PROMPT,
                },
                {
                    "role": "user",
                    "content": f"“{context}”，中，【{word}】是什么意思？",
                },
            ],
            reasoning_effort="none",
            stream=True,
        )
        async for chunk in quick_stream:
            content = chunk.choices[0].delta.content
            if content:
                yield f"data: {json.dumps({'step': 'quick_answer', 'chunk': content})}\n\n"
        logger.info("快速查询延迟: %.2fs", time() - start)

        yield f"data: {json.dumps({'step': 'corpus', 'status': 'fetching'})}\n\n"
        corpus_entries = get_corpus_by_word(word)
        yield f"data: {json.dumps({'step': 'corpus', 'entries': corpus_entries})}\n\n"
        logger.info("语料库查询完成 | word=%s | count=%d", word, len(corpus_entries))

        yield f"data: {json.dumps({'step': 'dictionary', 'status': 'fetching'})}\n\n"
        dict_data = await get_dict_entry(word)
        logger.info("字典数据获取完成 | word=%s | data_len=%d", word, len(dict_data))
        yield f"data: {json.dumps({'step': 'dictionary', 'result': dict_data})}\n\n"

        if mode == "deep":
            logger.info("深度分析开始 | word=%s", word)
            yield f"data: {json.dumps({'step': 'deep_think', 'status': 'start'})}\n\n"
            deep_stream = await client.chat.completions.create(
                model=settings.MODEL_DEEP_THINK,
                messages=[
                    {"role": "system", "content": DEEP_PROMPT},
                    {
                        "role": "user",
                        "content": f"“【字典数据】\n{dict_data}\n\n“{context}”中，【{word}】是什么意思？",
                    },
                ],
                stream=True,
                reasoning_effort="low",
            )
            async for chunk in deep_stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield f"data: {json.dumps({'step': 'deep_think', 'chunk': content})}\n\n"

        yield f"data: {json.dumps({'step': 'done'})}\n\n"

    except Exception:
        logger.exception("查询流水线异常 | word=%s | mode=%s", word, mode)


@app.get("/api/query")
async def query_endpoint(
    word: str, context: str, mode: str = "quick", _: str = Depends(verify_quota)
):
    return StreamingResponse(
        query_pipeline(word, context, mode), media_type="text/event-stream"
    )


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
ANKI_API_URL = "https://anki.cup11.top/api/generate"
ANKI_BASE_URL = "https://anki.cup11.top"


def _build_export_document(records: list[dict[str, Any]]) -> dict[str, Any]:
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


@app.post("/api/export")
async def export_history(request: Request):
    _, _, user_id = get_identifier_and_limit(request)
    if not user_id:
        raise HTTPException(401, "请先登录")

    body = await request.json()
    fmt = body.get("format", "json")

    records = get_all_query_history(user_id)
    if not records:
        raise HTTPException(400, "暂无历史记录可导出")

    doc = _build_export_document(records)

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


STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
