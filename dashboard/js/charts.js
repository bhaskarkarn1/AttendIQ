/* ─── Chart Configurations ─────────────────────────────────────── */

const CHART_COLORS = {
  cyan: '#3ecfb4', violet: '#a78bfa', emerald: '#4ade80',
  amber: '#fbbf24', rose: '#fb7185', blue: '#60a5fa',
  accent: '#e8804a', accent2: '#f5a623',
  cyanAlpha: 'rgba(62,207,180,0.15)', violetAlpha: 'rgba(167,139,250,0.15)',
  emeraldAlpha: 'rgba(74,222,128,0.15)', amberAlpha: 'rgba(251,191,36,0.15)',
};

const CHART_DEFAULTS = {
  responsive: true, maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: 'rgba(240,235,228,0.6)', font: { family: 'Inter', size: 12 }, padding: 16, usePointStyle: true, pointStyleWidth: 8 } },
    tooltip: {
      backgroundColor: 'rgba(17,17,24,0.95)', titleColor: '#f0ebe4',
      bodyColor: 'rgba(240,235,228,0.7)', borderColor: 'rgba(255,255,255,0.08)', borderWidth: 1,
      padding: 14, cornerRadius: 10, titleFont: { family: 'Inter', weight: '600', size: 13 },
      bodyFont: { family: 'JetBrains Mono', size: 12 },
      displayColors: true, boxPadding: 6,
    },
  },
  scales: {
    x: { grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false }, ticks: { color: 'rgba(240,235,228,0.35)', font: { family: 'Inter', size: 11 } } },
    y: { grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false }, ticks: { color: 'rgba(240,235,228,0.35)', font: { family: 'JetBrains Mono', size: 11 } } },
  },
};

function createDAUChart(ctx, data) {
  const labels = data.map(d => {
    const date = new Date(d.date);
    return `${date.getMonth()+1}/${date.getDate()}`;
  });
  const values = data.map(d => d.dau);

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Daily Active Users',
        data: values,
        borderColor: CHART_COLORS.accent,
        backgroundColor: 'rgba(232,128,74,0.15)',
        fill: true, tension: 0.4, borderWidth: 2.5,
        pointRadius: 0, pointHoverRadius: 6,
        pointStyle: 'rectRounded',
      }]
    },
    options: { ...CHART_DEFAULTS },
  });
}

function createWAUChart(ctx, data) {
  const labels = data.map(d => {
    const date = new Date(d.date);
    return `${date.getMonth()+1}/${date.getDate()}`;
  });
  const values = data.map(d => d.wau);

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Weekly Active Users',
        data: values,
        borderColor: CHART_COLORS.cyan,
        backgroundColor: CHART_COLORS.cyanAlpha,
        fill: true, tension: 0.4, borderWidth: 2.5,
        pointRadius: 0, pointHoverRadius: 6,
        pointStyle: 'rectRounded',
      }]
    },
    options: { ...CHART_DEFAULTS },
  });
}

function createDailyTrendChart(ctx, data) {
  const labels = data.map(d => {
    const date = new Date(d.metric_date);
    return `${date.getMonth()+1}/${date.getDate()}`;
  });

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        { label: 'Quiz Pass Rate', data: data.map(d => (d.quiz_pass_rate * 100).toFixed(1)),
          borderColor: CHART_COLORS.emerald, backgroundColor: CHART_COLORS.emeraldAlpha,
          fill: false, tension: 0.4, borderWidth: 2.5,
          pointRadius: 0, pointHoverRadius: 6,
          pointStyle: 'rectRounded', yAxisID: 'y' },
        { label: 'Approval Rate', data: data.map(d => (d.approval_rate * 100).toFixed(1)),
          borderColor: CHART_COLORS.amber, backgroundColor: CHART_COLORS.amberAlpha,
          fill: false, tension: 0.4, borderWidth: 2.5,
          pointRadius: 0, pointHoverRadius: 6,
          pointStyle: 'rectRounded', yAxisID: 'y' },
      ]
    },
    options: {
      ...CHART_DEFAULTS,
      scales: {
        ...CHART_DEFAULTS.scales,
        y: { ...CHART_DEFAULTS.scales.y, ticks: { ...CHART_DEFAULTS.scales.y.ticks, callback: v => v + '%' } },
      }
    },
  });
}

function createClusterChart(ctx, clusters) {
  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: clusters.map(c => c.segment),
      datasets: [{
        data: clusters.map(c => c.count),
        backgroundColor: [CHART_COLORS.cyan, CHART_COLORS.violet, CHART_COLORS.amber, CHART_COLORS.rose],
        borderColor: '#0a0a0f', borderWidth: 3,
        hoverOffset: 8,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: 'rgba(240,235,228,0.6)', font: { family: 'Inter', size: 12 }, padding: 20, usePointStyle: true } },
        tooltip: CHART_DEFAULTS.plugins.tooltip,
      },
      cutout: '65%',
    },
  });
}
