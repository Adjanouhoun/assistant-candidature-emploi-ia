-- Copie d'initialisation de db/migrations/001_initial.sql pour un volume neuf.
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.sync_runs (
    id varchar(36) PRIMARY KEY,
    provider varchar(80) NOT NULL,
    status varchar(24) NOT NULL,
    started_at timestamptz NOT NULL,
    completed_at timestamptz,
    offers_seen integer NOT NULL DEFAULT 0,
    segments_expected integer NOT NULL DEFAULT 0,
    segments_completed integer NOT NULL DEFAULT 0,
    error_summary text
);
CREATE INDEX IF NOT EXISTS ix_sync_runs_provider ON app.sync_runs(provider);
CREATE INDEX IF NOT EXISTS ix_sync_runs_status ON app.sync_runs(status);

CREATE TABLE IF NOT EXISTS app.job_offers (
    id varchar(36) PRIMARY KEY,
    provider varchar(80) NOT NULL,
    external_id varchar(160) NOT NULL,
    title text NOT NULL,
    location_label text NOT NULL DEFAULT '',
    contract_type varchar(80) NOT NULL DEFAULT '',
    is_alternance boolean NOT NULL DEFAULT false,
    payload jsonb NOT NULL,
    source_reference varchar(255) NOT NULL,
    first_seen_at timestamptz NOT NULL,
    last_seen_at timestamptz NOT NULL,
    last_seen_run_id varchar(36) NOT NULL REFERENCES app.sync_runs(id),
    CONSTRAINT uq_job_offers_provider_external_id UNIQUE(provider, external_id)
);

CREATE TABLE IF NOT EXISTS app.source_settings (
    provider VARCHAR(80) PRIMARY KEY,
    is_visible BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app.application_events (
    id varchar(36) PRIMARY KEY,
    provider varchar(80) NOT NULL,
    offer_external_id varchar(160) NOT NULL,
    status varchar(24) NOT NULL,
    occurred_at timestamptz NOT NULL,
    transmission_id varchar(160),
    error_summary varchar(160)
);
CREATE INDEX IF NOT EXISTS ix_application_events_provider ON app.application_events(provider);
CREATE INDEX IF NOT EXISTS ix_application_events_offer ON app.application_events(offer_external_id);
CREATE INDEX IF NOT EXISTS ix_application_events_occurred_at ON app.application_events(occurred_at DESC);
CREATE INDEX IF NOT EXISTS ix_job_offers_provider ON app.job_offers(provider);
CREATE INDEX IF NOT EXISTS ix_job_offers_last_seen_run ON app.job_offers(last_seen_run_id);
