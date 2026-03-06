from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/callback"

    # OpenAI
    openai_api_key: str = ""

    # Naver IMAP
    naver_imap_host: str = "imap.naver.com"
    naver_imap_port: int = 993

    # Database
    database_url: str = "sqlite+aiosqlite:///./gtool.db"

    # Frontend
    frontend_url: str = "http://localhost:3000"

    # Background Scheduler
    sync_interval_minutes: int = 15
    auto_classify: bool = True

    # JWT
    secret_key: str = ""
    jwt_expire_minutes: int = 1440  # 24시간

    # Error Bot
    error_bot_url: str = ""


settings = Settings()
