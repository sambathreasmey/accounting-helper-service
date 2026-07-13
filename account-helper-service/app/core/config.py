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

    # GitHub Actions calls this endpoint back when PO generation finishes.
    PO_CALLBACK_SECRET: str

    # Telegram Mini App (dashboard / history / regenerate UI)
    MINI_APP_URL: str = ""  # e.g. https://your-app.fastapicloud.dev/app

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def async_database_url(self) -> str:
        """Normalize a Neon/Postgres URL for SQLAlchemy's asyncpg driver."""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        # Neon URLs often carry "sslmode=require", which asyncpg doesn't
        # accept as a query param — ssl is configured via connect_args instead.
        if "?" in url:
            url = url.split("?", 1)[0]
        return url


settings = AppSettings()
