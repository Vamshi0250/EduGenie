EduGenie
EduGenie is a personal educational assistant designed to make studying more structured and interactive. It helps you get clear answers to questions, break down complex concepts, test your knowledge with auto-generated quizzes, summarize long study materials, and build custom learning roadmaps.

The application is built with a fast and lightweight FastAPI backend, a SQLite database for history tracking, and a responsive vanilla CSS/JS frontend interface styled around a clean navy and amber design system.

Usage
EduGenie provides five core interactive educational features:

Direct Q&A: Enter any topic or question and receive clear, concise, educational answers.
Concept Explainer: Breaks down complex terms into definitions, core importance, concrete examples, and common pitfalls.
Quiz Generator: Generates multiple-choice quizzes on any topic with interactive grading and explanation feedback.
Text Summarizer: Condenses long articles or textbook chapters into quick bullet points for exam preparation.
Learning Path Roadmaps: Builds beginner, intermediate, and advanced study plans with recommended resources and projects.
Study History: Automatically logs your past queries and quizzes so you can review them later.
Architecture & Tech Stack
Backend: FastAPI (Python 3.9+), SQLAlchemy, SQLite, Uvicorn
Frontend: HTML5, Vanilla CSS (using a custom design token system), and vanilla ES6 JavaScript
AI Integration: Google Gemini API via google-generativeai SDK
Testing: pytest & HTTPX (all API integrations are fully mocked for testing)
Directory Structure
EduGenie/
├── backend/
│   ├── main.py              # FastAPI application entry point & CORS configuration
│   ├── database.py           # Database connection and SQLite session management
│   ├── test_gemini.py        # Standalone verification script for API connection
│   ├── models/
│   │   ├── query_history.py  # Stores past Q&A, summaries, and paths
│   │   └── quiz.py           # Stores generated quiz structures
│   ├── routes/
│   │   └── api.py            # API routing and schema validations
│   ├── services/
│   │   ├── gemini_service.py # Core Gemini API wrapper and retry logic
│   │   └── features.py       # Prompt templates and feature logic
│   └── tests/
│       └── test_endpoints.py # Integration and endpoint unit tests
├── frontend/
│   ├── index.html            # Main dashboard layout
│   ├── css/
│   │   ├── design-tokens.css # CSS variables for typography, colors, and layout
│   │   └── styles.css        # Main stylesheet
│   └── js/
│       └── app.js            # API fetch requests and dynamic UI rendering
├── .env.example              # Template for credentials
├── requirements.txt          # Python dependencies
├── render.yaml               # Infrastructure configuration for deployment
└── README.md                 # Project documentation
Installation
1. Clone the Repository
git clone https://github.com/srinivas-workspace/EduGenie.git
cd EduGenie
2. Install Dependencies
Make sure you have Python 3.9 or newer installed:

pip install -r requirements.txt
3. Configure Your Environment
Copy the example environment file to .env:

cp .env.example .env
Open the .env file and set the required and optional parameters:

# Google Gemini API Key (Required)
GEMINI_API_KEY=your_actual_api_key_here

# Optional: Gemini model name (default: gemini-3.5-flash)
# GEMINI_MODEL=gemini-3.5-flash

# Optional: CORS Origins (comma-separated list of URLs)
# CORS_ORIGINS=http://localhost:5500,http://localhost:8080

# Optional: Rate limiting parameters (default: 30 requests / 60 seconds)
# RATE_LIMIT_MAX=30
# RATE_LIMIT_WINDOW=60

# Optional: Log levels (default: INFO)
# LOG_LEVEL=INFO
4. Verify API Key Configuration
Run the standalone verification script to test the connection to the Gemini API:

python -m backend.test_gemini
5. Start the Application
Run the FastAPI backend server:

uvicorn backend.main:app --reload --port 8000
The API documentation will be available at: http://localhost:8000/docs

To view the frontend, serve the frontend directory using any local web server, for example:

cd frontend
python -m http.server 8080
Open your browser and navigate to: http://localhost:8080

6. Run the Test Suite
You can run the mock-backed unit test suite using:

pytest
API Reference
All endpoint payloads and responses use standard JSON format.

POST /api/ask
Generates a straightforward answer to a question.

Request: { "question": "What is photosynthesis?" }
Response: { "question": "What is photosynthesis?", "answer": "..." }
POST /api/explain
Generates a 4-part concept breakdown.

Request: { "topic": "Quantum Entanglement" }
Response: { "topic": "Quantum Entanglement", "explanation": "..." }
POST /api/quiz
Generates a structured multiple-choice quiz.

Request: { "topic": "Photosynthesis", "num_questions": 3 }
Response: { "topic": "Photosynthesis", "questions": [ { "question": "...", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], "correct_answer": "A" } ] }
POST /api/summarize
Summarizes text into main concepts and bullet points.

Request: { "text": "..." }
Response: { "summary": "..." }
POST /api/recommend
Creates a structured learning roadmap.

Request: { "topic": "Data Science" }
Response: { "topic": "Data Science", "learning_path": { "beginner": {...}, "intermediate": {...}, "advanced": {...} } }
GET /api/history
Returns a list of the 20 most recent user queries and responses.

Response: { "history": [...] }
Production Deployment URLs
Frontend App: https://edugenie-frontend.onrender.com
Backend API: https://edugenie-api.onrender.com
