-- PHLIS — Retention Queries

-- Cohort retention summary
SELECT
    cohort_week,
    cohort_size,
    days_since_signup,
    retained_users,
    ROUND(retention_rate * 100, 1) AS retention_pct
FROM cohort_retention
ORDER BY cohort_week, days_since_signup;

-- Average retention by day
SELECT
    days_since_signup,
    ROUND(AVG(retention_rate) * 100, 1) AS avg_retention_pct,
    SUM(cohort_size) AS total_users
FROM cohort_retention
GROUP BY days_since_signup
ORDER BY days_since_signup;
