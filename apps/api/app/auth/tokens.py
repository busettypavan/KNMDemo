"""Issuing and checking the tokens this API signs: the session token (the cookie) and the password reset token.

Both use HS256 with JWT_SECRET (see app/auth/jwt.py). A reset token carries a purpose claim, so it can never be used as
a session, and a session token has no purpose, so it can never be used to reset a password. A reset token also carries
a fingerprint of the password hash it was issued for, so it stops working as soon as the password changes.
"""

import hashlib
import time
from typing import Any

import jwt

from app.auth.jwt import AuthConfigError, AuthSettings

RESET_PURPOSE = "password-reset"


def _sign(claims: dict[str, Any], cfg: AuthSettings) -> str:
    if len(cfg.jwt_secret) < 32:
        raise AuthConfigError("JWT_SECRET must be set to a random string of at least 32 characters")
    return jwt.encode(claims, cfg.jwt_secret, algorithm="HS256")


def _base_claims(subject: str, ttl_seconds: int, cfg: AuthSettings) -> dict[str, Any]:
    now = int(time.time())
    claims: dict[str, Any] = {"sub": subject, "iat": now, "exp": now + ttl_seconds}
    if cfg.jwt_issuer:
        claims["iss"] = cfg.jwt_issuer
    if cfg.jwt_audience:
        claims["aud"] = cfg.jwt_audience
    return claims


def password_fingerprint(password_hash: str) -> str:
    """Short, non-reversible tag of a stored hash. Changes whenever the password changes."""
    return hashlib.sha256(password_hash.encode()).hexdigest()[:32]


def issue_session_token(user_id: str, ttl_seconds: int, settings: AuthSettings | None = None) -> str:
    return _sign(_base_claims(user_id, ttl_seconds, settings or AuthSettings()), settings or AuthSettings())


def issue_reset_token(user_id: str, password_hash: str, ttl_seconds: int, settings: AuthSettings | None = None) -> str:
    cfg = settings or AuthSettings()
    claims = _base_claims(user_id, ttl_seconds, cfg)
    claims["purpose"] = RESET_PURPOSE
    claims["pwh"] = password_fingerprint(password_hash)
    return _sign(claims, cfg)


def verify_reset_token(token: str, settings: AuthSettings | None = None) -> dict[str, Any]:
    """Returns the reset claims. Raises jwt.PyJWTError for a bad, expired or non-reset token."""
    cfg = settings or AuthSettings()
    if len(cfg.jwt_secret) < 32:
        raise AuthConfigError("JWT_SECRET must be set to a random string of at least 32 characters")
    payload = jwt.decode(
        token,
        cfg.jwt_secret,
        algorithms=["HS256"],
        issuer=cfg.jwt_issuer,
        audience=cfg.jwt_audience,
        options={"require": ["exp", "sub", "iat"], "verify_aud": cfg.jwt_audience is not None},
    )
    if payload.get("purpose") != RESET_PURPOSE or not isinstance(payload.get("pwh"), str):
        raise jwt.InvalidTokenError("not a password reset token")
    return payload
