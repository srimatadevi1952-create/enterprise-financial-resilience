"""Local HTTP application for the M22 operating console."""

from __future__ import annotations

import csv
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from .config import ROOT
from .m22_console import ConsoleAuthorizationError, ConsoleService, Principal, group_variable_register


WEB_ROOT = Path(__file__).with_name("web")
ASSET_ROOT = ROOT / "docs" / "assets"

PRINCIPALS = {
    "analyst": Principal("analyst-1", "Asha Iyer", frozenset({"live:view", "simulation:create", "simulation:share"})),
    "viewer": Principal("viewer-1", "Dev Rao", frozenset({"live:view"})),
}


class ConsoleApplication:
    def __init__(self):
        self.service = ConsoleService()
        with (ROOT / "config" / "m22_manipulated_variables.csv").open(encoding="utf-8-sig", newline="") as handle:
            self.variables = group_variable_register(csv.DictReader(handle))


def make_handler(application: ConsoleApplication):
    class Handler(BaseHTTPRequestHandler):
        server_version = "EFRConsole/0.1"

        def do_GET(self):
            path = unquote(urlparse(self.path).path)
            if path == "/api/bootstrap":
                principal = self._principal()
                self._json({
                    "principal": {"actor_id": principal.actor_id, "display_name": principal.display_name, "scopes": sorted(principal.scopes)},
                    "mode": "live",
                    "live": application.service.live_state.as_dict(),
                    "variables": application.variables,
                    "environment": "development",
                    "identity_adapter": "local-development",
                })
            elif path.startswith("/api/simulation-sessions/"):
                try:
                    session = application.service.get_session(self._principal(), path.rsplit("/", 1)[-1])
                    self._json(self._session_payload(session))
                except Exception as exc:
                    self._error(exc)
            elif path.startswith("/assets/"):
                self._file(ASSET_ROOT / path.removeprefix("/assets/"))
            elif path.startswith("/web-assets/"):
                self._file(WEB_ROOT / path.removeprefix("/web-assets/"))
            elif path == "/dom-console-v2.html":
                self._file(WEB_ROOT / "dom-console-v2.html")
            elif path in {"/", "/index.html", "/*", "/**"}:
                self._file(WEB_ROOT / "index.html")
            else:
                self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self):
            path = urlparse(self.path).path
            try:
                body = self._body()
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
                    state = application.service.run_scenario(principal, session_id, body.get("controls", {}))
                    self._json({"state": state.as_dict(), "live_unchanged": True})
                elif path.endswith("/invite") and path.startswith("/api/simulation-sessions/"):
                    session_id = path.split("/")[3]
                    invite = application.service.invite(principal, session_id, str(body.get("actor_id", "")), str(body.get("role", "")))
                    self._json(invite, HTTPStatus.CREATED)
                else:
                    self.send_error(HTTPStatus.NOT_FOUND)
            except Exception as exc:
                self._error(exc)

        def _principal(self) -> Principal:
            return PRINCIPALS.get(self.headers.get("X-EFR-Principal", "analyst"), PRINCIPALS["viewer"])

        def _body(self) -> dict:
            length = int(self.headers.get("Content-Length", "0"))
            return json.loads(self.rfile.read(length) or b"{}")

        @staticmethod
        def _session_payload(session):
            return {
                "session_id": session.session_id,
                "owner_id": session.owner_id,
                "created_at": session.created_at,
                "baseline_hash": session.baseline_hash,
                "state": session.state.as_dict(),
                "collaborators": session.collaborators,
                "audit": session.audit,
            }

        def _json(self, payload: dict, status=HTTPStatus.OK):
            data = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'")
            self.end_headers()
            self.wfile.write(data)

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
            content_type = {".html": "text/html; charset=utf-8", ".png": "image/png", ".svg": "image/svg+xml"}.get(resolved.suffix.lower(), "application/octet-stream")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _error(self, exc: Exception):
            if isinstance(exc, ConsoleAuthorizationError):
                status = HTTPStatus.FORBIDDEN
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
