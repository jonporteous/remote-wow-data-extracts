"""
Builds animal pass summaries from timestamp records and generates a
self-contained HTML pass record report.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class AnimalPasses:
    eid: str
    passes: List[datetime] = field(default_factory=list)

    @property
    def first_seen(self) -> datetime:
        return self.passes[0] if self.passes else None

    @property
    def last_seen(self) -> datetime:
        return self.passes[-1] if self.passes else None

    @property
    def total_passes(self) -> int:
        return len(self.passes)

    @property
    def active_days(self) -> int:
        return len({p.date() for p in self.passes})


def build_animal_passes(records: list) -> List[AnimalPasses]:
    """Group [{eid, recorded}] records by EID. Returns list sorted by EID."""
    animals: dict[str, AnimalPasses] = {}
    for r in records:
        eid = r["eid"]
        if eid not in animals:
            animals[eid] = AnimalPasses(eid=eid)
        animals[eid].passes.append(r["recorded"])

    for a in animals.values():
        a.passes.sort()

    return sorted(animals.values(), key=lambda a: a.eid)


def generate_pass_report(animals: List[AnimalPasses], records: list, meta: dict) -> str:
    """Return a self-contained HTML pass record report string."""

    farm     = meta.get("farm", "")
    paddock  = meta.get("paddock", "")
    generated = meta.get("generated", "")

    all_dt   = [r["recorded"] for r in records]
    min_date = min(all_dt).strftime("%d %b %Y") if all_dt else "N/A"
    max_date = max(all_dt).strftime("%d %b %Y") if all_dt else "N/A"
    days_covered = (max(all_dt).date() - min(all_dt).date()).days + 1 if all_dt else 0
    total_passes = sum(a.total_passes for a in animals)

    title_suffix = f" / {paddock}" if paddock and paddock != farm else ""

    # ── CSV payload ───────────────────────────────────────────────────────────
    csv_lines = ["EID,Date,Time"]
    for r in sorted(records, key=lambda x: (x["eid"], x["recorded"])):
        csv_lines.append(
            f'{r["eid"]},{r["recorded"].strftime("%d/%m/%Y")},{r["recorded"].strftime("%H:%M:%S")}'
        )
    csv_data = "\n".join(csv_lines)
    csv_filename = f'{farm.replace(" ", "_")}_PassRecord.csv'

    # ── Summary table rows ────────────────────────────────────────────────────
    summary_rows = ""
    for a in animals:
        fs = a.first_seen.strftime("%d/%m/%Y %H:%M") if a.first_seen else ""
        ls = a.last_seen.strftime("%d/%m/%Y %H:%M")  if a.last_seen  else ""
        summary_rows += (
            f'<tr><td>{a.eid}</td><td>{fs}</td><td>{ls}</td>'
            f'<td class="num">{a.total_passes}</td><td class="num">{a.active_days}</td></tr>\n'
        )

    # ── Detail table rows ─────────────────────────────────────────────────────
    detail_rows = ""
    for r in sorted(records, key=lambda x: (x["eid"], x["recorded"])):
        detail_rows += (
            f'<tr><td>{r["eid"]}</td>'
            f'<td>{r["recorded"].strftime("%d/%m/%Y")}</td>'
            f'<td>{r["recorded"].strftime("%H:%M:%S")}</td></tr>\n'
        )

    # ── HTML ──────────────────────────────────────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Pass Record — {farm}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Arial,sans-serif;background:#f0f4f8;color:#1a1a2e;font-size:14px}}
header{{background:#1e3a5f;color:white;padding:18px 28px}}
header h1{{font-size:20px;font-weight:700}}
header p{{font-size:12px;opacity:.75;margin-top:4px}}
.kpi-row{{display:flex;gap:14px;padding:20px 28px 8px;flex-wrap:wrap}}
.kpi{{background:white;border-left:4px solid #1d4ed8;border-radius:6px;padding:14px 20px;min-width:140px;box-shadow:0 1px 4px rgba(0,0,0,.08)}}
.kpi .val{{font-size:24px;font-weight:700;color:#1e3a5f}}
.kpi .lbl{{font-size:11px;color:#666;text-transform:uppercase;letter-spacing:.05em;margin-top:2px}}
.section{{background:white;margin:16px 28px;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,.08);overflow:hidden}}
.section h2{{background:#f8fafc;padding:12px 18px;font-size:14px;color:#1e3a5f;border-bottom:1px solid #e2e8f0}}
.toolbar{{padding:10px 18px;background:#f8fafc;border-bottom:1px solid #e2e8f0;display:flex;gap:10px;align-items:center}}
.toolbar input{{padding:5px 10px;border:1px solid #cbd5e1;border-radius:4px;font-size:13px;width:260px}}
.btn{{background:#1d4ed8;color:white;border:none;padding:7px 16px;border-radius:5px;cursor:pointer;font-size:13px;font-weight:600}}
.btn:hover{{background:#1e40af}}
.tbl-wrap{{overflow-x:auto;max-height:520px;overflow-y:auto}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:#1e3a5f;color:white;padding:9px 12px;text-align:left;cursor:pointer;white-space:nowrap;position:sticky;top:0;z-index:1;user-select:none}}
th:hover{{background:#2d5282}}
th.asc::after{{content:" ▲";font-size:10px}}
th.desc::after{{content:" ▼";font-size:10px}}
td{{padding:7px 12px;border-bottom:1px solid #f1f5f9}}
tr:hover td{{background:#f0f7ff}}
td.num{{text-align:right;font-variant-numeric:tabular-nums}}
.toggle-bar{{padding:10px 18px;background:#f8fafc;border-top:1px solid #e2e8f0}}
.toggle-bar a{{color:#1d4ed8;cursor:pointer;font-size:13px;text-decoration:none}}
footer{{text-align:center;padding:20px;color:#999;font-size:11px}}
</style>
</head>
<body>
<header>
  <h1>Pass Record &mdash; {farm}{title_suffix}</h1>
  <p>{min_date} &mdash; {max_date} &nbsp;|&nbsp; Generated {generated}</p>
</header>

<div class="kpi-row">
  <div class="kpi"><div class="val">{len(animals)}</div><div class="lbl">Animals</div></div>
  <div class="kpi"><div class="val">{total_passes:,}</div><div class="lbl">Total Passes</div></div>
  <div class="kpi"><div class="val">{days_covered}</div><div class="lbl">Days Covered</div></div>
  <div class="kpi"><div class="val">{min_date}</div><div class="lbl">First Pass</div></div>
  <div class="kpi"><div class="val">{max_date}</div><div class="lbl">Last Pass</div></div>
</div>

<div class="section">
  <h2>Animal Summary</h2>
  <div class="toolbar">
    <input type="text" id="sf" placeholder="Filter by EID&hellip;" oninput="filterTbl(this,'sb')">
    <button class="btn" onclick="dlCSV()">&#11123; Download CSV</button>
  </div>
  <div class="tbl-wrap">
    <table id="st">
      <thead><tr>
        <th onclick="sort('st',0)">EID</th>
        <th onclick="sort('st',1)">First Seen</th>
        <th onclick="sort('st',2)">Last Seen</th>
        <th onclick="sort('st',3)">Passes</th>
        <th onclick="sort('st',4)">Active Days</th>
      </tr></thead>
      <tbody id="sb">{summary_rows}</tbody>
    </table>
  </div>
</div>

<div class="toggle-bar">
  <a id="dtoggle" onclick="toggleDetail()">&#9654; Show full pass detail ({total_passes:,} records)</a>
</div>
<div id="ds" style="display:none">
<div class="section">
  <h2>All Passes</h2>
  <div class="toolbar">
    <input type="text" id="df" placeholder="Filter by EID&hellip;" oninput="filterTbl(this,'db')">
  </div>
  <div class="tbl-wrap">
    <table id="dt">
      <thead><tr>
        <th onclick="sort('dt',0)">EID</th>
        <th onclick="sort('dt',1)">Date</th>
        <th onclick="sort('dt',2)">Time</th>
      </tr></thead>
      <tbody id="db">{detail_rows}</tbody>
    </table>
  </div>
</div>
</div>

<footer>Datamars Remote WOW &mdash; Pass Record &nbsp;|&nbsp; {generated}</footer>

<script>
const CSV={repr(csv_data)};
const FNAME={repr(csv_filename)};
function dlCSV(){{
  const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([CSV],{{type:'text/csv'}}));
  a.download=FNAME; a.click();
}}
function filterTbl(inp,bodyId){{
  const q=inp.value.toLowerCase();
  document.getElementById(bodyId).querySelectorAll('tr').forEach(r=>{{
    r.style.display=r.cells[0].textContent.toLowerCase().includes(q)?'':'none';
  }});
}}
function toggleDetail(){{
  const el=document.getElementById('ds');
  const lnk=document.getElementById('dtoggle');
  if(el.style.display==='none'){{
    el.style.display='';
    lnk.innerHTML='&#9660; Hide full pass detail ({total_passes:,} records)';
  }}else{{
    el.style.display='none';
    lnk.innerHTML='&#9654; Show full pass detail ({total_passes:,} records)';
  }}
}}
function sort(tid,col){{
  const tbl=document.getElementById(tid);
  const tb=tbl.tBodies[0];
  const rows=Array.from(tb.rows);
  const th=tbl.tHead.rows[0].cells[col];
  const asc=!th.classList.contains('asc');
  tbl.tHead.rows[0].querySelectorAll('th').forEach(h=>h.classList.remove('asc','desc'));
  th.classList.add(asc?'asc':'desc');
  rows.sort((a,b)=>{{
    const av=a.cells[col].textContent.trim();
    const bv=b.cells[col].textContent.trim();
    const an=parseFloat(av.replace(/[^0-9.+-]/g,''));
    const bn=parseFloat(bv.replace(/[^0-9.+-]/g,''));
    if(!isNaN(an)&&!isNaN(bn)) return asc?an-bn:bn-an;
    return asc?av.localeCompare(bv):bv.localeCompare(av);
  }});
  rows.forEach(r=>tb.appendChild(r));
}}
</script>
</body>
</html>"""
