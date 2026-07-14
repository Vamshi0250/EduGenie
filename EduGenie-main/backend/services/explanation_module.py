"""
EduGenie — Explanation Module  (Task 5 + Task 10)
Primary model: LaMini-Flan-T5-783M (local CPU)
Fallback: Google Gemini (if local model unavailable)
"""

import logging
from backend.services.common import MAX_TOPIC_CHARS, InputTooLongError
from backend.services.gemini_service import generate_response

logger = logging.getLogger("edugenie.explanation")

EXPLAIN_CONCEPT_PROMPT = """\
Explain the following concept to someone encountering it for the first time.

Topic: "{topic}"

Cover, in order: a one-sentence definition; why it matters in practice; the \
key components or principles; one concrete example; one common misconception.\
"""

# ── Local model (LaMini-Flan-T5-783M) ─────────────────────────────────────
# Loaded lazily once, then cached.  None means "not yet attempted".
# False means "failed to load — use Gemini fallback".
_local_tokenizer = None
_local_model = None
_local_model_loaded: bool | None = None   # None=untried, True=ok, False=failed


def _load_local_model():
    """Try to load LaMini-Flan-T5-783M. Sets module-level sentinels."""
    global _local_tokenizer, _local_model, _local_model_loaded
    if _local_model_loaded is not None:
        return _local_model_loaded

    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        import torch

        model_name = "MBZUAI/LaMini-Flan-T5-783M"
        logger.info("Loading local explanation model: %s …", model_name)
        _local_tokenizer = AutoTokenizer.from_pretrained(model_name)
        _local_model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,  # CPU-safe
        )
        _local_model.eval()
        logger.info("Local explanation model loaded successfully.")
        _local_model_loaded = True
    except Exception as e:
        logger.warning(
            "LaMini-Flan-T5-783M failed to load (%s). "
            "Falling back to Gemini for /explain.",
            e,
        )
        _local_model_loaded = False

    return _local_model_loaded


def _explain_via_local(topic: str) -> str:
    """Generate explanation using the local LaMini model."""
    import torch

    prompt = (
        f"Explain the concept '{topic}' in simple, beginner-friendly language. "
        f"Include a definition, why it matters, key components, a concrete example, "
        f"and one common misconception."
    )
    inputs = _local_tokenizer(
        prompt,
        return_tensors="pt",
        max_length=512,
        truncation=True,
    )
    with torch.no_grad():
        output_ids = _local_model.generate(
            **inputs,
            max_new_tokens=150,
            temperature=0.7,
            top_k=50,
            top_p=0.95,
            do_sample=True,
        )
    return _local_tokenizer.decode(output_ids[0], skip_special_tokens=True)


def explain_topic(topic: str) -> str:
    """Public entry-point matching the documented function name.
    Tries the local model first; falls back to Gemini on failure.
    """
    if not topic or not topic.strip():
        raise ValueError("Please provide a topic.")
    if len(topic) > MAX_TOPIC_CHARS:
        raise InputTooLongError(f"Topic exceeds {MAX_TOPIC_CHARS} characters.")

    model_ok = _load_local_model()
    if model_ok:
        try:
            return _explain_via_local(topic)
        except Exception as e:
            logger.warning(
                "Local model inference failed (%s); falling back to Gemini.", e
            )

    # Gemini fallback
    prompt = EXPLAIN_CONCEPT_PROMPT.format(topic=topic)
    return generate_response(prompt, max_output_tokens=4096)


# Alias used by api.py / features.py
explain_concept = explain_topic
