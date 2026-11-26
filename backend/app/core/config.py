"""Application settings — everything comes from environment / .env. No hardcoded secrets."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "UniAssist — IUB Student Portal"
    environment: str = "dev"  # dev | production
    database_url: str = "sqlite:///./uniassist.db"  # PostgreSQL in production via .env
    jwt_secret: str = "dev-only-uniassist-secret-change-in-env-0123456789"  # >=32 bytes; set JWT_SECRET in .env for any real deployment
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7

    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # LLM (optional). provider: none | gemini | groq | ollama
    llm_provider: str = "none"
    llm_api_key: str = ""
    llm_model: str = ""
    ollama_base_url: str = "http://localhost:11434"

    chat_rate_limit_per_min: int = 60
    auth_rate_limit_per_min: int = 20

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
