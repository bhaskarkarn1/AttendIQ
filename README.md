# AttendIQ — Behavioral Analytics & Retention Intelligence Platform

> Turning Behavioral Data Into Retention Decisions.

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-GitHub_Pages-4ade80?style=for-the-badge)](https://bhaskarkarn.github.io/AttendIQ/dashboard/)
[![License](https://img.shields.io/badge/License-MIT-60a5fa?style=for-the-badge)](#license)

---

## 🎯 Overview

**AttendIQ** is an enterprise-grade Decision Science dashboard that models **5,000 student journeys** across 90 days to identify funnel bottlenecks, predict churn risk using machine learning, and validate interventions through controlled experimentation — generating actionable, data-driven insights for retention optimization.

Built as a **zero-dependency** vanilla JavaScript application with Chart.js for visualization, SQLite for data warehousing, and Python for the analytics/ETL pipeline.

![Dashboard Preview](dashboard/assets/preview.png)

---

## ✨ Features

### 📊 18 Interactive Visualizations
| Category | Charts |
|----------|--------|
| **Health & KPIs** | Health gauge, animated KPI cards, impact flow chain |
| **Funnel Analysis** | 7-stage funnel with drill-down drop-off analysis |
| **Engagement** | DAU/WAU trend lines, quality metrics overlay |
| **Retention** | Cohort heatmap, retention decay curve, correlation matrix |
| **User Segmentation** | Doughnut distribution, radar profiles, comparison bars |
| **Churn Intelligence** | Feature importance, risk scatter plot, high-risk table |
| **Professor Analytics** | Approval rate bars, deviation chart |
| **Scenario Simulation** | Live radar + bar charts updating in real-time |

### 🧪 Statistical Experimentation
- Controlled A/B testing with Student's two-sample t-test
- 95% confidence intervals with lift calculations
- Win/loss variant chips with significance badges

### 🎛️ Scenario Simulator
- 4 intervention sliders (PDF engagement, notification reach, onboarding, quiz format)
- Cascading impact calculation using empirically-derived coefficients
- **Live radar and bar charts** updating as you adjust parameters

### 🎯 Cross-Filtering
- Segment-level filtering: Power Users, Regular, At-Risk, Churned
- All KPIs, funnels, and gauges respond to segment selection

### 🌑 Premium Dark Theme
- Consistent dark UI across landing page and dashboard
- Glassmorphic sidebar, animated aurora background orbs
- Professional typography (Inter + JetBrains Mono)

---

## 🏗️ Architecture

```
AttendIQ/
├── dashboard/
│   ├── index.html          # Landing page
│   ├── app.html            # Analytics dashboard
│   ├── css/
│   │   ├── landing.css     # Landing page styles
│   │   └── style.css       # Dashboard styles
│   └── js/
│       ├── utils.js        # Data loading, formatters
│       ├── charts.js       # Chart.js factory functions
│       ├── insights.js     # Experiment & insight renderers
│       ├── segments.js     # Advanced analytics charts
│       └── app.js          # Master controller
├── data/
│   └── dashboard/          # 13 JSON data files
│       ├── health_score.json
│       ├── funnel_data.json
│       ├── engagement_data.json
│       ├── retention_data.json
│       ├── churn_predictions.json
│       ├── cluster_data.json
│       ├── professor_stats.json
│       ├── interactive_data.json
│       ├── daily_trends.json
│       ├── experiment_results.json
│       ├── ai_insights.json
│       ├── action_recommendations.json
│       └── alerts.json
├── python/                 # ETL & ML pipeline
└── sql/                    # Data warehouse schemas
```

---

## 🚀 Quick Start

### Option 1: Live Demo
👉 **[Open Live Demo](https://bhaskarkarn.github.io/AttendIQ/dashboard/)**

### Option 2: Run Locally
```bash
git clone https://github.com/bhaskarkarn/AttendIQ.git
cd AttendIQ
python3 -m http.server 8000
```
Open: [http://localhost:8000/dashboard/](http://localhost:8000/dashboard/)

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Vanilla JS (zero-dependency), HTML5, CSS3 |
| **Visualization** | Chart.js v4 (line, bar, doughnut, radar, scatter) |
| **Data** | SQLite (warehouse), JSON (API layer) |
| **ML Pipeline** | Python (scikit-learn, pandas, numpy) |
| **Design** | Custom dark theme, glassmorphism, micro-animations |
| **Deployment** | GitHub Pages (static) |

---

## 📈 Data Pipeline

1. **Ingest** — Raw attendance, quiz, and session data loaded into SQLite
2. **Transform** — Python ETL pipeline computes KPIs, cohort retention, churn features
3. **Model** — Random Forest churn predictor (AUC-ROC: 0.9655), K-Means clustering
4. **Export** — 13 structured JSON files for frontend consumption
5. **Visualize** — Chart.js renders 18 interactive visualizations

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ☕ by <a href="https://github.com/bhaskarkarn">Bhaskar Karn</a>
</p>
