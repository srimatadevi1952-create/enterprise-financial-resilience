"""M25 immutable payloads and controlled information state transitions."""

from alembic import op
import sqlalchemy as sa


revision = "m25_0033"
down_revision = "m25_0032"


def upgrade(profile, **kwargs):
    op.execute(sa.text("""
        CREATE FUNCTION resilience_v2.guard_m25_stateful_records()
        RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE receipt_obligation uuid;
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'M25_RECORD_DELETE_PROHIBITED';
          END IF;

          IF TG_TABLE_NAME = 'authorized_data_sources' THEN
            IF (to_jsonb(NEW) - ARRAY['status','last_successful_at','updated_at'])
               IS DISTINCT FROM
               (to_jsonb(OLD) - ARRAY['status','last_successful_at','updated_at']) THEN
              RAISE EXCEPTION 'DATA_SOURCE_PAYLOAD_IMMUTABLE';
            END IF;
            IF NOT (
              NEW.status = OLD.status OR
              (OLD.status='ACTIVE' AND NEW.status IN ('SUSPENDED','REVOKED','EXPIRED')) OR
              (OLD.status='SUSPENDED' AND NEW.status IN ('ACTIVE','REVOKED','EXPIRED'))
            ) THEN RAISE EXCEPTION 'DATA_SOURCE_STATUS_TRANSITION_INVALID'; END IF;
            RETURN NEW;
          END IF;

          IF TG_TABLE_NAME = 'information_obligation_definitions' THEN
            IF (to_jsonb(NEW) - ARRAY['status','updated_at'])
               IS DISTINCT FROM (to_jsonb(OLD) - ARRAY['status','updated_at']) THEN
              RAISE EXCEPTION 'OBLIGATION_DEFINITION_PAYLOAD_IMMUTABLE';
            END IF;
            IF NOT (NEW.status=OLD.status OR (OLD.status='ACTIVE' AND NEW.status='RETIRED')) THEN
              RAISE EXCEPTION 'OBLIGATION_DEFINITION_STATUS_TRANSITION_INVALID';
            END IF;
            RETURN NEW;
          END IF;

          IF TG_TABLE_NAME = 'evidence_confidence_rules' THEN
            IF (to_jsonb(NEW) - 'status') IS DISTINCT FROM (to_jsonb(OLD) - 'status') THEN
              RAISE EXCEPTION 'CONFIDENCE_RULE_PAYLOAD_IMMUTABLE';
            END IF;
            IF NOT (NEW.status=OLD.status OR (OLD.status='ACTIVE' AND NEW.status='RETIRED')) THEN
              RAISE EXCEPTION 'CONFIDENCE_RULE_STATUS_TRANSITION_INVALID';
            END IF;
            RETURN NEW;
          END IF;

          IF TG_TABLE_NAME = 'information_obligations' THEN
            IF (to_jsonb(NEW) - ARRAY['status','current_receipt_id','updated_at'])
               IS DISTINCT FROM
               (to_jsonb(OLD) - ARRAY['status','current_receipt_id','updated_at']) THEN
              RAISE EXCEPTION 'INFORMATION_OBLIGATION_PAYLOAD_IMMUTABLE';
            END IF;
            IF NOT (
              NEW.status=OLD.status OR
              (OLD.status='REQUESTED' AND NEW.status IN ('OVERDUE','RECEIVED','WAIVED')) OR
              (OLD.status='OVERDUE' AND NEW.status IN ('RECEIVED','WAIVED')) OR
              (OLD.status='RECEIVED' AND NEW.status IN ('VALIDATED','REJECTED')) OR
              (OLD.status='REJECTED' AND NEW.status IN ('RECEIVED','WAIVED'))
            ) THEN RAISE EXCEPTION 'INFORMATION_OBLIGATION_STATUS_TRANSITION_INVALID'; END IF;
            IF NEW.current_receipt_id IS NOT NULL THEN
              SELECT obligation_id INTO receipt_obligation
              FROM resilience_v2.information_receipts
              WHERE tenant_id=NEW.tenant_id AND receipt_id=NEW.current_receipt_id;
              IF receipt_obligation IS DISTINCT FROM NEW.obligation_id THEN
                RAISE EXCEPTION 'CURRENT_RECEIPT_OBLIGATION_MISMATCH';
              END IF;
            END IF;
            RETURN NEW;
          END IF;

          RAISE EXCEPTION 'M25_GUARD_TABLE_UNKNOWN';
        END;
        $$
    """))
    for table in (
        "authorized_data_sources",
        "information_obligation_definitions",
        "information_obligations",
        "evidence_confidence_rules",
    ):
        op.execute(sa.text(
            f"CREATE TRIGGER {table}_state_guard BEFORE UPDATE OR DELETE ON resilience_v2.{table} "
            "FOR EACH ROW EXECUTE FUNCTION resilience_v2.guard_m25_stateful_records()"
        ))


def downgrade(**kwargs):
    raise RuntimeError("M25 guard downgrade disabled; rebuild disposable V2 database explicitly")
