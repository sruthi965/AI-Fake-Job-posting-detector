"""Authentication routes and the FastAPI dependencies other routers reuse."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token, limiter
from app.database import repository
from app.schemas.auth_schema import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=False)


def get_optional_user(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict | None:
    """Return the signed-in user, or None for anonymous or invalid tokens."""
    if credentials is None:
        return None
    user_id = decode_access_token(credentials.credentials)
    return repository.get_user_by_id(user_id) if user_id is not None else None


def get_current_user(user: dict | None = Depends(get_optional_user)) -> dict:
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in to continue", headers={"WWW-Authenticate": "Bearer"})
    return user


def rate_limit(name: str, limit: int, window_seconds: int):
    """Dependency factory: limit requests per user (or per IP when anonymous)."""

    def dependency(request: Request, user: dict | None = Depends(get_optional_user)) -> None:
        who = f"user:{user['id']}" if user else f"ip:{request.client.host if request.client else 'unknown'}"
        if not limiter.allow(f"{name}:{who}", limit, window_seconds):
            raise HTTPException(status_code=429, detail="Too many requests. Wait a few minutes and try again.")

    return dependency


_auth_limit = Depends(rate_limit("auth", 10, 300))


@router.post("/register", response_model=TokenResponse, status_code=201, dependencies=[_auth_limit])
def register(payload: RegisterRequest):
    try:
        user, token = auth_service.register_user(payload.full_name, payload.email, payload.password)
    except auth_service.ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/login", response_model=TokenResponse, dependencies=[_auth_limit])
def login(payload: LoginRequest):
    try:
        user, token = auth_service.login_user(payload.email, payload.password)
    except auth_service.ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user)):
    return auth_service.public_user(user)
