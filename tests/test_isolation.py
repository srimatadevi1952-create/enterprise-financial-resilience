from uuid import uuid4
from unittest.mock import patch
import pytest
import psycopg
from resilience.config import IsolationError, Profile, load_profile, REVISION
from resilience.database import connect_guarded


def fixture_profile():
    return Profile(environment="test",host="127.0.0.1",port=56432,dbname="efrco_v2_test",
                   instance_id=uuid4(),runtime_user="efrco_test_runtime",runtime_password="test-only",
                   migration_user="efrco_test_migrator",migration_password="test-only")


@pytest.mark.parametrize("database",["ledger_db","postgres","ledger_restore","efrco_v2_dev"])
def test_rejects_wrong_database_before_connection(database):
    profile=fixture_profile().model_copy(update={"dbname":database})
    with patch("resilience.database.psycopg.connect") as connect:
        with pytest.raises(IsolationError): connect_guarded(profile,"test")
        connect.assert_not_called()


def test_rejects_environment_confusion_before_connection():
    with patch("resilience.database.psycopg.connect") as connect:
        with pytest.raises(IsolationError): connect_guarded(fixture_profile(),"development")
        connect.assert_not_called()


def test_requires_explicit_profile():
    with pytest.raises(IsolationError): load_profile("")


def test_credentials_are_redacted():
    assert "test-only" not in repr(fixture_profile())


@pytest.mark.integration
@pytest.mark.parametrize("environment",["development","test"])
def test_actual_identity_and_revision(environment):
    p=load_profile(environment)
    with connect_guarded(p,environment) as c:
        assert c.execute("SHOW transaction_read_only").fetchone()[0]=="on"
        assert c.execute("SELECT version_num FROM resilience_v2.alembic_version").fetchone()[0]==REVISION
        assert c.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='resilience_v2'").fetchone()[0] >= 14


@pytest.mark.integration
def test_actual_instance_mismatch_rejected():
    p=load_profile("test").model_copy(update={"instance_id":uuid4()})
    with pytest.raises(IsolationError,match="DATABASE_IDENTITY_MISMATCH"):
        connect_guarded(p,"test")


@pytest.mark.integration
@pytest.mark.parametrize("operation",[
    "UPDATE resilience_v2.environment_identity SET environment='development'",
    "TRUNCATE resilience_v2.environment_identity",
    "CREATE TABLE resilience_v2.forbidden_m0_probe(id integer)",
])
def test_runtime_cannot_modify_identity_or_schema(operation):
    p=load_profile("test")
    with psycopg.connect(**p.connection_kwargs()) as c:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            c.execute(operation)
        c.rollback()


@pytest.mark.integration
@pytest.mark.parametrize("migration",[False,True])
def test_test_role_cannot_connect_to_development(migration):
    kwargs=load_profile("test").connection_kwargs(migration=migration)
    kwargs['dbname']='efrco_v2_dev'
    with pytest.raises(psycopg.OperationalError):
        psycopg.connect(**kwargs)
