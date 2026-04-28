"""
Utilidades de seguridad: hashing de contraseñas, JWT y tokens de reset.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
import bcrypt

from app.shared.config import settings

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Contraseñas ────────────────────────────────────────────────────────
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña plana contra su hash usando passlib."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Genera un hash de bcrypt para una contraseña plana usando passlib."""
    return pwd_context.hash(password)


# ── Tokens de recuperación de contraseña ───────────────────────────────
def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


# ── JWT ────────────────────────────────────────────────────────────────
def create_access_token(
    *, user_id: int, role: str, expires_delta: timedelta | None = None
) -> tuple[str, str, datetime]:
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {
        "sub": str(user_id),
        "role": role,
        "jti": jti,
        "exp": int(expire.timestamp()),
    }
    encoded = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded, jti, expire


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def jwt_payload_safe(token: str) -> dict | None:
    try:
        return decode_access_token(token)
    except JWTError:
        return None
