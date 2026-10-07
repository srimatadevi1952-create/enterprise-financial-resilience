# M29 — Invitation-Only Authentication Boundary

## Delivered in this increment

The console now has a dedicated editorial-theme sign-in screen before any enterprise dashboard or API can be reached. An invited user enters an email address and a six-digit, single-use code. Successful verification creates an HTTP-only, SameSite Strict session cookie; no browser-supplied role header is trusted.

Four governed roles are defined: Viewer, Simulation Analyst, Consultant and Client Approver. The authenticated identity supplies the server-side scopes used by simulation and operational-assurance services. The previous development mechanism that allowed JavaScript to select a principal with `X-EFR-Principal` has been removed from the active console.

The authentication service enforces a ten-minute code lifetime, five verification attempts, eight-hour absolute session lifetime, thirty-minute inactivity timeout, user access expiry, logout revocation and non-enumerating responses for unknown email addresses. Security responses add no-store caching, content-type protection, a referrer policy and restrictive browser permissions.

Local development exposes the issued code on the sign-in screen so UAT can proceed without an email provider. The development identities use the reserved `.test` domain. The development repository is in memory and the service explicitly refuses to use it when the environment is not `development`.

## Remaining hosted-UAT gate

Before the Vercel preview is released externally, M29 still requires a durable Neon-backed user, challenge, session and authentication-audit repository; transactional email delivery; hosted-environment secrets; durable simulation sessions; and end-to-end validation through the protected Vercel preview. No production or client data is authorised by this increment.
