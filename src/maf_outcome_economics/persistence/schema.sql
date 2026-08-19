PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS outcome_contracts (
    id TEXT PRIMARY KEY,
    variant TEXT NOT NULL,
    status TEXT NOT NULL,
    payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    gold_category TEXT NOT NULL,
    gold_priority TEXT NOT NULL,
    gold_resolver_group TEXT NOT NULL,
    payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL REFERENCES tickets(id),
    business_task_id TEXT,
    variant TEXT NOT NULL,
    trace_id TEXT,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    triage_payload TEXT,
    review_payload TEXT
);

CREATE TABLE IF NOT EXISTS telemetry_spans (
    id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES runs(id),
    trace_id TEXT NOT NULL,
    span_id TEXT NOT NULL,
    parent_span_id TEXT,
    name TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    status_code TEXT NOT NULL,
    status_description TEXT,
    attributes_json TEXT NOT NULL,
    UNIQUE (trace_id, span_id)
);

CREATE TABLE IF NOT EXISTS model_usage (
    id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES runs(id),
    trace_id TEXT NOT NULL,
    span_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    request_model TEXT,
    response_model TEXT,
    operation_name TEXT NOT NULL,
    agent_id TEXT,
    agent_name TEXT,
    workflow_id TEXT,
    session_id TEXT,
    executor_id TEXT,
    message_source TEXT,
    message_target TEXT,
    error_type TEXT,
    input_tokens INTEGER NOT NULL CHECK (input_tokens >= 0),
    output_tokens INTEGER NOT NULL CHECK (output_tokens >= 0),
    recorded_at TEXT NOT NULL,
    UNIQUE (trace_id, span_id)
);

CREATE TABLE IF NOT EXISTS pricing (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    effective_at TEXT NOT NULL,
    illustrative INTEGER NOT NULL CHECK (illustrative = 1),
    payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS verifications (
    id TEXT PRIMARY KEY,
    contract_id TEXT NOT NULL REFERENCES outcome_contracts(id),
    run_id TEXT REFERENCES runs(id),
    passed INTEGER NOT NULL CHECK (passed IN (0, 1)),
    payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS governance_decisions (
    id TEXT PRIMARY KEY,
    contract_id TEXT NOT NULL REFERENCES outcome_contracts(id),
    action TEXT NOT NULL,
    payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assessments (
    outcome_name TEXT PRIMARY KEY,
    payload TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_runs_ticket_id ON runs(ticket_id);
CREATE INDEX IF NOT EXISTS idx_spans_run_id ON telemetry_spans(run_id);
CREATE INDEX IF NOT EXISTS idx_usage_run_id ON model_usage(run_id);
CREATE INDEX IF NOT EXISTS idx_pricing_model ON pricing(provider, model, effective_at);
CREATE INDEX IF NOT EXISTS idx_verifications_contract_id ON verifications(contract_id);
CREATE INDEX IF NOT EXISTS idx_governance_contract_id ON governance_decisions(contract_id);