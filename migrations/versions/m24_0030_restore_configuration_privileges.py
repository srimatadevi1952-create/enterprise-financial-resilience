"""M24 restore M23 immutable configuration privileges after workbench migration."""

from alembic import op
import sqlalchemy as sa


revision = "m24_0030"
down_revision = "m24_0029"


def upgrade(profile, **kwargs):
    immutable_configuration_tables = (
        "enterprise_entities",
        "enterprise_processes",
        "enterprise_risks",
        "enterprise_controls",
        "process_risk_mappings",
        "risk_control_mappings",
        "process_dependencies",
    )
    for table in immutable_configuration_tables:
        op.execute(sa.text(f"REVOKE UPDATE, DELETE ON resilience_v2.{table} FROM {profile.runtime_user}"))


def downgrade(**kwargs):
    raise RuntimeError("M24 privilege downgrade disabled; rebuild disposable V2 database explicitly")
