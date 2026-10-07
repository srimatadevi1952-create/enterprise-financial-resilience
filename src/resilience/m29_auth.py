"""Invitation-only passwordless authentication for the M29 UAT console.

The in-memory repository is deliberately limited to the local development profile.
Hosted UAT must replace it with the durable repository before deployment.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
import os
import secrets
from typing import Callable

from .m22_console import Principal


class AuthenticationError(RuntimeError):
    pass


ROLE_SCOPES = {
    "viewer": frozenset({"live:view"}),
    "simulation_analyst": frozenset({
        "live:view", "simulation:create", "simulation:share", "assurance:enterprise:view"
    }),
    "consultant": frozenset({
        "live:view", "simulation:create", "simulation:share",
        "assurance:enterprise:view", "assurance:consultant:view",
    }),
    "client_approver": frozenset({
        "live:view", "assurance:client:view", "assurance:client:decide"
    }),
}


@dataclass(frozen=True)
class AuthUser:
    actor_id: str
    display_name: str
    email: str
    role: str
    access_expires_at: datetime
    active: bool = True

    def principal(self) -> Principal:
        return Principal(self.actor_id, self.display_name, ROLE_SCOPES[self.role])


@dataclass
class LoginChallenge:
    email: str
    code_digest: str
    expires_at: datetime
    attempts_remaining: int = 5
    consumed: bool = False


@dataclass
class WebSession:
    token_digest: str
    email: str
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    revoked: bool = False


class InMemoryAuthRepository:
    """Development-only repository with explicit invitations and revocation."""

    def __init__(self, users: list[AuthUser] | None = None):
        self.users = {user.email.casefold(): user for user in (users or [])}
        self.challenges: dict[str, LoginChallenge] = {}
        self.sessions: dict[str, WebSession] = {}
        self.audit: list[dict] = []


class AuthService:
    challenge_ttl = timedelta(minutes=10)
    idle_ttl = timedelta(minutes=30)
    session_ttl = timedelta(hours=8)

    def __init__(
        self,
        repository: InMemoryAuthRepository,
        *,
        secret: bytes,
        environment: str = "development",
        now: Callable[[], datetime] | None = None,
    ):
        if len(secret) < 32:
            raise ValueError("AUTH_SECRET_TOO_SHORT")
        if environment != "development" and isinstance(repository, InMemoryAuthRepository):
            raise AuthenticationError("DURABLE_AUTH_REPOSITORY_REQUIRED")
        self.repository = repository
        self.secret = secret
        self.environment = environment
        self._now = now or (lambda: datetime.now(timezone.utc))

    @classmethod
    def development(cls) -> "AuthService":
        now = datetime.now(timezone.utc)
        users = [
            AuthUser("analyst-1", "Asha Iyer", "asha.iyer@example.test", "simulation_analyst", now + timedelta(days=30)),
            AuthUser("viewer-1", "Dev Rao", "dev.rao@example.test", "viewer", now + timedelta(days=30)),
            AuthUser("consultant-1", "Maya Sen", "maya.sen@example.test", "consultant", now + timedelta(days=30)),
            AuthUser("client-1", "Arun Mehta", "arun.mehta@example.test", "client_approver", now + timedelta(days=30)),
        ]
        configured = os.environ.get("EFR_AUTH_SECRET", "")
        secret = configured.encode() if configured else secrets.token_bytes(32)
        return cls(InMemoryAuthRepository(users), secret=secret)

    @classmethod
    def from_environment(cls) -> "AuthService":
        environment = os.environ.get("EFR_APP_ENV", "development").strip().casefold()
        if environment == "development":
            return cls.development()
        # Hosted UAT must explicitly provide the durable repository in the next
        # deployment increment. Never fall back to demonstration identities.
        raise AuthenticationError("DURABLE_AUTH_REPOSITORY_REQUIRED")

    def request_code(self, email: str, *, remote_address: str = "") -> dict:
        normalized = email.strip().casefold()
        user = self.repository.users.get(normalized)
        now = self._now()
        # Return the same public result for unknown, inactive and expired identities.
        result = {"accepted": True, "message": "If this address is invited, a sign-in code has been issued."}
        if not user or not user.active or user.access_expires_at <= now:
            self._audit("LOGIN_CODE_NOT_ISSUED", normalized, remote_address)
            return result
        code = f"{secrets.randbelow(1_000_000):06d}"
        self.repository.challenges[normalized] = LoginChallenge(
            normalized, self._digest(f"code:{normalized}:{code}"), now + self.challenge_ttl
        )
        self._audit("LOGIN_CODE_ISSUED", normalized, remote_address)
        if self.environment == "development":
            result["development_code"] = code
        return result

    def verify_code(self, email: str, code: str, *, remote_address: str = "") -> tuple[str, AuthUser]:
        normalized = email.strip().casefold()
        challenge = self.repository.challenges.get(normalized)
        user = self.repository.users.get(normalized)
        now = self._now()
        if (
            not challenge or not user or challenge.consumed or challenge.expires_at <= now
            or challenge.attempts_remaining <= 0 or not user.active or user.access_expires_at <= now
        ):
            self._audit("LOGIN_REJECTED", normalized, remote_address)
            raise AuthenticationError("INVALID_OR_EXPIRED_CODE")
        expected = self._digest(f"code:{normalized}:{code.strip()}")
        if not hmac.compare_digest(challenge.code_digest, expected):
            challenge.attempts_remaining -= 1
            self._audit("LOGIN_CODE_FAILED", normalized, remote_address)
            raise AuthenticationError("INVALID_OR_EXPIRED_CODE")
        challenge.consumed = True
        token = secrets.token_urlsafe(32)
        digest = self._digest(f"session:{token}")
        self.repository.sessions[digest] = WebSession(digest, normalized, now, now, now + self.session_ttl)
        self._audit("LOGIN_SUCCEEDED", normalized, remote_address)
        return token, user

    def authenticate(self, token: str | None) -> AuthUser:
        if not token:
            raise AuthenticationError("AUTHENTICATION_REQUIRED")
        digest = self._digest(f"session:{token}")
        session = self.repository.sessions.get(digest)
        now = self._now()
        if (
            not session or session.revoked or session.expires_at <= now
            or session.last_seen_at + self.idle_ttl <= now
        ):
            raise AuthenticationError("SESSION_EXPIRED")
        user = self.repository.users.get(session.email)
        if not user or not user.active or user.access_expires_at <= now:
            raise AuthenticationError("ACCESS_REVOKED")
        session.last_seen_at = now
        return user

    def logout(self, token: str | None, *, remote_address: str = "") -> None:
        if not token:
            return
        session = self.repository.sessions.get(self._digest(f"session:{token}"))
        if session:
            session.revoked = True
            self._audit("LOGOUT", session.email, remote_address)

    def _digest(self, value: str) -> str:
        return hmac.new(self.secret, value.encode(), sha256).hexdigest()

    def _audit(self, event: str, email: str, remote_address: str) -> None:
        self.repository.audit.append({
            "event": event,
            "email_digest": self._digest(f"email:{email}"),
            "remote_address": remote_address,
            "recorded_at": self._now().isoformat(),
        })
