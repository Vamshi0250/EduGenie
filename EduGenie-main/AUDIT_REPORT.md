# EduGenie Project Audit Report

## 1. File Inventory
The following files were found and reviewed in the project structure:

**Root Directory**
- `README.md`: Project documentation.
- `SUBMISSION.md`: Developer notes mapping work to epics/stories.
- `requirements.txt`: Python dependencies.
- `.env` / `.env.example`: Environment variables (Gemini API key, CORS, etc.).
- `render.yaml`: Deployment configuration for Render.
- `scan_edugenie.py`, `edugenie-full-scan-report.json`: Likely external scanning/audit artifacts.

**Backend (`backend/`)**
- `main.py`: FastAPI entry point, CORS, rate-limiting, and static file serving.
- `database.py`: SQLAlchemy and SQLite database configuration.
- `test_gemini.py`: Standalone script to verify Gemini API key.
- `models/query_history.py`, `models/quiz.py`: SQLAlchemy database models.
- `routes/api.py`: FastAPI router defining the API endpoints.
- `services/features.py`: Core logic and prompt templates for all AI features.
- `services/gemini_service.py`: Wrapper for `google-generativeai` SDK with retry logic.
- `middleware/rate_limit.py`: Custom rate limiting middleware.
- `tests/test_endpoints.py`, `tests/test_gemini_service.py`: Test suite.

**Frontend (`frontend/`)**
- `index.html`: Main static HTML layout.
- `css/styles.css`: Application styling.
- `css/design-tokens.css`: CSS variables for design system.
- `js/app.js`: Vanilla JavaScript for UI interactions and AJAX API calls.

## 2. Structure Comparison Table

| Required File / Component | Present | Deviations & Notes |
| :--- | :---: | :--- |
| `main.py` | ✅ Yes | Located at `backend/main.py`. |
| `qna.py` | ⚠️ No | Logic consolidated into `backend/services/features.py` (`answer_question`). |
| `explanation_module.py` | ⚠️ No | Logic consolidated into `backend/services/features.py` (`explain_concept`). |
| `quiz_module.py` | ⚠️ No | Logic consolidated into `backend/services/features.py` (`generate_quiz`). |
| `summary_module.py` | ⚠️ No | Logic consolidated into `backend/services/features.py` (`summarize_text`). |
| `learning_path.py` | ⚠️ No | Logic consolidated into `backend/services/features.py` (`recommend_learning_path`). |
| `templates/index.html` | ⚠️ No | App uses a static frontend (`frontend/index.html`) rather than Jinja2 templates. |
| `static/style.css` | ⚠️ No | Located at `frontend/css/styles.css`. |
| `requirements.txt` | ✅ Yes | Located in the project root. |

## 3. Endpoint Comparison Table

| Required Endpoint | Method | Implemented? | Matches Spec? | Issues & Notes |
| :--- | :--- | :---: | :---: | :--- |
| `/qa` | GET | ⚠️ Partial | No | Implemented as `POST /api/ask` (body: `{"question": ...}`). |
| `/explain` | POST | ✅ Yes | ⚠️ Partial | Uses `POST /api/explain`. Missing field returns FastAPI's default `422 Unprocessable Entity` instead of requested `400` with specific error format. |
| `/quiz` | POST | ✅ Yes | ⚠️ Partial | Uses `POST /api/quiz`. Generates 5 MCQs by default (configurable) instead of strictly 3. Uses `422` instead of `400` for missing fields. |
| `/summarize` | POST | ✅ Yes | ⚠️ Partial | Uses `POST /api/summarize`. Uses `422` instead of `400` for missing fields. |
| `/learn/recommendations` | GET | ⚠️ Partial | No | Implemented as `POST /api/recommend` (body: `{"topic": ...}`). |

## 4. Model Usage Verification
- **Required**: Google Gemini 1.5 Pro (cloud) + LaMini-Flan-T5-783M (local, CPU).
- **Actual**: ❌ LaMini-Flan-T5 is **not** implemented. The application relies entirely on the Gemini API for all features. The default model used is `gemini-3.5-flash` (`backend/services/gemini_service.py:19`).

## 5. Frontend Verification
- **Sections Present**: ✅ All 5 sections (Ask, Explain, Quiz, Summarize, Path) plus a History section are present (`frontend/index.html:20`).
- **AJAX Wiring**: ✅ Uses `fetch()` in `frontend/js/app.js` (line 224) to dynamically load data. No full page reloads occur.
- **Output Containers**: ✅ Results are injected dynamically into the `#results-panel` and `#results-body`. The quiz has interactive "Check Answer" functionality.

## 6. Error Handling Verification
- **Validation Errors**: ⚠️ Instead of returning custom `400` JSONResponses with specific error messages, the app relies on Pydantic models which throw generic `422` validation errors.
- **Gemini Exceptions**: ⚠️ Exceptions are not caught and returned exactly as `"⚠️ Error in {Module}: {e}"`. Instead, they are mapped to standard HTTP statuses (503, 502, 400) via `_raise_ai_error` (`backend/routes/api.py:47`).
- **Learning Path Errors**: ⚠️ Errors are logged server-side, but a generic `500` HTTP exception (`Unexpected error: Failed to generate a valid learning path. Please try again.`) is thrown rather than the specific `"❌ Error occurred: {str(e)}"`.

## 7. Data Persistence Check
- **Spec requirement**: File-based JSON storage.
- **Actual implementation**: ❌ The app uses a **SQLite database** (`sqlite:///./edugenie.db`) via SQLAlchemy (`backend/database.py`), not file-based JSON storage.

## 8. Deployment Verification
- **Dependencies**: ✅ `pip list` matches packages inside `requirements.txt`. Key packages like `fastapi`, `uvicorn`, `google-generativeai`, and `sqlalchemy` are installed and correctly pinned.
- **Dry-run Startup**: ✅ `uvicorn backend.main:app --port 8000` ran successfully. Output confirmed: `INFO: Application startup complete.` No missing env vars or import errors.

## 9. Gap Summary

- ❌ **Missing**:
  - `LaMini-Flan-T5-783M` local model integration (All endpoints use Gemini).
  - Jinja2 templating (frontend is entirely static).
  - Custom `400` error formatting for missing parameters (currently using FastAPI default `422`).
  - File-based JSON storage (using SQLite instead).

- ⚠️ **Partial / Deviates from spec**:
  - Endpoints have been moved under an `/api/` prefix.
  - `/qa` is implemented as `POST /api/ask`.
  - `/learn/recommendations` is implemented as `POST /api/recommend`.
  - Modules (`qna.py`, `explanation_module.py`, etc.) are consolidated into `backend/services/features.py`.

- ✅ **Matches spec**:
  - FastAPI backend and HTML/Vanilla CSS/JS frontend.
  - Generates Quizzes, Summaries, Explanations, Learning Paths, and direct Answers.
  - Frontend uses AJAX and dynamic DOM updates.
  - Runs with `uvicorn`.

- 🐛 **Bugs / Risks**:
  - **No explicit input sanitization** before sending to Gemini, relying solely on Pydantic's length constraints (e.g. `max_length` missing on some endpoints, though custom length limits exist in `features.py`).
  - The history endpoint (`/api/history`) currently has no user segregation. Any user can see all queries from all other users.

## 10. Prioritized Recommendations

**Blocking Issues / High Priority**
1. **Model Compliance**: If `LaMini-Flan-T5` is a strict requirement for offline/local explanations, it must be integrated into `backend/services/features.py` for the `/explain` endpoint.
2. **Data Storage**: Refactor `backend/database.py` and the routes to use file-based JSON instead of SQLite if the spec requirement is inflexible.
3. **API Contracts**: Update routing paths (e.g., `/api/ask` to `GET /qa`) and Pydantic exception handlers to match the exact `400` error shapes required by the spec.

**Polish / Low Priority**
4. **Refactor Code Structure**: If the strict 6-module structure is required, split `backend/services/features.py` back into `qna.py`, `explanation_module.py`, etc.
5. **Update Frontend Templates**: Convert `frontend/index.html` into a Jinja2 template rendered via a FastAPI `Jinja2Templates` instance, passing variables if required.
6. **Error Message Formatting**: Add an exception handler in FastAPI to format errors exactly as `"⚠️ Error in {Module}: {e}"`.

---

## 11. Post-Fix Status (Implemented Gaps)

### Priority 1 — API Contract Compliance
- **Task 1: Route Aliases**: Implemented top-level route aliases matching the exact specs in `backend/main.py`:
  - `GET /qa?question=...` (wraps Ask logic).
  - `POST /explain` (wraps Explain logic).
  - `POST /quiz` (wraps Quiz logic).
  - `POST /summarize` (wraps Summarize logic).
  - `GET /learn/recommendations?topic=...` (wraps Path logic).
- **Task 2: Quiz MCQ Count**: Pinned the default question count strictly to `3` in `backend/services/quiz_module.py`.
- **Task 3: Custom 400 Responses**: Replaced Pydantic's generic `422` validation response for missing fields with manual schema validation in `backend/routes/api.py`. Missing fields on `/explain`, `/summarize`, and `/quiz` return `400` status codes with specific messages matching the spec (e.g. `{"error": "Please provide a topic."}`).
- **Task 4: AI Error Messages**: Modified `_raise_ai_error` and specific handlers in `backend/routes/api.py`. Exceptions from Gemini/AI return a standard body format (e.g. `{"error": "⚠️ Error in QnA: {exc}"}`). Learning path exceptions log tracebacks server-side and return `{"error": "❌ Error occurred: {exc}"}` to the client.

### Priority 2 — AI Model Compliance
- **Task 5: LaMini-Flan-T5-783M**: Added `transformers` and `torch` dependencies. Integrated local CPU execution of `MBZUAI/LaMini-Flan-T5-783M` inside `backend/services/explanation_module.py` (`explain_topic()`). Implemented a silent warning and graceful fallback to Gemini if model loading or local generation fails.
- **Task 6: Default Gemini Model**: Changed default model inside `backend/services/gemini_service.py` to `gemini-1.5-pro` as per documentation.

### Priority 3 — Data Persistence Compliance
- **Task 7: JSON Mirroring**: Added a lightweight JSON append-only mirror in `backend/services/persistence.py`. Every successful database transaction now writes records matching the documented entities to `data/queries.json`, `data/responses.json`, `data/quizzes.json`, `data/summaries.json`, and `data/learning_paths.json`.
- **Task 8: User Isolation**: Added `user_id` column to SQLAlchemy models (`QueryHistory` and `Quiz`). Appended browser-generated UUID logic inside `frontend/js/app.js` using `localStorage` and sent it via `X-User-Id` headers. Updated `/history` to filter results by header UUID.

### Priority 4 — Structure & Polish
- **Task 9: Jinja2 Integration**: Moved `frontend/index.html` to `frontend/templates/index.html` and wired FastAPI root route to serve it via `Jinja2Templates`.
- **Task 10: Modules Split**: Cleanly divided `backend/services/features.py` into distinct files (`qna.py`, `explanation_module.py`, `quiz_module.py`, `summary_module.py`, `learning_path.py`, `common.py`) and left a backward-compatible shim in `features.py`.
- **Task 11: Sanitization**: Ensured consistent maximum character validations on inputs across all AI feature endpoints (e.g., `MAX_QUESTION_CHARS = 2000`, `MAX_TOPIC_CHARS = 300`).

