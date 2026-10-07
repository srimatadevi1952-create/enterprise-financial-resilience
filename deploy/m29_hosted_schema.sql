CREATE SCHEMA IF NOT EXISTS efr_uat;

CREATE TABLE IF NOT EXISTS efr_uat.auth_users (
    actor_id text PRIMARY KEY,
    display_name text NOT NULL,
    email text NOT NULL UNIQUE CHECK (email = lower(email)),
    role text NOT NULL CHECK (role IN ('viewer','simulation_analyst','consultant','client_approver')),
    access_expires_at timestamptz NOT NULL,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS efr_uat.login_challenges (
    email text PRIMARY KEY REFERENCES efr_uat.auth_users(email) ON DELETE CASCADE,
    code_digest text NOT NULL,
    expires_at timestamptz NOT NULL,
    attempts_remaining integer NOT NULL CHECK (attempts_remaining BETWEEN 0 AND 5),
    consumed boolean NOT NULL DEFAULT false,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS efr_uat.web_sessions (
    token_digest text PRIMARY KEY,
    email text NOT NULL REFERENCES efr_uat.auth_users(email),
    created_at timestamptz NOT NULL,
    last_seen_at timestamptz NOT NULL,
    expires_at timestamptz NOT NULL,
    revoked boolean NOT NULL DEFAULT false
);
CREATE INDEX IF NOT EXISTS web_sessions_email_idx ON efr_uat.web_sessions(email);

CREATE TABLE IF NOT EXISTS efr_uat.auth_audit_events (
    event_id text PRIMARY KEY,
    event text NOT NULL,
    email_digest text NOT NULL,
    remote_address text NOT NULL,
    recorded_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS efr_uat.simulation_sessions (
    session_id text PRIMARY KEY,
    owner_id text NOT NULL REFERENCES efr_uat.auth_users(actor_id),
    created_at timestamptz NOT NULL,
    baseline_hash text NOT NULL,
    state jsonb NOT NULL,
    collaborators jsonb NOT NULL DEFAULT '{}'::jsonb,
    audit jsonb NOT NULL DEFAULT '[]'::jsonb,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS efr_uat.collaboration_invitations (
    token_digest text PRIMARY KEY,
    session_id text NOT NULL REFERENCES efr_uat.simulation_sessions(session_id) ON DELETE CASCADE,
    actor_id text NOT NULL REFERENCES efr_uat.auth_users(actor_id),
    role text NOT NULL CHECK (role IN ('viewer','co-analyst','approver','auditor')),
    created_by text NOT NULL REFERENCES efr_uat.auth_users(actor_id),
    created_at timestamptz NOT NULL,
    expires_at timestamptz NOT NULL,
    status text NOT NULL CHECK (status IN ('PENDING','JOINED','REVOKED','EXPIRED'))
);
CREATE INDEX IF NOT EXISTS collaboration_session_idx ON efr_uat.collaboration_invitations(session_id);

CREATE TABLE IF NOT EXISTS efr_uat.assurance_state (
    state_key text PRIMARY KEY,
    decision text NOT NULL CHECK (decision IN ('AWAITING_DECISION','APPROVED','REJECTED','CLARIFICATION_REQUESTED')),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS efr_uat.assurance_events (
    event_id text PRIMARY KEY,
    event_type text NOT NULL CHECK (event_type IN ('VIEW','DECISION')),
    actor_id text NOT NULL REFERENCES efr_uat.auth_users(actor_id),
    payload jsonb NOT NULL,
    recorded_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS assurance_events_actor_idx ON efr_uat.assurance_events(actor_id, recorded_at);
