-- PHLIS — Product Health Score Query

-- Component scores for health calculation
SELECT
    'retention_d7' AS component,
    ROUND(AVG(retention_rate), 4) AS value
FROM cohort_retention WHERE days_since_signup = 7

UNION ALL

SELECT
    'quiz_pass_rate' AS component,
    ROUND(AVG(quiz_pass_rate), 4) AS value
FROM users WHERE quiz_attempts > 0

UNION ALL

SELECT
    'avg_approval_rate' AS component,
    ROUND(AVG(approval_rate), 4) AS value
FROM daily_metrics WHERE approval_rate > 0

UNION ALL

SELECT
    'avg_dau' AS component,
    ROUND(AVG(dau), 1) AS value
FROM daily_metrics;
