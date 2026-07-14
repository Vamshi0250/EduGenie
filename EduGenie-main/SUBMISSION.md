# EduGenie — Submission Document

This document maps the work completed in EduGenie back to the original Epic/Story breakdown.

---

## Project Overview

**EduGenie** is an AI-powered educational assistant using Google Gemini that provides students with five core learning features: question answering, concept explanation, quiz generation, text summarization, and learning path recommendations — all behind a full login/signup system with per-user history.

---

## Pre-Requisites

| Requirement | Status | Notes |
|---|---|---|
| Python 3.9+ installed | ✅ Done | Python 3.13 used |
| Gemini API key obtained | ✅ Done | Loaded via .env |
| Git repository initialized | ✅ Done | Remote: github.com/srinivas-workspace/EduGenie |
| Project structure scaffolded | ✅ Done | backend/ + frontend/ layout |

---

## Epic 1 — Backend Foundation

### Story 1.1: Database Setup
- **Status**: ✅ Complete
- **Files**: `backend/database.py`, `backend/models/query_history.py`, `backend/models/quiz.py`, `backend/models/user.py`
- **Notes**: SQLAlchemy + SQLite. Three tables: `query_history`, `quizzes`, `users`. Auto-created on startup.

### Story 1.2: Gemini AI Integration
- **Status**: ✅ Complete
- **Files**: `backend/services/gemini_service.py`
- **Notes**: Lazy model init, retry/backoff on transient errors, 4096 token limit for full responses.

### Story 1.3: Core Feature Functions
- **Status**: ✅ Complete
- **Files**: `backend/services/qna.py`, `backend/services/explanation_module.py`, `backend/services/quiz_module.py`, `backend/services/summary_module.py`, `backend/services/learning_path.py`

---

## Epic 2 — API Layer

### Story 2.1: REST Endpoints
- **Status**: ✅ Complete
- **Files**: `backend/routes/api.py`, `backend/main.py`
- **Endpoints**: POST /api/ask, /api/explain, /api/quiz, /api/summarize, /api/recommend + GET /api/history

### Story 2.2: Auth System
- **Status**: ✅ Complete
- **Files**: `backend/routes/auth.py`, `backend/models/user.py`
- **Endpoints**: POST /api/auth/signup, /api/auth/login, /api/auth/logout + GET /api/auth/me
- **Notes**: bcrypt-hashed passwords via passlib. Rotating opaque session tokens. History scoped per logged-in user.

### Story 2.3: CORS + Rate Limiting
- **Status**: ✅ Complete
- **Files**: `backend/middleware/rate_limit.py`
- **Notes**: Sliding-window in-memory rate limiter. Auth endpoints excluded from rate limiting.

### Story 2.4: Input Validation
- **Status**: ✅ Complete
- **Notes**: Pydantic schemas, custom 400 responses, token limit guards.

---

## Epic 3 — Frontend

### Story 3.1: Design System
- **Status**: ✅ Complete
- **Files**: `frontend/css/design-tokens.css`
- **Notes**: Space Grotesk font, Navy + Amber palette, 4px spacing scale.

### Story 3.2: UI Implementation
- **Status**: ✅ Complete
- **Files**: `frontend/templates/index.html`, `frontend/templates/auth.html`, `frontend/css/styles.css`, `frontend/js/app.js`
- **Notes**: Auth-gated app. Login/signup page with tab switcher. Sidebar shows logged-in user + logout. Auth token sent as Bearer header on all requests.

### Story 3.3: Loading & Error States
- **Status**: ✅ Complete
- **Notes**: Typing-dot loading indicator, real error messages (not generic status codes).

---

## Epic 4 — Quality & Deployment

### Story 4.1: Automated Tests
- **Status**: ✅ Complete
- **Files**: `backend/tests/test_endpoints.py`, `backend/tests/test_gemini_service.py`

### Story 4.2: Documentation
- **Status**: ✅ Complete
- **Files**: `README.md`, `SUBMISSION.md`

### Story 4.3: GitHub
- **Status**: ✅ Complete
- **URL**: https://github.com/srinivas-workspace/EduGenie

### Story 4.4: Deployment Config
- **Status**: ✅ Ready
- **Files**: `render.yaml`
- **Notes**: Render.com config included. Set `GEMINI_API_KEY` as an env var in Render dashboard before deploying.

---

## Security Notes

- `.env` is in `.gitignore` — the API key is never committed
- Passwords are bcrypt-hashed, never stored in plaintext
- Session tokens are cryptographically random (48-byte urlsafe)
- Tokens are rotated on every login and invalidated on logout
- `data/` folder (runtime logs) and `*.db` files are excluded from git

---

*EduGenie — built with FastAPI + Google Gemini + vanilla JS*
