import os
from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from resilience.config import IsolationError, load_profile

if context.is_offline_mode():
    raise IsolationError("OFFLINE_MIGRATION_NOT_ALLOWED_WITHOUT_TARGET_GUARD")
profile = load_profile(os.environ.get("EFR_PROFILE", ""))
url = URL.create("postgresql+psycopg", username=profile.migration_user,
                 password=profile.migration_password.get_secret_value(), host=profile.host,
                 port=profile.port, database=profile.dbname)
engine = create_engine(url, hide_parameters=True)
with engine.connect() as connection:
    actual = connection.exec_driver_sql("SELECT current_database(), current_user, shobj_description(oid,'pg_database') FROM pg_database WHERE datname=current_database()").one()
    expected = (profile.dbname, profile.migration_user, f"efrco-v2:{profile.environment}:{profile.instance_id}")
    if tuple(actual) != expected:
        raise IsolationError("MIGRATION_TARGET_REJECTED")
    connection.commit()
    context.configure(connection=connection, version_table_schema="resilience_v2")
    with context.begin_transaction():
        context.run_migrations(profile=profile)
