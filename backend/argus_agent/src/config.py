from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Genuine secrets only. Everything else configurable lives in constants.py."""

    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    fortyguard_api_key: str = ""
    openai_api_key: str = ""
    groq_api_key: str = ""
    mongo_uri: str = ""


settings = Settings()
