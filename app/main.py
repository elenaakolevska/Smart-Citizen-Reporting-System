from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import app.db.base  # noqa: F401
from app.api.router import api_router
from app.core.config import get_settings
from app.services.ai_service import warmup_model
from app.utils.dependencies import DEV_USER, get_current_user
from app.utils.file_upload import UPLOAD_DIR

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    if settings.ai_enabled and settings.ai_preload_on_startup:
        warmup_model()
    yield


app = FastAPI(
    title=settings.project_name,
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_origin_regex=settings.backend_cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.dev_skip_auth:
    app.dependency_overrides[get_current_user] = lambda: DEV_USER

app.mount("/static/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(api_router, prefix=settings.api_v1_str)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Lightweight health check (no DB calls)."""
    return {"status": "ok"}