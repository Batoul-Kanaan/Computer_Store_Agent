import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo.database import Database

from backend.app.database import get_db

COOKIE_NAME = "store_admin"
ITERATIONS = 600_000
UNKNOWN_USER_HASH = None
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt, digest = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds))
        return hmac.compare_digest(actual, bytes.fromhex(digest))
    except (ValueError, TypeError):
        return False


def authenticate(db: Database, username: str, password: str) -> bool:
    user = db.admin_users.find_one({"username": username.lower().strip()})
    # Execute the same expensive hash even for unknown accounts.
    encoded = user["password_hash"] if user else _unknown_hash()
    valid = verify_password(password, encoded)
    return bool(user and valid)


def authenticate_account(db: Database, username: str, password: str) -> str | None:
    normalized = username.lower().strip()
    admin = db.admin_users.find_one({"username": normalized})
    user = None if admin else db.store_users.find_one({"username": normalized})
    account = admin or user
    encoded = account["password_hash"] if account else _unknown_hash()
    if not verify_password(password, encoded) or not account:
        return None
    return "admin" if admin else "customer"


def _unknown_hash() -> str:
    global UNKNOWN_USER_HASH
    if UNKNOWN_USER_HASH is None:
        UNKNOWN_USER_HASH = hash_password("invalid-account-placeholder", b"\x00" * 16)
    return UNKNOWN_USER_HASH


def new_session(db: Database, username: str, hours: int, role: str = "admin") -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(24)
    db.admin_sessions.insert_one(
        {
            "token_hash": hashlib.sha256(token.encode()).hexdigest(),
            "username": username,
            "role": role,
            "csrf_token": csrf_token,
            "expires_at": datetime.now(UTC) + timedelta(hours=hours),
        }
    )
    return token, csrf_token


def revoke_session(db: Database, token: str) -> None:
    db.admin_sessions.delete_one({"token_hash": hashlib.sha256(token.encode()).hexdigest()})


def require_session(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Database = Depends(get_db),
) -> dict:
    token = credentials.credentials if credentials else request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Admin login required")
    session = db.admin_sessions.find_one(
        {
            "token_hash": hashlib.sha256(token.encode()).hexdigest(),
            "expires_at": {"$gt": datetime.now(UTC)},
        }
    )
    if not session:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired")
    return session


def require_admin(session: dict = Depends(require_session)) -> dict:
    if session.get("role", "admin") != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return session


def require_csrf(
    session: dict = Depends(require_admin),
    x_csrf_token: str | None = Header(default=None),
) -> dict:
    if not x_csrf_token or not hmac.compare_digest(x_csrf_token, session["csrf_token"]):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid CSRF token")
    return session


def require_session_csrf(
    session: dict = Depends(require_session),
    x_csrf_token: str | None = Header(default=None),
) -> dict:
    if not x_csrf_token or not hmac.compare_digest(x_csrf_token, session["csrf_token"]):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid CSRF token")
    return session
