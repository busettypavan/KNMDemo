"""Data isolation: a signed-in user may only read or change the rows they own.

A resource that belongs to someone else (or has no owner) is answered with 404, the same as a missing one, so the API
does not reveal that it exists.
"""

from fastapi import HTTPException

from app.auth.jwt import AuthClaims


def owns(auth: AuthClaims | None, owner_id: str | None) -> bool:
    return auth is not None and owner_id is not None and auth.user_id == owner_id


def require_owner(auth: AuthClaims | None, owner_id: str | None) -> None:
    if not owns(auth, owner_id):
        raise HTTPException(status_code=404, detail="not-found")
