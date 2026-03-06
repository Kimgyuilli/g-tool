import logging

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_fixed

from app.config import settings

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


@retry(stop=stop_after_attempt(2), wait=wait_fixed(2), reraise=True)
def call_ai(
    system_prompt: str,
    user_prompt: str,
    response_format: dict | None = None,
) -> str:
    """OpenAI API를 호출하고 텍스트 응답을 반환한다."""
    kwargs: dict = {
        "model": "gpt-4o",
        "max_tokens": 16384,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if response_format:
        kwargs["response_format"] = response_format
    response = _get_client().chat.completions.create(**kwargs)
    return response.choices[0].message.content


def health_check() -> dict:
    """OpenAI API 연결 상태 확인."""
    try:
        _get_client().models.list()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
