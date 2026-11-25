"""Contract: the account building blocks (passwords, tokens, lockout, ownership, cookie settings) in isolation."""

import time

import jwt
import pytest
from fastapi import HTTPException

from app.auth.jwt import AuthClaims, verify_token
from app.auth.lockout import LoginLockout
from app.auth.ownership import owns, require_owner
from app.auth.passwords import hash_password, normalise_email, password_problem, verify_password
from app.auth.settings import AccountSettings
from app.auth.tokens import issue_reset_token, issue_session_token, password_fingerprint, verify_reset_token

SECRET = "s" * 40


@pytest.fixture(autouse=True)
def secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)


def test_email_is_trimmed_lower_cased_and_checked():
    assert normalise_email("  Ana@Example.COM ") == "ana@example.com"
    assert normalise_email("not-an-email") is None
    assert normalise_email("a b@example.com") is None
    assert normalise_email("x@" + "a" * 250 + ".com") is None


def test_password_needs_length_a_letter_and_a_digit():
    assert password_problem("short1") == "weak-password"
    assert password_problem("allletterslongenough") == "weak-password"
    assert password_problem("123456789012345") == "weak-password"
    assert password_problem("correct-horse-42") is None


def test_password_is_hashed_with_argon2id_and_verified():
    stored = hash_password("correct-horse-42")
    assert "correct-horse-42" not in stored
    assert stored.startswith("$argon2id$")
    assert verify_password(stored, "correct-horse-42") is True
    assert verify_password(stored, "wrong-password-99") is False
    assert verify_password(None, "correct-horse-42") is False


def test_a_session_token_is_not_a_reset_token_and_the_reverse():
    session = issue_session_token("u1", ttl_seconds=60)
    reset = issue_reset_token("u1", hash_password("correct-horse-42"), ttl_seconds=60)
    assert verify_token(session).user_id == "u1"
    with pytest.raises(jwt.PyJWTError):
        verify_token(reset)  # a reset token must never authenticate a session
    with pytest.raises(jwt.PyJWTError):
        verify_reset_token(session)  # and a session must never reset a password
    assert verify_reset_token(reset)["sub"] == "u1"


def test_reset_fingerprint_changes_with_the_password_hash():
    first = hash_password("correct-horse-42")
    second = hash_password("correct-horse-42")  # same password, new salt
    assert password_fingerprint(first) != password_fingerprint(second)


def test_expired_session_token_is_rejected():
    expired = jwt.encode({"sub": "u1", "exp": int(time.time()) - 10}, SECRET, algorithm="HS256")
    with pytest.raises(jwt.PyJWTError):
        verify_token(expired)


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_lockout_locks_after_the_limit_and_unlocks_after_the_period():
    clock = FakeClock()
    lockout = LoginLockout(max_failures=3, lock_seconds=60, clock=clock)
    for _ in range(2):
        lockout.record_failure("email:a@example.com")
    assert lockout.is_locked("email:a@example.com") is False
    lockout.record_failure("email:a@example.com")
    assert lockout.is_locked("email:a@example.com") is True
    clock.now += 61
    assert lockout.is_locked("email:a@example.com") is False


def test_a_successful_sign_in_clears_the_failure_count():
    lockout = LoginLockout(max_failures=3, lock_seconds=60, clock=FakeClock())
    lockout.record_failure("email:a@example.com")
    lockout.record_failure("email:a@example.com")
    lockout.reset("email:a@example.com")
    lockout.record_failure("email:a@example.com")
    assert lockout.is_locked("email:a@example.com") is False


def test_owner_only_access():
    owner = AuthClaims(user_id="u1")
    assert owns(owner, "u1") is True
    assert owns(owner, "u2") is False
    assert owns(owner, None) is False  # an unowned row belongs to nobody
    assert owns(None, "u1") is False  # anonymous callers own nothing
    require_owner(owner, "u1")
    with pytest.raises(HTTPException) as denied:
        require_owner(owner, "u2")
    assert denied.value.status_code == 404  # same answer as a missing row


def test_the_session_cookie_is_secure_by_default(monkeypatch):
    monkeypatch.delenv("COOKIE_SECURE", raising=False)
    assert AccountSettings(_env_file=None).cookie_secure is True
