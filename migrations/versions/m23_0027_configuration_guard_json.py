"""M23 make configuration immutability comparison JSON-safe."""

from alembic import op
import sqlalchemy as sa


revision = "m23_0027"
down_revision = "m23_0026"


def upgrade(profile, **kwargs):
    op.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION resilience_v2.guard_enterprise_configuration_version()
            RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN
              IF TG_OP = 'INSERT' THEN
                IF NEW.status <> 'DRAFT' OR NEW.effective_to IS NOT NULL THEN
                  RAISE EXCEPTION 'CONFIGURATION_MUST_START_AS_DRAFT';
                END IF;
                RETURN NEW;
              END IF;

              IF ROW(NEW.tenant_id,NEW.config_id,NEW.profile_key,NEW.version,NEW.legal_name,
                     NEW.industry,NEW.base_currency,NEW.owner_actor_id,NEW.effective_from,
                     NEW.evidence_refs::text,NEW.created_at)
                 IS DISTINCT FROM
                 ROW(OLD.tenant_id,OLD.config_id,OLD.profile_key,OLD.version,OLD.legal_name,
                     OLD.industry,OLD.base_currency,OLD.owner_actor_id,OLD.effective_from,
                     OLD.evidence_refs::text,OLD.created_at) THEN
                RAISE EXCEPTION 'CONFIGURATION_PAYLOAD_IMMUTABLE';
              END IF;

              IF OLD.status = 'DRAFT' AND NEW.status = 'VALIDATED'
                 AND NEW.effective_to IS NOT DISTINCT FROM OLD.effective_to THEN
                RETURN NEW;
              ELSIF OLD.status = 'VALIDATED' AND NEW.status = 'ACTIVE'
                    AND NEW.effective_to IS NULL THEN
                RETURN NEW;
              ELSIF OLD.status = 'ACTIVE' AND NEW.status = 'RETIRED'
                    AND NEW.effective_to IS NOT NULL
                    AND NEW.effective_to > NEW.effective_from THEN
                RETURN NEW;
              END IF;
              RAISE EXCEPTION 'CONFIGURATION_STATUS_TRANSITION_INVALID';
            END;
            $$
            """
        )
    )


def downgrade(**kwargs):
    raise RuntimeError("M23 guard downgrade disabled; rebuild disposable V2 database explicitly")
