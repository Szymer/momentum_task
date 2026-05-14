import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Momentum Task"
    api_v1_prefix: str = "/api/v1"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:change_me_in_real_env@localhost:5432/momentum_task",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
