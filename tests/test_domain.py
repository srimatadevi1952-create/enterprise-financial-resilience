from datetime import datetime, timezone
from uuid import uuid4
import pytest
from pydantic import ValidationError
from resilience.domain import BusinessClock, Money, RunSpec, SettlementObligationSpec


def test_money_and_obligation_are_exact_and_immutable():
    tenant, run, txn = uuid4(), uuid4(), uuid4()
    obligation = SettlementObligationSpec(
        tenant_id=tenant, run_id=run, obligation_id=uuid4(), business_key="M01-001",
        transaction_id=txn, merchant_key="M01", gross=Money(minor=10000, currency="INR"),
        fee_minor=0, tax_minor=0, due_at=datetime(2026, 9, 20, tzinfo=timezone.utc))
    assert obligation.net_minor() == 10000
    with pytest.raises(ValidationError): obligation.merchant_key = "changed"


def test_rejects_naive_clock_and_negative_money():
    with pytest.raises(ValidationError): BusinessClock(current=datetime(2026, 9, 20))
    with pytest.raises(ValidationError): Money(minor=-1, currency="INR")


def test_rejects_negative_net_obligation():
    with pytest.raises(ValueError, match="OBLIGATION_NET_NEGATIVE"):
        SettlementObligationSpec(
            tenant_id=uuid4(), run_id=uuid4(), obligation_id=uuid4(), business_key="x",
            transaction_id=uuid4(), merchant_key="M", gross=Money(minor=100, currency="INR"),
            fee_minor=60, tax_minor=50, due_at=datetime(2026, 9, 20, tzinfo=timezone.utc)).net_minor()


def test_run_spec_requires_utc_and_nonnegative_seed():
    base = dict(tenant_id=uuid4(), experiment_id=uuid4(), branch_role="BASELINE", seed=0,
                code_hash="code", model_hash="model", input_hash="input",
                virtual_time=datetime(2026, 9, 20, tzinfo=timezone.utc))
    assert RunSpec(**base).seed == 0
    with pytest.raises(ValidationError): RunSpec(**{**base, "seed": -1})
