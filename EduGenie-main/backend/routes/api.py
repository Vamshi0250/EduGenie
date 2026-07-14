"""
EduGenie — API Routes
All endpoints write to the database, mirror to JSON, and return structured JSON.

Priority-1 fixes applied:
  - Custom 400 JSONResponse for missing required fields (Task 3)
  - ⚠️/❌ error message format in AI failure responses (Task 4)
  - user_id from X-User-Id header for history segregation (Task 8)
  - JSON persistence mirror after every successful write (Task 7)
"""

import json
import logging
import traceback
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.query_history import QueryHistory
from backend.models.quiz import Quiz as QuizModel
from backend.routes.auth import get_current_user
from backend.services.qna import answer_question_with_gemini
from backend.services.explanation_module import explain_concept
from backend.services.quiz_module import generate_quiz
from backend.services.summary_module import summarize_text
from backend.services.learning_path import get_learning_recommendations
from backend.services.persistence import (
    record_query, record_response, record_quiz, record_summary, record_learning_path,
)
from backend.services.gemini_service import GeminiConfigError, GeminiAPIError

logger = logging.getLogger("edugenie.api")
router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _user_id(request: Request, db: Session) -> str:
    """Resolve the authenticated user's string ID.
    Checks the Bearer token first; falls back to the legacy X-User-Id UUID header
    so unauthenticated dev requests still work during testing."""
    user = get_current_user(request, db)
    if user:
        return str(user.id)
    # Legacy fallback — anonymous or UUID-based (dev / testing only)
    return request.headers.get("X-User-Id", "anonymous") or "anonymous"


def _ai_error_response(module_name: str, exc: Exception) -> JSONResponse:
    """Task 4: Return ⚠️ error format instead of raising HTTPException for AI errors."""
    msg = f"⚠️ Error in {module_name}: {exc}"
    logger.error("AI error in %s: %s", module_name, exc)
    return JSONResponse(status_code=502, content={"error": msg})


def _learning_path_error_response(exc: Exception) -> JSONResponse:
    """Task 4: Learning path errors — log full traceback + ❌ error format."""
    logger.error("Learning path error:\n%s", traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"error": f"❌ Error occurred: {str(exc)}"},
    )


# ── Request Schemas ────────────────────────────────────────────────────────────
# Fields are Optional[str] so we can intercept missing values before Pydantic
# raises a generic 422.  Manual validation returns spec-matching 400 messages.

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The question to ask")

class ExplainRequest(BaseModel):
    topic: str | None = Field(default=None, description="The topic to explain")

class QuizRequest(BaseModel):
    # Spec-facing field is 'text'; keep 'topic' as alias so /api/quiz stays compatible
    text: str | None = Field(default=None, description="Topic / text for the quiz")
    topic: str | None = Field(default=None, description="Alias for text (legacy /api/quiz)")
    num_questions: int = Field(default=3, ge=1, le=20)

class SummarizeRequest(BaseModel):
    text: str | None = Field(default=None, min_length=None, description="Text to summarize")

class RecommendRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="Topic for learning path")


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/ask")
async def ask(request_body: AskRequest, request: Request, db: Session = Depends(get_db)):
    """Ask a general educational question."""
    uid = _user_id(request, db)
    try:
        answer = answer_question_with_gemini(request_body.question)
    except Exception as e:
        return _ai_error_response("QnA", e)

    record = QueryHistory(
        user_id=uid,
        question=request_body.question,
        answer=answer,
        interaction_type="ask",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    record_query("ask", request_body.question, uid, record.id)
    record_response(request_body.question, answer, "ask", uid, record.id)

    return {"question": request_body.question, "answer": answer}


@router.post("/explain")
async def explain(request_body: ExplainRequest, request: Request, db: Session = Depends(get_db)):
    """Get a structured explanation of a topic."""
    # Task 3 — custom 400
    if not request_body.topic or not request_body.topic.strip():
        return JSONResponse(status_code=400, content={"error": "Please provide a topic."})

    uid = _user_id(request, db)
    try:
        explanation = explain_concept(request_body.topic)
    except Exception as e:
        return _ai_error_response("Explanation", e)

    record = QueryHistory(
        user_id=uid,
        question=request_body.topic,
        answer=explanation,
        interaction_type="explain",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    record_query("explain", request_body.topic, uid, record.id)
    record_response(request_body.topic, explanation, "explain", uid, record.id)

    return {"topic": request_body.topic, "explanation": explanation}


@router.post("/quiz")
async def quiz(request_body: QuizRequest, request: Request, db: Session = Depends(get_db)):
    """Generate a multiple-choice quiz.  Accepts 'text' (spec) or 'topic' (legacy)."""
    # Task 3 — custom 400; try 'text' first, then legacy 'topic' alias
    topic = (request_body.text or request_body.topic or "").strip()
    if not topic:
        return JSONResponse(status_code=400, content={"error": "Please provide text for quiz."})

    uid = _user_id(request, db)
    try:
        questions = generate_quiz(topic, request_body.num_questions)
    except Exception as e:
        return _ai_error_response("Quiz", e)

    questions_str = json.dumps(questions)

    quiz_record = QuizModel(
        user_id=uid,
        topic=topic,
        questions_json=questions_str,
    )
    db.add(quiz_record)

    history_record = QueryHistory(
        user_id=uid,
        question=f"Quiz: {topic} ({request_body.num_questions} questions)",
        answer=questions_str,
        interaction_type="quiz",
    )
    db.add(history_record)
    db.commit()
    db.refresh(quiz_record)
    db.refresh(history_record)

    record_quiz(topic, questions, uid, quiz_record.id)
    record_query("quiz", f"Quiz: {topic}", uid, history_record.id)

    # Return 'quiz' key for spec-matching; also keep 'questions' for /api/quiz compat
    return {"topic": topic, "questions": questions, "quiz": questions}


@router.post("/summarize")
async def summarize(request_body: SummarizeRequest, request: Request, db: Session = Depends(get_db)):
    """Summarize a block of text."""
    # Task 3 — custom 400
    if not request_body.text or not request_body.text.strip():
        return JSONResponse(status_code=400, content={"error": "Please provide text to summarize."})
    if len(request_body.text) < 10:
        return JSONResponse(status_code=400, content={"error": "Please provide text to summarize."})

    uid = _user_id(request, db)
    try:
        summary = summarize_text(request_body.text)
    except Exception as e:
        return _ai_error_response("Summary", e)

    truncated_input = request_body.text[:200] + "..." if len(request_body.text) > 200 else request_body.text
    record = QueryHistory(
        user_id=uid,
        question=truncated_input,
        answer=summary,
        interaction_type="summarize",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    record_summary(request_body.text, summary, uid, record.id)
    record_query("summarize", truncated_input, uid, record.id)

    return {"summary": summary}


@router.post("/recommend")
async def recommend(request_body: RecommendRequest, request: Request, db: Session = Depends(get_db)):
    """Generate a learning path for a topic."""
    uid = _user_id(request, db)
    try:
        path = get_learning_recommendations(request_body.topic)
    except RuntimeError as e:
        # RuntimeError from learning_path.py already wraps ❌ message
        return _learning_path_error_response(e)
    except Exception as e:
        return _learning_path_error_response(e)

    path_str = json.dumps(path)
    record = QueryHistory(
        user_id=uid,
        question=request_body.topic,
        answer=path_str,
        interaction_type="recommend",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    record_learning_path(request_body.topic, path, uid, record.id)
    record_query("recommend", request_body.topic, uid, record.id)

    return {"topic": request_body.topic, "learning_path": path, "recommendation": path}


@router.get("/history")
async def history(request: Request, limit: int = 50, db: Session = Depends(get_db)):
    """Retrieve recent interaction history — scoped to the logged-in user."""
    uid = _user_id(request, db)
    query = db.query(QueryHistory)
    if uid != "anonymous":
        query = query.filter(QueryHistory.user_id == uid)
    records = (
        query
        .order_by(QueryHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    return {"history": [r.to_dict() for r in records]}
