# M29 — Invitation-Only Authentication Boundary

## Delivered in this increment

The console now has a dedicated editorial-theme sign-in screen before any enterprise dashboard or API can be reached. An invited user enters an email address and a six-digit, single-use code. Successful verification creates an HTTP-only, SameSite Strict session cookie; no browser-supplied role header is trusted.

Four governed roles are defined: Viewer, Simulation Analyst, Consultant and Client Approver. The authenticated identity supplies the server-side scopes used by simulation and operational-assurance services. The previous development mechanism that allowed JavaScript to select a principal with `X-EFR-Principal` has been removed from the active console.

The authentication service enforces a ten-minute code lifetime, five verification attempts, eight-hour absolute session lifetime, thirty-minute inactivity timeout, user access expiry, logout revocation and non-enumerating responses for unknown email addresses. Security responses add no-store caching, content-type protection, a referrer policy and restrictive browser permissions.

Local development exposes the issued code on the sign-in screen so UAT can proceed without an email provider. The development identities use the reserved `.test` domain. The development repository is in memory and the service explicitly refuses to use it when the environment is not `development`.

## Hosted-UAT implementation

The second M29 increment adds a Vercel Python Function entry point and routing configuration; Neon PostgreSQL repositories for users, login challenges, web sessions, authentication audit events, simulation sessions and collaboration invitations; Resend transactional delivery for one-time codes; a public health endpoint; and guarded schema and user-administration scripts. Hosted configuration fails closed if the environment, database, signing secret or email provider is missing. Collaboration tokens are stored as hashes in PostgreSQL.

## Remaining external provisioning gate

The code is deployment-ready, but no Vercel, Neon or Resend resource has been created from this repository yet. The repository owner must authorize the GitHub-to-Vercel connection, select the service plan, provision the Neon and Resend integrations, verify the email sending identity, place secrets in Vercel, apply the isolated UAT schema and identify the first invited tester. A preview deployment must then pass the health, login, role-isolation, simulation-persistence, logout and revocation checks before its link is shared. No production or client data is authorised during this gate.
