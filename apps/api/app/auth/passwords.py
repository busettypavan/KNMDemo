"""Password hashing (Argon2id) and the password and email rules. Plain-text passwords are never stored or logged."""

import re

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 256
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_hasher = PasswordHasher()  # Argon2id with the library's defaults
# Checked when the email is unknown, so a missing account costs the same time as a wrong password.
_DUMMY_HASH = _hasher.hash("timing-equaliser-not-a-real-password")


def normalise_email(raw: str) -> str | None:
    """Lower-cased and trimmed, or None when the value is not a plausible email address."""
    email = raw.strip().lower()
    if len(email) > 254 or not _EMAIL.match(email):
        return None
    return email


def password_problem(password: str) -> str | None:
    """None when the password is strong enough; otherwise the error code. Requires length, a letter and a digit."""
    if len(password) < MIN_PASSWORD_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
        return "weak-password"
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "weak-password"
    return None


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(stored_hash: str | None, password: str) -> bool:
    """False for a wrong password or an unreadable hash. A missing hash is checked against a dummy (see _DUMMY_HASH)."""
    try:
        return _hasher.verify(stored_hash or _DUMMY_HASH, password) and stored_hash is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def dummy_verify(password: str) -> None:
    """Spends the same time as a real check when the email is unknown."""
    verify_password(None, password)
