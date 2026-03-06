from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import (
    create_auth_url,
    exchange_code,
    get_user_email,
)
from app.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, encrypt_value
from app.mail.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login():
    """Redirect user to Google OAuth consent screen."""
    url = create_auth_url()
    return {"auth_url": url}


@router.get("/callback")
async def callback(
    code: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle OAuth callback: exchange code, upsert user, set JWT cookie."""
    try:
        credentials = exchange_code(code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {exc}")

    email = await get_user_email(credentials)

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    encrypted_token = encrypt_value(credentials.token)
    encrypted_refresh = (
        encrypt_value(credentials.refresh_token)
        if credentials.refresh_token
        else None
    )

    if user is None:
        user = User(
            email=email,
            google_oauth_token=encrypted_token,
            google_refresh_token=encrypted_refresh,
        )
        db.add(user)
    else:
        user.google_oauth_token = encrypted_token
        if encrypted_refresh:
            user.google_refresh_token = encrypted_refresh

    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)
    response = RedirectResponse(url=settings.frontend_url)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )
    return response


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    """Get current user info."""
    has_google = bool(user.google_oauth_token)
    has_naver = bool(user.naver_email)

    return {
        "user_id": user.id,
        "email": user.email,
        "google_connected": has_google,
        "naver_connected": has_naver,
    }


@router.post("/logout")
async def logout():
    """Clear session cookie."""
    response = JSONResponse({"ok": True})
    response.delete_cookie("session_token", path="/")
    return response
