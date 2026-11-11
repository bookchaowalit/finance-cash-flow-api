-- SPEC-006 (2026-11-11): cross-service references between the finance cells (cash-flow).
-- Append-only: do not edit once applied.

-- The relay sends a record's events in insert order (the row lock makes it the commit order).
ALTER TABLE cash_flow.outbox ADD COLUMN seq bigint GENERATED ALWAYS AS IDENTITY;
DROP INDEX cash_flow.outbox_unrelayed;
CREATE INDEX outbox_unrelayed ON cash_flow.outbox (seq) WHERE relayed_at IS NULL;

-- SPEC-006: cross-service references, fed by finance.events.v1.
CREATE TABLE cash_flow.ref_targets (
    workspace_id   uuid NOT NULL,
    target         text NOT NULL,
    record_id      bigint NOT NULL,
    status         text,
    deleted        boolean NOT NULL DEFAULT false,
    record_version bigint NOT NULL DEFAULT 0,
    event_seq      bigint NOT NULL DEFAULT 0,
    updated_at     timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, target, record_id)
);
CREATE TABLE cash_flow.ref_sources (
    workspace_id    uuid NOT NULL,
    source          text NOT NULL,
    source_id       bigint NOT NULL,
    field           text NOT NULL,
    target_resource text NOT NULL,
    target_id       bigint,
    deleted         boolean NOT NULL DEFAULT false,
    record_version  bigint NOT NULL DEFAULT 0,
    event_seq       bigint NOT NULL DEFAULT 0,
    updated_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, source, source_id, field)
);
CREATE INDEX ref_sources_live ON cash_flow.ref_sources (workspace_id, target_resource, target_id) WHERE NOT deleted;
CREATE TABLE cash_flow.ref_offsets (
    topic       text NOT NULL,
    partition   integer NOT NULL,
    next_offset bigint NOT NULL,
    PRIMARY KEY (topic, partition)
);
ALTER TABLE cash_flow.ref_targets ENABLE ROW LEVEL SECURITY;
ALTER TABLE cash_flow.ref_targets FORCE ROW LEVEL SECURITY;
CREATE POLICY workspace_isolation ON cash_flow.ref_targets USING (workspace_id = cash_flow.current_workspace());
CREATE POLICY publisher_sync ON cash_flow.ref_targets TO cash_flow_publisher USING (true) WITH CHECK (true);
GRANT SELECT ON cash_flow.ref_targets TO cash_flow_api;
GRANT SELECT, INSERT, UPDATE ON cash_flow.ref_targets TO cash_flow_publisher;
ALTER TABLE cash_flow.ref_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE cash_flow.ref_sources FORCE ROW LEVEL SECURITY;
CREATE POLICY workspace_isolation ON cash_flow.ref_sources USING (workspace_id = cash_flow.current_workspace());
CREATE POLICY publisher_sync ON cash_flow.ref_sources TO cash_flow_publisher USING (true) WITH CHECK (true);
GRANT SELECT ON cash_flow.ref_sources TO cash_flow_api;
GRANT SELECT, INSERT, UPDATE ON cash_flow.ref_sources TO cash_flow_publisher;
GRANT SELECT, INSERT, UPDATE ON cash_flow.ref_offsets TO cash_flow_publisher;

-- Rows written before SPEC-005 announce themselves once, so other cells learn their ids.
ALTER TABLE cash_flow.outbox NO FORCE ROW LEVEL SECURITY;
ALTER TABLE cash_flow.cashflow_plans NO FORCE ROW LEVEL SECURITY;
INSERT INTO cash_flow.outbox (workspace_id, type, subject, classification, payload, correlation_id) SELECT workspace_id, 'cash-flow.cashflow-plan.snapshot', 'empire:cash-flow:cashflow-plan:' || id, 'confidential', jsonb_build_object('scope', scope, 'period_start', period_start, 'period_end', period_end, 'currency', currency, 'status', status, 'version', version, 'deleted', false), 'spec-006-snapshot' FROM cash_flow.cashflow_plans ORDER BY id;
ALTER TABLE cash_flow.cashflow_plans FORCE ROW LEVEL SECURITY;
ALTER TABLE cash_flow.outbox FORCE ROW LEVEL SECURITY;
