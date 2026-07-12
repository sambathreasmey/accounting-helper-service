from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    ENVIRONMENT: str = Field(default="production")
    DATABASE_URL: str
    REDIS_URL: str

    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_SECRET: str
    PUBLIC_BASE_URL: str

    GITHUB_TOKEN: str
    GITHUB_REPO_OWNER: str = "sambathreasmey"
    GITHUB_REPO_NAME: str = "po-generate-automation"
    ALERT_CHAT_ID: int | None = None  # optional ops chat for dispatch-failure alerts

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = AppSettings()