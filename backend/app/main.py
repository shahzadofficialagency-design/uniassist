"""UniAssist FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .api import admin, auth, catalog, chat
from .core.config import settings
from .db.base import SessionLocal, init_db
from .services.seed import seed


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables, seed the fee catalogue, then apply the
    # idempotent official-data imports (each upserts, safe on every boot).
    init_db()
    db = SessionLocal()
    try:
        seed(db)
        try:
            from .services.iub_web_import import import_iub_web
            print("IUB web import:", import_iub_web(db))
            from .services.campus_import import import_campus
            print("Campus import:", import_campus(db))
            from .services.enrichment_import import import_enrichment
            print("Enrichment import:", import_enrichment(db))
        except Exception:
            import traceback
            traceback.print_exc()
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Multilingual student portal + AI admissions & fee chatbot for "
                "the Islamia University of Bahawalpur. Fees come from the structured "
                "database (Revised Fee Structure Fall 2025) — never from an LLM.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(chat.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name, "llm_provider": settings.llm_provider}


@app.get("/")
def root():
    return {"app": settings.app_name, "docs": "/docs",
            "note": "Frontend runs separately (frontend/, Vite dev server on :5173)."}
