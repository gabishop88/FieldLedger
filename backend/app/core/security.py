from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

ALGORITHM = "HS256"

# ------------------------------ Argon2 Password Hashing -------------------------------


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the stored hash. Returns True if they match."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(plain_password: str) -> str:
    """Get a has for the given plain password string using Argon2."""
    return pwd_context.hash(plain_password)


# ------------------------ JWT OAuth2 Compatible Access Tokens -------------------------


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    """Given subject and expiration, create a JWT that returns subject when decoded."""
    now = datetime.now(UTC)
    payload = {"iat": now, "exp": now + expires_delta, "sub": str(subject)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> str | None:
    """Decode & verify a JWT access token. Returns payload if valid, otherwise None."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except (JWTError, KeyError):
        return None
