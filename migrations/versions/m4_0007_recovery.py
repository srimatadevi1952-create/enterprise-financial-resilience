"""M4 intervention execution and recovery measures."""
from alembic import op
import sqlalchemy as sa

revision = "m4_0007"
down_revision = "m3_0006"

def upgrade(profile, **kwargs):
    uuid = sa.UUID()
    op.create_table("intervention_executions", sa.Column("tenant_id", uuid, nullable=False), sa.Column("run_id", uuid, nullable=False), sa.Column("intervention_id", uuid, nullable=False), sa.Column("intervention_type", sa.Text, nullable=False), sa.Column("target_digest", sa.Text, nullable=False), sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False), sa.Column("actor_id", uuid, nullable=False), sa.PrimaryKeyConstraint("tenant_id", "intervention_id"), sa.ForeignKeyConstraint(["tenant_id", "run_id"], ["resilience_v2.runs.tenant_id", "resilience_v2.runs.run_id"]), sa.ForeignKeyConstraint(["tenant_id", "actor_id"], ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"]), schema="resilience_v2")
    op.create_table("recovery_measures", sa.Column("tenant_id", uuid, nullable=False), sa.Column("run_id", uuid, nullable=False), sa.Column("measure_id", uuid, nullable=False), sa.Column("measure_key", sa.Text, nullable=False), sa.Column("measure_value", sa.Numeric(20,6), nullable=False), sa.Column("unit", sa.Text, nullable=False), sa.Column("comparison_run_id", uuid, nullable=True), sa.Column("quality_state", sa.Text, nullable=False), sa.Column("evidence_refs", sa.JSON, nullable=False), sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False), sa.PrimaryKeyConstraint("tenant_id", "measure_id"), sa.ForeignKeyConstraint(["tenant_id", "run_id"], ["resilience_v2.runs.tenant_id", "resilience_v2.runs.run_id"]), sa.ForeignKeyConstraint(["tenant_id", "comparison_run_id"], ["resilience_v2.runs.tenant_id", "resilience_v2.runs.run_id"]), sa.UniqueConstraint("tenant_id", "run_id", "measure_key"), sa.CheckConstraint("quality_state IN ('TRUSTED','DEGRADED','UNRESOLVED')"), schema="resilience_v2")
    op.execute(sa.text(f"GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA resilience_v2 TO {profile.runtime_user}"))
    op.execute(sa.text(f"REVOKE INSERT, UPDATE, DELETE ON resilience_v2.tenants, resilience_v2.actors, resilience_v2.environment_identity, resilience_v2.alembic_version FROM {profile.runtime_user}"))

def downgrade(**kwargs):
    raise RuntimeError("M4 downgrade disabled; rebuild disposable V2 database explicitly")
