"""
EduGenie — Auth Routes
Handles user signup, login, logout, and /me (current user).

All passwords are bcrypt-hashed via passlib.
Sessions are opaque bearer tokens stored in the users table.
"""

import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from backend.database import get_db
from backend.models.user import User

logger = logging.getLogger("edugenie.auth")
router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Dependency — resolves the logged-in User from the Bearer token header.
    Returns None if unauthenticated (callers decide whether to reject or allow)."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[len("Bearer "):]
    return db.query(User).filter(User.session_token == token).first()


def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency — raises 401 if not authenticated."""
    user = get_current_user(request, db)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user


# ── Request schemas ────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: str = Field(..., min_length=5, max_length=128)
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    # Accept username OR email in the same field for convenience
    username_or_email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/signup")
async def signup(body: SignupRequest, db: Session = Depends(get_db)):
    """Register a new user. Returns a session token on success."""
    # Normalise
    username = body.username.strip()
    email = body.email.strip().lower()

    if db.query(User).filter(User.username == username).first():
        return JSONResponse(status_code=409, content={"error": "Username already taken."})
    if db.query(User).filter(User.email == email).first():
        return JSONResponse(status_code=409, content={"error": "Email already registered."})

    token = User.generate_token()
    user = User(
        username=username,
        email=email,
        hashed_password=_hash_password(body.password),
        session_token=token,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("New user registered: %s", username)
    return {"token": token, "user": user.to_dict()}


@router.post("/login")
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and return a fresh session token."""
    identifier = body.username_or_email.strip()

    # Try username first, then email
    user = db.query(User).filter(User.username == identifier).first()
    if not user:
        user = db.query(User).filter(User.email == identifier.lower()).first()

    if not user or not _verify_password(body.password, user.hashed_password):
        return JSONResponse(status_code=401, content={"error": "Invalid username/email or password."})

    # Rotate token on every login
    user.session_token = User.generate_token()
    db.commit()
    db.refresh(user)

    logger.info("User logged in: %s", user.username)
    return {"token": user.session_token, "user": user.to_dict()}


@router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    """Invalidate the current session token."""
    user = get_current_user(request, db)
    if user:
        user.session_token = None
        db.commit()
    return {"message": "Logged out."}


@router.get("/me")
async def me(request: Request, db: Session = Depends(get_db)):
    """Return the currently authenticated user's profile."""
    user = get_current_user(request, db)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Not authenticated."})
    return {"user": user.to_dict()}
