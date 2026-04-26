import time
import jwt
import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

JWT_SECRET = settings.LLM_API_KEY
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_SECONDS = 86400 * 7  # 7 天


def create_jwt(user_id: str, provider: str) -> str:
    payload = {
        "sub": user_id,
        "provider": provider,
        "exp": int(time.time()) + JWT_EXPIRE_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token 无效")


# ---------- GitHub OAuth ----------
@router.get("/github/login")
async def github_login():
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}&scope=read:user"
    )


@router.get("/github/callback")
async def github_callback(code: str):
    async with httpx.AsyncClient() as http:
        # 换取 access_token
        token_resp = await http.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise HTTPException(400, "GitHub 授权失败")

        # 获取用户信息
        user_resp = await http.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_data = user_resp.json()

    user_id = f"github:{user_data['id']}"
    token = create_jwt(user_id, "github")

    response = RedirectResponse(url="/")
    response.set_cookie("auth_token", token, httponly=True, max_age=JWT_EXPIRE_SECONDS, samesite="lax")
    return response


# ---------- Gitee OAuth ----------
@router.get("/gitee/login")
async def gitee_login():
    return RedirectResponse(
        f"https://gitee.com/oauth/authorize"
        f"?client_id={settings.GITEE_CLIENT_ID}"
        f"&redirect_uri=http://localhost:8000/auth/gitee/callback"
        f"&response_type=code"
    )


@router.get("/gitee/callback")
async def gitee_callback(code: str):
    async with httpx.AsyncClient() as http:
        token_resp = await http.post(
            "https://gitee.com/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.GITEE_CLIENT_ID,
                "client_secret": settings.GITEE_CLIENT_SECRET,
                "redirect_uri": "http://localhost:8000/auth/gitee/callback",
            },
        )
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise HTTPException(400, "Gitee 授权失败")

        user_resp = await http.get(
            "https://gitee.com/api/v5/user",
            params={"access_token": access_token},
        )
        user_data = user_resp.json()

    user_id = f"gitee:{user_data['id']}"
    token = create_jwt(user_id, "gitee")

    response = RedirectResponse(url="/")
    response.set_cookie("auth_token", token, httponly=True, max_age=JWT_EXPIRE_SECONDS, samesite="lax")
    return response


# ---------- 当前用户信息 ----------
@router.get("/me")
async def get_me(request: Request):
    token = request.cookies.get("auth_token")
    if not token:
        return JSONResponse({"logged_in": False})
    payload = decode_jwt(token)
    return JSONResponse({"logged_in": True, "user_id": payload["sub"], "provider": payload["provider"]})


@router.post("/logout")
async def logout():
    response = JSONResponse({"ok": True})
    response.delete_cookie("auth_token")
    return response
