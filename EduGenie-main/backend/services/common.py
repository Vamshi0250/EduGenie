"""
EduGenie — Shared Helpers
Common utilities used across all feature modules.
"""

import json
import re
import logging

logger = logging.getLogger("edugenie.common")

# ── Input caps ────────────────────────────────────────────────────────────────
MAX_QUESTION_CHARS = 2000
MAX_TOPIC_CHARS = 300
MAX_TEXT_CHARS = 20000


class InputTooLongError(ValueError):
    pass


def _extract_json(raw: str):
    """Pull a JSON value out of a model response that may be wrapped in
    markdown fences, have leading/trailing prose, etc. Returns parsed object
    or raises json.JSONDecodeError."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    # If there's still stray text around the JSON, grab the outermost
    # {...} or [...] block.
    match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1)

    return json.loads(cleaned)
