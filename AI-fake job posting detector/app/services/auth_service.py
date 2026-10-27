from __future__ import annotations

from app.core.security import DUMMY_HASH, create_access_token, hash_password, verify_password
from app.database import repository
from app.database.connection import integrity_errors


class ServiceError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "created_at": user.get("created_at"),
    }


def register_user(full_name: str, email: str, password: str) -> tuple[dict, str]:
    if repository.get_user_by_email(email):
        raise ServiceError(409, "An account with this email already exists")
    try:
        user_id = repository.create_user(full_name, email, hash_password(password))
    except integrity_errors() as exc:  # lost a race with a concurrent signup
        raise ServiceError(409, "An account with this email already exists") from exc
    user = repository.get_user_by_id(user_id)
    return public_user(user), create_access_token(user_id)


def login_user(email: str, password: str) -> tuple[dict, str]:
    user = repository.get_user_by_email(email)
    stored = user["password_hash"] if user else DUMMY_HASH
    valid = verify_password(password, stored)
    if not user or not valid:
        raise ServiceError(401, "Incorrect email or password")
    return public_user(user), create_access_token(user["id"])
