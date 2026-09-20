"""Pure M1 value objects and command contracts.

These objects do not connect to PostgreSQL and do not import V1 code.
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DomainError(ValueError):
    pass


class Money(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    minor: int
    currency: Literal["INR"]

    @field_validator("minor")
    @classmethod
    def finite_int(cls, value: int) -> int:
        if value < 0 or value > 9_223_372_036_854_775_807:
            raise ValueError("MONEY_OUT_OF_RANGE")
        return value


class BusinessClock(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    current: datetime

    @field_validator("current")
    @classmethod
    def utc_only(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
            raise ValueError("CLOCK_MUST_BE_TIMEZONE_AWARE_UTC")
        return value.astimezone(timezone.utc)


class RunSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    tenant_id: UUID
    experiment_id: UUID
    branch_role: Literal["BASELINE", "STRESS", "INTERVENTION", "CONTROL"]
    seed: int = Field(ge=0, le=9_223_372_036_854_775_807)
    code_hash: str = Field(min_length=1, max_length=128)
    model_hash: str = Field(min_length=1, max_length=128)
    input_hash: str = Field(min_length=1, max_length=128)
    virtual_time: datetime

    @field_validator("virtual_time")
    @classmethod
    def utc_time(cls, value: datetime) -> datetime:
        return BusinessClock(current=value).current


class SettlementObligationSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    tenant_id: UUID
    run_id: UUID
    obligation_id: UUID
    business_key: str = Field(min_length=1, max_length=128)
    transaction_id: UUID
    merchant_key: str = Field(min_length=1, max_length=128)
    gross: Money
    fee_minor: int = Field(ge=0)
    tax_minor: int = Field(ge=0)
    due_at: datetime

    @field_validator("due_at")
    @classmethod
    def due_utc(cls, value: datetime) -> datetime:
        return BusinessClock(current=value).current

    def net_minor(self) -> int:
        net = self.gross.minor - self.fee_minor - self.tax_minor
        if net < 0:
            raise DomainError("OBLIGATION_NET_NEGATIVE")
        return net


class CommandEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    tenant_id: UUID
    actor_id: UUID
    command_type: str = Field(min_length=1, max_length=80)
    idempotency_key: str = Field(min_length=1, max_length=160)
    payload_hash: str = Field(min_length=1, max_length=128)
