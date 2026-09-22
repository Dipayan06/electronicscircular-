"""Security utilities (FR-A2/FR-A3, NFR-3).

- Password hashing with bcrypt (passwords never stored in plaintext).
- JWT creation/verification for stateless authentication.
"""
from datetime import datetime, timedelta

from jose import jwt, JWTError
from passlib.context import CryptContext

from ..config import settings
from .responses import APIError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


# ---- passwords ----
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ---- JWT (Phase 7) ----
def create_access_token(user_id: int, role: str) -> str:
    """Issue a signed token carrying the user id (sub) and role."""
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode/verify a token, or raise a 401 APIError."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        raise APIError("Invalid or expired token", status_code=401)
