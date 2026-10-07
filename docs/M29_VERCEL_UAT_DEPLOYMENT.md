# M29 — Vercel Hosted UAT Deployment

## Intended environment

This deployment is a separate user-acceptance-test environment. It may contain synthetic demonstration information only. It must not connect to the recovered V1 database, the local V2 development database or a client production source.

## Included deployment components

- `api/index.py`: Vercel Python Function entry point.
- `vercel.json`: catch-all application routing, required static assets and security headers.
- `deploy/m29_hosted_schema.sql`: isolated Neon schema for identities, challenges, sessions, audit, simulations and collaboration invitations.
- `scripts/m29_apply_hosted_schema.py`: guarded hosted-schema installer.
- `scripts/m29_manage_users.py`: invitation, revocation and listing utility.
- `src/resilience/m29_hosted.py`: Neon and Resend adapters.
- `/api/health`: readiness check with no enterprise data.

## Required Vercel environment variables

| Variable | Purpose |
| --- | --- |
| `EFR_APP_ENV=uat` | Selects the hosted adapter and prevents local demonstration identities. |
| `DATABASE_URL` | Neon PostgreSQL connection supplied by the Vercel Marketplace integration. |
| `EFR_AUTH_SECRET` | Random signing material of at least 32 characters, stored only as a Vercel secret. |
| `RESEND_API_KEY` | Resend API credential, stored only as a Vercel secret. |
| `EFR_FROM_EMAIL` | Verified sender, for example `Enterprise Resilience <access@verified-domain.example>`. |

Do not paste credentials into source files, chat messages, deployment logs or GitHub. `.env.example` contains names and placeholders only.

## Provisioning sequence

1. Import `srimatadevi1952-create/enterprise-financial-resilience` into the repository owner's Vercel account.
2. Keep the project root at the repository root and enable Git preview deployments.
3. Add the Neon integration from the Vercel Marketplace and connect it only to Preview initially.
4. Add Resend, verify the intended sending identity and connect it only to Preview initially.
5. Add `EFR_APP_ENV`, `EFR_AUTH_SECRET` and `EFR_FROM_EMAIL` to the Preview environment. Confirm that the provider integrations supplied `DATABASE_URL` and `RESEND_API_KEY`.
6. Apply `deploy/m29_hosted_schema.sql` to the new Neon UAT database. The guarded Python installer can be used when `EFR_APP_ENV=uat` and `DATABASE_URL` are set locally.
7. Invite the application owner for seven days with `scripts/m29_manage_users.py`, then deploy a Vercel preview.
8. Confirm `/api/health` reports `status: ok`, `environment: uat` and `database: true`.
9. Complete the owner login, simulation creation, scenario run, browser refresh, logout and repeat login. The simulation must survive the refresh and a new function instance.
10. Invite one external Viewer for seven days. Verify view-only access, failed edit attempts, expiry and immediate revocation.
11. Record the preview URL, Vercel deployment identifier, Git commit, database branch and test evidence. Share the preview only after these checks pass.

## Release boundary

The Vercel preview is an external UAT environment, not a production release. Live data feeds, automatic remedies and production actions remain disabled. Moving beyond UAT requires approved data-processing terms, retention rules, monitoring, backup and recovery evidence, production identity integration and an explicit release decision.
