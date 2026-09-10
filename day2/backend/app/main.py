"""
LeadFlow AI — FastAPI Application Entrypoint (Day 2 v0)
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router
from .config import get_settings
from .services.audit_logger import init_audit_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("leadflow.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Initializing LeadFlow AI v0 (Day 2)...")
    logger.info(f"SQLite audit DB: {settings.sqlite_db_path}")
    init_audit_db(settings.sqlite_db_path)
    logger.info(f"Gemini API available: {settings.gemini_available}")
    yield
    logger.info("Shutting down LeadFlow AI v0.")


app = FastAPI(
    title="LeadFlow AI — Bounded AI Operating System (v0)",
    description=(
        "Inbound B2B lead triage, account enrichment, deterministic ICP qualification, "
        "first-touch drafting, claim validation, human approval, and CRM payload dispatch."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for local frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Mount frontend as static files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="frontend")

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_quickstart():
    html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "frontend", "quickstart.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>LeadFlow AI — Quickstart page not found.</h1>")

@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def serve_dashboard():
    html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "frontend", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>LeadFlow AI — Dashboard not found.</h1>")


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run("backend.app.main:app", host=settings.api_host, port=settings.api_port, reload=True)
