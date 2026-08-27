import datetime as dt
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    to_encode = data.copy()
    expire = dt.datetime.utcnow() + dt.timedelta(
        minutes=expires_minutes or settings.jwt_expire_minutes
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


# ---------- Límite de intentos de login (en memoria, por usuario) ----------
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

_failed_attempts: dict[str, list[dt.datetime]] = {}


def _cleanup_old_attempts(username: str):
    cutoff = dt.datetime.utcnow() - dt.timedelta(minutes=LOCKOUT_MINUTES)
    _failed_attempts[username] = [t for t in _failed_attempts.get(username, []) if t > cutoff]


def is_locked_out(username: str) -> Optional[int]:
    """Devuelve minutos restantes de bloqueo, o None si no está bloqueado."""
    _cleanup_old_attempts(username)
    attempts = _failed_attempts.get(username, [])
    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        oldest_relevant = attempts[-MAX_LOGIN_ATTEMPTS]
        unlock_at = oldest_relevant + dt.timedelta(minutes=LOCKOUT_MINUTES)
        remaining = (unlock_at - dt.datetime.utcnow()).total_seconds() / 60
        if remaining > 0:
            return max(1, int(remaining))
    return None


def register_failed_attempt(username: str):
    _cleanup_old_attempts(username)
    _failed_attempts.setdefault(username, []).append(dt.datetime.utcnow())


def clear_failed_attempts(username: str):
    _failed_attempts.pop(username, None)
