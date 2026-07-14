"""
EduGenie — User Model
Stores registered users with hashed passwords and session tokens.
"""

import secrets
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False)
    # Opaque session token — generated on login, cleared on logout
    session_token = Column(String(128), nullable=True, unique=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @staticmethod
    def generate_token() -> str:
        return secrets.token_urlsafe(48)
