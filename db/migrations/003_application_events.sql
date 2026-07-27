-- Sprint 7 : conservation exclusive des métadonnées de candidature.
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
