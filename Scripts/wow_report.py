from datetime import datetime
from typing import List, Optional
import html as html_module


# ── helpers ───────────────────────────────────────────────────────────────────

def _esc(v) -> str:
    return html_module.escape(str(v)) if v is not None else ""


def _fmt_weight(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"{v:.1f} kg"


def _fmt_growth(v: Optional[float]) -> str:
    if v is None:
        return "—"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.0f} g/day"


def _fmt_change(v: Optional[float]) -> str:
    if v is None:
        return "—"
    sign = "+" if v > 0 else ""
    color = "#16a34a" if v > 0 else ("#dc2626" if v < 0 else "#374151")
    return f'<span style="color:{color};font-weight:600">{sign}{v:.1f} kg</span>'


# ── CSS ───────────────────────────────────────────────────────────────────────

_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, -apple-system, Arial, sans-serif; font-size: 14px;
       background: #f3f4f6; color: #111827; }
a { color: #1d4ed8; }

.page-header {
  background: #1e3a5f;
  color: white;
  padding: 18px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.page-header h1 { font-size: 20px; font-weight: 700; letter-spacing: 0.3px; }
.page-header .meta { font-size: 12px; opacity: 0.75; text-align: right; line-height: 1.7; }

.content { max-width: 1200px; margin: 0 auto; padding: 24px 20px 48px; }

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
  margin-bottom: 28px;
}
.kpi-tile {
  background: white;
  border-radius: 8px;
  padding: 14px 16px;
  border-left: 4px solid #1d4ed8;
  box-shadow: 0 1px 3px rgba(0,0,0,.08);
}
.kpi-tile .label { font-size: 11px; color: #6b7280; text-transform: uppercase;
                   letter-spacing: 0.5px; margin-bottom: 4px; }
.kpi-tile .value { font-size: 22px; font-weight: 700; color: #1e3a5f; }
.kpi-tile .sub   { font-size: 11px; color: #9ca3af; margin-top: 2px; }

.section-title {
  font-size: 15px; font-weight: 700; color: #1e3a5f;
  margin: 0 0 12px; padding-bottom: 6px;
  border-bottom: 2px solid #e5e7eb;
}
.card {
  background: white; border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,.08);
  margin-bottom: 24px; overflow: hidden;
}
.card-body { padding: 20px 24px; }

/* Summary table */
table.summary { width: 100%; border-collapse: collapse; }
table.summary th {
  background: #1e3a5f; color: white;
  padding: 9px 12px; text-align: left;
  font-size: 12px; font-weight: 600;
  letter-spacing: 0.3px; cursor: pointer;
  user-select: none; white-space: nowrap;
}
table.summary th:hover { background: #2d5282; }
table.summary th::after { content: " ⇅"; opacity: 0.5; font-size: 10px; }
table.summary td { padding: 8px 12px; border-bottom: 1px solid #f3f4f6; font-size: 13px; }
table.summary tr:hover td { background: #f9fafb; }
table.summary tr:last-child td { border-bottom: none; }
.eid-link { cursor: pointer; color: #1d4ed8; text-decoration: underline; font-family: monospace; font-size: 12px; }

/* Navigator */
.nav-bar {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  background: #f8fafc; border-bottom: 1px solid #e5e7eb; padding: 12px 20px;
}
.nav-bar button {
  background: #1d4ed8; color: white; border: none; border-radius: 5px;
  padding: 7px 14px; cursor: pointer; font-size: 13px; font-weight: 600;
}
.nav-bar button:hover { background: #1e40af; }
.nav-bar button:disabled { background: #93c5fd; cursor: default; }
.nav-bar select {
  padding: 6px 10px; border-radius: 5px; border: 1px solid #d1d5db;
  font-size: 13px; font-family: monospace; min-width: 200px;
  background: white; color: #111827;
}
.nav-counter { font-size: 12px; color: #6b7280; margin-left: 4px; }

.animal-card { display: none; }
.animal-card.active { display: block; }
.animal-card img { width: 100%; max-width: 100%; display: block; }

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px; padding: 16px 20px 20px;
  background: #f8fafc; border-top: 1px solid #e5e7eb;
}
.stat-item .stat-label { font-size: 11px; color: #6b7280; text-transform: uppercase;
                          letter-spacing: 0.4px; }
.stat-item .stat-value { font-size: 15px; font-weight: 700; color: #1e3a5f; margin-top: 2px; }

/* Data table */
table.data { width: 100%; border-collapse: collapse; font-size: 12px; }
table.data th {
  background: #374151; color: white; padding: 8px 10px;
  text-align: left; cursor: pointer; user-select: none; white-space: nowrap;
}
table.data th:hover { background: #4b5563; }
table.data th::after { content: " ⇅"; opacity: 0.5; font-size: 10px; }
table.data td { padding: 6px 10px; border-bottom: 1px solid #f3f4f6; font-family: monospace; }
table.data tr:nth-child(even) td { background: #f9fafb; }
table.data tr:hover td { background: #eff6ff; }
.no-data { text-align:center; color:#9ca3af; padding: 32px; font-style: italic; }

.footer { text-align: center; color: #9ca3af; font-size: 11px; margin-top: 32px; }
"""

# ── JavaScript ────────────────────────────────────────────────────────────────

_JS = """
(function() {
  const cards = document.querySelectorAll('.animal-card');
  const select = document.getElementById('eid-select');
  const counter = document.getElementById('nav-counter');
  const btnPrev = document.getElementById('btn-prev');
  const btnNext = document.getElementById('btn-next');
  let current = 0;

  function showAnimal(idx) {
    if (idx < 0 || idx >= cards.length) return;
    cards[current].classList.remove('active');
    cards[idx].classList.add('active');
    select.selectedIndex = idx;
    counter.textContent = (idx + 1) + ' of ' + cards.length;
    btnPrev.disabled = idx === 0;
    btnNext.disabled = idx === cards.length - 1;
    current = idx;
    document.getElementById('animal-section').scrollIntoView({behavior:'smooth', block:'start'});
  }

  btnPrev.onclick = () => showAnimal(current - 1);
  btnNext.onclick = () => showAnimal(current + 1);
  select.onchange = () => showAnimal(select.selectedIndex);

  // EID links in summary table
  document.querySelectorAll('.eid-link').forEach(el => {
    el.onclick = () => {
      const idx = parseInt(el.dataset.idx);
      showAnimal(idx);
    };
  });

  showAnimal(0);

  // Sortable tables
  document.querySelectorAll('table.sortable').forEach(table => {
    const headers = table.querySelectorAll('th');
    const sortState = {};
    headers.forEach((th, col) => {
      sortState[col] = true;
      th.onclick = () => {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.rows);
        const asc = sortState[col];
        rows.sort((a, b) => {
          const va = a.cells[col] ? a.cells[col].textContent.trim() : '';
          const vb = b.cells[col] ? b.cells[col].textContent.trim() : '';
          const na = parseFloat(va.replace(/[^0-9.+-]/g, ''));
          const nb = parseFloat(vb.replace(/[^0-9.+-]/g, ''));
          if (!isNaN(na) && !isNaN(nb)) return asc ? na - nb : nb - na;
          return asc ? va.localeCompare(vb) : vb.localeCompare(va);
        });
        rows.forEach(r => tbody.appendChild(r));
        sortState[col] = !asc;
      };
    });
  });

  // CSV download
  document.getElementById('btn-download-csv').onclick = function() {
    const rows = document.querySelectorAll('table.data tbody tr');
    let csv = 'EID,Date,Time,Weight (kg),Growth (g/day)\\n';
    rows.forEach(r => {
      const cells = Array.from(r.querySelectorAll('td'));
      csv += cells.map(c => '"' + c.textContent.trim().replace(/"/g, '""') + '"').join(',') + '\\n';
    });
    const blob = new Blob([csv], {type: 'text/csv'});
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
    a.download = 'wow_data.csv'; a.click();
  };
})();
"""


# ── builders ──────────────────────────────────────────────────────────────────

def _kpi_tile(label, value, sub=""):
    return (
        f'<div class="kpi-tile">'
        f'<div class="label">{_esc(label)}</div>'
        f'<div class="value">{value}</div>'
        f'{"<div class=sub>" + _esc(sub) + "</div>" if sub else ""}'
        f'</div>'
    )


def _summary_table(animals) -> str:
    rows = []
    for idx, a in enumerate(animals):
        days = a.observation_days
        days_str = f"{days}d" if days is not None else "—"
        rows.append(
            f"<tr>"
            f'<td><span class="eid-link" data-idx="{idx}">{_esc(a.eid)}</span></td>'
            f"<td>{len(a.weights)}</td>"
            f"<td>{len(a.growths)}</td>"
            f"<td>{_fmt_weight(a.first_weight)}</td>"
            f"<td>{_fmt_weight(a.last_weight)}</td>"
            f"<td>{_fmt_change(a.weight_change)}</td>"
            f"<td>{_fmt_growth(a.avg_growth)}</td>"
            f"<td>{days_str}</td>"
            f"</tr>"
        )
    return (
        '<table class="summary sortable">'
        "<thead><tr>"
        "<th>EID</th><th>Weight readings</th><th>Growth readings</th>"
        "<th>First weight</th><th>Last weight</th><th>Change</th>"
        "<th>Avg growth</th><th>Span</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
    )


def _animal_cards(animals, charts) -> str:
    parts = []
    for idx, a in enumerate(animals):
        chart_b64 = charts.get(a.eid)
        img_html = f'<img src="{chart_b64}" alt="Chart for {_esc(a.eid)}">' if chart_b64 else '<p class="no-data">No chart available</p>'

        days = a.observation_days
        parts.append(
            f'<div class="animal-card" data-idx="{idx}">'
            f"{img_html}"
            f'<div class="stats-row">'
            f'<div class="stat-item"><div class="stat-label">EID</div>'
            f'<div class="stat-value" style="font-family:monospace;font-size:12px">{_esc(a.eid)}</div></div>'
            f'<div class="stat-item"><div class="stat-label">First weight</div>'
            f'<div class="stat-value">{_fmt_weight(a.first_weight)}</div></div>'
            f'<div class="stat-item"><div class="stat-label">Last weight</div>'
            f'<div class="stat-value">{_fmt_weight(a.last_weight)}</div></div>'
            f'<div class="stat-item"><div class="stat-label">Change</div>'
            f'<div class="stat-value">{_fmt_change(a.weight_change)}</div></div>'
            f'<div class="stat-item"><div class="stat-label">Avg growth</div>'
            f'<div class="stat-value">{_fmt_growth(a.avg_growth)}</div></div>'
            f'<div class="stat-item"><div class="stat-label">Observation span</div>'
            f'<div class="stat-value">{f"{days} days" if days is not None else "—"}</div></div>'
            f'<div class="stat-item"><div class="stat-label">Weight readings</div>'
            f'<div class="stat-value">{len(a.weights)}</div></div>'
            f'<div class="stat-item"><div class="stat-label">Growth readings</div>'
            f'<div class="stat-value">{len(a.growths)}</div></div>'
            f"</div>"
            f"</div>"
        )
    return "\n".join(parts)


def _data_table(weight_records, growth_records) -> str:
    # Merge by (eid, date) key — match weights and growths to the same row where possible
    rows_by_key: dict = {}
    for w in weight_records:
        key = (w.eid, w.recorded.strftime("%Y-%m-%d"), w.recorded.strftime("%H:%M:%S"))
        rows_by_key[key] = {"eid": w.eid, "date": w.recorded.strftime("%d/%m/%Y"),
                            "time": w.recorded.strftime("%H:%M:%S"), "weight": w.weight, "growth": None}

    for g in growth_records:
        # Growth records are often at midnight — try date-only match first
        date_str = g.recorded.strftime("%Y-%m-%d")
        time_str = g.recorded.strftime("%H:%M:%S")
        key = (g.eid, date_str, time_str)
        if key in rows_by_key:
            rows_by_key[key]["growth"] = g.growth
        else:
            rows_by_key[key] = {"eid": g.eid, "date": g.recorded.strftime("%d/%m/%Y"),
                                "time": time_str, "weight": None, "growth": g.growth}

    sorted_rows = sorted(rows_by_key.values(), key=lambda r: (r["eid"], r["date"], r["time"]))

    if not sorted_rows:
        return '<p class="no-data">No data records.</p>'

    trs = []
    for r in sorted_rows:
        w_str = f'{r["weight"]:.1f}' if r["weight"] is not None else ""
        g_str = f'{r["growth"]:.0f}' if r["growth"] is not None else ""
        trs.append(
            f'<tr><td>{_esc(r["eid"])}</td><td>{_esc(r["date"])}</td>'
            f'<td>{_esc(r["time"])}</td><td>{w_str}</td><td>{g_str}</td></tr>'
        )

    return (
        '<table class="data sortable">'
        "<thead><tr><th>EID</th><th>Date</th><th>Time</th>"
        "<th>Weight (kg)</th><th>Growth (g/day)</th></tr></thead>"
        f"<tbody>{''.join(trs)}</tbody>"
        "</table>"
    )


# ── main entry ────────────────────────────────────────────────────────────────

def generate_report(animals, weight_records, growth_records, charts: dict, meta: dict) -> str:
    farm = meta.get("farm", "")
    paddock = meta.get("paddock", "")
    start = meta.get("start", "")
    end = meta.get("end", "")
    generated = meta.get("generated", "")

    n_animals = len(animals)
    all_weights = [w.weight for a in animals for w in a.weights]
    all_growths = [g.growth for a in animals for g in a.growths]

    avg_weight = sum(all_weights) / len(all_weights) if all_weights else None
    min_weight = min(all_weights) if all_weights else None
    max_weight = max(all_weights) if all_weights else None
    avg_growth = sum(all_growths) / len(all_growths) if all_growths else None
    gainers = sum(1 for a in animals if a.weight_change is not None and a.weight_change > 0)

    kpis = "".join([
        _kpi_tile("Animals", n_animals),
        _kpi_tile("Date range", f"{start}", f"to {end}"),
        _kpi_tile("Avg weight", f"{avg_weight:.0f} kg" if avg_weight else "—"),
        _kpi_tile("Weight range", f"{min_weight:.0f}–{max_weight:.0f} kg" if min_weight else "—"),
        _kpi_tile("Avg growth", _fmt_growth(avg_growth)),
        _kpi_tile("Weight gain", f"{gainers} / {n_animals}", "animals gaining"),
        _kpi_tile("Weight readings", sum(len(a.weights) for a in animals)),
        _kpi_tile("Growth readings", sum(len(a.growths) for a in animals)),
    ])

    select_options = "\n".join(
        f'<option value="{i}">{_esc(a.eid)}</option>'
        for i, a in enumerate(animals)
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WOW Report — {_esc(farm)} — {_esc(paddock)}</title>
<style>{_CSS}</style>
</head>
<body>

<div class="page-header">
  <div>
    <h1>Remote WOW — Weight &amp; Growth Report</h1>
    <div style="font-size:13px;opacity:0.85;margin-top:3px">{_esc(farm)} &nbsp;/&nbsp; {_esc(paddock)}</div>
  </div>
  <div class="meta">
    Generated: {_esc(generated)}<br>
    Period: {_esc(start)} → {_esc(end)}
  </div>
</div>

<div class="content">

  <!-- KPIs -->
  <div class="kpi-grid">{kpis}</div>

  <!-- Summary table -->
  <div class="card">
    <div class="card-body">
      <h2 class="section-title">All Animals — Summary</h2>
      {_summary_table(animals)}
    </div>
  </div>

  <!-- Per-animal navigator -->
  <div class="card" id="animal-section">
    <div class="nav-bar">
      <button id="btn-prev">&#9664; Prev</button>
      <select id="eid-select">{select_options}</select>
      <button id="btn-next">Next &#9654;</button>
      <span class="nav-counter" id="nav-counter">1 of {n_animals}</span>
      <span style="flex:1"></span>
      <button id="btn-download-csv" style="background:#374151">&#8595; Download CSV</button>
    </div>
    <div id="animal-cards-container">
      {_animal_cards(animals, charts)}
    </div>
  </div>

  <!-- Full data table -->
  <div class="card">
    <div class="card-body">
      <h2 class="section-title">All Records</h2>
      {_data_table(weight_records, growth_records)}
    </div>
  </div>

  <div class="footer">Remote WOW Data Report &nbsp;·&nbsp; Generated {_esc(generated)} &nbsp;·&nbsp; Datamars Technical Support</div>

</div>

<script>{_JS}</script>
</body>
</html>"""
