from resilience.m22_console import (
    CONTROL_NAMES,
    ConsoleAuthorizationError,
    ConsoleService,
    Principal,
)
from resilience.config import ROOT


ANALYST = Principal("analyst-1", "Asha Iyer", frozenset({"live:view", "simulation:create", "simulation:share"}))
VIEWER = Principal("viewer-1", "Dev Rao", frozenset({"live:view"}))


def test_private_simulation_never_mutates_live_state():
    service = ConsoleService()
    before = service.live_state
    session = service.create_simulation(ANALYST, step_up_verified=True, purpose="Corridor stress review")
    state = service.run_scenario(ANALYST, session.session_id, dict(zip(CONTROL_NAMES, (52, 43, 48, 76, 61, 82))))
    assert state.resilience < before.resilience
    assert service.live_state == before
    assert state.payment_disruption in {"high", "critical"}


def test_mode_switch_requires_entitlement_and_step_up():
    service = ConsoleService()
    for principal, verified in ((VIEWER, True), (ANALYST, False)):
        try:
            service.create_simulation(principal, step_up_verified=verified, purpose="Test")
        except ConsoleAuthorizationError:
            pass
        else:
            raise AssertionError("unauthorised simulation was created")


def test_sharing_is_scoped_and_does_not_expose_other_sessions():
    service = ConsoleService()
    session = service.create_simulation(ANALYST, step_up_verified=True, purpose="Joint review")
    service.invite(ANALYST, session.session_id, VIEWER.actor_id, "viewer")
    assert service.get_session(VIEWER, session.session_id).collaborators[VIEWER.actor_id] == "viewer"
    try:
        service.run_scenario(VIEWER, session.session_id, dict(zip(CONTROL_NAMES, (50, 50, 50, 50, 50, 50))))
    except ConsoleAuthorizationError as exc:
        assert str(exc) == "SIMULATION_EDIT_DENIED"
    else:
        raise AssertionError("viewer edited a simulation")


def test_canvas_console_packages_the_approved_master_and_preserves_dom_version():
    web = ROOT / "src" / "resilience" / "web"
    index = (web / "index.html").read_text(encoding="utf-8")
    assert "m22-console-canvas-master-v2.png" in index
    assert "const DESIGN={w:1881,h:1073}" in index
    assert (web / "m22-console-canvas-master-v2.png").stat().st_size > 100_000
    assert (web / "dom-console-v2.html").exists()


def test_console_route_accepts_accidental_markdown_wildcard_suffix():
    source = (ROOT / "src" / "resilience" / "m22_web.py").read_text(encoding="utf-8")
    assert '"/**"' in source
    assert "unquote(urlparse(self.path).path)" in source
