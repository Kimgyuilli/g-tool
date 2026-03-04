from __future__ import annotations

import os

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from app.config import settings

# Google OAuth가 반환하는 스코프 순서/내용이 요청과 다를 수 있음
# (include_granted_scopes로 이전 스코프가 포함되는 등)
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]


def _client_config() -> dict:
    return {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_redirect_uri],
        }
    }


def create_auth_url(state: str | None = None) -> str:
    """Generate the Google OAuth consent URL."""
    flow = Flow.from_client_config(_client_config(), scopes=SCOPES)
    flow.redirect_uri = settings.google_redirect_uri
    url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return url


def exchange_code(code: str) -> Credentials:
    """Exchange the authorization code for credentials."""
    flow = Flow.from_client_config(_client_config(), scopes=SCOPES)
    flow.redirect_uri = settings.google_redirect_uri
    flow.fetch_token(code=code)
    return flow.credentials


def build_credentials(access_token: str, refresh_token: str) -> Credentials:
    """Build Credentials from stored tokens."""
    return Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=SCOPES,
    )


async def get_user_email(credentials: Credentials) -> str:
    """Fetch the authenticated user's email from Google userinfo."""
    import httpx

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"},
        )
        resp.raise_for_status()
        return resp.json()["email"]
