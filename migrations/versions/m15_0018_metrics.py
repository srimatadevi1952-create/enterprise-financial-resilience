"""M15 institutional resilience metric framework."""
from alembic import op
import sqlalchemy as sa
revision='m15_0018'; down_revision='m14_0017'
def upgrade(profile, **kwargs):
 u=sa.UUID()
 op.create_table('metric_definitions',sa.Column('tenant_id',u,nullable=False),sa.Column('definition_id',u,nullable=False),sa.Column('metric_key',sa.Text,nullable=False),sa.Column('formula',sa.Text,nullable=False),sa.Column('unit',sa.Text,nullable=False),sa.Column('thresholds',sa.JSON,nullable=False),sa.Column('version',sa.Text,nullable=False),sa.PrimaryKeyConstraint('tenant_id','definition_id'),sa.UniqueConstraint('tenant_id','metric_key','version'),schema='resilience_v2')
 op.create_table('institutional_metrics',sa.Column('tenant_id',u,nullable=False),sa.Column('run_id',u,nullable=False),sa.Column('metric_id',u,nullable=False),sa.Column('metric_key',sa.Text,nullable=False),sa.Column('metric_value',sa.Numeric(20,6),nullable=False),sa.Column('interpretation',sa.Text,nullable=False),sa.Column('definition_id',u,nullable=False),sa.Column('evidence_refs',sa.JSON,nullable=False),sa.Column('observed_at',sa.DateTime(timezone=True),nullable=False),sa.PrimaryKeyConstraint('tenant_id','metric_id'),sa.ForeignKeyConstraint(['tenant_id','run_id'],['resilience_v2.runs.tenant_id','resilience_v2.runs.run_id']),sa.ForeignKeyConstraint(['tenant_id','definition_id'],['resilience_v2.metric_definitions.tenant_id','resilience_v2.metric_definitions.definition_id']),sa.UniqueConstraint('tenant_id','run_id','metric_key'),schema='resilience_v2')
 op.execute(sa.text(f"GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA resilience_v2 TO {profile.runtime_user}"));op.execute(sa.text(f"REVOKE INSERT, UPDATE, DELETE ON resilience_v2.tenants, resilience_v2.actors, resilience_v2.environment_identity, resilience_v2.alembic_version FROM {profile.runtime_user}"))
def downgrade(**kwargs): raise RuntimeError('M15 downgrade disabled; rebuild disposable V2 database explicitly')
