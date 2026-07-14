"""
EduGenie — features.py  (backward-compat shim after Task 10 split)
Re-exports all functions from the spec-required module files so existing
imports (e.g. tests) continue to work unchanged.
"""
from backend.services.qna import answer_question_with_gemini, answer_question  # noqa: F401
from backend.services.explanation_module import explain_topic, explain_concept  # noqa: F401
from backend.services.quiz_module import generate_quiz, clean_json_block  # noqa: F401
from backend.services.summary_module import summarize_text  # noqa: F401
from backend.services.learning_path import (  # noqa: F401
    get_learning_recommendations,
    recommend_learning_path,
)
from backend.services.common import InputTooLongError  # noqa: F401
