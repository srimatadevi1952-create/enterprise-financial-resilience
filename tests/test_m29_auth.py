from datetime import datetime, timedelta, timezone
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from threading import Thread

import pytest

from resilience.m29_auth import AuthService, AuthenticationError, AuthUser, InMemoryAuthRepository
from resilience.m22_web import ConsoleApplication, make_handler


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
    with pytest.raises(AuthenticationError, match="DURABLE_AUTH_REPOSITORY_REQUIRED"):
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
