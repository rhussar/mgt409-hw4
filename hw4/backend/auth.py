"""Password verification and opaque, revocable login sessions."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from db import connection


HASH_ITERATIONS = 600_000
LEGACY_ITERATIONS = 120_000  # Format used by the supplied test account.
SESSION_DAYS = 7


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode(), HASH_ITERATIONS)
    return f"pbkdf2_sha256:{HASH_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        method, salt, digest = stored.split("$")
        if method == "pbkdf2_sha256":
            iterations = LEGACY_ITERATIONS
        elif method.startswith("pbkdf2_sha256:"):
            iterations = int(method.split(":", 1)[1])
            if not 100_000 <= iterations <= 2_000_000:
                return False
        else:
            return False
        calculated = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode(), iterations)
        return hmac.compare_digest(calculated.hex(), digest)
    except (ValueError, TypeError):
        return False


def public_user(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "email": row["email"],
        "created_at": row["created_at"],
    }


def register_user(first_name: str, last_name: str, email: str, password: str) -> dict:
    display_name = f"{first_name.strip()} {last_name.strip()}".strip()
    with connection() as conn:
        try:
            cursor = conn.execute(
                "INSERT INTO users (name, first_name, last_name, email, password_hash) VALUES (?, ?, ?, ?, ?)",
                (display_name, first_name.strip(), last_name.strip(), email.lower().strip(), hash_password(password)),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("An account with that email already exists") from exc
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return public_user(row)


def authenticate_user(email: str, password: str) -> dict | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()
        if row is None or not verify_password(password, row["password_hash"]):
            return None
        if row["password_hash"].startswith("pbkdf2_sha256$"):
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(password), row["id"]))
        return public_user(row)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    with connection() as conn:
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            (_token_hash(token), user_id, expires.isoformat()),
        )
    return token


def user_for_session(token: str | None) -> dict | None:
    if not token:
        return None
    with connection() as conn:
        row = conn.execute(
            """SELECT users.* FROM sessions JOIN users ON users.id = sessions.user_id
               WHERE sessions.token_hash = ? AND sessions.expires_at > ?""",
            (_token_hash(token), datetime.now(timezone.utc).isoformat()),
        ).fetchone()
        return public_user(row) if row else None


def revoke_session(token: str | None) -> None:
    if token:
        with connection() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))
