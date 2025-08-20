from fastapi import FastAPI
from app.core.logging import setup_logging
from app.core.config import settings
from app.api.health import router as health_router
from app.api.analyze import router as analyze_router


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="RAG Analysis Backend", version="0.1.0")

    # Routers
    app.include_router(health_router, prefix="")
    app.include_router(analyze_router, prefix="")

    return app


app = create_app()