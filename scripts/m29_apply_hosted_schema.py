"""Apply the isolated M29 hosted-UAT schema to the configured Neon database."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from urllib.parse import urlparse

import psycopg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-hosted-uat", action="store_true", required=True)
    args = parser.parse_args()
    if not args.confirm_hosted_uat or os.environ.get("EFR_APP_ENV", "").casefold() != "uat":
        raise SystemExit("HOSTED_UAT_CONFIRMATION_REQUIRED")
    database_url = os.environ.get("DATABASE_URL", "")
    target = urlparse(database_url)
    if target.scheme not in {"postgres", "postgresql"} or not target.hostname or target.hostname in {"127.0.0.1", "localhost"}:
        raise SystemExit("HOSTED_DATABASE_TARGET_INVALID")
    schema = (Path(__file__).resolve().parents[1] / "deploy" / "m29_hosted_schema.sql").read_text(encoding="utf-8")
    with psycopg.connect(database_url, connect_timeout=8) as conn:
        conn.execute(schema)
    print("M29 hosted UAT schema applied")


if __name__ == "__main__":
    main()
