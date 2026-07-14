"""
EduGenie — Learning Path Module  (Task 10 — spec-required module file)
Provides get_learning_recommendations() as documented.
"""

import json
import logging
import traceback
from backend.services.common import MAX_TOPIC_CHARS, InputTooLongError, _extract_json
from backend.services.gemini_service import generate_response

logger = logging.getLogger("edugenie.learning_path")

RECOMMEND_LEARNING_PATH_PROMPT = """\
Build a three-level learning path (beginner/intermediate/advanced) for: "{topic}"

You MUST return ONLY a valid JSON object. No markdown, no code fences, no extra text.
The JSON must be complete and properly closed. Use this exact structure:
{{
  "topic": "{topic}",
  "beginner": {{"description": "...", "resources": ["resource1", "resource2", "resource3"], "projects": ["project1", "project2"], "duration": "..."}},
  "intermediate": {{"description": "...", "resources": ["resource1", "resource2", "resource3"], "projects": ["project1", "project2"], "duration": "..."}},
  "advanced": {{"description": "...", "resources": ["resource1", "resource2", "resource3"], "projects": ["project1", "project2"], "duration": "..."}}
}}

Use real, specific resource names (books, courses, docs) and realistic time estimates.\
"""


def get_learning_recommendations(topic: str) -> dict:
    """Generate a structured learning path. Documented function name per spec."""
    if not topic or not topic.strip():
        raise ValueError("Please provide a topic.")
    if len(topic) > MAX_TOPIC_CHARS:
        raise InputTooLongError(f"Topic exceeds {MAX_TOPIC_CHARS} characters.")

    prompt = RECOMMEND_LEARNING_PATH_PROMPT.format(topic=topic)
    # Use 4096 tokens — the previous 1536 was too small and caused truncated/empty JSON
    raw = generate_response(prompt, max_output_tokens=4096)

    try:
        path = _extract_json(raw)
        if isinstance(path, dict) and "beginner" in path:
            return path
        raise ValueError("Model did not return the expected learning-path structure.")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(
            "Learning path JSON parse failed topic=%r\n%s\nRaw: %.800s",
            topic, traceback.format_exc(), raw,
        )
        # Return a raw_response fallback so the frontend can still display something
        return {"topic": topic, "raw_response": raw, "parse_error": str(e)}


# Internal alias used by api.py
recommend_learning_path = get_learning_recommendations
