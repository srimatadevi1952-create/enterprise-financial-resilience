"""M27 immutable dual-model pilot and readiness evidence."""

from alembic import op
import sqlalchemy as sa


revision = "m27_0036"
down_revision = "m26_0035"


def upgrade(profile, **kwargs):
    uuid = sa.UUID()
    op.create_table(
        "operational_assurance_pilots",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("pilot_id", uuid, nullable=False),
        sa.Column("operating_model", sa.Text, nullable=False),
        sa.Column("pilot_name", sa.Text, nullable=False),
        sa.Column("executed_by", uuid, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("live_actions", sa.Integer, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence_digest", sa.Text, nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "pilot_id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["resilience_v2.tenants.tenant_id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "executed_by"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("operating_model IN ('ENTERPRISE','CONSULTANT')"),
        sa.CheckConstraint("status IN ('PASS','FAIL')"),
        sa.CheckConstraint("live_actions = 0"),
        sa.CheckConstraint("completed_at >= started_at"),
        schema="resilience_v2",
    )
    op.create_table(
        "operational_assurance_pilot_steps",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("pilot_id", uuid, nullable=False),
        sa.Column("step_order", sa.Integer, nullable=False),
        sa.Column("step_key", sa.Text, nullable=False),
        sa.Column("outcome", sa.Text, nullable=False),
        sa.Column("evidence_ref", sa.Text, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "pilot_id", "step_order"),
        sa.UniqueConstraint("tenant_id", "pilot_id", "step_key"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "pilot_id"],
            ["resilience_v2.operational_assurance_pilots.tenant_id", "resilience_v2.operational_assurance_pilots.pilot_id"],
        ),
        sa.CheckConstraint("step_order > 0"),
        sa.CheckConstraint("outcome IN ('PASS','FAIL')"),
        schema="resilience_v2",
    )
    op.create_table(
        "operational_assurance_readiness_checks",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("pilot_id", uuid, nullable=False),
        sa.Column("category", sa.Text, nullable=False),
        sa.Column("outcome", sa.Text, nullable=False),
        sa.Column("evidence_ref", sa.Text, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "pilot_id", "category"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "pilot_id"],
            ["resilience_v2.operational_assurance_pilots.tenant_id", "resilience_v2.operational_assurance_pilots.pilot_id"],
        ),
        sa.CheckConstraint("category IN ('USABILITY','ACCESSIBILITY','PERFORMANCE','SECURITY','RETENTION','AUDIT','TENANT_ISOLATION')"),
        sa.CheckConstraint("outcome IN ('PASS','FAIL')"),
        schema="resilience_v2",
    )
    for table in (
        "operational_assurance_pilots",
        "operational_assurance_pilot_steps",
        "operational_assurance_readiness_checks",
    ):
        op.execute(sa.text(
            f"CREATE TRIGGER {table}_append_only BEFORE UPDATE OR DELETE ON resilience_v2.{table} "
            "FOR EACH ROW EXECUTE FUNCTION resilience_v2.guard_m24_append_only()"
        ))
        op.execute(sa.text(f"REVOKE UPDATE, DELETE ON resilience_v2.{table} FROM {profile.runtime_user}"))


def downgrade(**kwargs):
    raise RuntimeError("M27 downgrade disabled; rebuild disposable V2 database explicitly")
