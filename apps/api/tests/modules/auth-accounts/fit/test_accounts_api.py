"""Fit: sign-up, sign-in, the session cookie, lockout, password reset and the CSRF header through create_app with the
real glue, against a SQLite file."""

import time

import jwt
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine as sync_engine

from app.auth.jwt import AuthClaims
from app.auth.lockout import LoginLockout
from app.auth.middleware import require_auth
from app.db import models  # noqa: F401  (registers the tables)
from app.db.base import Base
from app.http.app import create_app
from app.http.settings import Settings

SECRET = "s" * 40
PASSWORD = "correct-horse-42"
CSRF = {"X-Requested-With": "knm"}


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "accounts.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file.as_posix()}")
    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("COOKIE_SECURE", "false")  # the test client talks plain http
    engine = sync_engine(f"sqlite:///{db_file.as_posix()}")
    Base.metadata.create_all(engine)
    engine.dispose()
    app = create_app(settings=Settings(env="production"))

    @app.post("/probe")
    def probe(auth: AuthClaims = Depends(require_auth)):
        return {"user": auth.user_id}

    with TestClient(app) as test_client:
        yield test_client


def post(client, path, body, headers=CSRF):
    return client.post(path, json=body, headers=headers)


def signup(client, email="ana@example.com", password=PASSWORD):
    return post(client, "/auth/signup", {"email": email, "password": password})


def signin(client, email="ana@example.com", password=PASSWORD):
    return post(client, "/auth/signin", {"email": email, "password": password})


def test_signup_signs_in_with_an_httponly_strict_cookie(client):
    response = signup(client)
    assert response.status_code == 201
    assert response.json()["email"] == "ana@example.com"
    assert PASSWORD not in response.text
    cookie = response.headers["set-cookie"].lower()
    assert "session=" in cookie and "httponly" in cookie and "samesite=strict" in cookie


def test_duplicate_email_is_refused(client):
    signup(client)
    response = signup(client, email="ANA@example.com")
    assert response.status_code == 409
    assert response.json() == {"error": "email-taken"}


def test_bad_email_and_weak_password_are_refused(client):
    assert signup(client, email="nope").json() == {"error": "invalid-email"}
    assert signup(client, password="short").json() == {"error": "weak-password"}


def test_wrong_password_and_unknown_email_give_the_same_answer(client):
    signup(client)
    wrong = signin(client, password="wrong-password-99")
    unknown = signin(client, email="nobody@example.com")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"error": "invalid-credentials"}


def test_sign_in_persists_across_visits_through_the_cookie_alone(client):
    signup(client)
    client.cookies.clear()  # a new visit: no header, only the cookie the browser kept
    assert client.get("/auth/me").status_code == 401
    assert signin(client).status_code == 200
    client.cookies.clear()
    assert client.get("/auth/me").status_code == 401
    response = signin(client)
    assert client.get("/auth/me").json()["email"] == "ana@example.com"
    assert response.status_code == 200


def test_sign_out_clears_the_session(client):
    signup(client)
    assert client.get("/auth/me").status_code == 200
    assert post(client, "/auth/signout", {}).status_code == 204
    client.cookies.clear()
    assert client.get("/auth/me").status_code == 401


def test_cookie_write_without_the_csrf_header_is_refused(client):
    signup(client)
    assert post(client, "/probe", {}, headers={}).status_code == 403
    assert post(client, "/probe", {}, headers={}).json() == {"error": "csrf-check-failed"}
    assert post(client, "/probe", {}, headers=CSRF).json()["user"]


def test_expired_cookie_is_treated_as_signed_out_and_sign_in_still_works(client):
    signup(client)
    expired = jwt.encode({"sub": "u1", "exp": int(time.time()) - 10}, SECRET, algorithm="HS256")
    client.cookies.set("session", expired)
    assert client.get("/auth/me").status_code == 401  # signed out, not a server error
    assert signin(client).status_code == 200  # the stale cookie does not block signing in again


def test_lockout_blocks_even_the_right_password_until_the_period_passes(client):
    signup(client)
    clock = FakeClock()
    client.app.state.accounts.lockout = LoginLockout(max_failures=3, lock_seconds=900, clock=clock)
    for _ in range(3):
        assert signin(client, password="wrong-password-99").status_code == 401
    locked = signin(client)
    assert locked.status_code == 429
    assert locked.json() == {"error": "too-many-attempts"}
    clock.now += 901
    assert signin(client).status_code == 200


def test_password_reset_link_works_once_and_changes_the_password(client):
    signup(client)
    sent: list[tuple[str, str]] = []

    async def sender(email: str, token: str) -> None:
        sent.append((email, token))

    client.app.state.accounts.reset_sender = sender
    assert post(client, "/auth/password-reset/request", {"email": "ana@example.com"}).status_code == 202
    assert post(client, "/auth/password-reset/request", {"email": "nobody@example.com"}).status_code == 202
    assert len(sent) == 1  # an unknown address gets the same answer but no email

    token = sent[0][1]
    confirm = post(client, "/auth/password-reset/confirm", {"token": token, "password": "new-password-77"})
    assert confirm.status_code == 200
    assert signin(client, password=PASSWORD).status_code == 401
    assert signin(client, password="new-password-77").status_code == 200

    reused = post(client, "/auth/password-reset/confirm", {"token": token, "password": "other-password-88"})
    assert reused.status_code == 400
    assert reused.json() == {"error": "invalid-or-expired-token"}


def test_reset_and_session_tokens_cannot_be_swapped(client):
    signup(client)
    sent: list[str] = []

    async def sender(email: str, token: str) -> None:
        sent.append(token)

    client.app.state.accounts.reset_sender = sender
    post(client, "/auth/password-reset/request", {"email": "ana@example.com"})
    reset_token = sent[0]
    session_token = client.cookies.get("session")

    assert client.get("/auth/me", headers={"Authorization": f"Bearer {reset_token}"}).status_code == 401
    refused = post(client, "/auth/password-reset/confirm", {"token": session_token, "password": "new-password-77"})
    assert refused.status_code == 400
