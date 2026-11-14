import json
from datetime import UTC, datetime

import pytest

from app.audit.trail import DEFAULT_REDACT, MAX_META_CHARS, AuditEntry, AuditEvent, AuditTrail, console_sink, redact

FIXED = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)


def trail(sink, **kw):
    return AuditTrail(sink=sink, now=lambda: FIXED, **kw)


async def test_records_who_did_what_and_when_and_hands_the_entry_to_the_sink():
    seen: list[AuditEntry] = []
    entry = await trail(seen.append).record(
        AuditEvent(actor="u1", action="POST /notes", target="note:1", tenant_id="t1", meta={"status": 200})
    )
    assert seen == [entry]
    assert entry.to_dict() == {
        "actor": "u1",
        "action": "POST /notes",
        "at": "2026-01-02T03:04:05+00:00",
        "target": "note:1",
        "tenantId": "t1",
        "meta": {"status": 200},
    }


async def test_unset_fields_are_left_out_of_the_json_shape():
    entry = await trail(lambda e: None).record(AuditEvent(actor="u1", action="login"))
    assert set(entry.to_dict()) == {"actor", "action", "at"}


async def test_an_event_needs_an_actor_and_an_action():
    for event in (AuditEvent(actor="", action="x"), AuditEvent(actor="u", action="")):
        with pytest.raises(ValueError):
            await trail(lambda e: None).record(event)


async def test_secrets_are_redacted_at_any_depth_case_insensitively_and_the_event_is_not_changed():
    meta = {"Password": "p", "user": {"token": "t", "tags": [{"apiKey": "k"}, "ok"]}, "note": "fine"}
    entry = await trail(lambda e: None).record(AuditEvent(actor="u", action="a", meta=meta))
    assert entry.meta == {
        "Password": "[redacted]",
        "user": {"token": "[redacted]", "tags": [{"apiKey": "[redacted]"}, "ok"]},
        "note": "fine",
    }
    assert meta["Password"] == "p"
    assert {"password", "token", "secret", "authorization", "cookie"} <= set(DEFAULT_REDACT)


def test_redaction_stops_at_a_depth_limit():
    deep: dict = {}
    node = deep
    for _ in range(9):
        node["a"] = {}
        node = node["a"]
    assert "[truncated]" in json.dumps(redact(deep, frozenset()))


async def test_oversized_metadata_is_replaced_by_a_marker():
    entry = await trail(lambda e: None).record(
        AuditEvent(actor="u", action="a", meta={"blob": "x" * (MAX_META_CHARS + 1)})
    )
    assert entry.meta == {"truncated": True}


async def test_entries_are_immutable():
    entry = await trail(lambda e: None).record(AuditEvent(actor="u", action="a"))
    with pytest.raises(AttributeError):
        entry.actor = "other"  # type: ignore[misc]


async def test_a_failing_sink_is_reported_and_the_request_goes_on_unless_fail_closed():
    def broken(entry):
        raise RuntimeError("disk full")

    errors: list[str] = []
    entry = await trail(broken, on_error=lambda err, e: errors.append(str(err))).record(
        AuditEvent(actor="u", action="a")
    )
    assert entry.actor == "u" and errors == ["disk full"]
    with pytest.raises(RuntimeError):
        await trail(broken, fail_closed=True).record(AuditEvent(actor="u", action="a"))


async def test_an_async_sink_is_awaited():
    seen: list[str] = []

    async def sink(entry):
        seen.append(entry.action)

    await trail(sink).record(AuditEvent(actor="u", action="async-sink"))
    assert seen == ["async-sink"]


async def test_the_console_sink_writes_one_json_line(capsys):
    await trail(console_sink).record(AuditEvent(actor="u", action="a", tenant_id="t"))
    line = capsys.readouterr().out.strip()
    assert json.loads(line)["tenantId"] == "t" and "\n" not in line
