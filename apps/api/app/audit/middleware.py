"""Records every state-changing request (not GET, HEAD or OPTIONS): actor, tenant, route and status.

Register it after authentication (in the middleware glue, inner) so the actor is known.
"""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.responses import Response

from app.audit.trail import AuditEvent, AuditTrail

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


def _actor_and_tenant(request: Request) -> tuple[str, str | None]:
    auth = getattr(request.state, "auth", None)
    user = getattr(auth, "user_id", None)
    tenant = getattr(auth, "tenant_id", None) or getattr(request.state, "tenant_id", None)
    return (user if isinstance(user, str) and user else "anonymous"), (tenant if isinstance(tenant, str) else None)


def create_audit_middleware(
    trail: AuditTrail,
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    async def audit(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.method.upper() in SAFE_METHODS:
            return await call_next(request)
        status = 500  # an exception that escapes the app is a 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            actor, tenant = _actor_and_tenant(request)
            await trail.record(
                AuditEvent(
                    actor=actor,
                    action=f"{request.method.upper()} {request.url.path}",
                    tenant_id=tenant,
                    meta={"status": status},
                )
            )

    return audit


def audit_middleware(app: FastAPI) -> None:
    """Registered in the middleware glue (inner, after authentication)."""
    trail = AuditTrail()
    app.state.audit = trail
    app.middleware("http")(create_audit_middleware(trail))
