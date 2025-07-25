from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from openai import AsyncOpenAI
from typing import Literal
from httpx import ConnectTimeout
from asyncio import create_task
from pydantic import BaseModel

from server.services.zdic_service import ZdicService
from server.services.completion_service import CompletionService
from server.services.logging_service import main_logger
from server.services.pocketbase_service import PocketBaseService
from server.config import Config, Roles
from server.models import (
    ZdicResult,
    ServerResponseZdic,
    ServerResponseFreqInfo,
)


class AuthorizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        host = request.client.host if request.client is not None else "Unknown"
        ip_address = request.headers.get("X-Forwarded-For", host)
        main_logger.info(f"Request from {ip_address}")

        authorization = request.headers.get("Authorization")
        request.state.pb = PocketBaseService()
        if authorization is not None:
            if authorization.startswith("Bearer "):
                authorization = authorization[len("Bearer ") :]
            request.state.auth_result = await request.state.pb.auth_user(authorization)
            main_logger.info(f"Authorization: {authorization}")
        else:
            request.state.token = None
            request.state.auth_result = await request.state.pb.auth_guest(ip_address)

        return await call_next(request)


class LoginBody(BaseModel):
    email: str
    password: str


class RegisterBody(BaseModel):
    email: str
    password: str


class AdoptBody(BaseModel):
    context: str
    query: str
    answer: str


def init_ai_client():
    if not Config.API_KEY:
        raise ValueError("API_KEY is not set")
    return AsyncOpenAI(
        api_key=Config.API_KEY,
        base_url=Config.AI_BASE_URL,
    )


app = FastAPI()
app.add_middleware(AuthorizationMiddleware)


async def pocketbase_init():
    superuser_pocketbase = PocketBaseService()
    await superuser_pocketbase.auth_superuser()
    await superuser_pocketbase.init_roles()
    await superuser_pocketbase.init_corpus()


create_task(pocketbase_init())
client = init_ai_client()


async def query_flash_core(pb: PocketBaseService, context: str, q: str):
    completion_service = CompletionService(client, pb)
    async for chunk in completion_service.generate_flash_response(context, q):
        yield chunk.to_jsonl_str()


async def query_thinking_core(pb: PocketBaseService, context: str, q: str):
    completion_service = CompletionService(client, pb)
    freq_info = await pb.corpus_freq_retrieve(q)
    if freq_info is not None:
        yield ServerResponseFreqInfo.create(freq_info).to_jsonl_str()

    try:
        zdic_result = await ZdicService(pb).get_result(q)

        if zdic_result is None:
            raise ValueError("Zdic unavailable.")

        yield ServerResponseZdic.create(zdic_result).to_jsonl_str()
        zdic_prompt = zdic_result.zdic_prompt
    except Exception as err:
        main_logger.warning(err)
        zdic_prompt = ""
        yield ServerResponseZdic.create(ZdicResult.empty()).to_jsonl_str()

    async for chunk in completion_service.generate_thought_response(
        context, q, zdic_prompt
    ):
        yield chunk.to_jsonl_str()


@app.get("/api/query/thinking")
async def query_thinking(
    request: Request,
    q: str = Query(..., description="The query word", min_length=1, max_length=100),
    context: str = Query(..., description="The context sentence", max_length=1000),
):
    return StreamingResponse(
        query_thinking_core(pb=request.state.pb, context=context, q=q),
        media_type="application/json",
    )


@app.get("/api/query/flash")
async def query_flash(
    request: Request,
    q: str = Query(..., description="The query word", min_length=1, max_length=100),
    context: str = Query(..., description="The context sentence", max_length=1000),
):
    return StreamingResponse(
        query_flash_core(context=context, q=q, pb=request.state.pb),
        media_type="application/json",
    )


@app.get("/api/search-original")
async def search_original(
    request: Request,
    excerpt: str = Query(..., description="Excerpt to search in", max_length=10000),
    target: Literal["sentence", "paragraph", "full-text"] = Query(
        "sentence", description="Target level of detail"
    ),
):
    completion_service = CompletionService(
        client,
        request.state.pb,
    )
    return StreamingResponse(
        completion_service.search_original_text(excerpt, target),
        media_type="application/json",
    )


@app.get("/api/zdic")
async def get_zdic_only(
    request: Request, q: str = Query(..., description="The query word", max_length=100)
):
    try:
        result = await ZdicService(request.state.pb).get_result(q)
    except ConnectTimeout:
        raise HTTPException(503, "Connection Timeout from zdic")
    if result is None:
        raise HTTPException(404, "Empty Response from zdic")
    return JSONResponse(result.model_dump())


@app.get("/api/balance-details")
async def get_balance(
    request: Request,
    page: int = Query(1, description="The page number"),
):
    pb: PocketBaseService = request.state.pb
    return JSONResponse(await pb.balance_details_list(page=page))


@app.get("/api/user")
def get_user_info(request: Request):
    return JSONResponse(request.state.auth_result)


@app.post("/api/adopt-answer")
async def adopt_answer(body: AdoptBody, request: Request):
    pb: PocketBaseService = request.state.pb
    return JSONResponse(
        await pb.corpus_create_query(body.query, body.context, body.answer)
    )


@app.post("/api/auth/register")
async def register(body: RegisterBody, request: Request):
    pb: PocketBaseService = request.state.pb
    return JSONResponse(await pb.auth_register(body.email, body.password, Roles.USER))


@app.post("/api/auth/login")
async def login(body: LoginBody, request: Request):
    pb: PocketBaseService = request.state.pb
    return JSONResponse(await pb.auth_login(body.email, body.password))


@app.get("/")
async def root():
    return RedirectResponse("/index.html")


app.mount("/", StaticFiles(directory="client/dist"), name="static")
