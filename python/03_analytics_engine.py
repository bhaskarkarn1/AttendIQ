#!/usr/bin/env python3
"""
PHLIS — Analytics Engine
Computes all KPIs, funnel metrics, and the composite Product Health Score.
"""

import os, json, sqlite3
import numpy as np
import pandas as pd

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
DB_PATH = os.path.join(BASE_DIR, 'data', 'phlis.db')

# Health Score weights
HEALTH_WEIGHTS = {
    'retention_d7': 0.25,
    'quiz_pass_rate': 0.20,
    'funnel_conversion': 0.20,
    'engagement_score': 0.20,
    'approval_rate': 0.15,
}

def get_conn():
    return sqlite3.connect(DB_PATH)

def compute_funnel_metrics(conn):
    """Compute overall funnel conversion rates."""
    print("\n📊 Computing funnel metrics...")
    df = pd.read_sql("SELECT * FROM daily_metrics ORDER BY metric_date", conn)
    totals = {
        'app_open': df['funnel_app_open'].sum(),
        'absence_declared': df['funnel_absence'].sum(),
        'pdf_viewed': df['funnel_pdf'].sum(),
        'quiz_started': df['funnel_quiz_start'].sum(),
        'quiz_submitted': df['funnel_quiz_submit'].sum(),
        'quiz_passed': df['funnel_quiz_pass'].sum(),
        'approved': df['funnel_approved'].sum(),
    }

    stages = list(totals.keys())
    funnel = []
    for i, stage in enumerate(stages):
        count = totals[stage]
        prev_count = totals[stages[i-1]] if i > 0 else count
        conversion = count / prev_count if prev_count > 0 else 0
        dropoff = 1 - conversion if i > 0 else 0
        overall = count / totals['app_open'] if totals['app_open'] > 0 else 0
        funnel.append({
            'stage': stage, 'count': int(count), 'stage_order': i + 1,
            'conversion_rate': round(conversion, 4),
            'dropoff_rate': round(dropoff, 4),
            'overall_conversion': round(overall, 4),
        })
        print(f"   {stage}: {int(count):,} (conv: {conversion:.1%}, dropoff: {dropoff:.1%})")

    return funnel, df

def compute_engagement_metrics(conn):
    """Compute DAU, WAU, MAU trends."""
    print("\n📈 Computing engagement metrics...")
    events = pd.read_sql("SELECT user_id, timestamp FROM event_logs", conn, parse_dates=['timestamp'])
    events['date'] = events['timestamp'].dt.date

    # DAU
    dau = events.groupby('date')['user_id'].nunique().reset_index()
    dau.columns = ['date', 'dau']

    # WAU (rolling 7-day)
    all_dates = pd.date_range(dau['date'].min(), dau['date'].max())
    wau_records = []
    for d in all_dates:
        week_start = d - pd.Timedelta(days=6)
        week_events = events[(events['timestamp'].dt.date >= week_start.date()) &
                             (events['timestamp'].dt.date <= d.date())]
        wau_records.append({'date': d.date(), 'wau': week_events['user_id'].nunique()})
    wau = pd.DataFrame(wau_records)

    avg_dau = dau['dau'].mean()
    avg_wau = wau['wau'].mean()
    stickiness = avg_dau / avg_wau if avg_wau > 0 else 0

    print(f"   Avg DAU: {avg_dau:.0f}")
    print(f"   Avg WAU: {avg_wau:.0f}")
    print(f"   Stickiness (DAU/WAU): {stickiness:.2%}")

    return {'dau': dau.to_dict('records'), 'wau': wau.to_dict('records'),
            'avg_dau': round(avg_dau), 'avg_wau': round(avg_wau),
            'stickiness': round(stickiness, 4)}

def compute_retention_summary(conn):
    """Summarize retention metrics."""
    print("\n🔄 Computing retention summary...")
    ret = pd.read_sql("SELECT * FROM cohort_retention", conn)
    summary = ret.groupby('days_since_signup')['retention_rate'].mean().to_dict()
    for day, rate in sorted(summary.items()):
        print(f"   D{day} Retention: {rate:.1%}")
    return {f"d{int(k)}": round(v, 4) for k, v in summary.items()}

def compute_product_health_score(conn, funnel_data, retention_summary, engagement):
    """Compute composite Product Health Score (0-100)."""
    print("\n🏥 Computing Product Health Score...")

    # Retention D7 normalized (benchmark: 30% is good)
    d7_ret = retention_summary.get('d7', 0)
    retention_score = min(d7_ret / 0.30, 1.0) * 100

    # Quiz pass rate (benchmark: 70% is good)
    users = pd.read_sql("SELECT quiz_pass_rate FROM users WHERE quiz_attempts > 0", conn)
    avg_pass = users['quiz_pass_rate'].mean()
    pass_score = min(avg_pass / 0.70, 1.0) * 100

    # Funnel conversion (app_open → approved, benchmark: 20% is good)
    overall_conv = funnel_data[-1]['overall_conversion'] if funnel_data else 0
    funnel_score = min(overall_conv / 0.20, 1.0) * 100

    # Engagement (stickiness, benchmark: 40% is good)
    eng_score = min(engagement['stickiness'] / 0.40, 1.0) * 100

    # Approval rate (benchmark: 80% is good)
    daily = pd.read_sql("SELECT approval_rate FROM daily_metrics WHERE approval_rate > 0", conn)
    avg_approval = daily['approval_rate'].mean()
    approval_score = min(avg_approval / 0.80, 1.0) * 100

    # Weighted composite
    health = (
        HEALTH_WEIGHTS['retention_d7'] * retention_score +
        HEALTH_WEIGHTS['quiz_pass_rate'] * pass_score +
        HEALTH_WEIGHTS['funnel_conversion'] * funnel_score +
        HEALTH_WEIGHTS['engagement_score'] * eng_score +
        HEALTH_WEIGHTS['approval_rate'] * approval_score
    )
    health = round(min(health, 100), 1)

    components = {
        'retention': round(retention_score, 1),
        'quiz_pass_rate': round(pass_score, 1),
        'funnel_conversion': round(funnel_score, 1),
        'engagement': round(eng_score, 1),
        'approval_rate': round(approval_score, 1),
    }
    print(f"   Components: {json.dumps(components, indent=2)}")
    print(f"   ⭐ Product Health Score: {health}/100")

    return health, components

def compute_professor_stats(conn):
    """Compute per-professor approval rates."""
    print("\n👨‍🏫 Computing professor stats...")
    query = """
        SELECT metadata, event_type FROM event_logs
        WHERE event_type IN ('approved', 'rejected') AND metadata IS NOT NULL
    """
    df = pd.read_sql(query, conn)
    records = []
    for _, row in df.iterrows():
        try:
            meta = json.loads(row['metadata'])
            records.append({'professor': meta.get('professor'), 'event_type': row['event_type']})
        except:
            pass
    pdf = pd.DataFrame(records)
    if len(pdf) == 0:
        return []
    stats = pdf.groupby('professor').apply(lambda g: pd.Series({
        'total': len(g),
        'approved': (g['event_type'] == 'approved').sum(),
        'rejected': (g['event_type'] == 'rejected').sum(),
        'approval_rate': (g['event_type'] == 'approved').mean(),
    })).reset_index()
    avg_rate = stats['approval_rate'].mean()
    stats['deviation'] = stats['approval_rate'] - avg_rate
    print(f"   Avg approval rate: {avg_rate:.1%}")
    print(f"   Strictest: {stats.loc[stats['approval_rate'].idxmin(), 'professor']} ({stats['approval_rate'].min():.1%})")
    return stats.to_dict('records')

def main():
    print("=" * 70)
    print("PHLIS — Analytics Engine")
    print("=" * 70)
    conn = get_conn()

    funnel_data, daily_df = compute_funnel_metrics(conn)
    engagement = compute_engagement_metrics(conn)
    retention = compute_retention_summary(conn)
    health_score, health_components = compute_product_health_score(conn, funnel_data, retention, engagement)
    professor_stats = compute_professor_stats(conn)

    # Save analytics results
    results = {
        'funnel': funnel_data,
        'engagement': engagement,
        'retention': retention,
        'health_score': health_score,
        'health_components': health_components,
        'professor_stats': professor_stats,
    }

    out_path = os.path.join(BASE_DIR, 'data', 'processed', 'analytics_results.json')
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Saved analytics results to: {out_path}")

    conn.close()
    print(f"\n{'=' * 70}\n✅ Analytics engine complete!\n{'=' * 70}")
    return results

if __name__ == '__main__':
    main()
