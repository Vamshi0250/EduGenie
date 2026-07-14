"""
EduGenie — QnA Module  (Task 10 — spec-required module file)
Provides answer_question_with_gemini() as documented.
"""

import logging
from backend.services.common import MAX_QUESTION_CHARS, InputTooLongError
from backend.services.gemini_service import generate_response

logger = logging.getLogger("edugenie.qna")

ANSWER_QUESTION_PROMPT = """\
Answer the following student question clearly and directly. Structure the \
answer in short paragraphs. If the question is ambiguous, answer the most \
likely interpretation and briefly note the assumption.

Question: "{question}"\
"""


def answer_question_with_gemini(question: str) -> str:
    """Public entry-point matching the documented function name."""
    if not question or not question.strip():
        raise ValueError("Please provide a question.")
    if len(question) > MAX_QUESTION_CHARS:
        raise InputTooLongError(f"Question exceeds {MAX_QUESTION_CHARS} characters.")
    prompt = ANSWER_QUESTION_PROMPT.format(question=question)
    # 4096 tokens ensures full answers are never cut mid-sentence
    return generate_response(prompt, max_output_tokens=4096)


# Alias for internal backward-compat
answer_question = answer_question_with_gemini
