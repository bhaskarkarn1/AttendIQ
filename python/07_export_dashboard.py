#!/usr/bin/env python3
"""
PHLIS — Dashboard Data Exporter
Reads all processed results and exports JSON files for the web dashboard.
"""

import os, json, sqlite3
import pandas as pd
import numpy as np

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
DB_PATH = os.path.join(BASE_DIR, 'data', 'phlis.db')
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')
DASHBOARD_DIR = os.path.join(BASE_DIR, 'data', 'dashboard')

def get_conn():
    return sqlite3.connect(DB_PATH)

def export_health_score():
    with open(os.path.join(PROCESSED_DIR, 'analytics_results.json')) as f:
        data = json.load(f)
    out = {
        'score': data['health_score'],
        'components': data['health_components'],
        'trend': [],  # Would be computed from historical
    }
    save('health_score.json', out)

def export_funnel():
    with open(os.path.join(PROCESSED_DIR, 'analytics_results.json')) as f:
        data = json.load(f)
    save('funnel_data.json', data['funnel'])

def export_engagement():
    with open(os.path.join(PROCESSED_DIR, 'analytics_results.json')) as f:
        data = json.load(f)
    eng = data['engagement']
    # Trim to last 30 data points for readability
    dau = eng['dau'][-60:] if len(eng.get('dau', [])) > 60 else eng.get('dau', [])
    wau = eng['wau'][-60:] if len(eng.get('wau', [])) > 60 else eng.get('wau', [])
    save('engagement_data.json', {
        'dau': dau, 'wau': wau,
        'avg_dau': eng['avg_dau'], 'avg_wau': eng['avg_wau'],
        'stickiness': eng['stickiness'],
    })

def export_retention():
    with open(os.path.join(PROCESSED_DIR, 'analytics_results.json')) as f:
        data = json.load(f)
    conn = get_conn()
    ret = pd.read_sql("SELECT * FROM cohort_retention", conn)
    conn.close()
    # Pivot for heatmap
    pivot = ret.pivot_table(index='cohort_week', columns='days_since_signup',
                            values='retention_rate', aggfunc='mean')
    save('retention_data.json', {
        'summary': data['retention'],
        'heatmap': {
            'cohorts': pivot.index.tolist(),
            'days': [int(d) for d in pivot.columns.tolist()],
            'values': [[round(v, 4) if not pd.isna(v) else 0 for v in row] for row in pivot.values],
        }
    })

def export_experiments():
    with open(os.path.join(PROCESSED_DIR, 'decision_results.json')) as f:
        data = json.load(f)
    save('experiment_results.json', data['experiments'])

def export_churn():
    with open(os.path.join(PROCESSED_DIR, 'ml_results.json')) as f:
        data = json.load(f)
    save('churn_predictions.json', data['churn'])

def export_clusters():
    with open(os.path.join(PROCESSED_DIR, 'ml_results.json')) as f:
        data = json.load(f)
    save('cluster_data.json', data['clustering'])

def export_insights():
    with open(os.path.join(PROCESSED_DIR, 'ai_insights.json')) as f:
        data = json.load(f)
    save('ai_insights.json', data)

def export_recommendations():
    with open(os.path.join(PROCESSED_DIR, 'decision_results.json')) as f:
        data = json.load(f)
    save('action_recommendations.json', data['recommendations'])

def export_alerts():
    with open(os.path.join(PROCESSED_DIR, 'decision_results.json')) as f:
        data = json.load(f)
    save('alerts.json', data['alerts'])

def export_professors():
    with open(os.path.join(PROCESSED_DIR, 'analytics_results.json')) as f:
        data = json.load(f)
    save('professor_stats.json', data.get('professor_stats', []))

def export_daily_trends():
    conn = get_conn()
    daily = pd.read_sql("SELECT * FROM daily_metrics ORDER BY metric_date", conn)
    conn.close()
    save('daily_trends.json', daily.to_dict('records'))

def save(filename, data):
    os.makedirs(DASHBOARD_DIR, exist_ok=True)
    path = os.path.join(DASHBOARD_DIR, filename)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"   ✓ {filename}")

def main():
    print("=" * 70)
    print("PHLIS — Dashboard Data Export")
    print("=" * 70)
    print("\n📦 Exporting dashboard JSON files...")

    export_health_score()
    export_funnel()
    export_engagement()
    export_retention()
    export_experiments()
    export_churn()
    export_clusters()
    export_insights()
    export_recommendations()
    export_alerts()
    export_professors()
    export_daily_trends()

    print(f"\n{'=' * 70}\n✅ Dashboard export complete!\n{'=' * 70}")

if __name__ == '__main__':
    main()
