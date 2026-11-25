"""Append-only audit trail: who did what to what, when.

Entries are redacted, size-capped and immutable before they reach the sink.
"""

import inspect
import json
import logging
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

log = logging.getLogger("app.audit")

DEFAULT_REDACT = ("password", "token", "secret", "authorization", "apikey", "api_key", "cookie")
MAX_META_CHARS = 4096


@dataclass(frozen=True)
class AuditEvent:
    actor: str
    action: str
    target: str | None = None
    tenant_id: str | None = None
    meta: dict[str, Any] | None = None


@dataclass(frozen=True)
class AuditEntry:
    actor: str
    action: str
    at: str
    target: str | None = None
    tenant_id: str | None = None
    meta: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """The JSON shape shared with the Node module: tenantId, and no key for what is not set."""
        body: dict[str, Any] = {"actor": self.actor, "action": self.action, "at": self.at}
        if self.target is not None:
            body["target"] = self.target
        if self.tenant_id is not None:
            body["tenantId"] = self.tenant_id
        if self.meta is not None:
            body["meta"] = self.meta
        return body


Sink = Callable[[AuditEntry], Awaitable[None] | None]


def redact(value: Any, keys: frozenset[str], depth: int = 0) -> Any:
    """Replaces the values of the given keys (case-insensitive) with "[redacted]" at any depth."""
    if depth > 6:
        return "[truncated]"
    if isinstance(value, list):
        return [redact(v, keys, depth + 1) for v in value]
    if isinstance(value, dict):
        return {k: "[redacted]" if str(k).lower() in keys else redact(v, keys, depth + 1) for k, v in value.items()}
    return value


def console_sink(entry: AuditEntry) -> None:
    """One JSON line per entry on stdout; replace with a database or log-service sink in production."""
    sys.stdout.write(json.dumps(entry.to_dict()) + "\n")


class AuditTrail:
    def __init__(
        self,
        sink: Sink = console_sink,
        redact_keys: tuple[str, ...] = DEFAULT_REDACT,
        fail_closed: bool = False,
        on_error: Callable[[BaseException, AuditEntry], None] | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.sink = sink
        self.keys = frozenset(k.lower() for k in redact_keys)
        self.fail_closed = fail_closed  # raise when the sink fails (default: report it and let the request go on)
        self.on_error = on_error or (lambda err, _entry: log.error("audit sink failed: %s", err))
        self.now = now or (lambda: datetime.now(UTC))

    async def record(self, event: AuditEvent) -> AuditEntry:
        if not event.actor or not event.action:
            raise ValueError("an audit event needs an actor and an action")
        meta = redact(event.meta, self.keys) if event.meta is not None else None
        if meta is not None and len(json.dumps(meta, default=str)) > MAX_META_CHARS:
            meta = {"truncated": True}
        entry = AuditEntry(
            actor=event.actor,
            action=event.action,
            at=self.now().isoformat(),
            target=event.target,
            tenant_id=event.tenant_id,
            meta=meta,
        )
        try:
            result = self.sink(entry)
            if inspect.isawaitable(result):
                await result
        except Exception as err:
            if self.fail_closed:
                raise
            self.on_error(err, entry)
        return entry
