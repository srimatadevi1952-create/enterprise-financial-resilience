import psycopg
from .config import IsolationError, Profile, REVISION


def verify_identity(conn, profile: Profile, expected: str):
    profile.validate_target(expected)
    row = conn.execute("SELECT current_database(),current_user,shobj_description(oid,'pg_database') FROM pg_database WHERE datname=current_database()").fetchone()
    if row != (profile.dbname, profile.runtime_user, f"efrco-v2:{expected}:{profile.instance_id}"):
        raise IsolationError("DATABASE_IDENTITY_MISMATCH")
    role = conn.execute("SELECT rolsuper,rolcreatedb,rolcreaterole,rolbypassrls FROM pg_roles WHERE rolname=current_user").fetchone()
    if any(role):
        raise IsolationError("PRIVILEGED_RUNTIME_REJECTED")
    marker = conn.execute("SELECT environment,instance_id::text FROM resilience_v2.environment_identity WHERE singleton=true").fetchone()
    if marker != (expected, str(profile.instance_id)):
        raise IsolationError("ENVIRONMENT_MARKER_MISMATCH")
    revision = conn.execute("SELECT version_num FROM resilience_v2.alembic_version").fetchall()
    if revision != [(REVISION,)]:
        raise IsolationError("SCHEMA_VERSION_MISMATCH")


def connect_guarded(profile: Profile, expected: str):
    profile.validate_target(expected)  # before even opening a socket
    conn = None
    try:
        conn = psycopg.connect(**profile.connection_kwargs(), options="-c default_transaction_read_only=on")
        verify_identity(conn, profile, expected)
        return conn
    except IsolationError:
        if conn: conn.close()
        raise
    except Exception:
        if conn: conn.close()
        raise IsolationError("DATABASE_GUARD_FAILED") from None
