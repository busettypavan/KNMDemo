"""Fit: the middleware is registered in THIS app's glue, after authentication, and records through create_app."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.http.app import create_app
from app.http.settings import Settings

GLUE = Path(__file__).resolve().parents[4] / "app" / "glue"


def test_the_audit_middleware_is_registered_in_the_middleware_glue():
    text = (GLUE / "middleware.py").read_text()
    assert "audit_middleware" in text and "# knm:module audit-trail" in text


def test_a_state_changing_call_through_the_real_glue_is_recorded(capsys):
    app = create_app(settings=Settings(env="production"))
    app.add_api_route("/things", lambda: {"ok": True}, methods=["POST"])
    assert TestClient(app).post("/things").status_code == 200
    lines = [line for line in capsys.readouterr().out.splitlines() if '"action": "POST /things"' in line]
    assert len(lines) == 1 and '"actor": "anonymous"' in lines[0]
