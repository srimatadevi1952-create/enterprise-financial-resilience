"""M26 immutable lesson payloads and controlled publication states."""

from alembic import op
import sqlalchemy as sa


revision = "m26_0035"
down_revision = "m26_0034"


def upgrade(profile, **kwargs):
    op.execute(sa.text("""
        CREATE FUNCTION resilience_v2.guard_m26_stateful_records()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF TG_OP='DELETE' THEN RAISE EXCEPTION 'M26_RECORD_DELETE_PROHIBITED'; END IF;

          IF TG_TABLE_NAME='knowledge_lesson_versions' THEN
            IF (to_jsonb(NEW) - ARRAY['status','reviewer_actor_id','updated_at'])
               IS DISTINCT FROM
               (to_jsonb(OLD) - ARRAY['status','reviewer_actor_id','updated_at']) THEN
              RAISE EXCEPTION 'LESSON_VERSION_PAYLOAD_IMMUTABLE';
            END IF;
            IF NOT (
              NEW.status=OLD.status OR
              (OLD.status='DRAFT' AND NEW.status='IN_REVIEW') OR
              (OLD.status='IN_REVIEW' AND NEW.status IN ('APPROVED','RETURNED','REJECTED')) OR
              (OLD.status='APPROVED' AND NEW.status='PUBLISHED') OR
              (OLD.status='PUBLISHED' AND NEW.status IN ('SUPERSEDED','WITHDRAWN'))
            ) THEN RAISE EXCEPTION 'LESSON_STATUS_TRANSITION_INVALID'; END IF;
            IF OLD.reviewer_actor_id IS NOT NULL AND NEW.reviewer_actor_id IS DISTINCT FROM OLD.reviewer_actor_id THEN
              RAISE EXCEPTION 'LESSON_REVIEWER_IMMUTABLE';
            END IF;
            RETURN NEW;
          END IF;

          IF TG_TABLE_NAME='knowledge_access_grants' THEN
            IF (to_jsonb(NEW) - ARRAY['status','updated_at'])
               IS DISTINCT FROM (to_jsonb(OLD) - ARRAY['status','updated_at']) THEN
              RAISE EXCEPTION 'KNOWLEDGE_ACCESS_GRANT_PAYLOAD_IMMUTABLE';
            END IF;
            IF NOT (
              NEW.status=OLD.status OR
              (OLD.status='ACTIVE' AND NEW.status IN ('REVOKED','EXPIRED'))
            ) THEN RAISE EXCEPTION 'KNOWLEDGE_ACCESS_GRANT_TRANSITION_INVALID'; END IF;
            RETURN NEW;
          END IF;

          RAISE EXCEPTION 'M26_GUARD_TABLE_UNKNOWN';
        END;
        $$
    """))
    for table in ("knowledge_lesson_versions", "knowledge_access_grants"):
        op.execute(sa.text(
            f"CREATE TRIGGER {table}_state_guard BEFORE UPDATE OR DELETE ON resilience_v2.{table} "
            "FOR EACH ROW EXECUTE FUNCTION resilience_v2.guard_m26_stateful_records()"
        ))


def downgrade(**kwargs):
    raise RuntimeError("M26 guard downgrade disabled; rebuild disposable V2 database explicitly")
