-- PHLIS — Experiment Analysis Queries

-- Experiment group sizes
SELECT
    'timer' AS experiment,
    timer_experiment AS variant,
    COUNT(*) AS users,
    ROUND(AVG(quiz_pass_rate), 3) AS avg_pass_rate,
    ROUND(AVG(total_sessions), 1) AS avg_sessions
FROM users GROUP BY timer_experiment
UNION ALL
SELECT
    'questions' AS experiment,
    question_experiment AS variant,
    COUNT(*) AS users,
    ROUND(AVG(quiz_pass_rate), 3) AS avg_pass_rate,
    ROUND(AVG(total_sessions), 1) AS avg_sessions
FROM users GROUP BY question_experiment
UNION ALL
SELECT
    'notification' AS experiment,
    notification_experiment AS variant,
    COUNT(*) AS users,
    ROUND(AVG(quiz_pass_rate), 3) AS avg_pass_rate,
    ROUND(AVG(total_sessions), 1) AS avg_sessions
FROM users GROUP BY notification_experiment;
