# EduGenie

EduGenie is a personal educational assistant designed to make studying more structured and interactive. It helps you get clear answers to questions, break down complex concepts, test your knowledge with auto-generated quizzes, summarize long study materials, and build custom learning roadmaps.

The application is built with a fast and lightweight **FastAPI** backend, a **SQLite** database for history tracking, and a responsive **HTML/CSS/JavaScript** frontend styled around a clean navy and amber design system.

---

# Usage

EduGenie provides five core interactive educational features:

- **Direct Q&A:** Enter any topic or question and receive clear, concise educational answers.
- **Concept Explainer:** Breaks down complex terms into definitions, importance, examples, and common pitfalls.
- **Quiz Generator:** Generates multiple-choice quizzes with interactive grading and explanation feedback.
- **Text Summarizer:** Condenses long articles or textbook chapters into concise bullet points.
- **Learning Path Roadmaps:** Builds beginner, intermediate, and advanced study plans with recommended resources and projects.
- **Study History:** Automatically logs previous queries and quizzes for later review.

---

# Architecture & Tech Stack

### Backend
- FastAPI (Python 3.9+)
- SQLAlchemy
- SQLite
- Uvicorn

### Frontend
- HTML5
- Vanilla CSS
- Vanilla ES6 JavaScript

### AI Integration
- Google Gemini API
- google-generativeai SDK

### Testing
- pytest
- HTTPX (API integrations are fully mocked)

---

# Directory Structure

```text
EduGenie/
├── backend/
│   ├── main.py              # FastAPI application entry point & CORS configuration
│   ├── database.py          # Database connection and SQLite session management
│   ├── test_gemini.py       # Standalone verification script for API connection
│   ├── models/
│   │   ├── query_history.py # Stores past Q&A, summaries, and paths
│   │   └── quiz.py          # Stores generated quiz structures
│   ├── routes/
│   │   └── api.py           # API routing and schema validations
│   ├── services/
│   │   ├── gemini_service.py # Core Gemini API wrapper and retry logic
│   │   └── features.py      # Prompt templates and feature logic
│   └── tests/
│       └── test_endpoints.py # Integration and endpoint unit tests
├── frontend/
│   ├── index.html
│   ├── css/
│   │   ├── design-tokens.css
│   │   └── styles.css
│   └── js/
│       └── app.js
├── .env.example
├── requirements.txt
├── render.yaml
└── README.md
```

---

# Installation

## 1. Clone the Repository

```bash
git clone https://github.com/srinivas-workspace/EduGenie.git
cd EduGenie
```

---

## 2. Install Dependencies

Make sure Python **3.9 or newer** is installed.

```bash
pip install -r requirements.txt
```

---

## 3. Configure Your Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Open `.env` and configure:

```env
# Google Gemini API Key (Required)
GEMINI_API_KEY=your_actual_api_key_here

# Optional: Gemini model
# GEMINI_MODEL=gemini-3.5-flash

# Optional: CORS Origins
# CORS_ORIGINS=http://localhost:5500,http://localhost:8080

# Optional: Rate Limiting
# RATE_LIMIT_MAX=30
# RATE_LIMIT_WINDOW=60

# Optional: Log Level
# LOG_LEVEL=INFO
```

---

## 4. Verify API Key Configuration

```bash
python -m backend.test_gemini
```

---

## 5. Start the Application

Run the FastAPI backend:

```bash
uvicorn backend.main:app --reload --port 8000
```

API Documentation:

```
http://localhost:8000/docs
```

Serve the frontend:

```bash
cd frontend
python -m http.server 8080
```

Open:

```
http://localhost:8080
```

---

## 6. Run the Test Suite

```bash
pytest
```

---

# API Reference

All endpoints accept and return **JSON**.

---

## POST `/api/ask`

Generates a straightforward answer.

**Request**

```json
{
  "question": "What is photosynthesis?"
}
```

**Response**

```json
{
  "question": "What is photosynthesis?",
  "answer": "..."
}
```

---

## POST `/api/explain`

Generates a concept explanation.

**Request**

```json
{
  "topic": "Quantum Entanglement"
}
```

**Response**

```json
{
  "topic": "Quantum Entanglement",
  "explanation": "..."
}
```

---

## POST `/api/quiz`

Generates a multiple-choice quiz.

**Request**

```json
{
  "topic": "Photosynthesis",
  "num_questions": 3
}
```

**Response**

```json
{
  "topic": "Photosynthesis",
  "questions": [
    {
      "question": "...",
      "options": [
        "A. ...",
        "B. ...",
        "C. ...",
        "D. ..."
      ],
      "correct_answer": "A"
    }
  ]
}
```

---

## POST `/api/summarize`

Summarizes text.

**Request**

```json
{
  "text": "..."
}
```

**Response**

```json
{
  "summary": "..."
}
```

---

## POST `/api/recommend`

Creates a structured learning roadmap.

**Request**

```json
{
  "topic": "Data Science"
}
```

**Response**

```json
{
  "topic": "Data Science",
  "learning_path": {
    "beginner": {},
    "intermediate": {},
    "advanced": {}
  }
}
```

---

## GET `/api/history`

Returns the 20 most recent user interactions.

**Response**

```json
{
  "history": []
}
```

---

# Production Deployment URLs

### Frontend

https://edugenie-frontend.onrender.com

### Backend API

https://edugenie-api.onrender.com
