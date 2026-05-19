/* ─── Utility helpers ───────────────────────────────────────────── */

const DATA_DIR = '../data/dashboard/';

async function loadJSON(file) {
  const res = await fetch(DATA_DIR + file);
  if (!res.ok) throw new Error(`Failed to load ${file}`);
  return res.json();
}

function animateValue(el, start, end, duration, suffix = '') {
  const range = end - start;
  const startTime = performance.now();
  function step(t) {
    const elapsed = t - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = start + range * eased;
    el.textContent = (Number.isInteger(end) ? Math.round(current) : current.toFixed(1)) + suffix;
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function formatNumber(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return n.toLocaleString();
}

function getRiskColor(value) {
  if (value > 0.7) return 'var(--rose)';
  if (value > 0.4) return 'var(--amber)';
  return 'var(--emerald)';
}

function getRetentionColor(value) {
  // Dark-theme optimized: low retention → rose, high → emerald
  const intensity = 0.15 + value * 0.55;
  if (value > 0.5) return `rgba(74, 222, 128, ${intensity})`;
  if (value > 0.3) return `rgba(251, 191, 36, ${intensity})`;
  return `rgba(251, 113, 133, ${intensity})`;
}

function getSeverityIcon(severity) {
  const icons = { critical: '🔴', warning: '🟡', info: '🔵' };
  return icons[severity] || '⚪';
}
