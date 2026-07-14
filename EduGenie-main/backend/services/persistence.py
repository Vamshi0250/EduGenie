"""
EduGenie — JSON Persistence Layer  (Task 7)
Mirrors every AI interaction from SQLite to append-only JSON files in data/
matching the ER diagram entities: USER_QUERY, AI_RESPONSE, QUIZ, SUMMARY, LEARNING_PATH.

Files created:
    data/queries.json       — USER_QUERY records
    data/responses.json     — AI_RESPONSE records
    data/quizzes.json       — QUIZ records
    data/summaries.json     — SUMMARY records
    data/learning_paths.json — LEARNING_PATH records
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("edugenie.persistence")

# Resolve data/ relative to the project root (two levels up from this file)
_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def _ensure_data_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _append(filename: str, record: dict) -> None:
    """Append one JSON record to a newline-delimited JSON file (JSON Lines)."""
    _ensure_data_dir()
    filepath = _DATA_DIR / filename
    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning("JSON persistence write failed for %s: %s", filename, e)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Public mirrors ─────────────────────────────────────────────────────────

def record_query(
    interaction_type: str,
    question: str,
    user_id: str = "anonymous",
    db_id: int | None = None,
) -> None:
    """Mirror a USER_QUERY record to data/queries.json."""
    _append("queries.json", {
        "id": db_id,
        "user_id": user_id,
        "interaction_type": interaction_type,
        "question": question,
        "created_at": _now_iso(),
    })


def record_response(
    question: str,
    answer: str,
    interaction_type: str,
    user_id: str = "anonymous",
    db_id: int | None = None,
) -> None:
    """Mirror an AI_RESPONSE record to data/responses.json."""
    _append("responses.json", {
        "id": db_id,
        "user_id": user_id,
        "interaction_type": interaction_type,
        "question": question,
        "answer": answer,
        "created_at": _now_iso(),
    })


def record_quiz(
    topic: str,
    questions: list,
    user_id: str = "anonymous",
    db_id: int | None = None,
) -> None:
    """Mirror a QUIZ record to data/quizzes.json."""
    _append("quizzes.json", {
        "id": db_id,
        "user_id": user_id,
        "topic": topic,
        "questions": questions,
        "created_at": _now_iso(),
    })


def record_summary(
    input_text: str,
    summary: str,
    user_id: str = "anonymous",
    db_id: int | None = None,
) -> None:
    """Mirror a SUMMARY record to data/summaries.json."""
    _append("summaries.json", {
        "id": db_id,
        "user_id": user_id,
        "input_preview": input_text[:200],
        "summary": summary,
        "created_at": _now_iso(),
    })


def record_learning_path(
    topic: str,
    path: dict,
    user_id: str = "anonymous",
    db_id: int | None = None,
) -> None:
    """Mirror a LEARNING_PATH record to data/learning_paths.json."""
    _append("learning_paths.json", {
        "id": db_id,
        "user_id": user_id,
        "topic": topic,
        "path": path,
        "created_at": _now_iso(),
    })
