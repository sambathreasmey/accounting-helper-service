from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.po_callback import router as po_callback_router
from app.api.telegram import router as telegram_router
from app.api.webapp_api import router as webapp_api_router
from app.api.auth import router as auth_router
from app.core.config import settings
from app.db.database import dispose_engine, init_models
from app.services.telegram_client import telegram_client

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()
    webhook_url = f"{settings.PUBLIC_BASE_URL.rstrip('/')}/telegram/webhook"
    await telegram_client.set_webhook(webhook_url, settings.TELEGRAM_WEBHOOK_SECRET)
    yield
    await telegram_client.close()
    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Accounting Helper Service",
        docs_url=None if settings.ENVIRONMENT == "production" else "/docs",
        redoc_url=None if settings.ENVIRONMENT == "production" else "/redoc",
        openapi_url=None if settings.ENVIRONMENT == "production" else "/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://accounting-helper-frontend.pages.dev",
            "https://myapp.sambathreasmey.site",
            "http://localhost:3000",
        ],
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "X-Telegram-Init-Data", "Authorization"],
    )

    app.include_router(auth_router)
    app.include_router(telegram_router)
    app.include_router(po_callback_router)
    app.include_router(webapp_api_router)
    # Old static Mini App — safe to remove once Cloudflare Pages is live,
    # or keep as a fallback at /app.
    app.mount(
        "/app", StaticFiles(directory=STATIC_DIR / "webapp", html=True), name="webapp"
    )

    @app.get("/healthz", status_code=status.HTTP_200_OK, tags=["System"])
    async def health_check():
        return {"status": "healthy"}

    @app.get("/")
    def main():
        return {"message": "ជោគជ័យទៀតហើយ"}

    return app


app = create_app()
