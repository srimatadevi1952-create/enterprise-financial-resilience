"""Durable hosted-UAT adapters for Neon Postgres and Resend email."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

from .m22_console import CollaborationInvitation, EnterpriseState, SimulationSession
from .m29_auth import AuthenticationError, AuthUser, LoginChallenge, WebSession


def _connection(database_url: str):
    return psycopg.connect(database_url, connect_timeout=8, row_factory=dict_row)


class ResendCodeSender:
    def __init__(self, api_key: str, from_email: str):
        self.api_key = api_key
        self.from_email = from_email

    def send(self, user: AuthUser, code: str, expires_at: datetime) -> None:
        payload = json.dumps({
            "from": self.from_email,
            "to": [user.email],
            "subject": "Your Enterprise Financial Resilience sign-in code",
            "text": (
                f"Hello {user.display_name},\n\n"
                f"Your one-time sign-in code is {code}. It expires at {expires_at.isoformat()}.\n\n"
                "If you did not request this code, do not share it and contact the UAT administrator."
            ),
        }).encode()
        request = Request(
            "https://api.resend.com/emails", data=payload, method="POST",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=10) as response:
                if response.status not in {200, 201, 202}:
                    raise AuthenticationError("EMAIL_DELIVERY_FAILED")
        except (HTTPError, URLError, TimeoutError):
            raise AuthenticationError("EMAIL_DELIVERY_FAILED") from None


class PostgresAuthRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def get_user(self, email: str) -> AuthUser | None:
        with _connection(self.database_url) as conn:
            row = conn.execute(
                "SELECT actor_id,display_name,email,role,access_expires_at,active "
                "FROM efr_uat.auth_users WHERE email=%s", (email,),
            ).fetchone()
        return AuthUser(**row) if row else None

    def list_active_users(self, now: datetime) -> list[AuthUser]:
        with _connection(self.database_url) as conn:
            rows = conn.execute(
                "SELECT actor_id,display_name,email,role,access_expires_at,active FROM efr_uat.auth_users "
                "WHERE active=true AND access_expires_at>%s ORDER BY display_name", (now,),
            ).fetchall()
        return [AuthUser(**row) for row in rows]

    def save_challenge(self, challenge: LoginChallenge) -> None:
        with _connection(self.database_url) as conn:
            conn.execute(
                "INSERT INTO efr_uat.login_challenges(email,code_digest,expires_at,attempts_remaining,consumed,updated_at) "
                "VALUES (%s,%s,%s,%s,%s,now()) ON CONFLICT(email) DO UPDATE SET "
                "code_digest=excluded.code_digest,expires_at=excluded.expires_at,attempts_remaining=excluded.attempts_remaining,"
                "consumed=excluded.consumed,updated_at=now()",
                (challenge.email, challenge.code_digest, challenge.expires_at, challenge.attempts_remaining, challenge.consumed),
            )

    def get_challenge(self, email: str) -> LoginChallenge | None:
        with _connection(self.database_url) as conn:
            row = conn.execute(
                "SELECT email,code_digest,expires_at,attempts_remaining,consumed "
                "FROM efr_uat.login_challenges WHERE email=%s", (email,),
            ).fetchone()
        return LoginChallenge(**row) if row else None

    def save_session(self, session: WebSession) -> None:
        with _connection(self.database_url) as conn:
            conn.execute(
                "INSERT INTO efr_uat.web_sessions(token_digest,email,created_at,last_seen_at,expires_at,revoked) "
                "VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(token_digest) DO UPDATE SET "
                "last_seen_at=excluded.last_seen_at,expires_at=excluded.expires_at,revoked=excluded.revoked",
                (session.token_digest, session.email, session.created_at, session.last_seen_at, session.expires_at, session.revoked),
            )

    def get_session(self, token_digest: str) -> WebSession | None:
        with _connection(self.database_url) as conn:
            row = conn.execute(
                "SELECT token_digest,email,created_at,last_seen_at,expires_at,revoked "
                "FROM efr_uat.web_sessions WHERE token_digest=%s", (token_digest,),
            ).fetchone()
        return WebSession(**row) if row else None

    def save_audit(self, event: dict) -> None:
        with _connection(self.database_url) as conn:
            conn.execute(
                "INSERT INTO efr_uat.auth_audit_events(event_id,event,email_digest,remote_address,recorded_at) "
                "VALUES (%s,%s,%s,%s,%s)",
                (str(uuid4()), event["event"], event["email_digest"], event["remote_address"], event["recorded_at"]),
            )

    def health(self) -> bool:
        with _connection(self.database_url) as conn:
            row = conn.execute("SELECT to_regclass('efr_uat.auth_users') IS NOT NULL AS ready").fetchone()
            return bool(row["ready"])


class PostgresConsoleRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    @staticmethod
    def _state(payload: dict) -> EnterpriseState:
        return EnterpriseState(
            as_of=payload["as_of"], probability=float(payload["probability"]), impact=float(payload["impact"]),
            resilience=int(payload["resilience"]), capital_trajectory=tuple(payload["capital_trajectory"]),
            payment_disruption=payload["payment_disruption"], controls=tuple(payload["controls"].items()),
        )

    def save_session(self, session: SimulationSession) -> None:
        with _connection(self.database_url) as conn:
            conn.execute(
                "INSERT INTO efr_uat.simulation_sessions(session_id,owner_id,created_at,baseline_hash,state,collaborators,audit,updated_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,now()) ON CONFLICT(session_id) DO UPDATE SET "
                "state=excluded.state,collaborators=excluded.collaborators,audit=excluded.audit,updated_at=now()",
                (session.session_id, session.owner_id, session.created_at, session.baseline_hash,
                 json.dumps(session.state.as_dict()), json.dumps(session.collaborators), json.dumps(session.audit)),
            )

    def get_session(self, session_id: str) -> SimulationSession | None:
        with _connection(self.database_url) as conn:
            row = conn.execute(
                "SELECT session_id,owner_id,created_at,baseline_hash,state,collaborators,audit "
                "FROM efr_uat.simulation_sessions WHERE session_id=%s", (session_id,),
            ).fetchone()
        if not row:
            return None
        return SimulationSession(
            session_id=row["session_id"], owner_id=row["owner_id"], created_at=row["created_at"].isoformat(),
            baseline_hash=row["baseline_hash"], state=self._state(row["state"]),
            collaborators=row["collaborators"], audit=row["audit"],
        )

    @staticmethod
    def _token_digest(token: str) -> str:
        return sha256(token.encode()).hexdigest()

    def save_invitation(self, invitation: CollaborationInvitation) -> None:
        digest = self._token_digest(invitation.token) if not invitation.token.startswith("redacted:") else invitation.token.removeprefix("redacted:")
        with _connection(self.database_url) as conn:
            conn.execute(
                "INSERT INTO efr_uat.collaboration_invitations(token_digest,session_id,actor_id,role,created_by,created_at,expires_at,status) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(token_digest) DO UPDATE SET status=excluded.status",
                (digest, invitation.session_id, invitation.actor_id, invitation.role, invitation.created_by,
                 invitation.created_at, invitation.expires_at, invitation.status),
            )

    def get_invitation(self, token: str) -> CollaborationInvitation | None:
        digest = self._token_digest(token)
        with _connection(self.database_url) as conn:
            row = conn.execute(
                "SELECT session_id,actor_id,role,created_by,created_at,expires_at,status "
                "FROM efr_uat.collaboration_invitations WHERE token_digest=%s", (digest,),
            ).fetchone()
        if not row:
            return None
        return CollaborationInvitation(token=token, **{**row, "created_at": row["created_at"].isoformat(), "expires_at": row["expires_at"].isoformat()})

    def list_invitations(self, session_id: str) -> list[CollaborationInvitation]:
        with _connection(self.database_url) as conn:
            rows = conn.execute(
                "SELECT token_digest,session_id,actor_id,role,created_by,created_at,expires_at,status "
                "FROM efr_uat.collaboration_invitations WHERE session_id=%s ORDER BY created_at", (session_id,),
            ).fetchall()
        return [CollaborationInvitation(
            token=f"redacted:{row['token_digest']}", session_id=row["session_id"], actor_id=row["actor_id"],
            role=row["role"], created_by=row["created_by"], created_at=row["created_at"].isoformat(),
            expires_at=row["expires_at"].isoformat(), status=row["status"],
        ) for row in rows]


class PostgresAssuranceRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def current_decision(self) -> str:
        with _connection(self.database_url) as conn:
            row = conn.execute(
                "SELECT decision FROM efr_uat.assurance_state WHERE state_key='M27-UAT-CLIENT-DECISION'"
            ).fetchone()
        return row["decision"] if row else "AWAITING_DECISION"

    def record_event(self, event_type: str, event: dict) -> None:
        with _connection(self.database_url) as conn:
            conn.execute(
                "INSERT INTO efr_uat.assurance_events(event_id,event_type,actor_id,payload,recorded_at) "
                "VALUES (%s,%s,%s,%s,%s)",
                (str(uuid4()), event_type, event["actor_id"], json.dumps(event), event["at"]),
            )
            if event_type == "DECISION":
                conn.execute(
                    "INSERT INTO efr_uat.assurance_state(state_key,decision,updated_at) VALUES ('M27-UAT-CLIENT-DECISION',%s,now()) "
                    "ON CONFLICT(state_key) DO UPDATE SET decision=excluded.decision,updated_at=now()",
                    (event["decision"],),
                )
