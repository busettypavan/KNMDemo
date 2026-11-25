"""Accounts: sign-up, sign-in, sign-out, the current user, and password reset.

The session is an httpOnly cookie named "session" that holds the signed token; the browser sends it back on later
requests, so sign-in persists across visits and no script can read it. Requests that authenticate with that cookie
and change data must carry the X-Requested-With header (see app/auth/middleware.py).

Errors use the project envelope {"error": "<code>"}. A password reset request always answers 202, so it does not
reveal whether an email has an account.
"""

import logging
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

import jwt
from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.lockout import LoginLockout
from app.auth.middleware import SESSION_COOKIE, current_auth
from app.auth.passwords import dummy_verify, hash_password, normalise_email, password_problem, verify_password
from app.auth.settings import AccountSettings
from app.auth.tokens import issue_reset_token, issue_session_token, password_fingerprint, verify_reset_token
from app.db.models import User
from app.db.session import get_session

log = logging.getLogger("app.auth")

ResetSender = Callable[[str, str], Awaitable[None]]  # (email, reset token) -> delivers the reset link


class AccountsState:
    """Per-app state: settings, the lockout counter and the reset sender (None until delivery is configured)."""

    def __init__(
        self, settings: AccountSettings, lockout: LoginLockout, reset_sender: ResetSender | None = None
    ) -> None:
        self.settings = settings
        self.lockout = lockout
        self.reset_sender = reset_sender


class Credentials(BaseModel):
    email: str
    password: str


class ResetRequest(BaseModel):
    email: str


class ResetConfirm(BaseModel):
    token: str
    password: str


router = APIRouter()


def _error(status: int, code: str) -> JSONResponse:
    return JSONResponse({"error": code}, status_code=status)


def _state(request: Request) -> AccountsState:
    state: AccountsState = request.app.state.accounts
    return state


def _set_session(response: Response, token: str, settings: AccountSettings) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.token_ttl_seconds,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path="/",
    )


def _client_key(request: Request) -> str:
    return f"ip:{request.client.host if request.client else 'unknown'}"


@router.post("/auth/signup", status_code=201)
async def signup(body: Credentials, request: Request, session: AsyncSession = Depends(get_session)) -> Response:
    state = _state(request)
    email = normalise_email(body.email)
    if email is None:
        return _error(422, "invalid-email")
    problem = password_problem(body.password)
    if problem:
        return _error(422, problem)
    existing = await session.execute(select(User.id).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        return _error(409, "email-taken")
    user = User(
        id=str(uuid.uuid4()), email=email, password_hash=hash_password(body.password), created_at=datetime.now(UTC)
    )
    session.add(user)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        return _error(409, "email-taken")
    response = JSONResponse({"id": user.id, "email": user.email}, status_code=201)
    _set_session(response, issue_session_token(user.id, state.settings.token_ttl_seconds), state.settings)
    return response


@router.post("/auth/signin")
async def signin(body: Credentials, request: Request, session: AsyncSession = Depends(get_session)) -> Response:
    state = _state(request)
    email = normalise_email(body.email)
    keys = [_client_key(request)] + ([f"email:{email}"] if email else [])
    if any(state.lockout.is_locked(key) for key in keys):
        return _error(429, "too-many-attempts")

    user = None
    if email is not None:
        user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None:
        dummy_verify(body.password)
        ok = False
    else:
        ok = verify_password(user.password_hash, body.password)
    if user is None or not ok:
        for key in keys:
            state.lockout.record_failure(key)
        return _error(401, "invalid-credentials")

    if email is not None:
        state.lockout.reset(f"email:{email}")
    response = JSONResponse({"id": user.id, "email": user.email})
    _set_session(response, issue_session_token(user.id, state.settings.token_ttl_seconds), state.settings)
    return response


@router.post("/auth/signout", status_code=204)
async def signout(request: Request) -> Response:
    response = Response(status_code=204)
    response.delete_cookie(
        SESSION_COOKIE, path="/", httponly=True, secure=_state(request).settings.cookie_secure, samesite="strict"
    )
    return response


@router.get("/auth/me")
async def me(request: Request, session: AsyncSession = Depends(get_session)) -> Response:
    auth = current_auth(request)
    if auth is None:
        return _error(401, "unauthorized")
    user = await session.get(User, auth.user_id)
    if user is None:
        return _error(401, "unauthorized")
    return JSONResponse({"id": user.id, "email": user.email})


@router.post("/auth/password-reset/request", status_code=202)
async def request_reset(body: ResetRequest, request: Request, session: AsyncSession = Depends(get_session)) -> Response:
    state = _state(request)
    accepted = JSONResponse({"status": "accepted"}, status_code=202)
    email = normalise_email(body.email)
    if email is None or state.reset_sender is None:
        return accepted
    user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None:
        return accepted
    token = issue_reset_token(user.id, user.password_hash, state.settings.reset_ttl_seconds)
    try:
        await state.reset_sender(email, token)
    except Exception:  # delivery problems are logged without the token or the address
        log.exception("password reset delivery failed")
    return accepted


@router.post("/auth/password-reset/confirm")
async def confirm_reset(body: ResetConfirm, request: Request, session: AsyncSession = Depends(get_session)) -> Response:
    problem = password_problem(body.password)
    if problem:
        return _error(422, problem)
    try:
        claims: dict[str, Any] = verify_reset_token(body.token)
    except jwt.PyJWTError:
        return _error(400, "invalid-or-expired-token")
    user = await session.get(User, claims["sub"])
    # The fingerprint check makes a reset link single-use: it stops matching once the password has changed.
    if user is None or claims["pwh"] != password_fingerprint(user.password_hash):
        return _error(400, "invalid-or-expired-token")
    user.password_hash = hash_password(body.password)
    return JSONResponse({"status": "password-updated"})


def mount(app: FastAPI) -> None:
    """Glue entry point: wires the settings, the lockout counter and the router. Tests and delivery code can replace
    app.state.accounts.reset_sender with a real sender."""
    settings = AccountSettings()
    app.state.accounts = AccountsState(
        settings,
        LoginLockout(settings.login_max_failures, settings.login_lock_seconds),
    )
    app.include_router(router)
