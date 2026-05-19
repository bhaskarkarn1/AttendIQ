/* ─── Insights & Experiment Renderers ─────────────────────────── */

function renderInsightsPanel(container, insights) {
  container.innerHTML = '';
  insights.forEach(ins => {
    const card = document.createElement('div');
    card.className = 'insight-card-rich';
    const iconMap = { critical: '🔴', warning: '🟡', info: '🔵' };
    const icon = iconMap[ins.severity] || '📊';
    card.innerHTML = `
      <div class="insight-header">
        <span class="insight-icon-lg">${icon}</span>
        <div class="insight-header-text">
          <div class="insight-title-lg">${ins.title}</div>
          <span class="severity-pill ${ins.severity}">${ins.severity.toUpperCase()}</span>
        </div>
      </div>
      <div class="insight-body-text">${ins.description}</div>
      <div class="insight-footer">
        <div class="insight-metric"><span class="insight-metric-label">Impact Score</span><span class="insight-metric-val">${((ins.impact_score || 0) * 100).toFixed(0)}%</span></div>
      </div>
    `;
    container.appendChild(card);
  });
}

function renderAlerts(container, alerts) {
  container.innerHTML = '';
  if (!alerts || alerts.length === 0) {
    container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">No active alerts</div>';
    return;
  }
  alerts.forEach(alert => {
    const item = document.createElement('div');
    item.className = 'alert-row';
    item.innerHTML = `
      <div class="alert-pulse ${alert.severity}"></div>
      <div class="alert-msg">${alert.description || alert.title}</div>
      <div class="alert-ts">${alert.triggered_at || ''}</div>
    `;
    container.appendChild(item);
  });
}

function renderRecommendations(container, recs) {
  container.innerHTML = '';
  recs.forEach(rec => {
    const card = document.createElement('div');
    card.className = 'action';
    card.innerHTML = `
      <div class="action-num">${rec.priority}</div>
      <div class="action-body">
        <div class="action-name">${rec.action_title}</div>
        <div class="action-desc">${rec.description}</div>
        <div class="action-tags">
          <span class="tag impact">${rec.expected_impact}</span>
          <span class="tag ${rec.effort_level || 'medium'}">${(rec.effort_level || 'medium').toUpperCase()}</span>
          ${rec.category ? `<span class="tag" style="background:rgba(107,76,138,0.08);color:var(--violet)">${rec.category.toUpperCase()}</span>` : ''}
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

function renderExperiments(container, experiments) {
  container.innerHTML = '';
  experiments.forEach(exp => {
    const card = document.createElement('div');
    card.className = 'card exp-card-rich';

    let metricsHTML = '';
    for (const [metricName, data] of Object.entries(exp.variants || {})) {
      const lift = data.lift_pct || 0;
      const va = data.variant_a || {};
      const vb = data.variant_b || {};
      const winnerName = data.winner || '';
      const isVaWinner = va.name === winnerName;
      const isSig = data.is_significant;

      metricsHTML += `
        <div class="exp-metric-row">
          <div class="exp-metric-label">${metricName.replace(/_/g, ' ')}</div>
          <div class="exp-variants">
            <div class="exp-variant-chip ${isVaWinner ? 'winner' : ''}">
              <span class="exp-variant-name">${va.name || 'A'}</span>
              <span class="exp-variant-val">${typeof va.mean === 'number' ? va.mean.toFixed(3) : va.mean}</span>
              ${isVaWinner ? '<span class="winner-badge">👑 WINNER</span>' : ''}
            </div>
            <span class="exp-vs">vs</span>
            <div class="exp-variant-chip ${!isVaWinner ? 'winner' : ''}">
              <span class="exp-variant-name">${vb.name || 'B'}</span>
              <span class="exp-variant-val">${typeof vb.mean === 'number' ? vb.mean.toFixed(3) : vb.mean}</span>
              ${!isVaWinner && winnerName ? '<span class="winner-badge">👑 WINNER</span>' : ''}
            </div>
          </div>
          <div class="exp-result-badges">
            <span class="exp-lift-badge ${lift > 0 ? 'positive' : 'negative'}">${lift > 0 ? '↑' : '↓'} ${Math.abs(lift).toFixed(1)}%</span>
            <span class="exp-sig-badge ${isSig ? 'significant' : 'not-sig'}">${isSig ? '✓ Significant (p<0.05)' : '✗ Not Significant'}</span>
          </div>
        </div>
      `;
    }

    card.innerHTML = `
      <div class="exp-header">
        <span class="exp-icon">🧪</span>
        <div class="exp-header-text">
          <div class="exp-title">${exp.name}</div>
          <div class="exp-subtitle">Controlled A/B Test · Student's t-test · 95% CI</div>
        </div>
      </div>
      <div class="exp-metrics-grid">${metricsHTML}</div>
    `;
    container.appendChild(card);
  });
}

function renderChurnTable(container, churnData) {
  const users = (churnData.high_risk_users || []).slice(0, 20);
  if (!users.length) { container.innerHTML = '<p style="color:var(--text-muted)">No high-risk users</p>'; return; }
  let html = `<table class="tbl"><thead><tr>
    <th>User ID</th><th>Segment</th><th>Churn Risk</th><th>Days Inactive</th><th>Sessions</th>
  </tr></thead><tbody>`;
  users.forEach(u => {
    const prob = (u.churn_probability || 0);
    const color = getRiskColor(prob);
    html += `<tr>
      <td class="mono">${u.user_id}</td>
      <td>${u.user_segment || '-'}</td>
      <td><div class="risk-bar"><div class="risk-fill" style="width:${prob*100}%;background:${color}"></div></div><span class="mono" style="color:${color}">${(prob*100).toFixed(1)}%</span></td>
      <td class="mono">${u.days_inactive || 0}d</td>
      <td class="mono">${u.total_sessions || 0}</td>
    </tr>`;
  });
  html += '</tbody></table>';
  container.innerHTML = html;
}

function renderRetentionHeatmap(container, retData) {
  const heatmap = retData.heatmap || {};
  if (!heatmap.cohorts) { container.innerHTML = '<p style="color:var(--text-muted)">No retention data</p>'; return; }
  let html = '<table class="heatmap"><thead><tr><th class="hm-label">Cohort</th>';
  (heatmap.days || []).forEach(d => { html += `<th>Day ${d}</th>`; });
  html += '</tr></thead><tbody>';
  (heatmap.cohorts || []).forEach((cohort, i) => {
    html += `<tr><td class="hm-label">${cohort}</td>`;
    (heatmap.values[i] || []).forEach(val => {
      const pct = (val * 100).toFixed(1);
      html += `<td class="hm-cell" style="background:${getRetentionColor(val)};color:${val > 0.4 ? '#fff' : 'var(--text-secondary)'}">${pct}%</td>`;
    });
    html += '</tr>';
  });
  html += '</tbody></table>';
  container.innerHTML = html;
}
