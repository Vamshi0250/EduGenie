"""
EduGenie — Automated Tests for API Endpoints
Mocks the Gemini API so tests don't consume real API calls.
Tests status codes, response shape, and database row creation.

Run with:  python -m pytest backend/tests/test_endpoints.py -v
"""

import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.database import Base, get_db
from backend.main import app


# --- Test Database Setup ------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///./test_edugenie.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# Standard test headers — include X-User-Id so history scoping works
TEST_HEADERS = {"X-User-Id": "test-user-uuid-1234"}


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test, drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


# --- Mock Gemini Response Helper ----------------------------------------------

MOCK_ANSWER = "Photosynthesis is the process by which plants convert light energy into chemical energy."

MOCK_QUIZ_JSON = json.dumps([
    {
        "question": "What is the powerhouse of the cell?",
        "options": ["A. Nucleus", "B. Mitochondria", "C. Ribosome", "D. Golgi body"],
        "correct_answer": "B",
    }
])

MOCK_LEARNING_PATH_JSON = json.dumps({
    "topic": "Python",
    "beginner": {
        "description": "Learn basics",
        "resources": ["Python Crash Course"],
        "projects": ["Calculator"],
        "duration": "4 weeks",
    },
    "intermediate": {
        "description": "Build projects",
        "resources": ["Fluent Python"],
        "projects": ["Web scraper"],
        "duration": "8 weeks",
    },
    "advanced": {
        "description": "Master patterns",
        "resources": ["CPython Internals"],
        "projects": ["Framework"],
        "duration": "12 weeks",
    },
})


# --- Tests --------------------------------------------------------------------

def test_frontend_root_and_health_endpoints():
    home = client.get("/")
    assert home.status_code == 200
    assert "text/html" in home.headers["content-type"]
    assert "EduGenie" in home.text

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"


class TestAskEndpoint:
    @patch("backend.services.qna.generate_response", return_value=MOCK_ANSWER)
    def test_ask_success(self, mock_gen):
        response = client.post("/api/ask", json={"question": "What is photosynthesis?"}, headers=TEST_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "question" in data
        assert "answer" in data
        assert data["question"] == "What is photosynthesis?"
        assert len(data["answer"]) > 0
        mock_gen.assert_called_once()

    def test_ask_empty_question(self):
        response = client.post("/api/ask", json={"question": ""})
        assert response.status_code == 422  # Pydantic min_length=1

    @patch("backend.services.qna.generate_response", return_value=MOCK_ANSWER)
    def test_ask_creates_db_row(self, mock_gen):
        client.post("/api/ask", json={"question": "Test question"}, headers=TEST_HEADERS)
        history = client.get("/api/history", headers=TEST_HEADERS)
        records = history.json()["history"]
        assert len(records) >= 1
        assert records[0]["interaction_type"] == "ask"

    @patch("backend.services.qna.generate_response", return_value=MOCK_ANSWER)
    def test_qa_alias_get(self, mock_gen):
        """Task 1: GET /qa with ?question= query param."""
        response = client.get("/qa?question=What+is+gravity", headers=TEST_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data


class TestExplainEndpoint:
    @patch("backend.services.explanation_module.generate_response", return_value=MOCK_ANSWER)
    @patch("backend.services.explanation_module._load_local_model", return_value=False)
    def test_explain_success(self, mock_load, mock_gen):
        response = client.post("/api/explain", json={"topic": "Gravity"}, headers=TEST_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "topic" in data
        assert "explanation" in data
        assert data["topic"] == "Gravity"

    def test_explain_missing_topic_returns_400(self):
        """Task 3: Missing topic → 400 with specific error message."""
        response = client.post("/api/explain", json={})
        assert response.status_code == 400
        assert response.json()["error"] == "Please provide a topic."

    def test_explain_empty_topic_returns_400(self):
        """Task 3: Empty topic string → 400."""
        response = client.post("/api/explain", json={"topic": ""})
        assert response.status_code == 400
        assert response.json()["error"] == "Please provide a topic."

    @patch("backend.services.explanation_module.generate_response", return_value=MOCK_ANSWER)
    @patch("backend.services.explanation_module._load_local_model", return_value=False)
    def test_explain_alias_post(self, mock_load, mock_gen):
        """Task 1: POST /explain alias."""
        response = client.post("/explain", json={"topic": "Gravity"}, headers=TEST_HEADERS)
        assert response.status_code == 200


class TestQuizEndpoint:
    @patch("backend.services.quiz_module.generate_response", return_value=MOCK_QUIZ_JSON)
    def test_quiz_success_with_text_field(self, mock_gen):
        """Task 1/3: Quiz accepts 'text' field per spec."""
        response = client.post("/api/quiz", json={"text": "Biology", "num_questions": 1}, headers=TEST_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "questions" in data
        assert "quiz" in data  # Spec-matching key also present
        assert isinstance(data["questions"], list)
        assert len(data["questions"]) >= 1
        q = data["questions"][0]
        assert "question" in q
        assert "options" in q
        assert "correct_answer" in q

    @patch("backend.services.quiz_module.generate_response", return_value=MOCK_QUIZ_JSON)
    def test_quiz_success_with_topic_field(self, mock_gen):
        """Legacy /api/quiz with 'topic' field still works."""
        response = client.post("/api/quiz", json={"topic": "Biology"}, headers=TEST_HEADERS)
        assert response.status_code == 200

    def test_quiz_missing_text_returns_400(self):
        """Task 3: Missing 'text' and 'topic' → 400."""
        response = client.post("/api/quiz", json={})
        assert response.status_code == 400
        assert response.json()["error"] == "Please provide text for quiz."

    @patch("backend.services.quiz_module.generate_response", return_value=MOCK_QUIZ_JSON)
    def test_quiz_creates_db_rows(self, mock_gen):
        client.post("/api/quiz", json={"text": "Math"}, headers=TEST_HEADERS)
        history = client.get("/api/history", headers=TEST_HEADERS)
        records = history.json()["history"]
        quiz_records = [r for r in records if r["interaction_type"] == "quiz"]
        assert len(quiz_records) >= 1

    @patch("backend.services.quiz_module.generate_response", return_value=MOCK_QUIZ_JSON)
    def test_quiz_alias_post(self, mock_gen):
        """Task 1: POST /quiz alias."""
        response = client.post("/quiz", json={"text": "Biology"}, headers=TEST_HEADERS)
        assert response.status_code == 200


class TestSummarizeEndpoint:
    @patch("backend.services.summary_module.generate_response", return_value=MOCK_ANSWER)
    def test_summarize_success(self, mock_gen):
        long_text = "This is a long educational text about science. " * 10
        response = client.post("/api/summarize", json={"text": long_text}, headers=TEST_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert len(data["summary"]) > 0

    def test_summarize_missing_text_returns_400(self):
        """Task 3: Missing 'text' → 400."""
        response = client.post("/api/summarize", json={})
        assert response.status_code == 400
        assert response.json()["error"] == "Please provide text to summarize."

    def test_summarize_empty_text_returns_400(self):
        """Task 3: Empty text → 400."""
        response = client.post("/api/summarize", json={"text": ""})
        assert response.status_code == 400

    @patch("backend.services.summary_module.generate_response", return_value=MOCK_ANSWER)
    def test_summarize_alias_post(self, mock_gen):
        """Task 1: POST /summarize alias."""
        long_text = "Educational content about science topics. " * 5
        response = client.post("/summarize", json={"text": long_text}, headers=TEST_HEADERS)
        assert response.status_code == 200


class TestRecommendEndpoint:
    @patch("backend.services.learning_path.generate_response", return_value=MOCK_LEARNING_PATH_JSON)
    def test_recommend_success(self, mock_gen):
        response = client.post("/api/recommend", json={"topic": "Python"}, headers=TEST_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "topic" in data
        assert "learning_path" in data
        assert "recommendation" in data  # Spec alias key
        path = data["learning_path"]
        assert "beginner" in path
        assert "intermediate" in path
        assert "advanced" in path

    @patch("backend.services.learning_path.generate_response", return_value=MOCK_LEARNING_PATH_JSON)
    def test_learn_recommendations_alias_get(self, mock_gen):
        """Task 1: GET /learn/recommendations with ?topic= query param."""
        response = client.get("/learn/recommendations?topic=Python", headers=TEST_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "learning_path" in data


class TestHistoryEndpoint:
    @patch("backend.services.qna.generate_response", return_value=MOCK_ANSWER)
    @patch("backend.services.explanation_module.generate_response", return_value=MOCK_ANSWER)
    @patch("backend.services.explanation_module._load_local_model", return_value=False)
    def test_history_returns_records(self, mock_load, mock_explain, mock_ask):
        client.post("/api/ask", json={"question": "Q1"}, headers=TEST_HEADERS)
        client.post("/api/explain", json={"topic": "T1"}, headers=TEST_HEADERS)

        response = client.get("/api/history", headers=TEST_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert len(data["history"]) == 2

    def test_history_empty(self):
        response = client.get("/api/history", headers=TEST_HEADERS)
        assert response.status_code == 200
        assert response.json()["history"] == []

    @patch("backend.services.qna.generate_response", return_value=MOCK_ANSWER)
    def test_history_ordered_by_newest_first(self, mock_gen):
        client.post("/api/ask", json={"question": "First"}, headers=TEST_HEADERS)
        client.post("/api/ask", json={"question": "Second"}, headers=TEST_HEADERS)

        response = client.get("/api/history", headers=TEST_HEADERS)
        records = response.json()["history"]
        assert records[0]["question"] == "Second"
        assert records[1]["question"] == "First"

    @patch("backend.services.qna.generate_response", return_value=MOCK_ANSWER)
    def test_history_segregated_by_user(self, mock_gen):
        """Task 8: User A's history should not appear for User B."""
        client.post("/api/ask", json={"question": "User A question"}, headers={"X-User-Id": "user-a"})
        response_b = client.get("/api/history", headers={"X-User-Id": "user-b"})
        records_b = response_b.json()["history"]
        assert len(records_b) == 0
