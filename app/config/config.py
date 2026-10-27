from functools import cached_property
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.schemas.llm import LLMProvider


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_MINUTES: int = 30
    JWT_REFRESH_TOKEN_MINUTES: int = 8640
    JWT_SECRET_KEY: str

    RESERVE_HOLD_MIN: int = 10

    LLM_PROVIDER: LLMProvider | None = None
    LLM_MODEL: str | None = None
    GEMINI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None

    DEVELOPMENT_MODE: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
    )

    @cached_property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}"
            f"/{self.POSTGRES_DB}"
        )


settings = Settings()
