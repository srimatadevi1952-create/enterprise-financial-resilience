import argparse
import json
from .config import IsolationError, REVISION, load_profile
from .database import connect_guarded


def main():
    parser = argparse.ArgumentParser(description="Enterprise Financial Resilience V2")
    parser.add_argument("command", choices=["doctor", "console"])
    parser.add_argument("--profile", required=True, choices=["development", "test"])
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    try:
        if args.command == "console":
            if args.profile != "development":
                raise IsolationError("CONSOLE_REQUIRES_DEVELOPMENT_PROFILE")
            load_profile(args.profile)
            from .m22_web import serve
            serve(port=args.port)
            return
        profile = load_profile(args.profile)
        with connect_guarded(profile, args.profile) as conn:
            version = conn.execute("SHOW server_version").fetchone()[0]
        print(json.dumps(dict(status="PASS", environment=args.profile, database=profile.dbname,
                             schema_revision=REVISION, postgres=version, access="read-only runtime")))
    except IsolationError as exc:
        print(json.dumps({"status":"REJECTED","reason":str(exc)}))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
