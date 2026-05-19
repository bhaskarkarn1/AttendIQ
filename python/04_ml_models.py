#!/usr/bin/env python3
"""
PHLIS — ML Models Layer
1. User Clustering (K-Means)
2. Churn Prediction (Random Forest)
3. Anomaly Detection (Isolation Forest)
"""

import os, json, sqlite3, warnings
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
warnings.filterwarnings('ignore')

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
DB_PATH = os.path.join(BASE_DIR, 'data', 'phlis.db')

def get_conn():
    return sqlite3.connect(DB_PATH)

def user_clustering(conn):
    """Cluster users into segments using K-Means."""
    print("\n🔬 User Clustering (K-Means, k=4)...")
    users = pd.read_sql("SELECT * FROM users", conn)

    features = ['total_sessions', 'avg_session_duration_sec', 'days_active',
                'funnel_max_stage', 'quiz_attempts', 'quiz_pass_rate', 'total_events']
    X = users[features].fillna(0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    users['cluster'] = kmeans.fit_predict(X_scaled)

    # Label clusters by engagement level
    cluster_means = users.groupby('cluster')[features].mean()
    engagement_rank = cluster_means['total_sessions'].rank()
    label_map = {}
    for cluster_id in range(4):
        rank = engagement_rank[cluster_id]
        if rank == 4:
            label_map[cluster_id] = 'Power User'
        elif rank == 3:
            label_map[cluster_id] = 'Regular User'
        elif rank == 2:
            label_map[cluster_id] = 'At-Risk User'
        else:
            label_map[cluster_id] = 'Churned User'

    users['user_segment'] = users['cluster'].map(label_map)
    print("   Segment distribution:")
    for seg, count in users['user_segment'].value_counts().items():
        print(f"     {seg}: {count:,} ({count/len(users)*100:.1f}%)")

    # Save back to DB
    conn.execute("DROP TABLE IF EXISTS user_segments")
    users[['user_id', 'cluster', 'user_segment']].to_sql('user_segments', conn, index=False)
    conn.commit()

    # Add user_segment column if missing, then update
    try:
        conn.execute("ALTER TABLE users ADD COLUMN user_segment TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    for _, row in users.iterrows():
        conn.execute("UPDATE users SET user_segment = ? WHERE user_id = ?",
                     (row['user_segment'], row['user_id']))
    conn.commit()

    cluster_profiles = []
    for seg in label_map.values():
        seg_data = users[users['user_segment'] == seg]
        cluster_profiles.append({
            'segment': seg,
            'count': int(len(seg_data)),
            'avg_sessions': round(seg_data['total_sessions'].mean(), 1),
            'avg_duration': round(seg_data['avg_session_duration_sec'].mean(), 1),
            'avg_pass_rate': round(seg_data['quiz_pass_rate'].mean(), 3),
            'avg_days_active': round(seg_data['days_active'].mean(), 1),
        })

    return cluster_profiles, users

def churn_prediction(conn, users_df):
    """Predict churn probability using Random Forest."""
    print("\n🔮 Churn Prediction (Random Forest)...")

    # Define churn: user inactive for last 14+ days
    users_df['last_active_date'] = pd.to_datetime(users_df['last_active_date'])
    max_date = users_df['last_active_date'].max()
    users_df['days_inactive'] = (max_date - users_df['last_active_date']).dt.days
    users_df['is_churned'] = (users_df['days_inactive'] > 14).astype(int)

    features = ['total_sessions', 'avg_session_duration_sec', 'days_active',
                'funnel_max_stage', 'quiz_attempts', 'quiz_pass_rate', 'total_events']
    X = users_df[features].fillna(0)
    y = users_df['is_churned']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

    model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    model.fit(X_train, y_train)

    y_pred_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_pred_proba)
    print(f"   AUC-ROC: {auc:.4f}")

    # Feature importance
    importances = dict(zip(features, model.feature_importances_))
    sorted_imp = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    print("   Feature importance:")
    for feat, imp in sorted_imp:
        print(f"     {feat}: {imp:.3f}")

    # Predict for all users
    all_proba = model.predict_proba(X)[:, 1]
    users_df['churn_probability'] = all_proba

    # High-risk users
    high_risk = users_df[users_df['churn_probability'] > 0.7].sort_values('churn_probability', ascending=False)
    print(f"   High-risk users (>70% churn prob): {len(high_risk):,}")

    churn_results = {
        'auc_roc': round(auc, 4),
        'feature_importance': {k: round(v, 4) for k, v in sorted_imp},
        'total_high_risk': int(len(high_risk)),
        'high_risk_users': high_risk[['user_id', 'user_segment', 'churn_probability',
                                       'days_inactive', 'total_sessions']].head(50).to_dict('records'),
    }

    # Save churn scores to DB
    conn.execute("DROP TABLE IF EXISTS churn_scores")
    users_df[['user_id', 'churn_probability', 'is_churned']].to_sql('churn_scores', conn, index=False)
    conn.commit()

    return churn_results, users_df

def anomaly_detection(conn):
    """Detect anomalies in daily metrics using Isolation Forest."""
    print("\n🚨 Anomaly Detection (Isolation Forest)...")
    daily = pd.read_sql("SELECT * FROM daily_metrics ORDER BY metric_date", conn)

    features = ['dau', 'total_sessions', 'quiz_pass_rate', 'approval_rate', 'avg_session_duration']
    X = daily[features].fillna(0)

    iso = IsolationForest(contamination=0.08, random_state=42)
    daily['anomaly'] = iso.fit_predict(X)
    daily['is_anomaly'] = (daily['anomaly'] == -1).astype(int)

    anomalies = daily[daily['is_anomaly'] == 1]
    print(f"   Detected {len(anomalies)} anomalous days")

    anomaly_list = []
    for _, row in anomalies.iterrows():
        # Determine which metric is most anomalous
        deviations = {}
        for feat in features:
            mean_val = daily[feat].mean()
            std_val = daily[feat].std()
            if std_val > 0:
                z = (row[feat] - mean_val) / std_val
                deviations[feat] = round(z, 2)

        worst_metric = max(deviations.items(), key=lambda x: abs(x[1]))
        direction = "spike" if worst_metric[1] > 0 else "drop"

        anomaly_list.append({
            'date': str(row['metric_date']),
            'metric': worst_metric[0],
            'direction': direction,
            'z_score': worst_metric[1],
            'description': f"{worst_metric[0].replace('_', ' ').title()} {direction} (z={worst_metric[1]:.1f}) on {row['metric_date']}",
        })

    return anomaly_list

def main():
    print("=" * 70)
    print("PHLIS — ML Models Layer")
    print("=" * 70)
    conn = get_conn()

    clusters, users_df = user_clustering(conn)
    churn, users_df = churn_prediction(conn, users_df)
    anomalies = anomaly_detection(conn)

    results = {
        'clustering': clusters,
        'churn': churn,
        'anomalies': anomalies,
    }

    out_path = os.path.join(BASE_DIR, 'data', 'processed', 'ml_results.json')
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Saved ML results to: {out_path}")
    conn.close()
    print(f"\n{'=' * 70}\n✅ ML models complete!\n{'=' * 70}")
    return results

if __name__ == '__main__':
    main()
