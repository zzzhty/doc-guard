from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = f"sqlite:///{Path(__file__).parent.parent / 'data' / 'docwatcher.db'}"

    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    gitea_url: str = ""
    gitea_token: str = ""

    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
