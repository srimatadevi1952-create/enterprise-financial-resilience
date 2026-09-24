from datetime import datetime, timezone
from uuid import uuid4

import psycopg
import pytest
from pydantic import ValidationError

from resilience.config import load_profile
from resilience.m23_enterprise import (
    EnterpriseConfigurationError,
    EnterpriseConfigurationSpec,
    activate_enterprise_configuration,
    example_enterprise_spec,
    register_enterprise_configuration,
    resolve_enterprise_configuration,
)


def test_m23_rejects_unknown_and_cyclic_process_parents():
    actor = uuid4()
    value = example_enterprise_spec(actor).model_dump()
    value["processes"][0]["parent_key"] = "UNKNOWN"
    with pytest.raises(ValidationError, match="PROCESS_PARENT_UNKNOWN"):
        EnterpriseConfigurationSpec.model_validate(value)

    value = example_enterprise_spec(actor).model_dump()
    value["processes"][0]["parent_key"] = "SETTLEMENT"
    with pytest.raises(ValidationError, match="PROCESS_PARENT_CYCLE"):
        EnterpriseConfigurationSpec.model_validate(value)


@pytest.mark.integration
def test_m23_configures_two_distinct_enterprises_and_resolves_effective_versions():
    profile = load_profile("test")
    payments_tenant, payments_actor = uuid4(), uuid4()
    advisory_tenant, advisory_actor = uuid4(), uuid4()
    with psycopg.connect(**profile.connection_kwargs(migration=True)) as admin:
        admin.execute(
            "INSERT INTO resilience_v2.tenants VALUES (%s,'m23-payments','ACTIVE')",
            (payments_tenant,),
        )
        admin.execute(
            "INSERT INTO resilience_v2.actors VALUES (%s,%s,'Payments configuration owner')",
            (payments_tenant, payments_actor),
        )
        admin.execute(
            "INSERT INTO resilience_v2.tenants VALUES (%s,'m23-advisory','ACTIVE')",
            (advisory_tenant,),
        )
        admin.execute(
            "INSERT INTO resilience_v2.actors VALUES (%s,%s,'Advisory configuration owner')",
            (advisory_tenant, advisory_actor),
        )
        admin.commit()

    with psycopg.connect(**profile.connection_kwargs()) as conn:
        with conn.transaction():
            payments = register_enterprise_configuration(
                conn, payments_tenant, example_enterprise_spec(payments_actor)
            )
            advisory = register_enterprise_configuration(
                conn,
                advisory_tenant,
                example_enterprise_spec(advisory_actor, variant="advisory"),
            )
            active = activate_enterprise_configuration(conn, payments_tenant, payments["config_id"])
            activate_enterprise_configuration(conn, advisory_tenant, advisory["config_id"])
            version_one = resolve_enterprise_configuration(
                conn,
                payments_tenant,
                "PAYMENTS-GROUP",
                datetime(2026, 10, 2, tzinfo=timezone.utc),
            )
            version_two_spec = example_enterprise_spec(payments_actor).model_copy(
                update={
                    "version": 2,
                    "effective_from": datetime(2026, 11, 1, tzinfo=timezone.utc),
                    "evidence_refs": ("change:payments:v2:approved",),
                }
            )
            version_two = register_enterprise_configuration(conn, payments_tenant, version_two_spec)
            activate_enterprise_configuration(conn, payments_tenant, version_two["config_id"])
            resolved_history = resolve_enterprise_configuration(
                conn,
                payments_tenant,
                "PAYMENTS-GROUP",
                datetime(2026, 10, 15, tzinfo=timezone.utc),
            )
            resolved_current = resolve_enterprise_configuration(
                conn,
                payments_tenant,
                "PAYMENTS-GROUP",
                datetime(2026, 11, 2, tzinfo=timezone.utc),
            )

        assert payments["status"] == "VALIDATED"
        assert active["status"] == "ACTIVE"
        assert payments["entities"] == 3
        assert payments["processes"] == 4
        assert payments["risks"] == 4
        assert payments["controls"] == 5
        assert payments["dependencies"] == 3
        assert advisory["processes"] == 2
        assert version_one["config_id"] == payments["config_id"]
        assert resolved_history["version"] == 1
        assert resolved_history["status"] == "RETIRED"
        assert resolved_current["version"] == 2
        assert resolved_current["status"] == "ACTIVE"
        assert conn.execute(
            "SELECT count(DISTINCT jurisdiction) FROM resilience_v2.enterprise_entities WHERE tenant_id=%s",
            (payments_tenant,),
        ).fetchone()[0] == 3
        assert conn.execute(
            "SELECT count(*) FROM resilience_v2.enterprise_processes WHERE tenant_id=%s",
            (advisory_tenant,),
        ).fetchone()[0] == 2
        assert conn.execute(
            "SELECT count(*) FROM resilience_v2.enterprise_processes WHERE tenant_id=%s",
            (payments_tenant,),
        ).fetchone()[0] == 8
        assert conn.execute(
            """SELECT evidence_refs FROM resilience_v2.enterprise_configuration_versions
            WHERE tenant_id=%s AND version=1""",
            (payments_tenant,),
        ).fetchone()[0] == ["onboarding:payments:approved", "process-register:v1"]

        with pytest.raises(psycopg.errors.RaiseException, match="CONFIGURATION_PAYLOAD_IMMUTABLE"):
            conn.execute(
                """UPDATE resilience_v2.enterprise_configuration_versions
                SET legal_name='Tampered name' WHERE tenant_id=%s AND config_id=%s""",
                (payments_tenant, version_two["config_id"]),
            )
        conn.rollback()

        with pytest.raises(psycopg.errors.RaiseException, match="CONFIGURATION_CHILDREN_REQUIRE_DRAFT"):
            conn.execute(
                """INSERT INTO resilience_v2.enterprise_processes
                VALUES (%s,%s,%s,'LATE-PROCESS','Late process',%s,'LOW',60,NULL)""",
                (payments_tenant, version_two["config_id"], uuid4(), payments_actor),
            )
        conn.rollback()

        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute(
                """UPDATE resilience_v2.enterprise_processes SET name='Tampered process'
                WHERE tenant_id=%s AND config_id=%s""",
                (payments_tenant, version_two["config_id"]),
            )
        conn.rollback()


@pytest.mark.integration
def test_m23_requires_validated_configuration_before_activation():
    profile = load_profile("test")
    tenant, actor, config_id = uuid4(), uuid4(), uuid4()
    with psycopg.connect(**profile.connection_kwargs(migration=True)) as admin:
        admin.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m23-draft','ACTIVE')", (tenant,))
        admin.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'Draft owner')", (tenant, actor))
        admin.execute(
            """INSERT INTO resilience_v2.enterprise_configuration_versions
            VALUES (%s,%s,'DRAFT-PROFILE',1,'Draft Enterprise','Test','USD',%s,%s,NULL,'DRAFT','[]'::json,%s)""",
            (
                tenant,
                config_id,
                actor,
                datetime(2026, 10, 1, tzinfo=timezone.utc),
                datetime(2026, 9, 24, tzinfo=timezone.utc),
            ),
        )
        admin.commit()

    with psycopg.connect(**profile.connection_kwargs()) as conn:
        with pytest.raises(EnterpriseConfigurationError, match="CONFIGURATION_NOT_VALIDATED"):
            activate_enterprise_configuration(conn, tenant, config_id)
