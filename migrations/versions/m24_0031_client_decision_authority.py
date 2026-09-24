"""M24 time-bound client decision authority."""

from alembic import op
import sqlalchemy as sa


revision = "m24_0031"
down_revision = "m24_0030"


def upgrade(profile, **kwargs):
    uuid = sa.UUID()
    op.create_table(
        "client_decision_authorities",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("authority_id", uuid, nullable=False),
        sa.Column("actor_id", uuid, nullable=False),
        sa.Column("granted_by", uuid, nullable=False),
        sa.Column("authority_scope", sa.JSON, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence_ref", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "authority_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "actor_id"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "granted_by"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("actor_id <> granted_by"),
        sa.CheckConstraint("status IN ('ACTIVE','REVOKED','EXPIRED')"),
        sa.CheckConstraint("expires_at > effective_from"),
        schema="resilience_v2",
    )
    op.create_index(
        "ix_client_decision_authorities_actor",
        "client_decision_authorities",
        ["tenant_id", "actor_id", "status"],
        schema="resilience_v2",
    )


def downgrade(**kwargs):
    raise RuntimeError("M24 authority downgrade disabled; rebuild disposable V2 database explicitly")
