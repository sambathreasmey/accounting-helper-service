from contextlib import asynccontextmanager

from fastapi import FastAPI, status

from app.api.telegram import router as telegram_router
from app.core.config import settings
from app.services.telegram_client import telegram_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    webhook_url = f"{settings.PUBLIC_BASE_URL.rstrip('/')}/telegram/webhook"
    await telegram_client.set_webhook(webhook_url, settings.TELEGRAM_WEBHOOK_SECRET)
    yield
    await telegram_client.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Accounting Helper Service",
        docs_url=None if settings.ENVIRONMENT == "production" else "/docs",
        redoc_url=None if settings.ENVIRONMENT == "production" else "/redoc",
        openapi_url=None if settings.ENVIRONMENT == "production" else "/openapi.json",
        lifespan=lifespan,
    )

    app.include_router(telegram_router)

    @app.get("/healthz", status_code=status.HTTP_200_OK, tags=["System"])
    async def health_check():
        return {"status": "healthy"}

    @app.get("/")
    def main():
        return {"message": "ជោគជ័យទៀតហើយ"}

    return app


app = create_app()