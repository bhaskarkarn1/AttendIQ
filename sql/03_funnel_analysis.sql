-- PHLIS — Funnel Analysis Queries

-- Overall funnel conversion
SELECT
    event_type,
    COUNT(DISTINCT user_id) AS unique_users,
    COUNT(*) AS total_events
FROM event_logs
WHERE event_type IN ('app_open','absence_declared','pdf_viewed','quiz_started','quiz_submitted','quiz_passed','approved')
GROUP BY event_type
ORDER BY
    CASE event_type
        WHEN 'app_open' THEN 1
        WHEN 'absence_declared' THEN 2
        WHEN 'pdf_viewed' THEN 3
        WHEN 'quiz_started' THEN 4
        WHEN 'quiz_submitted' THEN 5
        WHEN 'quiz_passed' THEN 6
        WHEN 'approved' THEN 7
    END;

-- Daily funnel conversion
SELECT
    DATE(timestamp) AS date,
    SUM(CASE WHEN event_type = 'app_open' THEN 1 ELSE 0 END) AS app_open,
    SUM(CASE WHEN event_type = 'absence_declared' THEN 1 ELSE 0 END) AS absence_declared,
    SUM(CASE WHEN event_type = 'pdf_viewed' THEN 1 ELSE 0 END) AS pdf_viewed,
    SUM(CASE WHEN event_type = 'quiz_started' THEN 1 ELSE 0 END) AS quiz_started,
    SUM(CASE WHEN event_type = 'quiz_submitted' THEN 1 ELSE 0 END) AS quiz_submitted,
    SUM(CASE WHEN event_type = 'quiz_passed' THEN 1 ELSE 0 END) AS quiz_passed,
    SUM(CASE WHEN event_type = 'approved' THEN 1 ELSE 0 END) AS approved
FROM event_logs
GROUP BY DATE(timestamp)
ORDER BY date;

-- Per-session funnel depth
SELECT
    max_funnel_stage,
    COUNT(*) AS session_count,
    ROUND(AVG(duration_sec), 1) AS avg_duration_sec
FROM sessions
GROUP BY max_funnel_stage
ORDER BY max_funnel_stage;
