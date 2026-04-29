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
run_wow.bat          # Interactive launcher — API mode (requires IP whitelist)
run_local.bat        # Interactive launcher — local file mode (no API required)
```

```bash
# API mode — select farm from spreadsheet list:
python analyse_wow.py --days 14

# Specify farm directly:
python analyse_wow.py --farm tobruk --days 14
python analyse_wow.py --farm tobruk --paddock "Tobruk WOW" --start 2025-03-01 --end 2025-03-31

# List paddocks for a farm:
python analyse_wow.py --farm tobruk --list-paddocks

# Local file mode (device CSVs or PPL Upload xlsx — no API required):
python analyse_wow.py --input-dir Input

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
├── run_wow.bat                 # Interactive launcher — API mode
├── run_local.bat               # Interactive launcher — local file mode
├── Scripts/
│   ├── wow_fetcher.py          # PPL API calls (login, paddock list, weights, growth)
│   ├── wow_parser.py           # JSON → dataclasses (WeightRecord, GrowthRecord, AnimalData)
│   ├── wow_charts.py           # Per-animal matplotlib charts (weight + growth), base64 PNG
│   ├── wow_report.py           # Self-contained HTML report generator
│   └── wow_csv_parser.py       # Local file parser (device CSVs + PPL Upload xlsx)
├── Background Info/
│   ├── Global WOW Claude.xlsx  # Master WOW unit list (farm name, PPL Name, status)
│   └── Json to Spiner.xlsx     # Reference: JSON field mapping for PPL API responses
├── Input/                      # Drop source files here for local file mode
│   └── Processed/              # Files moved here automatically after processing
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
API MODE                                LOCAL FILE MODE
─────────────────────────────────       ───────────────────────────────────────
PPL API (JSON)   or  Postman JSON       Input\*.csv  /  Input\*.xlsx
       │                    │                    │
       ▼                    ▼                    ▼
wow_fetcher.py       (file read)         wow_csv_parser.py
       │                    │                    │
       └────────────────────┘                    │
                    │                            │
                    ▼                            ▼
             wow_parser.py ◄──────────── raw weight dicts
                    │
                    ▼
            build_animals()
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

After local file processing, source files are automatically moved to `Input\Processed\`.

---

## Farm Selection

`Global WOW Claude.xlsx` in `Background Info/` contains all global WOW installations.
When `--farm` is omitted, `analyse_wow.py` reads this file and shows a numbered list of
all **Installed** units with a valid PPL Name, **sorted alphabetically**:

```
  Available WOW Units  (92 installed)

    #    Farm / Account                       Asset
    1.   3D Grazing (Current)                 3D Grazing WOW (Current)
    2.   3M Dairy                             3M Dairy WOW #2 - West Exit WOW
    3.   3M Dairy                             3M Dairy WOW #1 - East Exit Race WOW
    ...

  Select unit number: 49
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

## Local File Mode

When the PPL API is inaccessible (IP not whitelisted, working from home, VPN issues),
device data can be processed from raw files instead.

**Supported formats:**

| File type | Format detected | Weight data? |
|---|---|---|
| `[IMEI] exported weightdata data.csv` | Columns: row_num, EID, weight, datetime, score | Yes |
| `PPL Upload*.xlsx` / `*PPL Upload*.xlsx` | Header: EID, Weight, Date, Time, Score | Yes |
| `*Timestamps*.csv` / `*Passes*.csv` | Columns: EID, datetime (no weight) | No |

**Workflow:**
1. Save raw device CSV exports or PPL Upload xlsx files into the `Input\` folder
2. Double-click `run_local.bat`
3. Select which files to process (single, range, comma-separated, or 'all')
4. Enter a report name (or press Enter for the default)
5. Report opens in browser; processed files are moved to `Input\Processed\` automatically

Note: local file mode produces weight charts only — growth/regression data requires the API.

---

## Deploying to Another PC (no OneDrive)

Copy these files/folders manually (e.g. via USB):

```
run_wow.bat
run_local.bat
analyse_wow.py
Scripts\
    __init__.py
    wow_fetcher.py
    wow_parser.py
    wow_charts.py
    wow_report.py
    wow_csv_parser.py
Background Info\
    Global WOW Claude.xlsx
```

Create an empty `Input\` folder on the target PC. The `Output\`, `Input\Processed\`,
and `__pycache__\` folders are created automatically — do not copy them.
Python must already be installed on the target PC. Required packages (requests, matplotlib,
pandas, openpyxl) are installed automatically by `run_wow.bat` / `run_local.bat` on first run.

---

## Common Issues

| Symptom | Cause | Fix |
|---|---|---|
| Connection timeout | IP not whitelisted for this farm | Add IP via nsavant master account (API IP ACL) + BGP support ticket for Security Groups |
| "Cannot reach PPL server" message | IP whitelist or VPN | See detailed guidance printed by the tool |
| Login fails (returns false) | Wrong PPL Name | Check PPL Name column in `Global WOW Claude.xlsx` |
| PPL very slow to respond | Server performance | Login/paddock calls allow up to 60 s; data fetch allows 120 s |
| No paddocks returned | Correct login but no active paddock | Verify farm has an active paddock in PPL |
| No data for date range | WOW offline or no animals weighed | Try a wider date range |
| Paddock not auto-matched | PPL Name ≠ paddock name | Select manually from the numbered list shown |
| PPL web dashboard works but API doesn't | API has IP restrictions; web dashboard does not | Whitelist your IP for API access (see above) |
