"""Server-side officer PIN sessions for the restricted registry."""
import os
import secrets
import time
from dataclasses import dataclass
from typing import Dict
from fastapi import HTTPException, Request, status

SESSION_SECONDS = int(os.getenv("REGISTRY_SESSION_SECONDS", "900"))
MAX_ATTEMPTS, LOCKOUT_SECONDS = 5, 60
_sessions: Dict[str, float] = {}
_attempts: Dict[str, tuple[int, float]] = {}

def _pin() -> str:
    pin = os.getenv("REGISTRY_OFFICER_PIN", "")
    if len(pin) != 6 or not pin.isascii() or not pin.isdigit():
        raise HTTPException(status_code=503, detail="Registry access has not been configured")
    return pin

def _pin_hash() -> bytes:
    """A bcrypt hash is retained only in process memory; the configured PIN is never persisted."""
    import bcrypt
    return bcrypt.hashpw(_pin().encode("utf-8"), bcrypt.gensalt())

def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"

def unlock(pin: str, request: Request) -> Dict[str, int | str]:
    expected_hash, key, now = _pin_hash(), _client_key(request), time.time()
    attempts, until = _attempts.get(key, (0, 0))
    if until > now:
        raise HTTPException(status_code=429, detail="Too many attempts. Try again shortly.", headers={"Retry-After": str(int(until-now)+1)})
    import bcrypt
    if not (len(pin) == 6 and pin.isascii() and pin.isdigit() and bcrypt.checkpw(pin.encode("utf-8"), expected_hash)):
        attempts += 1
        _attempts[key] = (attempts, now + LOCKOUT_SECONDS if attempts >= MAX_ATTEMPTS else 0)
        raise HTTPException(status_code=401, detail="Invalid officer PIN")
    _attempts.pop(key, None)
    token = secrets.token_urlsafe(32); _sessions[token] = now + SESSION_SECONDS
    return {"token": token, "expires_in": SESSION_SECONDS}

def lock(token: str) -> None: _sessions.pop(token, None)

def require_session(request: Request) -> str:
    token = request.headers.get("X-Registry-Session", "")
    expires = _sessions.get(token, 0)
    if not token or expires <= time.time():
        _sessions.pop(token, None)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Officer registry session required")
    _sessions[token] = time.time() + SESSION_SECONDS
    return token

def session_status(request: Request) -> Dict[str, int | bool]:
    token = request.headers.get("X-Registry-Session", ""); expires = _sessions.get(token, 0)
    if expires <= time.time(): return {"unlocked": False}
    return {"unlocked": True, "expires_in": int(expires-time.time())}
