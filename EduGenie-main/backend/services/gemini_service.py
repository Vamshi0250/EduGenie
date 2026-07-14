"""
EduGenie — Gemini AI Service
Handles communication with Google's Gemini AI: lazy client init, retries with
backoff on transient failures, and a single shared system instruction so
individual prompts don't need to re-introduce the assistant's persona.
"""

import os
import time
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, DeadlineExceeded

load_dotenv()

logger = logging.getLogger("edugenie.gemini")

# gemini-3.5-flash is confirmed available and working for this API key.
DEFAULT_MODEL_NAME = "gemini-3.5-flash"
MODEL_NAME = os.getenv("GEMINI_MODEL", DEFAULT_MODEL_NAME)
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 1.5

SYSTEM_INSTRUCTION = (
    "You are EduGenie, an educational assistant. Give accurate, well-organized "
    "answers pitched at a curious student. Prefer short paragraphs and concrete "
    "examples over generic filler. Never pad answers with disclaimers or "
    "restate the question back to the user."
)

# Errors worth retrying — transient/server-side. Anything else (bad request,
# auth failure) should fail fast instead of burning retries.
_RETRYABLE_EXCEPTIONS = (ResourceExhausted, ServiceUnavailable, DeadlineExceeded)

_model = None


class GeminiConfigError(Exception):
    """Raised when the Gemini API key is missing or invalid."""


class GeminiAPIError(Exception):
    """Raised when the Gemini API returns a non-retryable or exhausted-retry error."""


def _get_model():
    """Lazily initialize and cache the Gemini model instance."""
    global _model
    if _model is not None:
        return _model

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        raise GeminiConfigError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your "
            "key from https://aistudio.google.com/apikey"
        )

    genai.configure(api_key=api_key)
    _model = genai.GenerativeModel(MODEL_NAME, system_instruction=SYSTEM_INSTRUCTION)
    return _model


def generate_response(
    prompt: str,
    *,
    temperature: float = 0.6,
    max_output_tokens: int = 1024,
) -> str:
    """Send a prompt to Gemini and return the text response.

    Retries transient failures (rate limits, timeouts, 503s) with exponential
    backoff. Config errors and non-retryable errors surface immediately.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    model = _get_model()  # raises GeminiConfigError before we touch the network

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )
            if not response.candidates:
                raise GeminiAPIError("Gemini returned no candidates (likely blocked by safety filters).")
            return response.text

        except _RETRYABLE_EXCEPTIONS as e:
            last_error = e
            if attempt < MAX_RETRIES:
                sleep_for = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
                logger.warning("Gemini call failed (attempt %d/%d): %s — retrying in %.1fs",
                               attempt, MAX_RETRIES, e, sleep_for)
                time.sleep(sleep_for)
            continue

        except Exception as e:
            # Non-retryable — fail fast.
            raise GeminiAPIError(f"Gemini API call failed: {e}") from e

    raise GeminiAPIError(f"Gemini API call failed after {MAX_RETRIES} attempts: {last_error}")
