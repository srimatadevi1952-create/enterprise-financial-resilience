"""M12 capital depletion and regeneration facts."""
from alembic import op
import sqlalchemy as sa
revision='m12_0015'; down_revision='m11_0014'
def upgrade(profile, **kwargs):
 u=sa.UUID()
 op.create_table('capital_scenarios',sa.Column('tenant_id',u,nullable=False),sa.Column('run_id',u,nullable=False),sa.Column('capital_scenario_id',u,nullable=False),sa.Column('scenario_type',sa.Text,nullable=False),sa.Column('starting_capital_minor',sa.BigInteger,nullable=False),sa.Column('stress_loss_minor',sa.BigInteger,nullable=False),sa.Column('reserve_draw_minor',sa.BigInteger,nullable=False),sa.Column('recovery_horizon_months',sa.Integer,nullable=False),sa.PrimaryKeyConstraint('tenant_id','capital_scenario_id'),sa.ForeignKeyConstraint(['tenant_id','run_id'],['resilience_v2.runs.tenant_id','resilience_v2.runs.run_id']),schema='resilience_v2')
 op.create_table('capital_trajectories',sa.Column('tenant_id',u,nullable=False),sa.Column('run_id',u,nullable=False),sa.Column('trajectory_id',u,nullable=False),sa.Column('capital_scenario_id',u,nullable=False),sa.Column('period_index',sa.Integer,nullable=False),sa.Column('capital_balance_minor',sa.BigInteger,nullable=False),sa.Column('regeneration_inflow_minor',sa.BigInteger,nullable=False),sa.Column('buffer_ratio_pct',sa.Numeric(8,4),nullable=False),sa.Column('capital_state',sa.Text,nullable=False),sa.PrimaryKeyConstraint('tenant_id','trajectory_id'),sa.ForeignKeyConstraint(['tenant_id','run_id'],['resilience_v2.runs.tenant_id','resilience_v2.runs.run_id']),sa.CheckConstraint("capital_state IN ('DEPLETED','STABILIZING','REGENERATING','RESTORED')"),schema='resilience_v2')
 op.create_table('capital_measures',sa.Column('tenant_id',u,nullable=False),sa.Column('run_id',u,nullable=False),sa.Column('measure_id',u,nullable=False),sa.Column('measure_key',sa.Text,nullable=False),sa.Column('measure_value',sa.Numeric(20,6),nullable=False),sa.Column('unit',sa.Text,nullable=False),sa.Column('evidence_refs',sa.JSON,nullable=False),sa.PrimaryKeyConstraint('tenant_id','measure_id'),sa.ForeignKeyConstraint(['tenant_id','run_id'],['resilience_v2.runs.tenant_id','resilience_v2.runs.run_id']),sa.UniqueConstraint('tenant_id','run_id','measure_key'),schema='resilience_v2')
 op.execute(sa.text(f"GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA resilience_v2 TO {profile.runtime_user}"));op.execute(sa.text(f"REVOKE INSERT, UPDATE, DELETE ON resilience_v2.tenants, resilience_v2.actors, resilience_v2.environment_identity, resilience_v2.alembic_version FROM {profile.runtime_user}"))
def downgrade(**kwargs): raise RuntimeError('M12 downgrade disabled; rebuild disposable V2 database explicitly')



