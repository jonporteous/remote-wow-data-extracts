# Remote WOW Data Extractor

## Overview

Python tool that fetches weight and growth data from Precision Pastoral (PPL) for
Remote Walkover Weighing (WOW) devices, then generates a self-contained HTML report
with per-animal weight and growth charts.

Replaces the manual 20-step process: Postman API calls → JSON → 3 Excel spinner files
→ copy-paste → per-animal charts in an .xlsm macro workbook.

**Target product**: Datamars Remote Walkover Weighing (WOW) units  
**Data source**: Precision Pastoral (PPL) REST API at `http://cawd2.nsavant.com.au/api`

---

## Quick Start

```batch
run_wow.bat          # Interactive launcher — prompts for date range, then farm
```

```bash
# Command line — select farm from spreadsheet list:
python analyse_wow.py --days 14

# Specify farm directly:
python analyse_wow.py --farm tobruk --days 14
python analyse_wow.py --farm tobruk --paddock "Tobruk WOW" --start 2025-03-01 --end 2025-03-31

# List paddocks for a farm:
python analyse_wow.py --farm tobruk --list-paddocks

# File mode (previously downloaded JSON from Postman):
python analyse_wow.py --weights blue.json --growth red.json --farm MyFarm --paddock "WOW Unit 1"
```

Output saved to `Output\YYYY-MM-DD_FarmName_PaddockName\report.html` — opens automatically in browser.

---

## Architecture

```
Remote WOW Data Extracts/
├── CLAUDE.md
├── analyse_wow.py              # Entry point — orchestrates everything
├── run_wow.bat                 # Interactive launcher (date range → farm → report)
├── Scripts/
│   ├── wow_fetcher.py          # PPL API calls (login, paddock list, weights, growth)
│   ├── wow_parser.py           # JSON → dataclasses (WeightRecord, GrowthRecord, AnimalData)
│   ├── wow_charts.py           # Per-animal matplotlib charts (weight + growth), base64 PNG
│   └── wow_report.py           # Self-contained HTML report generator
├── Background Info/
│   ├── Global WOW Claude.xlsx  # Master WOW unit list (farm name, PPL Name, status)
│   └── Json to Spiner.xlsx     # Reference: JSON field mapping for PPL API responses
└── Output/                     # Generated reports (git-ignored)
```

---

## PPL API

Base URL: `http://cawd2.nsavant.com.au/api`

**IP whitelisting required**: The PPL server blocks all requests from non-whitelisted IPs.
Whitelisting must be done per farm via the master `nsavant` account, and the IP must also
be added to the PPL Server's Security Groups by BGP support.

| Endpoint | Purpose |
|---|---|
| `GET /api/login/<username>/<password>` | Session auth — returns `true`/`false` |
| `GET /api/paddock/` | List paddocks for logged-in farm |
| `GET /api/data/cleansed/<id>/<start>/<end>` | Cleansed/validated weight records (JSON) |
| `GET /api/data/reported/<id>/<start>/<end>` | Growth / polynomial regression records (JSON) |

- Farm **username == password** (PPL Name from `Global WOW Claude.xlsx`)
- Date format: `YYYY-MM-DD`
- PPL GUI export is limited to 65,000 rows; API has no such limit

---

## Data Flow

```
PPL API (JSON)                          or   Postman JSON files
       │                                            │
       ▼                                            ▼
wow_fetcher.py ──► wow_parser.py ──► build_animals()
                        │
                        ▼
                  wow_charts.py  ──► per-animal matplotlib charts (base64 PNG)
                        │
                        ▼
                  wow_report.py  ──► self-contained HTML report
                                       • KPI summary tiles
                                       • All-animals sortable table
                                       • Per-animal navigator (dropdown + prev/next)
                                       • Weight chart (blue) + Growth chart (red)
                                       • Download CSV button
```

---

## Farm Selection

`Global WOW Claude.xlsx` in `Background Info/` contains all global WOW installations.
When `--farm` is omitted, `analyse_wow.py` reads this file and shows a numbered list of
all **Installed** units with a valid PPL Name:

```
  Available WOW Units  (92 installed)

    #    Farm / Account                       Asset
    1.   Gladfield Dairies Ltd                Gladfield Dairies WOW
    2.   Tobruk Farms Ltd                     Tobruk Dairy WOW
    ...

  Select unit number: 2
```

The selected row's **PPL Name** is used as both the username and password for PPL login.

---

## Paddock Matching

After login, `analyse_wow.py` tries to auto-match the paddock to the PPL Name:

1. Exact case-insensitive match
2. PPL Name contained in paddock name (or vice versa)
3. If only one paddock exists → auto-select
4. If no match → show numbered paddock list for manual selection

Note: some farms have paddock names that differ from the PPL Name
(e.g. Glenflorrie 2023 has paddocks "Tarall Caral" and "Merejida").

---

## JSON Field Names

**Cleansed weights** (`/api/data/cleansed/`):
- `eid`, `weight`, `recorded`, `paddock_name`

**Growth / reported** (`/api/data/reported/`):
- `eid`, `growth` (or `reported_weight` / `value`), `recorded`, `paddock_name`

The parser handles Power Query-style `Column1.fieldname` prefixes automatically
(produced when loading API JSON via Excel's Get Data feature).

---

## Dependencies

```
requests       # HTTP client for PPL API
matplotlib     # Per-animal charts
pandas         # Farm list spreadsheet reading
openpyxl       # Excel file support for pandas
```

All installed automatically by `run_wow.bat` on first run.
Python 3.9+ required (3.13 tested).

---

## Output

Each run produces a folder `Output/YYYY-MM-DD_FarmName_PaddockName/` containing:

- **`report.html`** — self-contained report (no external dependencies, safe to email)

The report includes:
- KPI tiles: animal count, date range, avg weight, weight range, avg growth, gainers
- Sortable summary table (one row per animal)
- Per-animal navigator with weight + growth charts
- Full sortable data table
- Download CSV button

---

## Common Issues

| Symptom | Cause | Fix |
|---|---|---|
| Connection timeout | IP not whitelisted | Add IP via nsavant master account + BGP support ticket |
| Login fails | Wrong username or VPN active | Check PPL Name in spreadsheet; disconnect VPN |
| No paddocks returned | Correct login but empty account | Verify farm has active paddock in PPL |
| No data for date range | WOW offline or no animals weighed | Try a wider date range |
| Paddock not auto-matched | PPL Name ≠ paddock name | Select manually from the list shown |
