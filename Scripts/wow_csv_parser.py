"""
Parses raw WOW data files exported directly from devices or prepared for PPL upload.
Returns dicts compatible with wow_parser.parse_weights().

Supported formats:
  exported_weight  — "<IMEI> exported weightdata data.csv"
                     Columns: row_num, EID, weight, datetime(MM/DD/YYYY HH:MM:SS), score
  ppl_xlsx         — "* PPL Upload*.xlsx"
                     Columns: EID, Weight, Date, Time, Score  (header row present)
  timestamp        — "* Timestamps*.csv" / "* Passes*.csv"
                     Columns: EID, datetime  (no weight — cannot produce weight report)
"""

import csv
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional


# ── Format detection ──────────────────────────────────────────────────────────

def detect_format(path: Path) -> str:
    name = path.name.lower()
    if path.suffix.lower() in (".xlsx", ".xls"):
        return "ppl_xlsx"
    if "exported weightdata" in name or "exported weight" in name:
        return "exported_weight"
    if "timestamp" in name or "passes" in name or "pass" in name:
        return "timestamp"
    # Auto-detect from first line
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as fh:
            first = fh.readline().strip()
        parts = first.split(",")
        if len(parts) == 5:
            # row_num, EID, weight, datetime, score
            try:
                int(parts[0]); float(parts[2]); int(parts[4])
                return "exported_weight"
            except ValueError:
                pass
        if len(parts) == 2:
            return "timestamp"
    except Exception:
        pass
    return "unknown"


# ── Datetime parsing ──────────────────────────────────────────────────────────

_DT_FORMATS = (
    "%m/%d/%Y %H:%M:%S",   # 04/19/2026 23:01:21
    "%m/%d/%Y %H:%M",       # 4/02/2026 0:04
    "%Y-%m-%d %H:%M:%S",   # 2026-02-25 00:00:00
    "%Y-%m-%dT%H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
)


def _parse_dt(s: str) -> Optional[datetime]:
    s = s.strip()
    for fmt in _DT_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


# ── Parsers ───────────────────────────────────────────────────────────────────

def parse_exported_weight(path: Path, source_name: str = "") -> list[dict]:
    """
    Parse: row_num, EID, weight, datetime, score
    Keeps all rows where weight > 0.
    """
    paddock = source_name or path.stem.replace(" exported weightdata data", "").strip()
    records = []
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as fh:
            for line in fh:
                parts = line.strip().split(",")
                if len(parts) < 4:
                    continue
                try:
                    eid = parts[1].strip()
                    weight = float(parts[2].strip())
                    dt_str = parts[3].strip()
                    if weight <= 0 or not eid:
                        continue
                    dt = _parse_dt(dt_str)
                    if dt is None:
                        continue
                    records.append({"eid": eid, "weight": weight, "recorded": dt, "paddock": paddock})
                except (ValueError, IndexError):
                    continue
    except Exception as e:
        print(f"  Warning: could not read {path.name}: {e}")
    return records


def parse_ppl_xlsx(path: Path, source_name: str = "") -> list[dict]:
    """
    Parse PPL Upload xlsx: header row EID, Weight, Date, Time, Score
    Sheet name is used as paddock name.
    """
    import pandas as pd
    records = []
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sheets = pd.read_excel(path, sheet_name=None, dtype={"EID": str})
        for sheet_name, df in sheets.items():
            paddock = source_name or sheet_name
            # Normalise column names
            df.columns = [str(c).strip() for c in df.columns]
            eid_col = next((c for c in df.columns if c.upper() == "EID"), None)
            wt_col = next((c for c in df.columns if c.upper() == "WEIGHT"), None)
            dt_col = next((c for c in df.columns if c.upper() == "DATE"), None)
            if not eid_col or not wt_col or not dt_col:
                continue
            for _, row in df.iterrows():
                try:
                    eid = str(row[eid_col]).strip()
                    weight = float(row[wt_col])
                    if weight <= 0 or not eid or eid == "nan":
                        continue
                    dt_val = row[dt_col]
                    if hasattr(dt_val, "to_pydatetime"):
                        dt = dt_val.to_pydatetime()
                    else:
                        dt = _parse_dt(str(dt_val))
                    if dt is None:
                        continue
                    records.append({"eid": eid, "weight": weight, "recorded": dt, "paddock": paddock})
                except (ValueError, TypeError):
                    continue
    except Exception as e:
        print(f"  Warning: could not read {path.name}: {e}")
    return records


def parse_timestamp(path: Path) -> list[dict]:
    """
    Parse timestamp-only files: EID, datetime — NO weight data.
    Returns list of {eid, recorded} dicts for pass record reports.
    """
    records = []
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as fh:
            for line in fh:
                parts = line.strip().split(",", 1)
                if len(parts) < 2:
                    continue
                eid = parts[0].strip()
                dt_str = parts[1].strip()
                if not eid:
                    continue
                dt = _parse_dt(dt_str)
                if dt is None:
                    continue
                records.append({"eid": eid, "recorded": dt})
    except Exception as e:
        print(f"  Warning: could not read {path.name}: {e}")
    return records


# ── Directory scanner ─────────────────────────────────────────────────────────

def scan_directory(directory: Path) -> list[dict]:
    """
    Scan a directory for all CSV/xlsx files.
    Returns list of dicts: {path, format, label, record_count_estimate}
    Sorted: weight-bearing formats first, then by name.
    """
    results = []
    for path in sorted(directory.iterdir()):
        if path.is_dir() or path.suffix.lower() not in (".csv", ".xlsx", ".xls"):
            continue
        fmt = detect_format(path)
        results.append({"path": path, "format": fmt})

    # Sort: exported_weight and ppl_xlsx first, timestamp/unknown last
    order = {"exported_weight": 0, "ppl_xlsx": 1, "timestamp": 2, "unknown": 3}
    results.sort(key=lambda r: (order.get(r["format"], 9), r["path"].name.lower()))
    return results


def parse_file(path: Path, fmt: str, source_name: str = "") -> list[dict]:
    """Parse a single file given its detected format. Returns record dicts."""
    if fmt == "exported_weight":
        return parse_exported_weight(path, source_name)
    if fmt == "ppl_xlsx":
        return parse_ppl_xlsx(path, source_name)
    if fmt == "timestamp":
        return parse_timestamp(path)
    return []
