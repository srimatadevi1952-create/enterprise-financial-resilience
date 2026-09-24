"""M23 versioned enterprise configuration and process-risk-control model."""

from alembic import op
import sqlalchemy as sa


revision = "m23_0025"
down_revision = "m21_0024"


def upgrade(profile, **kwargs):
    uuid = sa.UUID()
    def tenant_config():
        return [
            sa.Column("tenant_id", uuid, nullable=False),
            sa.Column("config_id", uuid, nullable=False),
        ]

    op.create_table(
        "enterprise_configuration_versions",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("config_id", uuid, nullable=False),
        sa.Column("profile_key", sa.Text, nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("legal_name", sa.Text, nullable=False),
        sa.Column("industry", sa.Text, nullable=False),
        sa.Column("base_currency", sa.Text, nullable=False),
        sa.Column("owner_actor_id", uuid, nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("evidence_refs", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "config_id"),
        sa.UniqueConstraint("tenant_id", "profile_key", "version"),
        sa.ForeignKeyConstraint(["tenant_id"], ["resilience_v2.tenants.tenant_id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "owner_actor_id"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("version > 0"),
        sa.CheckConstraint("base_currency ~ '^[A-Z]{3}$'"),
        sa.CheckConstraint("effective_to IS NULL OR effective_to > effective_from"),
        sa.CheckConstraint("status IN ('DRAFT','VALIDATED','ACTIVE','RETIRED')"),
        schema="resilience_v2",
    )
    op.create_index(
        "uq_enterprise_configuration_active_profile",
        "enterprise_configuration_versions",
        ["tenant_id", "profile_key"],
        unique=True,
        schema="resilience_v2",
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )

    op.create_table(
        "enterprise_entities",
        *tenant_config(),
        sa.Column("entity_id", uuid, nullable=False),
        sa.Column("entity_key", sa.Text, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("entity_type", sa.Text, nullable=False),
        sa.Column("jurisdiction", sa.Text, nullable=False),
        sa.Column("parent_entity_id", uuid, nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "config_id", "entity_id"),
        sa.UniqueConstraint("tenant_id", "config_id", "entity_key"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "config_id"],
            ["resilience_v2.enterprise_configuration_versions.tenant_id", "resilience_v2.enterprise_configuration_versions.config_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "config_id", "parent_entity_id"],
            ["resilience_v2.enterprise_entities.tenant_id", "resilience_v2.enterprise_entities.config_id", "resilience_v2.enterprise_entities.entity_id"],
        ),
        sa.CheckConstraint("entity_type IN ('GROUP','LEGAL_ENTITY','BUSINESS_UNIT','OPERATING_UNIT')"),
        sa.CheckConstraint("jurisdiction ~ '^[A-Z]{2}$'"),
        schema="resilience_v2",
    )

    op.create_table(
        "enterprise_processes",
        *tenant_config(),
        sa.Column("process_id", uuid, nullable=False),
        sa.Column("process_key", sa.Text, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("owner_actor_id", uuid, nullable=False),
        sa.Column("criticality", sa.Text, nullable=False),
        sa.Column("service_target_minutes", sa.Integer, nullable=False),
        sa.Column("parent_process_id", uuid, nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "config_id", "process_id"),
        sa.UniqueConstraint("tenant_id", "config_id", "process_key"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "config_id"],
            ["resilience_v2.enterprise_configuration_versions.tenant_id", "resilience_v2.enterprise_configuration_versions.config_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "owner_actor_id"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "config_id", "parent_process_id"],
            ["resilience_v2.enterprise_processes.tenant_id", "resilience_v2.enterprise_processes.config_id", "resilience_v2.enterprise_processes.process_id"],
        ),
        sa.CheckConstraint("criticality IN ('LOW','MEDIUM','HIGH','CRITICAL')"),
        sa.CheckConstraint("service_target_minutes > 0"),
        schema="resilience_v2",
    )

    op.create_table(
        "enterprise_risks",
        *tenant_config(),
        sa.Column("risk_id", uuid, nullable=False),
        sa.Column("risk_key", sa.Text, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("category", sa.Text, nullable=False),
        sa.Column("owner_actor_id", uuid, nullable=False),
        sa.Column("inherent_likelihood", sa.Integer, nullable=False),
        sa.Column("inherent_impact", sa.Integer, nullable=False),
        sa.Column("tolerance_score", sa.Integer, nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "config_id", "risk_id"),
        sa.UniqueConstraint("tenant_id", "config_id", "risk_key"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "config_id"],
            ["resilience_v2.enterprise_configuration_versions.tenant_id", "resilience_v2.enterprise_configuration_versions.config_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "owner_actor_id"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("inherent_likelihood BETWEEN 1 AND 5"),
        sa.CheckConstraint("inherent_impact BETWEEN 1 AND 5"),
        sa.CheckConstraint("tolerance_score BETWEEN 1 AND 25"),
        schema="resilience_v2",
    )

    op.create_table(
        "enterprise_controls",
        *tenant_config(),
        sa.Column("control_id", uuid, nullable=False),
        sa.Column("control_key", sa.Text, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("control_type", sa.Text, nullable=False),
        sa.Column("owner_actor_id", uuid, nullable=False),
        sa.Column("frequency", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "config_id", "control_id"),
        sa.UniqueConstraint("tenant_id", "config_id", "control_key"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "config_id"],
            ["resilience_v2.enterprise_configuration_versions.tenant_id", "resilience_v2.enterprise_configuration_versions.config_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "owner_actor_id"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("control_type IN ('PREVENTIVE','DETECTIVE','CORRECTIVE','RECOVERY')"),
        sa.CheckConstraint("status IN ('DESIGNED','ACTIVE','SUSPENDED','RETIRED')"),
        schema="resilience_v2",
    )

    op.create_table(
        "process_risk_mappings",
        *tenant_config(),
        sa.Column("mapping_id", uuid, nullable=False),
        sa.Column("process_id", uuid, nullable=False),
        sa.Column("risk_id", uuid, nullable=False),
        sa.Column("exposure_weight_pct", sa.Numeric(5, 2), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "config_id", "mapping_id"),
        sa.UniqueConstraint("tenant_id", "config_id", "process_id", "risk_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "config_id", "process_id"],
            ["resilience_v2.enterprise_processes.tenant_id", "resilience_v2.enterprise_processes.config_id", "resilience_v2.enterprise_processes.process_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "config_id", "risk_id"],
            ["resilience_v2.enterprise_risks.tenant_id", "resilience_v2.enterprise_risks.config_id", "resilience_v2.enterprise_risks.risk_id"],
        ),
        sa.CheckConstraint("exposure_weight_pct > 0 AND exposure_weight_pct <= 100"),
        schema="resilience_v2",
    )

    op.create_table(
        "risk_control_mappings",
        *tenant_config(),
        sa.Column("mapping_id", uuid, nullable=False),
        sa.Column("risk_id", uuid, nullable=False),
        sa.Column("control_id", uuid, nullable=False),
        sa.Column("effectiveness_pct", sa.Numeric(5, 2), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "config_id", "mapping_id"),
        sa.UniqueConstraint("tenant_id", "config_id", "risk_id", "control_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "config_id", "risk_id"],
            ["resilience_v2.enterprise_risks.tenant_id", "resilience_v2.enterprise_risks.config_id", "resilience_v2.enterprise_risks.risk_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "config_id", "control_id"],
            ["resilience_v2.enterprise_controls.tenant_id", "resilience_v2.enterprise_controls.config_id", "resilience_v2.enterprise_controls.control_id"],
        ),
        sa.CheckConstraint("effectiveness_pct >= 0 AND effectiveness_pct <= 100"),
        schema="resilience_v2",
    )

    op.create_table(
        "process_dependencies",
        *tenant_config(),
        sa.Column("dependency_id", uuid, nullable=False),
        sa.Column("upstream_process_id", uuid, nullable=False),
        sa.Column("downstream_process_id", uuid, nullable=False),
        sa.Column("dependency_type", sa.Text, nullable=False),
        sa.Column("criticality", sa.Text, nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "config_id", "dependency_id"),
        sa.UniqueConstraint("tenant_id", "config_id", "upstream_process_id", "downstream_process_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "config_id", "upstream_process_id"],
            ["resilience_v2.enterprise_processes.tenant_id", "resilience_v2.enterprise_processes.config_id", "resilience_v2.enterprise_processes.process_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "config_id", "downstream_process_id"],
            ["resilience_v2.enterprise_processes.tenant_id", "resilience_v2.enterprise_processes.config_id", "resilience_v2.enterprise_processes.process_id"],
        ),
        sa.CheckConstraint("upstream_process_id <> downstream_process_id"),
        sa.CheckConstraint("dependency_type IN ('DATA','FUNDING','SERVICE','CONTROL','REGULATORY')"),
        sa.CheckConstraint("criticality IN ('LOW','MEDIUM','HIGH','CRITICAL')"),
        schema="resilience_v2",
    )

    op.execute(
        sa.text(
            f"GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA resilience_v2 TO {profile.runtime_user}"
        )
    )
    op.execute(
        sa.text(
            f"REVOKE INSERT, UPDATE, DELETE ON resilience_v2.tenants, resilience_v2.actors, "
            f"resilience_v2.environment_identity, resilience_v2.alembic_version FROM {profile.runtime_user}"
        )
    )


def downgrade(**kwargs):
    raise RuntimeError("M23 downgrade disabled; rebuild disposable V2 database explicitly")
