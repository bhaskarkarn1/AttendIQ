#!/usr/bin/env python3
"""
PHLIS — ETL Pipeline
Transforms raw event logs into structured tables and loads to SQLite.
"""

import os, json, sqlite3
import numpy as np
import pandas as pd
from datetime import timedelta

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')
DB_PATH = os.path.join(BASE_DIR, 'data', 'phlis.db')
SQL_DIR = os.path.join(BASE_DIR, 'sql')

FUNNEL_STAGES = [
    ('app_open', 1), ('absence_declared', 2), ('pdf_viewed', 3),
    ('quiz_started', 4), ('quiz_submitted', 5), ('quiz_passed', 6), ('approved', 7),
]

def load_raw_events():
    print("\n📥 Loading raw event logs...")
    df = pd.read_csv(os.path.join(RAW_DIR, 'event_logs.csv'), parse_dates=['timestamp'])
    print(f"   ✓ Loaded {len(df):,} events")
    return df

def deduplicate_events(df):
    before = len(df)
    df = df.drop_duplicates(subset=['user_id', 'event_type', 'timestamp'], keep='first')
    print(f"   ✓ Removed {before - len(df):,} duplicates ({len(df):,} remaining)")
    return df

def derive_sessions(events_df):
    print("\n🔄 Deriving sessions...")
    sessions = events_df.dropna(subset=['session_id']).groupby('session_id').agg(
        user_id=('user_id', 'first'),
        session_date=('timestamp', lambda x: x.min().date()),
        start_time=('timestamp', 'min'),
        end_time=('timestamp', 'max'),
        event_count=('event_id', 'count'),
    ).reset_index()
    sessions['duration_sec'] = (sessions['end_time'] - sessions['start_time']).dt.total_seconds()

    stage_map = {s[0]: s[1] for s in FUNNEL_STAGES}
    se = events_df.dropna(subset=['session_id']).copy()
    se['stage_order'] = se['event_type'].map(stage_map)
    ms = se.groupby('session_id')['stage_order'].max().reset_index()
    ms.columns = ['session_id', 'max_funnel_stage']
    sessions = sessions.merge(ms, on='session_id', how='left')
    sessions['max_funnel_stage'] = sessions['max_funnel_stage'].fillna(0).astype(int)

    qe = se[se['event_type'].isin(['quiz_started', 'quiz_passed'])]
    sessions['quiz_attempted'] = sessions['session_id'].isin(
        qe[qe['event_type'] == 'quiz_started']['session_id'].unique()).astype(int)
    sessions['quiz_passed'] = sessions['session_id'].isin(
        qe[qe['event_type'] == 'quiz_passed']['session_id'].unique()).astype(int)

    print(f"   ✓ Derived {len(sessions):,} sessions")
    return sessions

def derive_users(events_df, users_raw_df, sessions_df):
    print("\n👤 Deriving user profiles...")
    users = users_raw_df[['user_id', 'archetype', 'signup_date', 'assigned_professor',
                           'timer_experiment', 'question_experiment', 'notification_experiment']].copy()

    ue = events_df.groupby('user_id').agg(
        total_events=('event_id', 'count'), last_active_date=('timestamp', 'max')).reset_index()
    ue['last_active_date'] = ue['last_active_date'].dt.date

    us = sessions_df.groupby('user_id').agg(
        total_sessions=('session_id', 'count'),
        avg_session_duration_sec=('duration_sec', 'mean'),
        funnel_max_stage=('max_funnel_stage', 'max')).reset_index()

    da = events_df.groupby('user_id')['timestamp'].apply(lambda x: x.dt.date.nunique()).reset_index()
    da.columns = ['user_id', 'days_active']

    qsub = events_df[events_df['event_type'] == 'quiz_submitted'].groupby('user_id').size().reset_index(name='quiz_attempts')
    qpass = events_df[events_df['event_type'] == 'quiz_passed'].groupby('user_id').size().reset_index(name='quiz_passes')

    for df in [ue, us, da, qsub, qpass]:
        users = users.merge(df, on='user_id', how='left')

    fill_cols = ['total_events', 'total_sessions', 'days_active', 'quiz_attempts', 'quiz_passes',
                 'avg_session_duration_sec', 'funnel_max_stage']
    for col in fill_cols:
        users[col] = users[col].fillna(0)

    users['quiz_pass_rate'] = np.where(users['quiz_attempts'] > 0, users['quiz_passes'] / users['quiz_attempts'], 0)
    users = users.drop(columns=['quiz_passes'])
    print(f"   ✓ Enriched {len(users):,} users")
    return users

def compute_daily_metrics(events_df, sessions_df):
    print("\n📊 Computing daily metrics...")
    events_df['date'] = events_df['timestamp'].dt.date
    dates = pd.date_range(events_df['timestamp'].min().date(), events_df['timestamp'].max().date())
    records = []
    for date in dates:
        d = date.date()
        de = events_df[events_df['date'] == d]
        ds = sessions_df[sessions_df['session_date'] == d]
        if len(de) == 0:
            continue
        tc = de['event_type'].value_counts()
        qs, qp = tc.get('quiz_submitted', 0), tc.get('quiz_passed', 0)
        ap, rj = tc.get('approved', 0), tc.get('rejected', 0)
        records.append({
            'metric_date': d, 'dau': de['user_id'].nunique(), 'new_users': 0,
            'total_sessions': len(ds), 'total_events': len(de),
            'avg_session_duration': ds['duration_sec'].mean() if len(ds) > 0 else 0,
            'funnel_app_open': tc.get('app_open', 0), 'funnel_absence': tc.get('absence_declared', 0),
            'funnel_pdf': tc.get('pdf_viewed', 0), 'funnel_quiz_start': tc.get('quiz_started', 0),
            'funnel_quiz_submit': qs, 'funnel_quiz_pass': qp, 'funnel_approved': ap,
            'quiz_pass_rate': qp / qs if qs > 0 else 0,
            'approval_rate': ap / (ap + rj) if (ap + rj) > 0 else 0,
            'avg_quiz_score': 0, 'product_health_score': 0,
        })
    daily_df = pd.DataFrame(records)
    print(f"   ✓ Computed metrics for {len(daily_df)} days")
    return daily_df

def compute_cohort_retention(events_df, users_raw_df):
    print("\n🔄 Computing cohort retention...")
    users_raw_df['signup_date'] = pd.to_datetime(users_raw_df['signup_date'])
    users_raw_df['cohort_week'] = users_raw_df['signup_date'].dt.isocalendar().week.apply(lambda w: f"2025-W{w:02d}")
    uad = events_df.groupby('user_id')['timestamp'].apply(lambda x: set(x.dt.date)).reset_index()
    uad.columns = ['user_id', 'active_dates']
    rb = users_raw_df[['user_id', 'signup_date', 'cohort_week']].merge(uad, on='user_id', how='left')
    records = []
    for cohort, group in rb.groupby('cohort_week'):
        cs = len(group)
        for dn in [1, 3, 7, 14, 30, 60]:
            ret = sum(1 for _, u in group.iterrows()
                      if isinstance(u.get('active_dates'), set) and
                      (u['signup_date'] + timedelta(days=dn)).date() in u['active_dates'])
            records.append({'cohort_week': cohort, 'cohort_size': cs, 'days_since_signup': dn,
                            'retained_users': ret, 'retention_rate': ret / cs if cs > 0 else 0})
    ret_df = pd.DataFrame(records)
    print(f"   ✓ Computed {len(ret_df)} retention records")
    return ret_df

def load_to_sqlite(events_df, users_df, sessions_df, daily_df, retention_df):
    print(f"\n💾 Loading into SQLite: {DB_PATH}")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    with open(os.path.join(SQL_DIR, '01_schema.sql')) as f:
        conn.executescript(f.read())
    for name, df in [('event_logs', events_df), ('users', users_df),
                      ('sessions', sessions_df), ('daily_metrics', daily_df),
                      ('cohort_retention', retention_df)]:
        df.to_sql(name, conn, if_exists='replace', index=False)
        print(f"   ✓ {name}: {len(df):,} rows")
    conn.commit()
    conn.close()
    print(f"   DB size: {os.path.getsize(DB_PATH) / 1024 / 1024:.1f} MB")

def main():
    print("=" * 70)
    print("PHLIS — ETL Pipeline")
    print("=" * 70)
    events_df = load_raw_events()
    users_raw_df = pd.read_csv(os.path.join(RAW_DIR, 'users_raw.csv'))
    events_df = deduplicate_events(events_df)
    sessions_df = derive_sessions(events_df)
    users_df = derive_users(events_df, users_raw_df, sessions_df)
    daily_df = compute_daily_metrics(events_df, sessions_df)
    retention_df = compute_cohort_retention(events_df, users_raw_df)

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    for name, df in [('users', users_df), ('sessions', sessions_df),
                      ('metrics_daily', daily_df), ('retention', retention_df)]:
        df.to_csv(os.path.join(PROCESSED_DIR, f'{name}.csv'), index=False)
    print(f"\n📂 Saved CSVs to: {PROCESSED_DIR}")

    load_to_sqlite(events_df, users_df, sessions_df, daily_df, retention_df)
    print(f"\n{'=' * 70}\n✅ ETL pipeline complete!\n{'=' * 70}")

if __name__ == '__main__':
    main()
