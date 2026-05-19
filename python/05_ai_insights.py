#!/usr/bin/env python3
"""
PHLIS — AI Insights Generator
Generates natural-language, data-backed insights from analytics results.
"""

import os, json, sqlite3
import numpy as np
import pandas as pd

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
DB_PATH = os.path.join(BASE_DIR, 'data', 'phlis.db')

def get_conn():
    return sqlite3.connect(DB_PATH)

def generate_engagement_insights(conn):
    """Insights about user engagement patterns."""
    insights = []
    users = pd.read_sql("SELECT * FROM users", conn)

    # Time vs pass rate correlation
    low_time = users[users['avg_session_duration_sec'] < 180]
    high_time = users[users['avg_session_duration_sec'] >= 180]
    if len(low_time) > 0 and len(high_time) > 0:
        low_pass = low_time[low_time['quiz_attempts'] > 0]['quiz_pass_rate'].mean()
        high_pass = high_time[high_time['quiz_attempts'] > 0]['quiz_pass_rate'].mean()
        low_fail = 1 - low_pass if not np.isnan(low_pass) else 0
        insights.append({
            'category': 'engagement', 'severity': 'critical',
            'title': 'Low study time → high failure rate',
            'description': f'Users spending <3 minutes have {low_fail:.0%} failure rate vs {1-high_pass:.0%} for users spending more time.',
            'metric_value': round(low_fail, 3), 'benchmark_value': round(1 - high_pass, 3),
            'impact_score': 0.9,
        })

    # PDF skip correlation
    pdf_viewers = users[users['funnel_max_stage'] >= 3]
    pdf_skippers = users[(users['funnel_max_stage'] >= 2) & (users['funnel_max_stage'] < 3)]
    if len(pdf_viewers) > 0 and len(pdf_skippers) > 0:
        viewer_pass = pdf_viewers[pdf_viewers['quiz_attempts'] > 0]['quiz_pass_rate'].mean()
        skipper_pass = pdf_skippers[pdf_skippers['quiz_attempts'] > 0]['quiz_pass_rate'].mean()
        if not np.isnan(viewer_pass) and not np.isnan(skipper_pass) and viewer_pass > skipper_pass:
            ratio = viewer_pass / skipper_pass if skipper_pass > 0 else 999
            insights.append({
                'category': 'engagement', 'severity': 'warning',
                'title': 'PDF skippers fail significantly more',
                'description': f'Users who view PDFs pass quizzes at {viewer_pass:.0%} vs {skipper_pass:.0%} for those who skip. That\'s {ratio:.1f}x better.',
                'metric_value': round(viewer_pass, 3), 'benchmark_value': round(skipper_pass, 3),
                'impact_score': 0.8,
            })

    # Segment engagement gaps
    if 'user_segment' in users.columns:
        seg_stats = users.groupby('user_segment').agg(
            avg_sessions=('total_sessions', 'mean'),
            avg_pass=('quiz_pass_rate', 'mean'),
        )
        if 'At-Risk User' in seg_stats.index and 'Power User' in seg_stats.index:
            gap = seg_stats.loc['Power User', 'avg_sessions'] - seg_stats.loc['At-Risk User', 'avg_sessions']
            insights.append({
                'category': 'engagement', 'severity': 'warning',
                'title': 'Massive engagement gap between segments',
                'description': f'Power users average {seg_stats.loc["Power User", "avg_sessions"]:.0f} sessions vs {seg_stats.loc["At-Risk User", "avg_sessions"]:.0f} for at-risk users — a {gap:.0f} session gap.',
                'metric_value': round(seg_stats.loc['At-Risk User', 'avg_sessions'], 1),
                'benchmark_value': round(seg_stats.loc['Power User', 'avg_sessions'], 1),
                'impact_score': 0.75,
            })

    return insights

def generate_professor_insights(conn):
    """Insights about professor approval patterns."""
    insights = []
    query = """SELECT metadata, event_type FROM event_logs
               WHERE event_type IN ('approved', 'rejected') AND metadata IS NOT NULL"""
    df = pd.read_sql(query, conn)
    records = []
    for _, row in df.iterrows():
        try:
            meta = json.loads(row['metadata'])
            records.append({'professor': meta.get('professor'), 'approved': row['event_type'] == 'approved'})
        except:
            pass
    if not records:
        return insights

    pdf = pd.DataFrame(records)
    stats = pdf.groupby('professor')['approved'].agg(['mean', 'count']).reset_index()
    stats.columns = ['professor', 'approval_rate', 'total_reviews']
    avg_rate = stats['approval_rate'].mean()

    # Find outlier professors
    for _, prof in stats.iterrows():
        if prof['approval_rate'] < avg_rate * 0.75 and prof['total_reviews'] > 20:
            ratio = avg_rate / prof['approval_rate'] if prof['approval_rate'] > 0 else 999
            insights.append({
                'category': 'quality', 'severity': 'critical',
                'title': f'{prof["professor"]} rejects {ratio:.1f}x more than average',
                'description': f'{prof["professor"]} has {prof["approval_rate"]:.0%} approval rate vs {avg_rate:.0%} average ({int(prof["total_reviews"])} reviews). This is a potential bottleneck.',
                'metric_value': round(prof['approval_rate'], 3),
                'benchmark_value': round(avg_rate, 3),
                'impact_score': 0.85,
            })

    return insights

def generate_funnel_insights(conn):
    """Insights about funnel drop-offs."""
    insights = []
    results_path = os.path.join(BASE_DIR, 'data', 'processed', 'analytics_results.json')
    if not os.path.exists(results_path):
        return insights

    with open(results_path) as f:
        analytics = json.load(f)

    funnel = analytics.get('funnel', [])
    # Find biggest drop-off
    max_drop = max(funnel, key=lambda x: x.get('dropoff_rate', 0))
    if max_drop['dropoff_rate'] > 0.15:
        insights.append({
            'category': 'funnel', 'severity': 'critical',
            'title': f'Biggest drop-off at {max_drop["stage"].replace("_", " ").title()}',
            'description': f'{max_drop["dropoff_rate"]:.0%} of users drop off at the {max_drop["stage"].replace("_", " ")} stage. This is the #1 conversion bottleneck.',
            'metric_value': round(max_drop['dropoff_rate'], 3),
            'benchmark_value': 0.15,
            'impact_score': 0.95,
        })

    return insights

def generate_retention_insights(conn):
    """Insights about retention patterns."""
    insights = []
    ret = pd.read_sql("SELECT * FROM cohort_retention", conn)
    if len(ret) == 0:
        return insights

    d1 = ret[ret['days_since_signup'] == 1]['retention_rate'].mean()
    d7 = ret[ret['days_since_signup'] == 7]['retention_rate'].mean()
    d30 = ret[ret['days_since_signup'] == 30]['retention_rate'].mean()

    if d1 > 0 and d7 > 0:
        d1_to_d7_drop = d1 - d7
        insights.append({
            'category': 'retention', 'severity': 'warning' if d1_to_d7_drop > 0.2 else 'info',
            'title': f'D1→D7 retention drops {d1_to_d7_drop:.0%}',
            'description': f'Day 1 retention is {d1:.0%} but drops to {d7:.0%} by Day 7 — a {d1_to_d7_drop:.0%} loss. Early engagement is critical.',
            'metric_value': round(d7, 3),
            'benchmark_value': round(d1, 3),
            'impact_score': 0.85,
        })

    return insights

def main():
    print("=" * 70)
    print("PHLIS — AI Insights Generator")
    print("=" * 70)
    conn = get_conn()

    all_insights = []
    all_insights.extend(generate_engagement_insights(conn))
    all_insights.extend(generate_professor_insights(conn))
    all_insights.extend(generate_funnel_insights(conn))
    all_insights.extend(generate_retention_insights(conn))

    # Sort by impact
    all_insights.sort(key=lambda x: x.get('impact_score', 0), reverse=True)

    # Add IDs
    for i, insight in enumerate(all_insights):
        insight['insight_id'] = f'insight_{i+1:03d}'

    print(f"\n🧠 Generated {len(all_insights)} insights:")
    for ins in all_insights:
        icon = {'critical': '🔴', 'warning': '🟡', 'info': '🔵'}.get(ins['severity'], '⚪')
        print(f"   {icon} [{ins['severity'].upper()}] {ins['title']}")

    # Save
    out_path = os.path.join(BASE_DIR, 'data', 'processed', 'ai_insights.json')
    with open(out_path, 'w') as f:
        json.dump(all_insights, f, indent=2)
    print(f"\n💾 Saved to: {out_path}")

    # Also save to DB
    ins_df = pd.DataFrame(all_insights)
    ins_df.to_sql('ai_insights', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()

    print(f"\n{'=' * 70}\n✅ AI Insights complete!\n{'=' * 70}")
    return all_insights

if __name__ == '__main__':
    main()
