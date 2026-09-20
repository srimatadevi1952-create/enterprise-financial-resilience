"""M14 scale profiles and benchmark evidence."""
from alembic import op
import sqlalchemy as sa
revision='m14_0017'; down_revision='m13_0016'
def upgrade(profile, **kwargs):
 u=sa.UUID()
 op.create_table('population_profiles',sa.Column('tenant_id',u,nullable=False),sa.Column('profile_id',u,nullable=False),sa.Column('profile_key',sa.Text,nullable=False),sa.Column('merchant_count',sa.Integer,nullable=False),sa.Column('transaction_count',sa.BigInteger,nullable=False),sa.Column('currency_count',sa.Integer,nullable=False),sa.Column('gateway_count',sa.Integer,nullable=False),sa.Column('status',sa.Text,nullable=False),sa.PrimaryKeyConstraint('tenant_id','profile_id'),sa.UniqueConstraint('tenant_id','profile_key'),sa.CheckConstraint("status IN ('DRAFT','VALIDATED','RETIRED')"),schema='resilience_v2')
 op.create_table('benchmark_runs',sa.Column('tenant_id',u,nullable=False),sa.Column('benchmark_id',u,nullable=False),sa.Column('profile_id',u,nullable=False),sa.Column('operation',sa.Text,nullable=False),sa.Column('records_processed',sa.BigInteger,nullable=False),sa.Column('elapsed_ms',sa.Numeric(20,6),nullable=False),sa.Column('throughput_per_sec',sa.Numeric(20,6),nullable=False),sa.Column('result_state',sa.Text,nullable=False),sa.Column('evidence_ref',sa.Text,nullable=False),sa.PrimaryKeyConstraint('tenant_id','benchmark_id'),sa.ForeignKeyConstraint(['tenant_id','profile_id'],['resilience_v2.population_profiles.tenant_id','resilience_v2.population_profiles.profile_id']),sa.CheckConstraint("result_state IN ('PASS','FAIL')"),schema='resilience_v2')
 op.execute(sa.text(f"GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA resilience_v2 TO {profile.runtime_user}"));op.execute(sa.text(f"REVOKE INSERT, UPDATE, DELETE ON resilience_v2.tenants, resilience_v2.actors, resilience_v2.environment_identity, resilience_v2.alembic_version FROM {profile.runtime_user}"))
def downgrade(**kwargs): raise RuntimeError('M14 downgrade disabled; rebuild disposable V2 database explicitly')
