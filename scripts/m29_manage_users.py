"""Invite, revoke or list hosted-UAT users without handling passwords."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import os
from urllib.parse import urlparse
from uuid import uuid4

import psycopg


ROLES = ("viewer", "simulation_analyst", "consultant", "client_approver")


def connection_url() -> str:
    if os.environ.get("EFR_APP_ENV", "").casefold() != "uat":
        raise SystemExit("HOSTED_UAT_ENVIRONMENT_REQUIRED")
    value = os.environ.get("DATABASE_URL", "")
    target = urlparse(value)
    if target.scheme not in {"postgres", "postgresql"} or not target.hostname or target.hostname in {"127.0.0.1", "localhost"}:
        raise SystemExit("HOSTED_DATABASE_TARGET_INVALID")
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-hosted-uat", action="store_true", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    invite = commands.add_parser("invite")
    invite.add_argument("--email", required=True)
    invite.add_argument("--name", required=True)
    invite.add_argument("--role", choices=ROLES, required=True)
    invite.add_argument("--days", type=int, default=7)
    revoke = commands.add_parser("revoke")
    revoke.add_argument("--email", required=True)
    commands.add_parser("list")
    args = parser.parse_args()
    if not args.confirm_hosted_uat:
        raise SystemExit("HOSTED_UAT_CONFIRMATION_REQUIRED")
    with psycopg.connect(connection_url(), connect_timeout=8) as conn:
        if args.command == "invite":
            if args.days < 1 or args.days > 30:
                raise SystemExit("ACCESS_DURATION_MUST_BE_1_TO_30_DAYS")
            email = args.email.strip().casefold()
            expiry = datetime.now(timezone.utc) + timedelta(days=args.days)
            conn.execute(
                "INSERT INTO efr_uat.auth_users(actor_id,display_name,email,role,access_expires_at,active) "
                "VALUES (%s,%s,%s,%s,%s,true) ON CONFLICT(email) DO UPDATE SET "
                "display_name=excluded.display_name,role=excluded.role,access_expires_at=excluded.access_expires_at,active=true",
                (str(uuid4()), args.name.strip(), email, args.role, expiry),
            )
            print(f"Invited {email} as {args.role} until {expiry.isoformat()}")
        elif args.command == "revoke":
            email = args.email.strip().casefold()
            conn.execute("UPDATE efr_uat.auth_users SET active=false WHERE email=%s", (email,))
            conn.execute("UPDATE efr_uat.web_sessions SET revoked=true WHERE email=%s", (email,))
            print(f"Revoked {email}")
        else:
            rows = conn.execute(
                "SELECT display_name,email,role,access_expires_at,active FROM efr_uat.auth_users ORDER BY email"
            ).fetchall()
            for row in rows:
                print(" | ".join(map(str, row)))


if __name__ == "__main__":
    main()
