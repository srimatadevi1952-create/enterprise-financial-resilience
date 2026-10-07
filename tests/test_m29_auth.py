from datetime import datetime, timedelta, timezone
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from threading import Thread
from pathlib import Path

import pytest

from resilience.m29_auth import AuthService, AuthenticationError, AuthUser, InMemoryAuthRepository
from resilience.m22_web import ConsoleApplication, make_handler
from resilience.config import ROOT
from resilience.m27_assurance import OperationalAssuranceService
from resilience.m22_console import Principal


class Clock:
    def __init__(self):
        self.value = datetime(2026, 10, 7, 12, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.value


def service():
    clock = Clock()
    user = AuthUser("actor-1", "Test Analyst", "analyst@example.test", "simulation_analyst", clock() + timedelta(days=7))
    return AuthService(InMemoryAuthRepository([user]), secret=b"x" * 32, now=clock), clock


def test_invited_user_receives_one_time_code_and_role_scopes():
    auth, _ = service()
    issued = auth.request_code("ANALYST@example.test")
    token, user = auth.verify_code("analyst@example.test", issued["development_code"])
    assert user.role == "simulation_analyst"
    assert "simulation:create" in auth.authenticate(token).principal().scopes
    with pytest.raises(AuthenticationError, match="INVALID_OR_EXPIRED_CODE"):
        auth.verify_code("analyst@example.test", issued["development_code"])


def test_only_share_entitled_user_can_read_active_collaborator_directory():
    auth, _ = service()
    analyst = auth.repository.get_user("analyst@example.test").principal()
    assert auth.eligible_collaborators(analyst) == []
    viewer = AuthUser("viewer-2", "Test Viewer", "viewer@example.test", "viewer", datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc))
    auth.repository.users[viewer.email] = viewer
    assert auth.eligible_collaborators(analyst)[0]["actor_id"] == "viewer-2"
    with pytest.raises(AuthenticationError, match="COLLABORATOR_DIRECTORY_DENIED"):
        auth.eligible_collaborators(viewer.principal())


def test_unknown_identity_does_not_reveal_invitation_status():
    auth, _ = service()
    known = auth.request_code("analyst@example.test")
    unknown = auth.request_code("unknown@example.test")
    assert known["message"] == unknown["message"]
    assert "development_code" not in unknown


def test_session_idle_expiry_logout_and_user_revocation_are_enforced():
    auth, clock = service()
    issued = auth.request_code("analyst@example.test")
    token, _ = auth.verify_code("analyst@example.test", issued["development_code"])
    clock.value += timedelta(minutes=31)
    with pytest.raises(AuthenticationError, match="SESSION_EXPIRED"):
        auth.authenticate(token)

    issued = auth.request_code("analyst@example.test")
    token, _ = auth.verify_code("analyst@example.test", issued["development_code"])
    auth.logout(token)
    with pytest.raises(AuthenticationError, match="SESSION_EXPIRED"):
        auth.authenticate(token)


def test_hosted_environment_refuses_ephemeral_auth_repository():
    with pytest.raises(AuthenticationError, match="DURABLE_AUTH_REPOSITORY_REQUIRED"):
        AuthService(InMemoryAuthRepository(), secret=b"x" * 32, environment="uat")


def test_environment_factory_does_not_seed_demo_users_in_hosted_uat(monkeypatch):
    monkeypatch.setenv("EFR_APP_ENV", "uat")
    with pytest.raises(AuthenticationError, match="HOSTED_AUTH_CONFIGURATION_INCOMPLETE"):
        AuthService.from_environment()


def test_console_requires_cookie_session_and_ignores_legacy_role_header():
    auth, _ = service()
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ConsoleApplication(auth)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
    try:
        connection.request("GET", "/", headers={"X-EFR-Principal": "analyst"})
        response = connection.getresponse()
        response.read()
        assert response.status == 303
        assert response.getheader("Location") == "/login"

        connection.request("GET", "/api/bootstrap", headers={"X-EFR-Principal": "analyst"})
        response = connection.getresponse()
        response.read()
        assert response.status == 401

        connection.request("GET", "/api/health")
        response = connection.getresponse()
        health = json.loads(response.read())
        assert response.status == 200
        assert health == {"status": "ok", "environment": "development", "database": True}

        body = json.dumps({"email": "analyst@example.test"})
        connection.request("POST", "/api/auth/request-code", body, {"Content-Type": "application/json"})
        issued = json.loads(connection.getresponse().read())
        body = json.dumps({"email": "analyst@example.test", "code": issued["development_code"]})
        connection.request("POST", "/api/auth/verify-code", body, {"Content-Type": "application/json"})
        response = connection.getresponse()
        response.read()
        cookie = response.getheader("Set-Cookie").split(";", 1)[0]

        connection.request("GET", "/api/bootstrap", headers={"Cookie": cookie, "X-EFR-Principal": "client"})
        response = connection.getresponse()
        bootstrap = json.loads(response.read())
        assert response.status == 200
        assert bootstrap["principal"]["actor_id"] == "actor-1"
        assert "simulation:create" in bootstrap["principal"]["scopes"]
    finally:
        connection.close()
        server.shutdown()
        server.server_close()


def test_vercel_package_declares_single_python_entry_and_durable_tables():
    config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    assert "api/index.py" in config["functions"]
    assert config["rewrites"][0]["destination"] == "/api/index.py"
    entry = (ROOT / "api" / "index.py").read_text(encoding="utf-8")
    assert "handler = make_handler(ConsoleApplication())" in entry
    schema = (ROOT / "deploy" / "m29_hosted_schema.sql").read_text(encoding="utf-8")
    for table in ("auth_users", "login_challenges", "web_sessions", "auth_audit_events", "simulation_sessions", "collaboration_invitations", "assurance_state", "assurance_events"):
        assert f"efr_uat.{table}" in schema
    console = (ROOT / "src" / "resilience" / "web" / "console.js").read_text(encoding="utf-8")
    assert "'/api/auth/collaborators'" in console
    assert "actor_id:'viewer-1'" not in console


def test_assurance_decision_adapter_survives_service_recreation():
    state = {"decision": "AWAITING_DECISION", "events": []}
    def load(): return state["decision"]
    def record(kind, event):
        state["events"].append((kind, event))
        if kind == "DECISION": state["decision"] = event["decision"]
    client = Principal("client-1", "Client Approver", frozenset({"assurance:client:view", "assurance:client:decide"}))
    first = OperationalAssuranceService(decision_loader=load, event_recorder=record)
    first.record_client_decision(client, "APPROVED", step_up_verified=True, rationale="Hosted UAT")
    recreated = OperationalAssuranceService(decision_loader=load, event_recorder=record)
    assert recreated.bootstrap(client, "client")["recommendation"]["status"] == "APPROVED"
    assert state["events"][0][0] == "DECISION"
