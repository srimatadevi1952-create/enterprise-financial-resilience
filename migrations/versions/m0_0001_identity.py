"""M0 environment marker only; no simulation business tables."""
from alembic import op
import sqlalchemy as sa

revision = "m0_0001"
down_revision = None


def upgrade(profile, **kwargs):
    op.create_table("environment_identity",
        sa.Column("singleton", sa.Boolean(), primary_key=True),
        sa.Column("environment", sa.Text(), nullable=False),
        sa.Column("instance_id", sa.UUID(), nullable=False, unique=True),
        sa.CheckConstraint("singleton=true"),
        sa.CheckConstraint("environment IN ('development','test')"), schema="resilience_v2")
    op.get_bind().execute(sa.text("INSERT INTO resilience_v2.environment_identity VALUES (true,:env,:instance)"),
                         {"env": profile.environment, "instance": profile.instance_id})


def downgrade(**kwargs):
    raise RuntimeError("M0 identity downgrade disabled; use an explicitly disposable rebuild")
