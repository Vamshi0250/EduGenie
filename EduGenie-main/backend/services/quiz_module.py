"""
EduGenie — Quiz Module  (Task 10 — spec-required module file)
Provides generate_quiz() and clean_json_block() as documented.
Default MCQ count is 3 (Task 2 fix).
"""

import json
import re
import logging
from backend.services.common import MAX_TOPIC_CHARS, InputTooLongError, _extract_json
from backend.services.gemini_service import generate_response

logger = logging.getLogger("edugenie.quiz")

# Spec default: 3 MCQs  (Task 2 — was 5)
DEFAULT_NUM_QUESTIONS = 3

GENERATE_QUIZ_PROMPT = """\
Create exactly {num_questions} multiple-choice questions about: "{topic}"

You MUST return ONLY a valid JSON array. No markdown, no code fences, no extra text.
The JSON must be complete and properly closed. Each element:
{{"question": "...", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], "correct_answer": "A"}}

correct_answer must be exactly one of: A, B, C, or D.
Vary difficulty from easy to hard. Make distractors plausible.\
"""


def clean_json_block(raw: str) -> str:
    """Strip markdown fences and surrounding prose from a JSON string."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned


def generate_quiz(topic: str, num_questions: int = DEFAULT_NUM_QUESTIONS) -> list:
    """Generate a multiple-choice quiz. Uses 3 questions by default per spec."""
    if not topic or not topic.strip():
        raise ValueError("Please provide text for quiz.")
    if len(topic) > MAX_TOPIC_CHARS:
        raise InputTooLongError(f"Topic exceeds {MAX_TOPIC_CHARS} characters.")
    if not (1 <= num_questions <= 20):
        num_questions = DEFAULT_NUM_QUESTIONS

    prompt = GENERATE_QUIZ_PROMPT.format(topic=topic, num_questions=num_questions)
    # Use 4096 tokens — 2048 was too small for 5+ questions and caused truncated JSON
    raw = generate_response(prompt, max_output_tokens=4096)

    try:
        questions = _extract_json(raw)
        if isinstance(questions, list) and questions:
            return questions
        raise ValueError("Model did not return a non-empty JSON array.")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("Quiz JSON parse failed topic=%r: %s\nRaw: %.800s", topic, e, raw)
        raise RuntimeError("Failed to generate a valid quiz. Please try again.") from e
