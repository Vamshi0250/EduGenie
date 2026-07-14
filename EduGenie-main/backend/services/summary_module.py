"""
EduGenie — Summary Module  (Task 10 — spec-required module file)
Provides summarize_text() as documented.
"""

import logging
from backend.services.common import MAX_TEXT_CHARS, InputTooLongError
from backend.services.gemini_service import generate_response

logger = logging.getLogger("edugenie.summary")

SUMMARIZE_TEXT_PROMPT = """\
Summarize the following text for a student reviewing it before an exam.

---
{text}
---

Provide: a 2-3 sentence executive summary; up to 5 key points as a numbered \
list; one takeaway worth remembering.\
"""


def summarize_text(text: str) -> str:
    """Summarize text using Gemini."""
    if not text or not text.strip():
        raise ValueError("Please provide text to summarize.")
    if len(text) > MAX_TEXT_CHARS:
        raise InputTooLongError(f"Text exceeds {MAX_TEXT_CHARS} characters.")
    prompt = SUMMARIZE_TEXT_PROMPT.format(text=text)
    return generate_response(prompt, max_output_tokens=4096)
