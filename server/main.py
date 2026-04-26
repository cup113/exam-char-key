import json
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from time import time

from config import settings
from db_helper import init_db, check_and_decrease_quota
from spider import get_dict_entry
from auth import router as auth_router, decode_jwt

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

client = AsyncOpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)


@app.on_event("startup")
def startup():
    init_db()


# --- 依赖注入：限流 ---
def verify_quota(request: Request):
    token = request.cookies.get("auth_token")
    if token:
        try:
            payload = decode_jwt(token)
            identifier = f"user:{payload['sub']}"
            limit = settings.QUOTA_USER_DAILY
        except Exception:
            identifier = f"ip:{request.client.host}"
            limit = settings.QUOTA_GUEST_DAILY
    else:
        identifier = f"ip:{request.client.host}"
        limit = settings.QUOTA_GUEST_DAILY

    if not check_and_decrease_quota(identifier, limit):
        raise HTTPException(status_code=429, detail="今日额度已耗尽")
    return identifier


# --- SSE 流水线 ---
async def query_pipeline(word: str, context: str, mode: str):
    try:
        # 1. 快速回答
        yield f"data: {json.dumps({'step': 'quick_answer', 'status': 'start'})}\n\n"
        start = time()
        quick_stream = await client.chat.completions.create(
            model=settings.MODEL_QUICK_ANSWER,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个高中文言文学习助手。根据语境简要解释词语含义，直接给出答案，不要废话。",
                },
                {
                    "role": "user",
                    "content": f"语境：{context}\n请解释词语【{word}】在此处的含义。",
                },
            ],
            reasoning_effort="none",
            stream=True,
        )
        async for chunk in quick_stream:
            content = chunk.choices[0].delta.content
            if content:
                yield f"data: {json.dumps({'step': 'quick_answer', 'chunk': content})}\n\n"
        print(f"快速查询延迟: {time() - start: .2f}s")

        # 2. 字典查询
        yield f"data: {json.dumps({'step': 'dictionary', 'status': 'fetching'})}\n\n"
        dict_data = await get_dict_entry(word)
        yield f"data: {json.dumps({'step': 'dictionary', 'result': dict_data})}\n\n"

        # 3. 深度思考 (仅 deep 模式)
        if mode == "deep":
            yield f"data: {json.dumps({'step': 'deep_think', 'status': 'start'})}\n\n"
            deep_stream = await client.chat.completions.create(
                model=settings.MODEL_DEEP_THINK,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是一个深度语言分析助手。"
                            "根据提供的语境、词语和字典释义，给出：\n"
                            "1. 该词在语境中的精确含义\n"
                            "2. 整段语境的翻译"
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"语境：{context}\n"
                            f"词语：{word}\n"
                            f"字典释义：{dict_data}\n"
                            f"请进行深度分析。"
                        ),
                    },
                ],
                stream=True,
                reasoning_effort="low"
            )
            async for chunk in deep_stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield f"data: {json.dumps({'step': 'deep_think', 'chunk': content})}\n\n"

        yield f"data: {json.dumps({'step': 'done'})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


@app.get("/api/query")
async def query_endpoint(
    word: str, context: str, mode: str = "quick", _: str = Depends(verify_quota)
):
    return StreamingResponse(
        query_pipeline(word, context, mode), media_type="text/event-stream"
    )
