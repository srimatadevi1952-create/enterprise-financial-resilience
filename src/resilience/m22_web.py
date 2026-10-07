"""Local HTTP application for the M22 operating console."""

from __future__ import annotations

import csv
import json
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from .config import ROOT
from .m22_console import ConsoleAuthorizationError, ConsoleService, Principal, group_variable_register
from .m27_assurance import OperationalAssuranceService
from .m28_scenario_intelligence import explain_console_scenario
from .m29_auth import AuthService, AuthenticationError


WEB_ROOT = Path(__file__).with_name("web")
ASSET_ROOT = ROOT / "docs" / "assets"

SESSION_COOKIE = "efr_uat_session"


class ConsoleApplication:
    def __init__(self, auth: AuthService | None = None):
        self.auth = auth or AuthService.from_environment()
        self.service = ConsoleService()
        self.assurance = OperationalAssuranceService(lambda: self.service.live_state)
        with (ROOT / "config" / "m22_manipulated_variables.csv").open(encoding="utf-8-sig", newline="") as handle:
            self.variables = group_variable_register(csv.DictReader(handle))


def make_handler(application: ConsoleApplication):
    class Handler(BaseHTTPRequestHandler):
        server_version = "EFRConsole/0.1"

        def do_GET(self):
            path = unquote(urlparse(self.path).path)
            query = parse_qs(urlparse(self.path).query)
            if path.startswith("/api/"):
                try:
                    self._user()
                except AuthenticationError as exc:
                    self._error(exc)
                    return
            if path == "/login":
                if self._optional_user():
                    self._redirect("/")
                else:
                    self._file(WEB_ROOT / "login.html")
            elif path == "/api/auth/session":
                user = self._user()
                self._json({
                    "authenticated": True,
                    "user": {"actor_id": user.actor_id, "display_name": user.display_name, "role": user.role},
                    "access_expires_at": user.access_expires_at.isoformat(),
                })
            elif path == "/api/bootstrap":
                principal = self._principal()
                self._json({
                    "principal": {"actor_id": principal.actor_id, "display_name": principal.display_name, "scopes": sorted(principal.scopes)},
                    "mode": "live",
                    "live": application.service.live_state.as_dict(),
                    "variables": application.variables,
                    "environment": application.auth.environment,
                    "identity_adapter": "invitation-one-time-code",
                    "model_profile": {
                        "model_version": "DEFAULT-UAT-V1",
                        "calibration_state": "DEFAULT_UNCALIBRATED",
                        "enterprise_specific": False,
                        "notice": "Connect approved enterprise history and activate an independently approved M28 calibration.",
                    },
                })
            elif path == "/api/operational-assurance/bootstrap":
                try:
                    view = query.get("view", ["enterprise"])[0]
                    self._json(application.assurance.bootstrap(self._principal(), view))
                except Exception as exc:
                    self._error(exc)
            elif path == "/api/operational-assurance/detail":
                try:
                    view = query.get("view", ["enterprise"])[0]
                    panel = query.get("panel", [""])[0]
                    self._json(application.assurance.detail(self._principal(), view, panel))
                except Exception as exc:
                    self._error(exc)
            elif path.startswith("/api/simulation-sessions/"):
                try:
                    parts = path.strip("/").split("/")
                    session_id = parts[2]
                    if len(parts) == 4 and parts[3] == "collaboration":
                        self._json(application.service.list_collaboration(self._principal(), session_id))
                    else:
                        session = application.service.get_session(self._principal(), session_id)
                        self._json(self._session_payload(session))
                except Exception as exc:
                    self._error(exc)
            elif path.startswith("/assets/"):
                self._file(ASSET_ROOT / path.removeprefix("/assets/"))
            elif path.startswith("/web-assets/"):
                self._file(WEB_ROOT / path.removeprefix("/web-assets/"))
            elif path == "/dom-console-v2.html":
                if self._optional_user():
                    self._file(WEB_ROOT / "dom-console-v2.html")
                else:
                    self._redirect("/login")
            elif path in {"/", "/index.html", "/*", "/**"}:
                if self._optional_user():
                    self._file(WEB_ROOT / "index.html")
                else:
                    self._redirect("/login")
            else:
                self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self):
            path = urlparse(self.path).path
            try:
                body = self._body()
                if path == "/api/auth/request-code":
                    result = application.auth.request_code(str(body.get("email", "")), remote_address=self.client_address[0])
                    self._json(result, HTTPStatus.ACCEPTED)
                    return
                if path == "/api/auth/verify-code":
                    token, user = application.auth.verify_code(
                        str(body.get("email", "")), str(body.get("code", "")), remote_address=self.client_address[0]
                    )
                    secure = self.headers.get("X-Forwarded-Proto", "http").casefold() == "https"
                    self._json(
                        {"authenticated": True, "user": {"display_name": user.display_name, "role": user.role}},
                        headers={"Set-Cookie": self._session_cookie(token, secure=secure)},
                    )
                    return
                if path == "/api/auth/logout":
                    application.auth.logout(self._session_token(), remote_address=self.client_address[0])
                    self._json(
                        {"authenticated": False},
                        headers={"Set-Cookie": self._session_cookie("", max_age=0)},
                    )
                    return
                principal = self._principal()
                if path == "/api/simulation-sessions":
                    session = application.service.create_simulation(
                        principal,
                        step_up_verified=bool(body.get("step_up_verified")),
                        purpose=str(body.get("purpose", "")),
                    )
                    self._json(self._session_payload(session), HTTPStatus.CREATED)
                elif path.endswith("/run") and path.startswith("/api/simulation-sessions/"):
                    session_id = path.split("/")[3]
                    baseline = application.service.get_session(principal, session_id).state.as_dict()
                    state = application.service.run_scenario(principal, session_id, body.get("controls", {}))
                    result = state.as_dict()
                    self._json({"state": result, "scenario": explain_console_scenario(baseline, result), "live_unchanged": True})
                elif path.endswith("/invite") and path.startswith("/api/simulation-sessions/"):
                    session_id = path.split("/")[3]
                    invite = application.service.invite(principal, session_id, str(body.get("actor_id", "")), str(body.get("role", "")))
                    self._json(invite, HTTPStatus.CREATED)
                elif path.endswith("/invitations") and path.startswith("/api/simulation-sessions/"):
                    session_id = path.split("/")[3]
                    invitation = application.service.create_invitation(
                        principal, session_id, str(body.get("actor_id", "")), str(body.get("role", "viewer")),
                        ttl_minutes=int(body.get("ttl_minutes", 30)),
                    )
                    self._json(invitation, HTTPStatus.CREATED)
                elif path.endswith("/invitations/revoke") and path.startswith("/api/simulation-sessions/"):
                    session_id = path.split("/")[3]
                    invitation = application.service.revoke_invitation(
                        principal, session_id, str(body.get("token", ""))
                    )
                    self._json(invitation)
                elif path == "/api/collaboration/join":
                    result = application.service.join_invitation(principal, str(body.get("token", "")))
                    self._json(result)
                elif path == "/api/operational-assurance/client-decision":
                    result = application.assurance.record_client_decision(
                        principal,
                        str(body.get("decision", "")),
                        step_up_verified=bool(body.get("step_up_verified")),
                        rationale=str(body.get("rationale", "")),
                    )
                    self._json(result, HTTPStatus.CREATED)
                else:
                    self.send_error(HTTPStatus.NOT_FOUND)
            except Exception as exc:
                self._error(exc)

        def _session_token(self) -> str | None:
            cookie = SimpleCookie()
            cookie.load(self.headers.get("Cookie", ""))
            morsel = cookie.get(SESSION_COOKIE)
            return morsel.value if morsel else None

        def _user(self):
            return application.auth.authenticate(self._session_token())

        def _optional_user(self):
            try:
                return self._user()
            except AuthenticationError:
                return None

        def _principal(self) -> Principal:
            return self._user().principal()

        def _body(self) -> dict:
            length = int(self.headers.get("Content-Length", "0"))
            return json.loads(self.rfile.read(length) or b"{}")

        @staticmethod
        def _session_payload(session):
            return ConsoleService.session_payload(session)

        def _json(self, payload: dict, status=HTTPStatus.OK, headers: dict | None = None):
            data = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'")
            for name, value in (headers or {}).items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(data)

        @staticmethod
        def _session_cookie(value: str, *, secure: bool = False, max_age: int | None = None) -> str:
            cookie = SimpleCookie()
            cookie[SESSION_COOKIE] = value
            cookie[SESSION_COOKIE]["path"] = "/"
            cookie[SESSION_COOKIE]["httponly"] = True
            cookie[SESSION_COOKIE]["samesite"] = "Strict"
            if secure:
                cookie[SESSION_COOKIE]["secure"] = True
            if max_age is not None:
                cookie[SESSION_COOKIE]["max-age"] = max_age
            return cookie.output(header="").strip()

        def _redirect(self, location: str):
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", location)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

        def _file(self, path: Path):
            try:
                resolved = path.resolve(strict=True)
                allowed = {WEB_ROOT.resolve(), ASSET_ROOT.resolve()}
                if not any(root == resolved or root in resolved.parents for root in allowed):
                    raise FileNotFoundError
                data = resolved.read_bytes()
            except (FileNotFoundError, OSError):
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            content_type = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".png": "image/png", ".svg": "image/svg+xml"}.get(resolved.suffix.lower(), "application/octet-stream")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _error(self, exc: Exception):
            if isinstance(exc, ConsoleAuthorizationError):
                status = HTTPStatus.FORBIDDEN
            elif isinstance(exc, AuthenticationError):
                status = HTTPStatus.UNAUTHORIZED
            elif isinstance(exc, KeyError):
                status = HTTPStatus.NOT_FOUND
            elif isinstance(exc, (ValueError, TypeError, json.JSONDecodeError)):
                status = HTTPStatus.BAD_REQUEST
            else:
                status = HTTPStatus.INTERNAL_SERVER_ERROR
            self._json({"error": str(exc)}, status)

        def log_message(self, format, *args):
            return

    return Handler


def serve(host: str = "127.0.0.1", port: int = 8766):
    if host != "127.0.0.1":
        raise ValueError("LOCALHOST_ONLY")
    server = ThreadingHTTPServer((host, port), make_handler(ConsoleApplication()))
    print(f"EFR M22 console available at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
