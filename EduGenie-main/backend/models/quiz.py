"""
EduGenie — Quiz Model
Stores generated quizzes with their topic and structured question data.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime

from backend.database import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(64), nullable=True, index=True, default="anonymous")
    topic = Column(String(200), nullable=False)
    questions_json = Column(Text, nullable=False)  # JSON string of quiz questions
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "topic": self.topic,
            "questions_json": self.questions_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
