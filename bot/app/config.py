from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    github_token: str
    github_repo: str
    github_base_branch: str = "main"
    project_root: str = "backend/app"
    discord_webhook_url: str
    bot_port: int = 8001
    import_depth: int = 2
    local_source_path: str = ""
    container_workdir: str = "/app"

    model_config = {"env_file": ".env"}


settings = Settings()
