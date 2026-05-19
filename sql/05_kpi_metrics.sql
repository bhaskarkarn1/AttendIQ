-- PHLIS — KPI Metrics Queries

-- DAU trend
SELECT metric_date, dau, total_sessions, total_events
FROM daily_metrics ORDER BY metric_date;

-- Weekly active users
SELECT
    strftime('%Y-W%W', metric_date) AS week,
    AVG(dau) AS avg_dau,
    SUM(total_sessions) AS total_sessions,
    AVG(quiz_pass_rate) AS avg_pass_rate
FROM daily_metrics
GROUP BY strftime('%Y-W%W', metric_date)
ORDER BY week;

-- User engagement segments
SELECT
    user_segment,
    COUNT(*) AS user_count,
    ROUND(AVG(total_sessions), 1) AS avg_sessions,
    ROUND(AVG(days_active), 1) AS avg_days_active,
    ROUND(AVG(quiz_pass_rate), 3) AS avg_pass_rate,
    ROUND(AVG(avg_session_duration_sec), 1) AS avg_session_sec
FROM users
GROUP BY user_segment
ORDER BY avg_sessions DESC;
