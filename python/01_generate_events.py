#!/usr/bin/env python3
"""
===============================================================================
PHLIS — Event Generation Layer
===============================================================================
Simulates realistic EdTech product event data for 5,000 users over 90 days.

User Archetypes:
  - Power Users (15%):  High engagement, complete funnels, high pass rates
  - Regular Users (45%): Moderate engagement, some drop-offs
  - At-Risk Users (25%): Low engagement, high drop-off, low pass rates
  - Churned Users (15%): Stop using after first few days

Event Types:
  app_open, absence_declared, pdf_viewed, quiz_started,
  quiz_submitted, quiz_passed, quiz_failed, approved, rejected

A/B Test Groups:
  - timer_experiment:      timer vs no_timer
  - question_experiment:   3_questions vs 5_questions
  - notification_experiment: notification vs no_notification
===============================================================================
"""

import os
import uuid
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ─── Configuration ────────────────────────────────────────────────────────────
NUM_USERS = 5000
NUM_DAYS = 90
START_DATE = datetime(2025, 1, 1)
RANDOM_SEED = 42
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')

# User archetype distribution
ARCHETYPES = {
    'power_user':   {'pct': 0.15, 'daily_open_prob': 0.85, 'funnel_depth': 0.95, 'pass_rate': 0.88, 'churn_day': None,       'avg_session_min': 12},
    'regular_user': {'pct': 0.45, 'daily_open_prob': 0.45, 'funnel_depth': 0.65, 'pass_rate': 0.62, 'churn_day': None,       'avg_session_min': 7},
    'at_risk_user': {'pct': 0.25, 'daily_open_prob': 0.20, 'funnel_depth': 0.35, 'pass_rate': 0.30, 'churn_day': None,       'avg_session_min': 3},
    'churned_user': {'pct': 0.15, 'daily_open_prob': 0.60, 'funnel_depth': 0.50, 'pass_rate': 0.40, 'churn_day': (5, 20),   'avg_session_min': 5},
}

# Professor pool for approvals
PROFESSORS = [f'prof_{i:03d}' for i in range(1, 21)]
# Make 2 professors notably stricter
STRICT_PROFESSORS = PROFESSORS[:2]

# A/B experiments
EXPERIMENTS = {
    'timer_experiment':        ['timer', 'no_timer'],
    'question_experiment':     ['3_questions', '5_questions'],
    'notification_experiment': ['notification', 'no_notification'],
}

np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)


def generate_users():
    """Generate user profiles with archetypes and experiment assignments."""
    users = []
    user_id_counter = 0

    for archetype, config in ARCHETYPES.items():
        count = int(NUM_USERS * config['pct'])
        for _ in range(count):
            user_id_counter += 1
            user = {
                'user_id': f'u_{user_id_counter:05d}',
                'archetype': archetype,
                'signup_date': START_DATE + timedelta(days=np.random.randint(0, 14)),
                'daily_open_prob': config['daily_open_prob'] + np.random.normal(0, 0.05),
                'funnel_depth': config['funnel_depth'] + np.random.normal(0, 0.05),
                'pass_rate': config['pass_rate'] + np.random.normal(0, 0.05),
                'churn_day': np.random.randint(*config['churn_day']) if config['churn_day'] else None,
                'avg_session_min': max(1, config['avg_session_min'] + np.random.normal(0, 1.5)),
                'assigned_professor': random.choice(PROFESSORS),
            }
            # Clip probabilities to valid range
            user['daily_open_prob'] = np.clip(user['daily_open_prob'], 0.05, 0.98)
            user['funnel_depth'] = np.clip(user['funnel_depth'], 0.1, 0.99)
            user['pass_rate'] = np.clip(user['pass_rate'], 0.05, 0.95)

            # Assign experiment groups
            for exp_name, groups in EXPERIMENTS.items():
                user[exp_name] = random.choice(groups)

            users.append(user)

    return users


def generate_events_for_user(user, all_events):
    """Generate a sequence of events for one user across all days."""
    user_id = user['user_id']
    signup_date = user['signup_date']
    churn_day = user['churn_day']

    # Experiment effect modifiers
    timer_boost = 1.15 if user['timer_experiment'] == 'timer' else 1.0
    question_boost = 1.10 if user['question_experiment'] == '3_questions' else 1.0
    notif_boost = 1.20 if user['notification_experiment'] == 'notification' else 1.0

    effective_open_prob = user['daily_open_prob'] * notif_boost
    effective_funnel = user['funnel_depth'] * question_boost
    effective_pass = user['pass_rate'] * timer_boost

    effective_open_prob = min(effective_open_prob, 0.98)
    effective_funnel = min(effective_funnel, 0.99)
    effective_pass = min(effective_pass, 0.95)

    for day_offset in range(NUM_DAYS):
        current_date = START_DATE + timedelta(days=day_offset)

        # User hasn't signed up yet
        if current_date < signup_date:
            continue

        days_since_signup = (current_date - signup_date).days

        # Churned user — stop generating events after churn day
        if churn_day and days_since_signup > churn_day:
            continue

        # Gradual engagement decay for at-risk users
        decay = 1.0
        if user['archetype'] == 'at_risk_user':
            decay = max(0.1, 1.0 - (days_since_signup * 0.008))

        # Weekend effect: slightly lower engagement
        is_weekend = current_date.weekday() >= 5
        weekend_factor = 0.7 if is_weekend else 1.0

        # Check if user opens app today
        if np.random.random() > effective_open_prob * decay * weekend_factor:
            continue

        # ─── Generate session ─────────────────────────────────────────
        session_id = str(uuid.uuid4())[:12]

        # Random hour with realistic distribution (peak 9am-3pm, 7pm-11pm)
        hour_weights = [0.5,0.3,0.2,0.1,0.1,0.1,0.3,0.8,1.5,2.5,2.8,2.5,
                        2.0,2.2,2.5,2.0,1.5,1.2,1.5,2.0,2.5,2.2,1.5,0.8]
        hour = np.random.choice(24, p=np.array(hour_weights)/sum(hour_weights))
        minute = np.random.randint(0, 60)
        second = np.random.randint(0, 60)
        ts = current_date.replace(hour=hour, minute=minute, second=second)

        # Event: app_open
        all_events.append({
            'event_id': str(uuid.uuid4())[:16],
            'user_id': user_id,
            'event_type': 'app_open',
            'timestamp': ts,
            'session_id': session_id,
            'metadata': None,
        })

        # Funnel: absence_declared
        if np.random.random() < effective_funnel * decay:
            ts += timedelta(seconds=np.random.randint(10, 120))
            all_events.append({
                'event_id': str(uuid.uuid4())[:16],
                'user_id': user_id,
                'event_type': 'absence_declared',
                'timestamp': ts,
                'session_id': session_id,
                'metadata': None,
            })

            # Funnel: pdf_viewed
            if np.random.random() < effective_funnel * decay:
                duration_sec = max(30, int(user['avg_session_min'] * 60 * np.random.uniform(0.3, 1.0)))
                ts += timedelta(seconds=np.random.randint(5, 30))
                all_events.append({
                    'event_id': str(uuid.uuid4())[:16],
                    'user_id': user_id,
                    'event_type': 'pdf_viewed',
                    'timestamp': ts,
                    'session_id': session_id,
                    'metadata': f'{{"duration_sec": {duration_sec}}}',
                })

                # Funnel: quiz_started
                if np.random.random() < effective_funnel * decay * 0.9:
                    ts += timedelta(seconds=duration_sec + np.random.randint(5, 30))
                    all_events.append({
                        'event_id': str(uuid.uuid4())[:16],
                        'user_id': user_id,
                        'event_type': 'quiz_started',
                        'timestamp': ts,
                        'session_id': session_id,
                        'metadata': None,
                    })

                    # Funnel: quiz_submitted (some users abandon)
                    if np.random.random() < 0.85 * decay:
                        quiz_duration = np.random.randint(60, 600)
                        ts += timedelta(seconds=quiz_duration)

                        # Determine pass/fail
                        passed = np.random.random() < effective_pass
                        score = int(np.random.normal(75 if passed else 35, 10))
                        score = np.clip(score, 0, 100)

                        all_events.append({
                            'event_id': str(uuid.uuid4())[:16],
                            'user_id': user_id,
                            'event_type': 'quiz_submitted',
                            'timestamp': ts,
                            'session_id': session_id,
                            'metadata': f'{{"score": {score}, "duration_sec": {quiz_duration}}}',
                        })

                        result_type = 'quiz_passed' if passed else 'quiz_failed'
                        ts += timedelta(seconds=2)
                        all_events.append({
                            'event_id': str(uuid.uuid4())[:16],
                            'user_id': user_id,
                            'event_type': result_type,
                            'timestamp': ts,
                            'session_id': session_id,
                            'metadata': f'{{"score": {score}}}',
                        })

                        # Professor approval/rejection (only if passed)
                        if passed:
                            ts += timedelta(hours=np.random.randint(1, 48))
                            professor = user['assigned_professor']

                            if professor in STRICT_PROFESSORS:
                                approval_rate = 0.55  # Strict professors
                            else:
                                approval_rate = 0.85  # Normal professors

                            approved = np.random.random() < approval_rate
                            all_events.append({
                                'event_id': str(uuid.uuid4())[:16],
                                'user_id': user_id,
                                'event_type': 'approved' if approved else 'rejected',
                                'timestamp': ts,
                                'session_id': session_id,
                                'metadata': f'{{"professor": "{professor}"}}',
                            })

    # Add some noise: ~2% chance of duplicate events
    if len(all_events) > 100 and np.random.random() < 0.02:
        dup = random.choice(all_events[-20:]).copy()
        dup['event_id'] = str(uuid.uuid4())[:16]  # New ID but same data
        all_events.append(dup)


def add_missing_values(df):
    """Introduce realistic missing values (~1.5% of metadata, ~0.3% of session_id)."""
    n = len(df)
    # Missing metadata
    mask = np.random.random(n) < 0.015
    df.loc[mask, 'metadata'] = None

    # Missing session_id (rare)
    mask = np.random.random(n) < 0.003
    df.loc[mask, 'session_id'] = None

    return df


def main():
    print("=" * 70)
    print("PHLIS — Event Generation Layer")
    print("=" * 70)

    # Generate users
    print(f"\n🧑 Generating {NUM_USERS} users with archetypes...")
    users = generate_users()
    users_df = pd.DataFrame(users)
    print(f"   ✓ Power Users:  {len(users_df[users_df.archetype == 'power_user'])}")
    print(f"   ✓ Regular Users: {len(users_df[users_df.archetype == 'regular_user'])}")
    print(f"   ✓ At-Risk Users: {len(users_df[users_df.archetype == 'at_risk_user'])}")
    print(f"   ✓ Churned Users: {len(users_df[users_df.archetype == 'churned_user'])}")

    # Generate events
    print(f"\n📊 Generating events for {NUM_DAYS} days...")
    all_events = []
    for i, user in enumerate(users):
        generate_events_for_user(user, all_events)
        if (i + 1) % 1000 == 0:
            print(f"   ... processed {i + 1}/{NUM_USERS} users ({len(all_events):,} events so far)")

    events_df = pd.DataFrame(all_events)
    events_df = events_df.sort_values('timestamp').reset_index(drop=True)

    # Add realistic noise
    events_df = add_missing_values(events_df)

    print(f"\n   ✓ Total events generated: {len(events_df):,}")
    print(f"   ✓ Event type distribution:")
    for et, count in events_df['event_type'].value_counts().items():
        print(f"     - {et}: {count:,} ({count/len(events_df)*100:.1f}%)")

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    events_path = os.path.join(OUTPUT_DIR, 'event_logs.csv')
    events_df.to_csv(events_path, index=False)
    print(f"\n💾 Saved event logs to: {events_path}")
    print(f"   File size: {os.path.getsize(events_path) / 1024 / 1024:.1f} MB")

    users_path = os.path.join(OUTPUT_DIR, 'users_raw.csv')
    users_df.to_csv(users_path, index=False)
    print(f"💾 Saved user profiles to: {users_path}")

    print(f"\n{'=' * 70}")
    print("✅ Event generation complete!")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
