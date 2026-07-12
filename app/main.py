
from fastapi import FastAPI

def create_app() -> FastAPI:

    app = FastAPI(
        version="1.0.0"
    )

    @app.get("/healthz", tags=["ops"])
    async def health_check() -> dict:
        return {"status": "ok"}
    
    @app.get("/")
    def main():
        return {"message": "ជោគជ័យទៀតហើយ"}
    
    return app

app = create_app()  