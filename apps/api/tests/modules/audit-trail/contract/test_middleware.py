from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from app.audit.middleware import create_audit_middleware
from app.audit.trail import AuditEntry, AuditTrail


class Auth:
    def __init__(self, user_id, tenant_id=None):
        self.user_id, self.tenant_id = user_id, tenant_id


def make(entries: list[AuditEntry], auth=None):
    app = FastAPI()
    app.middleware("http")(create_audit_middleware(AuditTrail(sink=entries.append)))

    @app.middleware("http")
    async def identify(request, call_next):  # stands in for the authentication middleware (outer)
        request.state.auth = auth
        return await call_next(request)

    router = APIRouter()
    router.add_api_route("/notes", lambda: [], methods=["GET"])
    router.add_api_route("/notes", lambda: {"ok": True}, methods=["POST"])
    router.add_api_route("/notes/{n}", lambda n: {"n": n}, methods=["DELETE"])

    @router.post("/boom")
    def boom():
        raise RuntimeError("secret internals")

    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


def test_state_changing_requests_are_recorded_with_actor_tenant_route_and_status():
    entries: list[AuditEntry] = []
    client = make(entries, Auth("u1", "t1"))
    client.post("/notes")
    client.delete("/notes/7")
    assert [(e.actor, e.tenant_id, e.action, e.meta) for e in entries] == [
        ("u1", "t1", "POST /notes", {"status": 200}),
        ("u1", "t1", "DELETE /notes/7", {"status": 200}),
    ]


def test_reads_are_not_recorded():
    entries: list[AuditEntry] = []
    client = make(entries, Auth("u1"))
    client.get("/notes")
    client.options("/notes")
    assert entries == []


def test_an_anonymous_caller_is_recorded_as_anonymous():
    entries: list[AuditEntry] = []
    make(entries).post("/notes")
    assert entries[0].actor == "anonymous" and entries[0].tenant_id is None


def test_a_failed_request_is_recorded_with_its_status():
    entries: list[AuditEntry] = []
    client = make(entries, Auth("u1"))
    assert client.post("/boom").status_code == 500
    assert client.post("/missing").status_code == 404
    assert [e.meta for e in entries] == [{"status": 500}, {"status": 404}]


def test_the_query_string_and_body_are_not_recorded():
    entries: list[AuditEntry] = []
    make(entries, Auth("u1")).post("/notes?token=abc", json={"password": "p"})
    assert entries[0].action == "POST /notes"
    assert "abc" not in repr(entries[0]) and "password" not in repr(entries[0])
