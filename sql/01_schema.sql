-- =============================================================================
-- PHLIS — Data Warehouse Schema
-- =============================================================================
-- All tables derived from the event_logs source of truth.
-- Compatible with SQLite and PostgreSQL.
-- =============================================================================

-- ─── Raw Event Stream ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS event_logs (
    event_id        TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL,
    event_type      TEXT NOT NULL CHECK(event_type IN (
        'app_open', 'absence_declared', 'pdf_viewed',
        'quiz_started', 'quiz_submitted', 'quiz_passed', 'quiz_failed',
        'approved', 'rejected'
    )),
    timestamp       TIMESTAMP NOT NULL,
    session_id      TEXT,
    metadata        TEXT  -- JSON string
);

-- ─── User Profiles (derived) ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id              TEXT PRIMARY KEY,
    archetype            TEXT,
    signup_date          DATE,
    assigned_professor   TEXT,
    timer_experiment     TEXT,
    question_experiment  TEXT,
    notification_experiment TEXT,
    total_sessions       INTEGER DEFAULT 0,
    total_events         INTEGER DEFAULT 0,
    last_active_date     DATE,
    days_active          INTEGER DEFAULT 0,
    avg_session_duration_sec REAL DEFAULT 0,
    funnel_max_stage     INTEGER DEFAULT 0,
    quiz_attempts        INTEGER DEFAULT 0,
    quiz_pass_rate       REAL DEFAULT 0,
    churn_risk_score     REAL DEFAULT 0,
    user_segment         TEXT  -- derived from ML clustering
);

-- ─── Sessions (derived from event grouping) ──────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    session_id       TEXT PRIMARY KEY,
    user_id          TEXT NOT NULL,
    session_date     DATE NOT NULL,
    start_time       TIMESTAMP NOT NULL,
    end_time         TIMESTAMP,
    duration_sec     REAL,
    event_count      INTEGER DEFAULT 0,
    max_funnel_stage INTEGER DEFAULT 0,
    quiz_attempted   BOOLEAN DEFAULT 0,
    quiz_passed      BOOLEAN DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- ─── Daily Metrics (pre-aggregated) ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS daily_metrics (
    metric_date         DATE PRIMARY KEY,
    dau                 INTEGER,   -- daily active users
    new_users           INTEGER,
    total_sessions      INTEGER,
    total_events        INTEGER,
    avg_session_duration REAL,
    funnel_app_open     INTEGER,
    funnel_absence      INTEGER,
    funnel_pdf          INTEGER,
    funnel_quiz_start   INTEGER,
    funnel_quiz_submit  INTEGER,
    funnel_quiz_pass    INTEGER,
    funnel_approved     INTEGER,
    quiz_pass_rate      REAL,
    approval_rate       REAL,
    avg_quiz_score      REAL,
    product_health_score REAL
);

-- ─── Funnel Stages ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS funnel_stages (
    user_id       TEXT,
    session_id    TEXT,
    session_date  DATE,
    stage_name    TEXT,
    stage_order   INTEGER,
    reached       BOOLEAN DEFAULT 0,
    timestamp     TIMESTAMP,
    PRIMARY KEY (user_id, session_id, stage_name)
);

-- ─── Cohort Retention ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cohort_retention (
    cohort_week      TEXT,    -- e.g. '2025-W01'
    cohort_size      INTEGER,
    days_since_signup INTEGER,
    retained_users   INTEGER,
    retention_rate   REAL
);

-- ─── Experiment Definitions ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id   TEXT PRIMARY KEY,
    experiment_name TEXT NOT NULL,
    variant_a       TEXT NOT NULL,
    variant_b       TEXT NOT NULL,
    start_date      DATE,
    end_date        DATE,
    status          TEXT DEFAULT 'running'
);

-- ─── Experiment Results ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS experiment_results (
    experiment_id    TEXT,
    variant          TEXT,
    metric_name      TEXT,
    metric_value     REAL,
    sample_size      INTEGER,
    p_value          REAL,
    is_significant   BOOLEAN,
    PRIMARY KEY (experiment_id, variant, metric_name)
);

-- ─── AI Insights ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ai_insights (
    insight_id      TEXT PRIMARY KEY,
    category        TEXT,     -- engagement, churn, quality, experiment
    severity        TEXT,     -- critical, warning, info
    title           TEXT,
    description     TEXT,
    metric_value    REAL,
    benchmark_value REAL,
    impact_score    REAL,
    generated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── Action Recommendations ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS action_recommendations (
    action_id       TEXT PRIMARY KEY,
    priority        INTEGER,
    category        TEXT,
    action_title    TEXT,
    description     TEXT,
    expected_impact TEXT,
    effort_level    TEXT,     -- low, medium, high
    status          TEXT DEFAULT 'pending'
);

-- ─── Alerts ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    alert_id        TEXT PRIMARY KEY,
    alert_type      TEXT,     -- anomaly, threshold, trend
    severity        TEXT,     -- critical, warning, info
    title           TEXT,
    description     TEXT,
    metric_name     TEXT,
    current_value   REAL,
    threshold_value REAL,
    triggered_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged    BOOLEAN DEFAULT 0
);

-- ─── Indexes for Performance ─────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_events_user ON event_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON event_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON event_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_session ON event_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(session_date);
CREATE INDEX IF NOT EXISTS idx_funnel_user ON funnel_stages(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_metrics(metric_date);
