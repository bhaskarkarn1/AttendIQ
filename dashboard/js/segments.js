/* ─── AttendIQ — Advanced Analytics Charts ─────────────────────── */

/* ═══ USER SEGMENTATION ═══ */

function renderSegmentKPIs(clusters) {
  const container = document.getElementById('seg-kpis');
  if (!container) return;
  const total = clusters.reduce((s, c) => s + c.count, 0);
  const colors = { 'Power User': 'cyan', 'Regular User': 'violet', 'At-Risk User': 'amber', 'Churned User': 'rose' };
  const icons = { 'Power User': '⚡', 'Regular User': '👤', 'At-Risk User': '⚠️', 'Churned User': '💀' };
  container.innerHTML = '';
  clusters.forEach(c => {
    const pct = ((c.count / total) * 100).toFixed(1);
    const d = document.createElement('div');
    d.className = 'card kpi';
    d.innerHTML = `<div class="kpi-icon">${icons[c.segment] || '📊'}</div><div class="kpi-val ${colors[c.segment] || 'cyan'}">${c.count.toLocaleString()}</div><div class="kpi-name">${c.segment}</div><div class="kpi-sub">${pct}% of total</div>`;
    container.appendChild(d);
  });
}

function renderSegmentDoughnut(ctx, clusters) {
  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: clusters.map(c => c.segment),
      datasets: [{
        data: clusters.map(c => c.count),
        backgroundColor: ['#3ecfb4', '#a78bfa', '#fbbf24', '#fb7185'],
        borderColor: '#0a0a0f', borderWidth: 3, hoverOffset: 12,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: '62%',
      plugins: {
        legend: { position: 'bottom', labels: { color: 'rgba(240,235,228,0.6)', font: { family: 'Inter', size: 11 }, padding: 16, usePointStyle: true } },
        tooltip: CHART_DEFAULTS.plugins.tooltip,
      },
    },
  });
}

function renderSegmentRadar(ctx, clusters) {
  const maxSessions = Math.max(...clusters.map(c => c.avg_sessions));
  const maxDays = Math.max(...clusters.map(c => c.avg_days_active));
  const maxDuration = Math.max(...clusters.map(c => c.avg_duration));
  const colors = ['#3ecfb4', '#a78bfa', '#fbbf24', '#fb7185'];

  return new Chart(ctx, {
    type: 'radar',
    data: {
      labels: ['Sessions', 'Days Active', 'Pass Rate', 'Duration', 'Engagement'],
      datasets: clusters.map((c, i) => ({
        label: c.segment,
        data: [
          (c.avg_sessions / maxSessions * 100).toFixed(0),
          (c.avg_days_active / maxDays * 100).toFixed(0),
          (c.avg_pass_rate * 100).toFixed(0),
          (c.avg_duration / maxDuration * 100).toFixed(0),
          ((c.avg_sessions * c.avg_days_active) / (maxSessions * maxDays) * 100).toFixed(0),
        ],
        borderColor: colors[i], backgroundColor: colors[i] + '18',
        borderWidth: 2, pointRadius: 3, pointBackgroundColor: colors[i],
      })),
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: {
        r: {
          grid: { color: 'rgba(255,255,255,0.06)' },
          angleLines: { color: 'rgba(255,255,255,0.06)' },
          pointLabels: { color: 'rgba(240,235,228,0.6)', font: { family: 'Inter', size: 11 } },
          ticks: { display: false }, suggestedMin: 0, suggestedMax: 100,
        }
      },
      plugins: {
        legend: { position: 'bottom', labels: { color: 'rgba(240,235,228,0.6)', font: { family: 'Inter', size: 10 }, padding: 14, usePointStyle: true } },
        tooltip: CHART_DEFAULTS.plugins.tooltip,
      },
    },
  });
}

function renderSegmentBars(ctx, clusters) {
  const colors = ['#3ecfb4', '#a78bfa', '#fbbf24', '#fb7185'];
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: clusters.map(c => c.segment),
      datasets: [
        { label: 'Avg Sessions', data: clusters.map(c => c.avg_sessions.toFixed(1)), backgroundColor: colors[0] + '99', borderRadius: 6 },
        { label: 'Days Active', data: clusters.map(c => c.avg_days_active.toFixed(1)), backgroundColor: colors[1] + '99', borderRadius: 6 },
        { label: 'Pass Rate %', data: clusters.map(c => (c.avg_pass_rate * 100).toFixed(1)), backgroundColor: colors[2] + '99', borderRadius: 6 },
      ]
    },
    options: { ...CHART_DEFAULTS, indexAxis: 'y' },
  });
}

/* ═══ CHURN INTELLIGENCE ═══ */

function renderChurnKPIs(churn) {
  const container = document.getElementById('churn-kpis');
  if (!container) return;
  const users = churn.high_risk_users || [];
  const avgInactive = users.length ? (users.reduce((s, u) => s + u.days_inactive, 0) / users.length).toFixed(0) : 0;
  const avgSessions = users.length ? (users.reduce((s, u) => s + u.total_sessions, 0) / users.length).toFixed(1) : 0;
  container.innerHTML = '';
  [
    { icon: '🎯', val: churn.auc_roc?.toFixed(4) || '—', name: 'Model AUC-ROC', color: 'emerald', sub: 'Random Forest classifier' },
    { icon: '🚨', val: (churn.total_high_risk || 0).toLocaleString(), name: 'High-Risk Users', color: 'rose', sub: '>70% churn probability' },
    { icon: '📅', val: avgInactive + 'd', name: 'Avg Days Inactive', color: 'amber', sub: 'Among high-risk cohort' },
    { icon: '📱', val: avgSessions, name: 'Avg Sessions', color: 'violet', sub: 'High-risk user baseline' },
  ].forEach(k => {
    const d = document.createElement('div');
    d.className = 'card kpi';
    d.innerHTML = `<div class="kpi-icon">${k.icon}</div><div class="kpi-val ${k.color}">${k.val}</div><div class="kpi-name">${k.name}</div><div class="kpi-sub">${k.sub}</div>`;
    container.appendChild(d);
  });
}

function renderChurnFeatures(ctx, featureImportance) {
  const entries = Object.entries(featureImportance).sort((a, b) => b[1] - a[1]);
  const labels = { total_sessions: 'Total Sessions', days_active: 'Days Active', total_events: 'Total Events', avg_session_duration_sec: 'Avg Session Duration', quiz_attempts: 'Quiz Attempts', funnel_max_stage: 'Funnel Max Stage', quiz_pass_rate: 'Quiz Pass Rate' };
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: entries.map(e => labels[e[0]] || e[0]),
      datasets: [{
        label: 'Importance',
        data: entries.map(e => (e[1] * 100).toFixed(1)),
        backgroundColor: entries.map((_, i) => {
          const colors = ['#e8804a', '#f5a623', '#fbbf24', '#4ade80', '#3ecfb4', '#60a5fa', '#a78bfa'];
          return colors[i] + 'cc';
        }),
        borderRadius: 8,
      }]
    },
    options: { ...CHART_DEFAULTS, indexAxis: 'y', plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false } } },
  });
}

function renderChurnScatter(ctx, users) {
  const top50 = users.slice(0, 50);
  return new Chart(ctx, {
    type: 'scatter',
    data: {
      datasets: [{
        label: 'High-Risk Users',
        data: top50.map(u => ({ x: u.days_inactive, y: (u.churn_probability * 100).toFixed(1) })),
        backgroundColor: '#fb718588', borderColor: '#fb7185', borderWidth: 1,
        pointRadius: 5, pointHoverRadius: 8,
      }]
    },
    options: {
      ...CHART_DEFAULTS,
      plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false } },
      scales: {
        x: { ...CHART_DEFAULTS.scales.x, title: { display: true, text: 'Days Inactive', color: 'rgba(240,235,228,0.5)', font: { family: 'Inter', size: 11 } } },
        y: { ...CHART_DEFAULTS.scales.y, title: { display: true, text: 'Churn Probability %', color: 'rgba(240,235,228,0.5)', font: { family: 'Inter', size: 11 } } },
      },
    },
  });
}

function renderChurnTable(churn) {
  const container = document.getElementById('churn-table');
  if (!container) return;
  const users = (churn.high_risk_users || []).slice(0, 20);
  let html = '<table class="tbl"><thead><tr><th>User ID</th><th>Segment</th><th>Churn Probability</th><th>Days Inactive</th><th>Sessions</th></tr></thead><tbody>';
  users.forEach(u => {
    const pct = (u.churn_probability * 100).toFixed(1);
    const color = pct > 99 ? 'var(--rose)' : pct > 95 ? 'var(--amber)' : 'var(--emerald)';
    html += `<tr><td class="mono">${u.user_id}</td><td>${u.user_segment}</td><td><div class="risk-bar"><div class="risk-fill" style="width:${pct}%;background:${color}"></div></div><span class="mono">${pct}%</span></td><td class="mono">${u.days_inactive}d</td><td class="mono">${u.total_sessions}</td></tr>`;
  });
  html += '</tbody></table>';
  container.innerHTML = html;
}

/* ═══ PROFESSOR ANALYTICS ═══ */

function renderProfessorKPIs(profs) {
  const container = document.getElementById('prof-kpis');
  if (!container) return;
  const sorted = [...profs].sort((a, b) => b.approval_rate - a.approval_rate);
  const mean = profs.reduce((s, p) => s + p.approval_rate, 0) / profs.length;
  const variance = profs.reduce((s, p) => s + Math.pow(p.approval_rate - mean, 2), 0) / profs.length;
  container.innerHTML = '';
  [
    { icon: '🏆', val: (sorted[0].approval_rate * 100).toFixed(1) + '%', name: 'Highest Approval', color: 'emerald', sub: sorted[0].professor },
    { icon: '📉', val: (sorted[sorted.length - 1].approval_rate * 100).toFixed(1) + '%', name: 'Lowest Approval', color: 'rose', sub: sorted[sorted.length - 1].professor },
    { icon: '📊', val: (mean * 100).toFixed(1) + '%', name: 'Mean Approval Rate', color: 'cyan', sub: `σ² = ${(variance * 10000).toFixed(2)}` },
    { icon: '👨‍🏫', val: profs.length, name: 'Total Professors', color: 'violet', sub: `${profs.reduce((s, p) => s + p.total, 0).toLocaleString()} total decisions` },
  ].forEach(k => {
    const d = document.createElement('div');
    d.className = 'card kpi';
    d.innerHTML = `<div class="kpi-icon">${k.icon}</div><div class="kpi-val ${k.color}">${k.val}</div><div class="kpi-name">${k.name}</div><div class="kpi-sub">${k.sub}</div>`;
    container.appendChild(d);
  });
}

function renderProfessorBars(ctx, profs) {
  const sorted = [...profs].sort((a, b) => a.approval_rate - b.approval_rate);
  const mean = profs.reduce((s, p) => s + p.approval_rate, 0) / profs.length;
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: sorted.map(p => p.professor.replace('prof_', 'P')),
      datasets: [{
        label: 'Approval Rate %',
        data: sorted.map(p => (p.approval_rate * 100).toFixed(1)),
        backgroundColor: sorted.map(p => p.approval_rate < mean - 0.1 ? '#fb718599' : p.approval_rate > mean + 0.02 ? '#4ade8099' : '#fbbf2499'),
        borderRadius: 4,
      }]
    },
    options: {
      ...CHART_DEFAULTS,
      plugins: {
        ...CHART_DEFAULTS.plugins,
        legend: { display: false },
        annotation: undefined,
      },
    },
  });
}

function renderProfessorDeviation(ctx, profs) {
  const sorted = [...profs].sort((a, b) => a.deviation - b.deviation);
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: sorted.map(p => p.professor.replace('prof_', 'P')),
      datasets: [{
        label: 'Deviation from Mean',
        data: sorted.map(p => (p.deviation * 100).toFixed(2)),
        backgroundColor: sorted.map(p => p.deviation < 0 ? '#fb718599' : '#4ade8066'),
        borderColor: sorted.map(p => p.deviation < 0 ? '#fb7185' : '#4ade80'),
        borderWidth: 1, borderRadius: 4,
      }]
    },
    options: {
      ...CHART_DEFAULTS,
      plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false } },
      scales: {
        ...CHART_DEFAULTS.scales,
        y: { ...CHART_DEFAULTS.scales.y, ticks: { ...CHART_DEFAULTS.scales.y.ticks, callback: v => v + '%' } },
      },
    },
  });
}

/* ═══ SIMULATOR LIVE CHARTS ═══ */

let simRadarChart = null;
let simBarChart = null;

function renderSimulatorCharts(baseline, projected) {
  const labels = ['Quiz Pass', 'D7 Retention', 'Funnel Conv.', 'Health Score', 'Engagement'];

  // Radar
  const rCtx = document.getElementById('sim-radar');
  if (rCtx) {
    if (simRadarChart) simRadarChart.destroy();
    simRadarChart = new Chart(rCtx.getContext('2d'), {
      type: 'radar',
      data: {
        labels,
        datasets: [
          { label: 'Baseline', data: baseline, borderColor: 'rgba(240,235,228,0.3)', backgroundColor: 'rgba(240,235,228,0.04)', borderWidth: 2, borderDash: [5, 5], pointRadius: 3, pointBackgroundColor: 'rgba(240,235,228,0.5)' },
          { label: 'Projected', data: projected, borderColor: '#4ade80', backgroundColor: 'rgba(74,222,128,0.1)', borderWidth: 2.5, pointRadius: 4, pointBackgroundColor: '#4ade80' },
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: { r: { grid: { color: 'rgba(255,255,255,0.06)' }, angleLines: { color: 'rgba(255,255,255,0.06)' }, pointLabels: { color: 'rgba(240,235,228,0.6)', font: { family: 'Inter', size: 10 } }, ticks: { display: false }, suggestedMin: 0 } },
        plugins: { legend: { position: 'bottom', labels: { color: 'rgba(240,235,228,0.6)', font: { family: 'Inter', size: 10 }, padding: 12, usePointStyle: true } }, tooltip: CHART_DEFAULTS.plugins.tooltip },
      },
    });
  }

  // Bar
  const bCtx = document.getElementById('sim-bars');
  if (bCtx) {
    if (simBarChart) simBarChart.destroy();
    simBarChart = new Chart(bCtx.getContext('2d'), {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label: 'Baseline', data: baseline, backgroundColor: 'rgba(240,235,228,0.12)', borderRadius: 4 },
          { label: 'Projected', data: projected, backgroundColor: '#4ade8088', borderRadius: 4 },
        ]
      },
      options: { ...CHART_DEFAULTS },
    });
  }
}

/* ═══ RETENTION DECAY CURVE ═══ */

function renderRetentionCurve(ctx, summary) {
  const days = [1, 3, 7, 14, 30, 60];
  const values = days.map(d => {
    const val = summary[`d${d}`];
    return val != null ? (val * 100).toFixed(1) : null;
  }).filter(v => v !== null);
  const validDays = days.slice(0, values.length);

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: validDays.map(d => `D${d}`),
      datasets: [{
        label: 'Retention %',
        data: values,
        borderColor: '#3ecfb4', backgroundColor: 'rgba(62,207,180,0.1)',
        fill: true, tension: 0.35, borderWidth: 2.5,
        pointRadius: 5, pointBackgroundColor: '#3ecfb4', pointBorderColor: '#0a0a0f', pointBorderWidth: 2,
        pointHoverRadius: 8, pointStyle: 'circle',
      }]
    },
    options: {
      ...CHART_DEFAULTS,
      plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false } },
      scales: {
        ...CHART_DEFAULTS.scales,
        y: { ...CHART_DEFAULTS.scales.y, ticks: { ...CHART_DEFAULTS.scales.y.ticks, callback: v => v + '%' }, suggestedMin: 0, suggestedMax: 100 },
      },
    },
  });
}

/* ═══ CORRELATION MATRIX ═══ */

function renderCorrelationMatrix(container, correlations) {
  if (!container || !correlations) return;
  const keys = Object.keys(correlations);
  const labels = { total_sessions: 'Sessions', days_active: 'Days Active', avg_session_duration_sec: 'Avg Duration', quiz_pass_rate: 'Pass Rate', quiz_attempts: 'Quiz Attempts', funnel_max_stage: 'Funnel Depth' };

  let html = '<table class="heatmap"><thead><tr><th></th>';
  keys.forEach(k => { html += `<th>${labels[k] || k}</th>`; });
  html += '</tr></thead><tbody>';

  keys.forEach(row => {
    html += `<tr><td class="hm-label">${labels[row] || row}</td>`;
    keys.forEach(col => {
      const val = correlations[row]?.[col];
      const v = val != null ? val : (row === col ? 1 : 0);
      const abs = Math.abs(v);
      const r = v > 0 ? 74 : 251; const g = v > 0 ? 222 : 113; const b = v > 0 ? 128 : 133;
      const bg = `rgba(${r},${g},${b},${(abs * 0.6).toFixed(2)})`;
      const textColor = abs > 0.4 ? '#fff' : 'rgba(240,235,228,0.6)';
      html += `<td class="hm-cell" style="background:${bg};color:${textColor}" title="${labels[row] || row} × ${labels[col] || col}: r=${v.toFixed(3)}">${v.toFixed(2)}</td>`;
    });
    html += '</tr>';
  });
  html += '</tbody></table>';
  container.innerHTML = html;
}
