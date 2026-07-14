"""
EduGenie — QueryHistory Model
Stores every AI interaction (question, explanation, summary, etc.) for the history endpoint.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime

from backend.database import Base


class QueryHistory(Base):
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # user_id is supplied by the client as X-User-Id header (browser-generated UUID).
    # This is a lightweight interim session isolation — not a full auth system.
    user_id = Column(String(64), nullable=True, index=True, default="anonymous")
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    interaction_type = Column(String(50), nullable=False)  # ask, explain, quiz, summarize, recommend
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "question": self.question,
            "answer": self.answer,
            "interaction_type": self.interaction_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
