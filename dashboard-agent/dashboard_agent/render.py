"""Rendu d'un dashboard calculé en une page HTML autonome (Chart.js via CDN)."""

from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path


def render_html(data: dict) -> str:
    payload = dict(data, generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"))
    # "</" échappé : une valeur du fichier ne peut pas fermer la balise <script>.
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return (
        TEMPLATE.replace("__TITLE__", html.escape(data["title"]))
        .replace("__LANG__", html.escape(data.get("locale", "fr-FR").split("-")[0]))
        .replace("__DATA__", blob)
    )


def write_html(data: dict, path: str | Path) -> Path:
    path = Path(path)
    path.write_text(render_html(data), encoding="utf-8")
    return path


TEMPLATE = r"""<!doctype html>
<html lang="__LANG__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root {
  color-scheme: light;
  --page: #f9f9f7;
  --surface: #fcfcfb;
  --text-primary: #0b0b0b;
  --text-secondary: #52514e;
  --text-muted: #898781;
  --grid: #e1e0d9;
  --axis: #c3c2b7;
  --border: rgba(11,11,11,0.10);
  --good-text: #006300;
  --bad-text: #d03b3b;
  --deemph: #c3c2b7;
  --other: #b5b3ab;
  --series-1: #2a78d6; --series-2: #eb6834; --series-3: #1baf7a; --series-4: #eda100;
  --series-5: #e87ba4; --series-6: #008300; --series-7: #6250d6; --series-8: #e34948;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --page: #0d0d0d; --surface: #1a1a19;
    --text-primary: #f0efec; --text-secondary: #c3c2b7; --text-muted: #898781;
    --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
    --good-text: #0ca30c; --bad-text: #e66767; --deemph: #52514e; --other: #6b6a65;
    --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70; --series-4: #c98500;
    --series-5: #d55181; --series-6: #008300; --series-7: #9085e9; --series-8: #e66767;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --page: #0d0d0d; --surface: #1a1a19;
  --text-primary: #f0efec; --text-secondary: #c3c2b7; --text-muted: #898781;
  --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
  --good-text: #0ca30c; --bad-text: #e66767; --deemph: #52514e; --other: #6b6a65;
  --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70; --series-4: #c98500;
  --series-5: #d55181; --series-6: #008300; --series-7: #9085e9; --series-8: #e66767;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--page); color: var(--text-primary);
  font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif;
}
main { max-width: 1280px; margin: 0 auto; padding: 32px 24px 48px; }
header { display: flex; gap: 16px; align-items: flex-start; justify-content: space-between; margin-bottom: 24px; }
h1 { font-size: 28px; line-height: 1.2; margin: 0 0 4px; font-weight: 650; }
.subtitle { color: var(--text-secondary); margin: 0; }
.meta { color: var(--text-muted); font-size: 13px; margin-top: 4px; }
button.theme {
  flex: none; font: inherit; font-size: 13px; color: var(--text-secondary); background: var(--surface);
  border: 1px solid var(--border); border-radius: 8px; padding: 6px 12px; cursor: pointer;
}
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; min-width: 0; }
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 16px; }
.kpi-label { color: var(--text-secondary); font-size: 14px; }
.kpi-value { font-size: 30px; font-weight: 650; line-height: 1.2; margin: 6px 0 2px; }
.kpi-delta { font-size: 13px; color: var(--text-muted); min-height: 20px; }
.kpi-delta .up, .kpi-delta .down { font-weight: 600; }
.good { color: var(--good-text); } .bad { color: var(--bad-text); }
.spark { height: 40px; margin-top: 8px; }
.kpi-why { color: var(--text-muted); font-size: 12px; margin: 8px 0 0; }
.insights { margin-bottom: 16px; }
.insights h2, .chart h2 { font-size: 16px; margin: 0; font-weight: 600; }
.insights ul { margin: 8px 0 0; padding-left: 20px; color: var(--text-secondary); }
.charts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.chart.full { grid-column: 1 / -1; }
.why { color: var(--text-muted); font-size: 13px; margin: 2px 0 12px; }
.plot { position: relative; height: 300px; }
.chart.full .plot { height: 340px; }
details { margin-top: 12px; font-size: 13px; color: var(--text-secondary); }
summary { cursor: pointer; color: var(--text-muted); }
.scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { padding: 6px 10px; text-align: left; border-bottom: 1px solid var(--grid); white-space: nowrap; }
th { color: var(--text-muted); font-weight: 500; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
.heat td.num { border: 2px solid var(--surface); border-radius: 4px; }
.data-table { max-height: 420px; overflow: auto; }
footer { color: var(--text-muted); font-size: 12px; margin-top: 32px; text-align: center; }
@media (max-width: 860px) {
  main { padding: 20px 16px 32px; }
  .charts { grid-template-columns: minmax(0, 1fr); }
  header { flex-direction: column; }
  h1 { font-size: 24px; }
}
</style>
</head>
<body>
<main>
  <header>
    <div>
      <h1 id="title"></h1>
      <p class="subtitle" id="subtitle"></p>
      <div class="meta" id="meta"></div>
    </div>
    <button class="theme" id="theme" type="button">Thème</button>
  </header>
  <section class="kpis" id="kpis" aria-label="Indicateurs clés"></section>
  <section class="card insights" id="insights" hidden><h2>Constats clés</h2><ul></ul></section>
  <section class="charts" id="charts"></section>
  <footer>KPI et visuels choisis par l'agent IA · chiffres recalculés à partir des données source</footer>
</main>
<script type="application/json" id="dashboard-data">__DATA__</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script>
(() => {
const D = JSON.parse(document.getElementById('dashboard-data').textContent);
const OTHER = 'Autres';
const RAMP = ['#cde2fb','#b7d3f6','#9ec5f4','#86b6ef','#6da7ec','#5598e7','#3987e5','#2a78d6','#256abf','#1c5cab','#184f95','#104281','#0d366b'];
const charts = [];

const css = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const series = i => css(`--series-${(i % 8) + 1}`);
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
const alpha = (hex, a) => { const n = parseInt(hex.slice(1), 16); return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`; };

// ---------------------------------------------------------------- formats
function fmt(v, format, compact = false) {
  if (v == null || Number.isNaN(v)) return '–';
  // Notation compacte (12,5 k) seulement à partir de 1 000, sinon les petites décimales s'écrasent.
  const big = Math.abs(v) >= (compact ? 1000 : 100000);
  const c = big ? { notation: 'compact', maximumFractionDigits: 1 } : {};
  switch (format) {
    case 'currency':
      return new Intl.NumberFormat(D.locale, { style: 'currency', currency: D.currency,
        maximumFractionDigits: Math.abs(v) >= 100 || Number.isInteger(v) ? 0 : 2, ...c }).format(v);
    case 'percent':
      return new Intl.NumberFormat(D.locale, { style: 'percent', maximumFractionDigits: 1 }).format(v);
    case 'decimal':
      return new Intl.NumberFormat(D.locale, { maximumFractionDigits: 2, ...c }).format(v);
    default:
      return new Intl.NumberFormat(D.locale, { maximumFractionDigits: Number.isInteger(v) ? 0 : 1, ...c }).format(v);
  }
}
function toDate(iso) { const [y, m, d] = iso.split('-').map(Number); return new Date(y, m - 1, d); }
function fmtPeriod(iso, grain) {
  const d = toDate(iso);
  switch (grain) {
    case 'year': return String(d.getFullYear());
    case 'quarter': return `T${Math.floor(d.getMonth() / 3) + 1} ${d.getFullYear()}`;
    case 'month': return new Intl.DateTimeFormat(D.locale, { month: 'short', year: 'numeric' }).format(d);
    case 'week': return 'sem. du ' + new Intl.DateTimeFormat(D.locale, { day: 'numeric', month: 'short' }).format(d);
    default: return new Intl.DateTimeFormat(D.locale, { day: 'numeric', month: 'short', year: 'numeric' }).format(d);
  }
}
function chartLabels(c) {
  if (c.type === 'histogram') return c.labels.map(([a, b]) => `${fmt(a, c.format, true)} – ${fmt(b, c.format, true)}`);
  if (c.time_grain) return c.labels.map(l => fmtPeriod(l, c.time_grain));
  return c.labels;
}

// ---------------------------------------------------------------- header + KPI
function renderStatic() {
  document.getElementById('title').textContent = D.title;
  document.getElementById('subtitle').textContent = D.subtitle;
  document.getElementById('meta').textContent =
    `${new Intl.NumberFormat(D.locale).format(D.rows)} lignes analysées · généré le ${D.generated_at}`;

  const box = document.getElementById('kpis');
  D.kpis.forEach((k, i) => {
    const card = el('article', 'card kpi');
    card.append(el('div', 'kpi-label', k.label), el('div', 'kpi-value', fmt(k.value, k.format)));
    const delta = el('div', 'kpi-delta');
    if (k.delta_pct != null) {
      const up = k.delta_pct > 0, flat = k.delta_pct === 0;
      const good = flat ? '' : (up === k.higher_is_better ? 'good' : 'bad');
      const sign = el('span', `${up ? 'up' : 'down'} ${good}`,
        `${flat ? '■' : up ? '▲' : '▼'} ${new Intl.NumberFormat(D.locale, { style: 'percent', maximumFractionDigits: 1, signDisplay: 'exceptZero' }).format(k.delta_pct)}`);
      delta.append(sign, document.createTextNode(` ${fmtPeriod(k.current_period, k.trend_grain)} vs ${fmtPeriod(k.previous_period, k.trend_grain)}`));
    }
    card.append(delta);
    if (k.trend.length > 1) {
      const wrap = el('div', 'spark'); const cv = el('canvas');
      cv.setAttribute('role', 'img'); cv.setAttribute('aria-label', `Tendance de ${k.label}`);
      wrap.append(cv); card.append(wrap); k._canvas = cv;
    }
    if (k.rationale) card.append(el('p', 'kpi-why', k.rationale));
    box.append(card);
  });

  if (D.insights && D.insights.length) {
    const sec = document.getElementById('insights'); sec.hidden = false;
    const ul = sec.querySelector('ul');
    D.insights.forEach(t => ul.append(el('li', null, t)));
  }

  const grid = document.getElementById('charts');
  D.charts.forEach(c => {
    const card = el('article', `card chart ${c.width === 'full' ? 'full' : ''}`);
    card.append(el('h2', null, c.title), el('p', 'why', c.rationale));
    if (c.partial_period_excluded) {
      card.append(el('p', 'why', `Période en cours exclue (${fmtPeriod(c.partial_period_excluded, c.time_grain)}) : incomplète, elle fausserait la tendance.`));
    }
    if (c.type === 'heatmap') card.append(heatmapTable(c));
    else if (c.type === 'table') card.append(rankTable(c));
    else {
      const plot = el('div', 'plot'); const cv = el('canvas');
      cv.setAttribute('role', 'img'); cv.setAttribute('aria-label', c.title);
      plot.append(cv); card.append(plot); c._canvas = cv;
      card.append(dataTable(c));
    }
    grid.append(card);
  });
}

// ---------------------------------------------------------------- tables
function table(head, rows, numericFrom = 1) {
  const t = el('table'); const tr = el('tr');
  head.forEach((h, i) => tr.append(el('th', i >= numericFrom ? 'num' : null, h)));
  const thead = el('thead'); thead.append(tr); t.append(thead);
  const tb = el('tbody');
  rows.forEach(r => { const row = el('tr'); r.forEach((v, i) => row.append(el('td', i >= numericFrom ? 'num' : null, v))); tb.append(row); });
  t.append(tb); return t;
}
function dataTable(c) {
  const d = el('details'); d.append(el('summary', null, 'Voir les données'));
  const wrap = el('div', 'data-table');
  if (c.type === 'scatter') {
    const pts = c.datasets[0].data;
    wrap.append(table(['', c.x_label, c.value_label], pts.map((p, i) => [p.label || String(i + 1), fmt(p.x, 'decimal'), fmt(p.y, c.format)])));
  } else {
    const labels = chartLabels(c);
    const head = [''].concat(c.datasets.map(ds => ds.label));
    wrap.append(table(head, labels.map((l, i) => [l].concat(c.datasets.map(ds => fmt(ds.data[i], c.type === 'histogram' ? 'number' : c.format))))));
  }
  d.append(wrap); return d;
}
function rankTable(c) {
  const vals = c.datasets[0].data;
  const head = ['#', '', c.value_label].concat(c.shares ? ['Part'] : []);
  const rows = c.labels.map((l, i) => [String(i + 1), l, fmt(vals[i], c.format)]
    .concat(c.shares ? [fmt(c.shares[i], 'percent')] : []));
  const w = el('div', 'scroll'); w.append(table(head, rows, 2)); return w;
}
function heatmapTable(c) {
  const all = c.datasets.flatMap(ds => ds.data).filter(v => v != null);
  const lo = Math.min(...all), hi = Math.max(...all);
  const t = el('table', 'heat'); const tr = el('tr'); tr.append(el('th'));
  chartLabels(c).forEach(l => tr.append(el('th', 'num', l)));
  const thead = el('thead'); thead.append(tr); t.append(thead);
  const tb = el('tbody');
  c.datasets.forEach(ds => {
    const row = el('tr'); row.append(el('th', null, ds.label));
    ds.data.forEach((v, i) => {
      const td = el('td', 'num', fmt(v, c.format, true));
      td.title = `${ds.label} · ${c.labels[i]} : ${fmt(v, c.format)}`;
      if (v != null) {
        const step = hi > lo ? Math.round((v - lo) / (hi - lo) * (RAMP.length - 1)) : 6;
        td.style.background = RAMP[step];
        td.style.color = step >= 7 ? '#ffffff' : '#0b0b0b';
      }
      row.append(td);
    });
    tb.append(row);
  });
  t.append(tb);
  const w = el('div', 'scroll'); w.append(t); return w;
}

// ---------------------------------------------------------------- Chart.js
function baseOptions(c, { horizontal = false, legend = false, stacked = false } = {}) {
  const grid = { color: css('--grid'), drawTicks: false };
  const ticks = { color: css('--text-muted'), padding: 6 };
  const valueAxis = { beginAtZero: true, stacked, grid, border: { display: false },
    ticks: { ...ticks, callback: v => fmt(v, c.format, true) } };
  const catAxis = { stacked, grid: { display: false }, border: { color: css('--axis') }, ticks: { ...ticks, autoSkip: true, maxRotation: 0 } };
  return {
    responsive: true, maintainAspectRatio: false, animation: false,
    indexAxis: horizontal ? 'y' : 'x',
    interaction: { mode: 'index', intersect: false, axis: horizontal ? 'y' : 'x' },
    plugins: {
      legend: { display: legend, position: 'bottom', labels: { color: css('--text-secondary'), usePointStyle: true, boxWidth: 8, boxHeight: 8 } },
      tooltip: { callbacks: { label: ctx => `${ctx.dataset.label} : ${fmt(horizontal ? ctx.parsed.x : ctx.parsed.y, c.format)}` } },
    },
    scales: horizontal ? { x: valueAxis, y: catAxis } : { x: catAxis, y: valueAxis },
  };
}

function buildChart(c) {
  const labels = chartLabels(c);
  const multi = c.datasets.length > 1;
  const colorFor = (label, i) => label === OTHER ? css('--other') : series(i);
  const surface = css('--surface');
  let config;

  if (c.type === 'line' || c.type === 'area') {
    config = { type: 'line', data: { labels, datasets: c.datasets.map((ds, i) => {
      const col = colorFor(ds.label, i);
      return { label: ds.label, data: ds.data, borderColor: col, backgroundColor: alpha(col, 0.1),
        fill: c.type === 'area' || !multi, borderWidth: 2, tension: 0.25, pointRadius: 0,
        pointHoverRadius: 5, pointHoverBorderColor: surface, pointHoverBorderWidth: 2, spanGaps: true };
    }) }, options: baseOptions(c, { legend: multi }) };
  } else if (c.type === 'bar' || c.type === 'horizontal_bar') {
    const horizontal = c.type === 'horizontal_bar';
    config = { type: 'bar', data: { labels, datasets: [{ label: c.datasets[0].label, data: c.datasets[0].data,
      backgroundColor: c.labels.map(l => l === OTHER ? css('--other') : series(0)),
      maxBarThickness: 24, borderRadius: 4, borderSkipped: 'start' }] },
      options: baseOptions(c, { horizontal }) };
  } else if (c.type === 'stacked_bar' || c.type === 'grouped_bar') {
    const stacked = c.type === 'stacked_bar';
    config = { type: 'bar', data: { labels, datasets: c.datasets.map((ds, i) => ({ label: ds.label, data: ds.data,
      backgroundColor: colorFor(ds.label, i), maxBarThickness: stacked ? 32 : 18,
      borderColor: surface, borderWidth: stacked ? { top: 2 } : 0,
      borderRadius: stacked ? 0 : 4, borderSkipped: 'start' })) },
      options: baseOptions(c, { legend: true, stacked }) };
  } else if (c.type === 'donut') {
    const opts = { responsive: true, maintainAspectRatio: false, animation: false, cutout: '62%',
      plugins: { legend: { position: 'right', labels: { color: css('--text-secondary'), usePointStyle: true, boxWidth: 8, boxHeight: 8 } },
        tooltip: { callbacks: { label: ctx => `${ctx.label} : ${fmt(ctx.parsed, c.format)}${c.shares ? ' (' + fmt(c.shares[ctx.dataIndex], 'percent') + ')' : ''}` } } } };
    config = { type: 'doughnut', data: { labels, datasets: [{ label: c.datasets[0].label, data: c.datasets[0].data,
      backgroundColor: c.labels.map((l, i) => colorFor(l, i)), borderColor: surface, borderWidth: 2 }] }, options: opts };
  } else if (c.type === 'histogram') {
    const o = baseOptions({ ...c, format: 'number' });
    o.plugins.tooltip.callbacks.label = ctx => `${fmt(ctx.parsed.y, 'number')} lignes`;
    o.scales.x.ticks.maxRotation = 0;
    config = { type: 'bar', data: { labels, datasets: [{ label: 'Nombre de lignes', data: c.datasets[0].data,
      backgroundColor: series(0), barPercentage: 1, categoryPercentage: 1,
      borderColor: surface, borderWidth: { left: 1, right: 1 }, borderRadius: { topLeft: 4, topRight: 4 }, borderSkipped: 'start' }] }, options: o };
  } else if (c.type === 'scatter') {
    const o = baseOptions(c);
    o.interaction = { mode: 'nearest', intersect: true };
    o.scales.x = { type: 'linear', grid: { color: css('--grid') }, border: { display: false },
      title: { display: true, text: c.x_label, color: css('--text-muted') },
      ticks: { color: css('--text-muted'), callback: v => fmt(v, 'decimal', true) } };
    o.scales.y.beginAtZero = false;
    o.scales.y.title = { display: true, text: c.value_label, color: css('--text-muted') };
    o.plugins.tooltip.callbacks.label = ctx => `${ctx.raw.label ? ctx.raw.label + ' · ' : ''}${fmt(ctx.raw.x, 'decimal')} ; ${fmt(ctx.raw.y, c.format)}`;
    config = { type: 'scatter', data: { datasets: [{ label: c.datasets[0].label, data: c.datasets[0].data,
      backgroundColor: series(0), borderColor: surface, borderWidth: 2, pointRadius: 5, pointHoverRadius: 7 }] }, options: o };
  }
  if (config) charts.push(new Chart(c._canvas, config));
}

function buildSpark(k) {
  const muted = css('--deemph'), accent = series(0), n = k.trend.length;
  charts.push(new Chart(k._canvas, {
    type: 'line',
    data: { labels: k.trend.map(t => fmtPeriod(t.period, k.trend_grain)), datasets: [{ data: k.trend.map(t => t.value),
      borderColor: muted, borderWidth: 2, tension: 0.3, fill: false,
      pointRadius: k.trend.map((_, i) => i === n - 1 ? 3.5 : 0), pointBackgroundColor: accent, pointBorderColor: accent,
      pointHoverRadius: 4 }] },
    options: { responsive: true, maintainAspectRatio: false, animation: false,
      interaction: { mode: 'index', intersect: false },
      plugins: { legend: { display: false }, tooltip: { displayColors: false, callbacks: { label: ctx => fmt(ctx.parsed.y, k.format) } } },
      scales: { x: { display: false }, y: { display: false } } },
  }));
}

function drawAll() {
  charts.splice(0).forEach(ch => ch.destroy());
  if (typeof Chart === 'undefined') return;
  Chart.defaults.font.family = 'system-ui, -apple-system, "Segoe UI", sans-serif';
  Chart.defaults.color = css('--text-secondary');
  D.kpis.forEach(k => k._canvas && buildSpark(k));
  D.charts.forEach(c => c._canvas && buildChart(c));
}

// ---------------------------------------------------------------- thème
const root = document.documentElement;
const btn = document.getElementById('theme');
try { const saved = localStorage.getItem('dashboard-theme'); if (saved) root.dataset.theme = saved; } catch (e) {}
const isDark = () => root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
const syncBtn = () => { btn.textContent = isDark() ? 'Thème clair' : 'Thème sombre'; };
btn.addEventListener('click', () => {
  root.dataset.theme = isDark() ? 'light' : 'dark';
  try { localStorage.setItem('dashboard-theme', root.dataset.theme); } catch (e) {}
  syncBtn(); drawAll();
});
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => { syncBtn(); drawAll(); });

renderStatic(); syncBtn(); drawAll();
})();
</script>
</body>
</html>
"""
