"""Restrict runtime role from tenant and actor administration."""
from alembic import op
import sqlalchemy as sa

revision = "m1_0003"
down_revision = "m1_0002"


def upgrade(profile, **kwargs):
    op.execute(sa.text(f"REVOKE INSERT, UPDATE, DELETE ON resilience_v2.tenants, resilience_v2.actors, resilience_v2.environment_identity, resilience_v2.alembic_version FROM {profile.runtime_user}"))


def downgrade(profile, **kwargs):
    raise RuntimeError("M1 privilege downgrade disabled")
