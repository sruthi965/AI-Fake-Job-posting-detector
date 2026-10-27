"""FastAPI application entry point.

Run locally:  uvicorn app.main:app --reload
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api import auth, dashboard, history, predict
from app.core.config import get_settings
from app.database.connection import check_connection, init_db
from app.services.prediction_service import get_prediction_service

logging.basicConfig(level=logging.INFO)

CSP = "default-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
DOC_PATHS = ("/docs", "/redoc", "/openapi.json")


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings().validate()
    init_db()
    get_prediction_service()  # loads the model once at startup
    yield


app = FastAPI(
    title="JobGuard API",
    version=__version__,
    description="AI-Based Fake Job Posting Detector API",
    lifespan=lifespan,
)

_settings = get_settings()
if _settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_settings.cors_origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    if not request.url.path.startswith(DOC_PATHS):  # Swagger UI needs inline scripts and a CDN
        response.headers.setdefault("Content-Security-Policy", CSP)
    return response


@app.get("/health", tags=["system"], summary="Check application health")
def health():
    service = get_prediction_service()
    return {"status": "ok", "database": check_connection(), "model_loaded": service.model_loaded}


app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(history.router)
app.include_router(dashboard.router)

# The static frontend is mounted last so API routes take priority.
if _settings.frontend_dir.exists():
    app.mount("/", StaticFiles(directory=_settings.frontend_dir, html=True), name="frontend")
