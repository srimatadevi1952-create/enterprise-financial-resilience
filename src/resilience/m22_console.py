"""M22 mode-aware console application services.

This module is deliberately independent of the live-action path.  It supplies a
small, testable application boundary for the dashboard: immutable live state,
authorised per-user simulations, and explicitly scoped collaboration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Iterable
from uuid import uuid4


CONTROL_NAMES = (
    "Capital",
    "Liquidity",
    "Operations",
    "Regulation",
    "Merchants",
    "Countries & Corridors",
)


class ConsoleAuthorizationError(PermissionError):
    """Raised when a principal requests a console action outside its scope."""


@dataclass(frozen=True)
class Principal:
    actor_id: str
    display_name: str
    scopes: frozenset[str]


@dataclass(frozen=True)
class EnterpriseState:
    as_of: str
    probability: float
    impact: float
    resilience: int
    capital_trajectory: tuple[int, ...]
    payment_disruption: str
    controls: tuple[tuple[str, int], ...]

    def as_dict(self) -> dict:
        return {
            "as_of": self.as_of,
            "probability": self.probability,
            "impact": self.impact,
            "resilience": self.resilience,
            "capital_trajectory": list(self.capital_trajectory),
            "payment_disruption": self.payment_disruption,
            "controls": dict(self.controls),
        }


@dataclass
class SimulationSession:
    session_id: str
    owner_id: str
    created_at: str
    baseline_hash: str
    state: EnterpriseState
    collaborators: dict[str, str] = field(default_factory=dict)
    audit: list[dict] = field(default_factory=list)


def stable_live_state() -> EnterpriseState:
    return EnterpriseState(
        as_of=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        probability=0.0,
        impact=0.0,
        resilience=87,
        capital_trajectory=(100, 99, 98, 97, 96, 96, 97, 98, 99),
        payment_disruption="stable",
        controls=tuple((name, value) for name, value in zip(CONTROL_NAMES, (76, 72, 82, 28, 31, 24))),
    )


class ConsoleService:
    """In-memory M22 session boundary for the local application.

    Persistence and an external identity provider are deployment adapters.  The
    service itself enforces the important product invariant: simulations never
    mutate the live view or another user's session.
    """

    def __init__(self, live_state: EnterpriseState | None = None):
        self._live = live_state or stable_live_state()
        self._sessions: dict[str, SimulationSession] = {}

    @property
    def live_state(self) -> EnterpriseState:
        return self._live

    def create_simulation(self, principal: Principal, *, step_up_verified: bool, purpose: str) -> SimulationSession:
        self._require(principal, "simulation:create")
        if not step_up_verified:
            raise ConsoleAuthorizationError("STEP_UP_REQUIRED")
        if not purpose.strip():
            raise ValueError("PURPOSE_REQUIRED")
        snapshot = repr(self._live.as_dict()).encode("utf-8")
        session = SimulationSession(
            session_id=str(uuid4()),
            owner_id=principal.actor_id,
            created_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            baseline_hash=sha256(snapshot).hexdigest(),
            state=self._live,
        )
        session.audit.append(self._event(principal, "SIMULATION_CREATED", purpose=purpose.strip()))
        self._sessions[session.session_id] = session
        return session

    def get_session(self, principal: Principal, session_id: str) -> SimulationSession:
        session = self._sessions.get(session_id)
        if not session:
            raise KeyError("SESSION_NOT_FOUND")
        if principal.actor_id != session.owner_id and principal.actor_id not in session.collaborators:
            raise ConsoleAuthorizationError("SESSION_ACCESS_DENIED")
        return session

    def run_scenario(self, principal: Principal, session_id: str, values: dict[str, int]) -> EnterpriseState:
        session = self.get_session(principal, session_id)
        role = "owner" if principal.actor_id == session.owner_id else session.collaborators[principal.actor_id]
        if role not in {"owner", "co-analyst"}:
            raise ConsoleAuthorizationError("SIMULATION_EDIT_DENIED")
        normalised = self._normalise_controls(values)
        session.state = self._calculate(normalised)
        session.audit.append(self._event(principal, "SCENARIO_RUN", controls=normalised))
        return session.state

    def invite(self, principal: Principal, session_id: str, actor_id: str, role: str) -> dict:
        session = self.get_session(principal, session_id)
        if principal.actor_id != session.owner_id:
            raise ConsoleAuthorizationError("OWNER_REQUIRED")
        self._require(principal, "simulation:share")
        if role not in {"viewer", "co-analyst", "approver", "auditor"}:
            raise ValueError("ROLE_INVALID")
        if not actor_id.strip():
            raise ValueError("COLLABORATOR_REQUIRED")
        session.collaborators[actor_id.strip()] = role
        session.audit.append(self._event(principal, "COLLABORATOR_INVITED", actor_id=actor_id.strip(), role=role))
        return {"actor_id": actor_id.strip(), "role": role}

    @staticmethod
    def _require(principal: Principal, scope: str) -> None:
        if scope not in principal.scopes:
            raise ConsoleAuthorizationError("SCOPE_REQUIRED")

    @staticmethod
    def _normalise_controls(values: dict[str, int]) -> dict[str, int]:
        if set(values) != set(CONTROL_NAMES):
            raise ValueError("ALL_CONTROLS_REQUIRED")
        result = {name: int(values[name]) for name in CONTROL_NAMES}
        if any(value < 0 or value > 100 for value in result.values()):
            raise ValueError("CONTROL_OUT_OF_RANGE")
        return result

    @staticmethod
    def _calculate(values: dict[str, int]) -> EnterpriseState:
        capital, liquidity, operations, regulation, merchants, corridors = (values[name] for name in CONTROL_NAMES)
        probability = round(min(10.0, (100 - operations) * .035 + regulation * .025 + merchants * .022 + corridors * .018), 1)
        impact = round(min(10.0, (100 - capital) * .04 + (100 - liquidity) * .04 + (100 - operations) * .018 + corridors * .015), 1)
        resilience = max(0, min(100, round(100 - probability * 4.2 - impact * 4.8)))
        severity = probability * impact
        disruption = "stable" if severity < 3 else "watch" if severity < 18 else "high" if severity < 45 else "critical"
        low = max(5, round(100 - impact * 7.2))
        trajectory = tuple(round(100 + (low - 100) * (i / 4)) if i <= 4 else round(low + (resilience - low) * ((i - 4) / 4)) for i in range(9))
        return EnterpriseState(
            as_of=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            probability=probability,
            impact=impact,
            resilience=resilience,
            capital_trajectory=trajectory,
            payment_disruption=disruption,
            controls=tuple(values.items()),
        )

    @staticmethod
    def _event(principal: Principal, event: str, **detail) -> dict:
        return {
            "at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "actor_id": principal.actor_id,
            "event": event,
            "detail": detail,
        }


def group_variable_register(rows: Iterable[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped = {name: [] for name in CONTROL_NAMES}
    for row in rows:
        if row.get("control") in grouped:
            grouped[row["control"]].append(row)
    return grouped
