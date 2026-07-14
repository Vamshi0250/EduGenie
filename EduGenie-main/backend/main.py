"""
EduGenie — FastAPI Application Entry Point

Changes applied:
  - Task 1: Spec-matching route aliases (GET /qa, POST /explain, /quiz,
    /summarize, GET /learn/recommendations) added at the top level.
  - Task 9: frontend/index.html is now served via Jinja2Templates instead of
    FileResponse, so the rendering pipeline matches the documented architecture.
"""

import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.database import create_tables, get_db
from backend.routes.api import router as api_router
from backend.routes.auth import router as auth_router
from backend.middleware.rate_limit import RateLimitMiddleware

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("edugenie")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
TEMPLATES_DIR = FRONTEND_DIR / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    logger.info("EduGenie startup complete.")
    yield


app = FastAPI(
    title="EduGenie",
    description="Educational assistant application",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
_default_dev_origins = [
    "http://localhost:5500", "http://127.0.0.1:5500",
    "http://localhost:8080", "http://127.0.0.1:8080",
    "http://localhost:3000", "http://127.0.0.1:3000",
    "http://localhost:8000", "http://127.0.0.1:8000",
]
_env_origins = os.getenv("CORS_ORIGINS", "")
allowed_origins = _default_dev_origins + [o.strip() for o in _env_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_middleware(
    RateLimitMiddleware,
    max_requests=int(os.getenv("RATE_LIMIT_MAX", "30")),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW", "60")),
)

# ── Jinja2 Templates (Task 9) ─────────────────────────────────────────────────
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ── Existing /api/* routes ────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth")

# ── Static assets ─────────────────────────────────────────────────────────────
app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")


# ── Root → Jinja2-rendered index.html ────────────────────────────────────────
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "auth.html")


# ── Spec-matching top-level route aliases (Task 1) ────────────────────────────
# Lazy import to avoid circular deps at module load.
from backend.routes.api import (  # noqa: E402
    ask as _ask_handler,
    explain as _explain_handler,
    quiz as _quiz_handler,
    summarize as _summarize_handler,
    recommend as _recommend_handler,
)
from backend.routes.api import AskRequest, ExplainRequest, QuizRequest, SummarizeRequest, RecommendRequest  # noqa: E402


@app.get("/qa")
async def qa_alias(
    request: Request,
    question: str = Query(..., description="The question to ask"),
    db: Session = Depends(get_db),
):
    """GET /qa — spec alias. Accepts 'question' as a query parameter."""
    req_body = AskRequest(question=question)
    return await _ask_handler(req_body, request, db)


@app.post("/explain")
async def explain_alias(
    request_body: ExplainRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """POST /explain — spec alias for POST /api/explain."""
    return await _explain_handler(request_body, request, db)


@app.post("/quiz")
async def quiz_alias(
    request_body: QuizRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """POST /quiz — spec alias. Accepts 'text' field; returns 3 MCQs by default."""
    return await _quiz_handler(request_body, request, db)


@app.post("/summarize")
async def summarize_alias(
    request_body: SummarizeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """POST /summarize — spec alias for POST /api/summarize."""
    return await _summarize_handler(request_body, request, db)


@app.get("/learn/recommendations")
async def learn_recommendations_alias(
    request: Request,
    topic: str = Query(..., description="Topic for learning path"),
    db: Session = Depends(get_db),
):
    """GET /learn/recommendations — spec alias. Accepts 'topic' as query param."""
    req_body = RecommendRequest(topic=topic)
    return await _recommend_handler(req_body, request, db)


# ── Utility endpoints ─────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


@app.get("/health")
async def health():
    return {"status": "healthy"}
