"""Complete runtime protection for environment metadata."""
from alembic import op
import sqlalchemy as sa

revision = "m1_0004"
down_revision = "m1_0003"


def upgrade(profile, **kwargs):
    op.execute(sa.text(f"REVOKE INSERT, UPDATE, DELETE ON resilience_v2.environment_identity, resilience_v2.alembic_version FROM {profile.runtime_user}"))


def downgrade(profile, **kwargs):
    raise RuntimeError("M1 privilege downgrade disabled")
