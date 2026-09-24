import json
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, SecretStr

ROOT = Path(__file__).resolve().parents[2]
NAMES = {"development": "efrco_v2_dev", "test": "efrco_v2_test"}
REVISION = "m24_0031"


class IsolationError(RuntimeError):
    pass


class Profile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    environment: Literal["development", "test"]
    host: Literal["127.0.0.1"]
    port: int
    dbname: str
    instance_id: UUID
    runtime_user: str
    runtime_password: SecretStr
    migration_user: str
    migration_password: SecretStr

    def validate_target(self, expected: str):
        if expected not in NAMES or self.environment != expected:
            raise IsolationError("ENVIRONMENT_MISMATCH")
        suffix = "dev" if expected == "development" else "test"
        if self.dbname != NAMES[expected] or self.port != 56432:
            raise IsolationError("TARGET_NOT_ALLOWLISTED")
        if self.runtime_user != f"efrco_{suffix}_runtime" or self.migration_user != f"efrco_{suffix}_migrator":
            raise IsolationError("ROLE_NOT_ALLOWLISTED")

    def connection_kwargs(self, migration=False):
        return dict(host=self.host, port=self.port, dbname=self.dbname,
                    user=self.migration_user if migration else self.runtime_user,
                    password=(self.migration_password if migration else self.runtime_password).get_secret_value(),
                    connect_timeout=5, application_name="efrco-v2-m0")


def load_profile(expected: str, path: Path | None = None):
    if expected not in NAMES:
        raise IsolationError("EXPLICIT_PROFILE_REQUIRED")
    try:
        profiles = json.loads((path or ROOT / ".local/profiles.json").read_text(encoding="utf-8"))
        profile = Profile.model_validate(profiles[expected])
    except Exception:
        raise IsolationError("LOCAL_PROFILE_INVALID") from None
    profile.validate_target(expected)
    return profile
