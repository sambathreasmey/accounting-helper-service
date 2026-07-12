from fastapi import FastAPI, HTTPException, status
from app.core.config import settings


def create_app() -> FastAPI:

    app = FastAPI(
        title="Accounting Helper Service",
        docs_url=None if settings.ENVIRONMENT == "production" else "/docs",
        redoc_url=None if settings.ENVIRONMENT == "production" else "/redoc",
        openapi_url=None if settings.ENVIRONMENT == "production" else "/openapi.json",
    )

    @app.get("/healthz", status_code=status.HTTP_200_OK, tags=["System"])
    async def health_check():
        try:
            # Fast query execution test (e.g., SELECT 1)
            # await verify_database_connection()
            return {"status": "healthy"}
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database connectivity issue: {str(err)}",
            )

    @app.get("/")
    def main():
        return {"message": "ជោគជ័យទៀតហើយ"}

    return app


app = create_app()
