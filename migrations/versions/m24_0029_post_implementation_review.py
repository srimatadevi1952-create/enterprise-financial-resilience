"""M24 post-implementation outcome validation."""

from alembic import op
import sqlalchemy as sa


revision = "m24_0029"
down_revision = "m24_0028"


def upgrade(profile, **kwargs):
    uuid = sa.UUID()
    op.create_table(
        "consultant_post_implementation_reviews",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("review_id", uuid, nullable=False),
        sa.Column("case_id", uuid, nullable=False),
        sa.Column("proposal_id", uuid, nullable=False),
        sa.Column("reviewed_by", uuid, nullable=False),
        sa.Column("outcome", sa.Text, nullable=False),
        sa.Column("expected_metrics", sa.JSON, nullable=False),
        sa.Column("observed_metrics", sa.JSON, nullable=False),
        sa.Column("conclusion", sa.Text, nullable=False),
        sa.Column("evidence_refs", sa.JSON, nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "review_id"),
        sa.UniqueConstraint("tenant_id", "proposal_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "case_id"],
            ["resilience_v2.consultant_cases.tenant_id", "resilience_v2.consultant_cases.case_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "proposal_id"],
            ["resilience_v2.consultant_change_proposals.tenant_id", "resilience_v2.consultant_change_proposals.proposal_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "reviewed_by"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("outcome IN ('MATCHED','PARTIAL','FAILED')"),
        schema="resilience_v2",
    )
    op.execute(sa.text(
        "CREATE TRIGGER consultant_post_implementation_reviews_append_only "
        "BEFORE UPDATE OR DELETE ON resilience_v2.consultant_post_implementation_reviews "
        "FOR EACH ROW EXECUTE FUNCTION resilience_v2.guard_m24_append_only()"
    ))
    op.execute(sa.text(
        f"GRANT SELECT, INSERT ON resilience_v2.consultant_post_implementation_reviews TO {profile.runtime_user}"
    ))


def downgrade(**kwargs):
    raise RuntimeError("M24 review downgrade disabled; rebuild disposable V2 database explicitly")
