import time
import jwt
import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from config import settings, get_admin_users
from typing import Any

router = APIRouter(prefix="/auth", tags=["auth"])
callback_router = APIRouter()

JWT_SECRET = settings.JWT_SECRET or settings.LLM_API_KEY
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_SECONDS = 86400 * 7  # 7 天


def create_jwt(user_id: str, provider: str) -> str:
    assert JWT_SECRET is not None
    payload: dict[str, Any] = {
        "sub": user_id,
        "provider": provider,
        "exp": int(time.time()) + JWT_EXPIRE_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> dict[str, Any]:
    assert JWT_SECRET is not None
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token 无效")


@router.get("/github/login")
async def github_login():
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.APP_BASE_URL}/api/oauth2-redirect"
        f"&state=github&scope=read:user"
    )


@router.get("/gitee/login")
async def gitee_login():
    return RedirectResponse(
        f"https://gitee.com/oauth/authorize"
        f"?client_id={settings.GITEE_CLIENT_ID}"
        f"&redirect_uri={settings.APP_BASE_URL}/api/oauth2-redirect"
        f"&state=gitee&response_type=code"
    )


@callback_router.get("/oauth2-redirect")
async def oauth2_redirect(code: str, state: str = "github"):
    async with httpx.AsyncClient() as http:
        if state == "github":
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
            user_resp = await http.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_data = user_resp.json()
            user_id = f"github:{user_data['id']}"
            provider = "github"
        elif state == "gitee":
            token_resp = await http.post(
                "https://gitee.com/oauth/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": settings.GITEE_CLIENT_ID,
                    "client_secret": settings.GITEE_CLIENT_SECRET,
                    "redirect_uri": f"{settings.APP_BASE_URL}/api/oauth2-redirect",
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
            provider = "gitee"
        else:
            raise HTTPException(400, "不支持的 OAuth 提供商")

    token = create_jwt(user_id, provider)
    response = RedirectResponse(url=f"{settings.APP_BASE_URL}/")
    response.set_cookie(
        "auth_token", token, httponly=True, max_age=JWT_EXPIRE_SECONDS, samesite="lax"
    )
    return response


# ---------- 当前用户信息 ----------
@router.get("/me")
async def get_me(request: Request):
    token = request.cookies.get("auth_token")
    if not token:
        return JSONResponse({"logged_in": False})
    payload = decode_jwt(token)
    return JSONResponse(
        {
            "logged_in": True,
            "user_id": payload["sub"],
            "provider": payload["provider"],
            "is_admin": payload["sub"] in get_admin_users(),
        }
    )


@router.post("/logout")
async def logout():
    response = JSONResponse({"ok": True})
    response.delete_cookie("auth_token")
    return response
