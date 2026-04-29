"""
Remote WOW Data Report Generator
---------------------------------
Fetches cleansed weight and growth data from Precision Pastoral (PPL) via API,
then produces a self-contained HTML report with per-animal charts.

NORMAL USE (farm selected from spreadsheet):
    python analyse_wow.py --days 14
    python analyse_wow.py --start 2025-03-01 --end 2025-03-31

SPECIFY FARM DIRECTLY:
    python analyse_wow.py --farm tobruk --days 14
    python analyse_wow.py --farm tobruk --paddock "Tobruk WOW" --start 2025-03-01 --end 2025-03-31

LIST PADDOCKS FOR A FARM:
    python analyse_wow.py --farm tobruk --list-paddocks

FILE MODE (use previously downloaded JSON files):
    python analyse_wow.py --weights blue.json --growth red.json
"""

import argparse
import json
import sys
import warnings
import webbrowser
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "Scripts"))

from wow_fetcher import create_session, login, list_paddocks, fetch_weights, fetch_growth
from wow_parser import parse_weights, parse_growth, build_animals
from wow_charts import animal_chart
from wow_report import generate_report

_FARMS_FILE = Path(__file__).parent / "Background Info" / "Global WOW Claude.xlsx"


# ── Farm list from spreadsheet ─────────────────────────────────────────────────

def _load_farms():
    """Load Installed WOW units from the Global spreadsheet. Returns DataFrame or None."""
    if not _FARMS_FILE.exists():
        return None
    try:
        import pandas as pd
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df = pd.read_excel(_FARMS_FILE)
        installed = df[
            (df["Status"].str.strip() == "Installed") &
            df["PPL Name"].notna() &
            (df["PPL Name"].astype(str).str.strip() != "")
        ].reset_index(drop=True)
        return installed if len(installed) > 0 else None
    except Exception as e:
        print(f"  (Could not load farm list: {e})")
        return None


def _display_name(row) -> str:
    import pandas as pd
    farm = row.get("Farm Name")
    if farm is None or (isinstance(farm, float) and pd.isna(farm)) or str(farm).strip() in ("", "nan"):
        farm = row.get("Account Name", "")
    return str(farm).strip()


def _select_farm_interactive() -> tuple[str, str]:
    """Show numbered WOW unit list, prompt user. Returns (ppl_name, farm_display_name)."""
    farms = _load_farms()

    if farms is None:
        print("\n  (Farm list spreadsheet not found — enter PPL username manually)")
        ppl = input("  PPL farm username: ").strip()
        return ppl, ppl

    print(f"\n  Available WOW Units  ({len(farms)} installed)\n")
    print(f"  {'#':>4}   {'Farm / Account':<36}  Asset")
    print(f"  {'─'*4}   {'─'*36}  {'─'*44}")

    for i, row in farms.iterrows():
        farm = _display_name(row)[:35]
        asset = str(row.get("Asset Name", "")).strip()[:44]
        print(f"  {i+1:>4}.  {farm:<36}  {asset}")

    print()
    while True:
        choice = input("  Select unit number: ").strip()
        if choice.isdigit():
            n = int(choice) - 1
            if 0 <= n < len(farms):
                row = farms.iloc[n]
                ppl_name = str(row["PPL Name"]).strip()
                farm_name = _display_name(row) or ppl_name
                return ppl_name, farm_name
        print(f"  Please enter a number between 1 and {len(farms)}.")


# ── Paddock matching ───────────────────────────────────────────────────────────

def _resolve_paddock(paddocks: list, paddock_arg: str):
    """Find paddock by name (case-insensitive) or numeric ID."""
    if paddock_arg.lstrip("-").isdigit():
        pid = int(paddock_arg)
        return next((p for p in paddocks if p.get("id") == pid), None)
    return next(
        (p for p in paddocks if p.get("name", "").lower() == paddock_arg.lower()),
        None,
    )


def _auto_match_paddock(paddocks: list, ppl_name: str):
    """Try to match paddock to PPL login name automatically."""
    ppl_lower = ppl_name.lower().strip()
    # 1. Exact match
    for p in paddocks:
        if p.get("name", "").lower().strip() == ppl_lower:
            return p
    # 2. PPL name contained in paddock name or vice versa
    for p in paddocks:
        name = p.get("name", "").lower().strip()
        if ppl_lower in name or name in ppl_lower:
            return p
    return None


def _pick_paddock_interactive(paddocks: list, ppl_name: str):
    """Show paddock list and prompt user to select one."""
    print(f"\n  Paddocks for '{ppl_name}':\n")
    for i, p in enumerate(paddocks, 1):
        print(f"    {i}.  {p.get('name', '?')}  (ID {p.get('id', '?')})")
    print()
    while True:
        choice = input("  Select paddock number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(paddocks):
            return paddocks[int(choice) - 1]
        print(f"  Please enter a number between 1 and {len(paddocks)}.")


# ── Output dir ────────────────────────────────────────────────────────────────

def _make_output_dir(farm: str, paddock: str) -> Path:
    safe = lambda s: s.replace(" ", "_").replace("/", "-").replace("\\", "-")
    folder = f"{date.today().strftime('%Y-%m-%d')}_{safe(farm)}_{safe(paddock)}"
    out = Path(__file__).parent / "Output" / folder
    out.mkdir(parents=True, exist_ok=True)
    return out


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Remote WOW weight & growth report generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--farm", "-f",
                        help="PPL farm username (omit to select from the WOW unit list)")
    parser.add_argument("--paddock", "-p",
                        help="Paddock name or numeric ID (auto-matched from PPL Name if omitted)")
    parser.add_argument("--days", "-d", type=int,
                        help="Days back from today (e.g. 7, 14, 21)")
    parser.add_argument("--start", "-s",
                        help="Start date YYYY-MM-DD")
    parser.add_argument("--end", "-e",
                        help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--list-paddocks", action="store_true",
                        help="List all paddocks for the farm and exit")
    parser.add_argument("--weights",
                        help="Path to cleansed weights JSON (file mode)")
    parser.add_argument("--growth",
                        help="Path to growth JSON (file mode)")
    parser.add_argument("--output", "-o",
                        help="Output directory override")
    args = parser.parse_args()

    file_mode = bool(args.weights or args.growth)

    # ── LIST PADDOCKS ─────────────────────────────────────────────────────────
    if args.list_paddocks:
        farm = args.farm or input("  PPL farm username: ").strip()
        print(f"\nConnecting to PPL as '{farm}'...")
        session = create_session()
        if not login(session, farm, farm):
            sys.exit("ERROR: Login failed — check username and IP whitelist status.")
        paddocks = list_paddocks(session)
        if paddocks:
            print(f"\nPaddocks for '{farm}':")
            for p in paddocks:
                print(f"  ID {str(p.get('id', '?')):>6}  —  {p.get('name', '?')}")
        else:
            print("No paddocks returned.")
        sys.exit(0)

    # ── DATE RANGE ────────────────────────────────────────────────────────────
    today = date.today()
    end_date = args.end or today.strftime("%Y-%m-%d")

    if args.days:
        start_date = (today - timedelta(days=args.days)).strftime("%Y-%m-%d")
    elif args.start:
        start_date = args.start
    else:
        start_date = None

    # ── FILE MODE ─────────────────────────────────────────────────────────────
    if file_mode:
        farm_name    = args.farm    or "Unknown Farm"
        paddock_name = args.paddock or "Unknown Paddock"
        weight_data, growth_data = [], []

        if args.weights:
            p = Path(args.weights)
            if not p.exists():
                sys.exit(f"ERROR: File not found: {p}")
            with open(p, encoding="utf-8") as fh:
                weight_data = json.load(fh)
            print(f"Loaded {len(weight_data)} weight records from {p.name}")

        if args.growth:
            p = Path(args.growth)
            if not p.exists():
                sys.exit(f"ERROR: File not found: {p}")
            with open(p, encoding="utf-8") as fh:
                growth_data = json.load(fh)
            print(f"Loaded {len(growth_data)} growth records from {p.name}")

    # ── FETCH MODE ────────────────────────────────────────────────────────────
    else:
        if not start_date:
            parser.error("--start YYYY-MM-DD or --days N is required")

        # Farm selection: spreadsheet list or direct arg
        if args.farm:
            ppl_name  = args.farm
            farm_name = args.farm
        else:
            ppl_name, farm_name = _select_farm_interactive()

        print(f"\nConnecting to PPL as '{ppl_name}'...")
        session = create_session()
        if not login(session, ppl_name, ppl_name):
            sys.exit(
                "\nERROR: Login failed.\n"
                "  - Check the farm username is correct\n"
                "  - Your IP address must be whitelisted for this farm on the PPL server\n"
                "  - Disconnect any VPN (VPN changes your IP address)\n"
            )
        print("  Login OK.")

        paddocks = list_paddocks(session)
        if not paddocks:
            sys.exit("ERROR: No paddocks returned for this account.")

        # Paddock resolution: explicit arg > auto-match > interactive
        if args.paddock:
            paddock = _resolve_paddock(paddocks, args.paddock)
            if not paddock:
                print(f"  WARNING: Paddock '{args.paddock}' not found.")
                paddock = _pick_paddock_interactive(paddocks, ppl_name)
        elif len(paddocks) == 1:
            paddock = paddocks[0]
            print(f"  Paddock: {paddock.get('name')}  (only paddock on this account)")
        else:
            paddock = _auto_match_paddock(paddocks, ppl_name)
            if paddock:
                print(f"  Paddock auto-matched: {paddock.get('name')}")
            else:
                paddock = _pick_paddock_interactive(paddocks, ppl_name)

        paddock_id   = paddock["id"]
        paddock_name = paddock.get("name", str(paddock_id))

        print(f"  Period:  {start_date} → {end_date}")
        print()
        print("  Fetching cleansed weights...")
        weight_data = fetch_weights(session, paddock_id, start_date, end_date)
        print(f"    {len(weight_data)} records")

        print("  Fetching growth (polynomial regression)...")
        growth_data = fetch_growth(session, paddock_id, start_date, end_date)
        print(f"    {len(growth_data)} records")

    # ── PARSE & BUILD ─────────────────────────────────────────────────────────
    weight_records = parse_weights(weight_data)
    growth_records = parse_growth(growth_data)

    if not weight_records and not growth_records:
        sys.exit("\nNo usable records found for this period. Check the date range and try again.")

    animals = build_animals(weight_records, growth_records)
    print(f"\n  {len(animals)} animals  |  {len(weight_records)} weight records  |  {len(growth_records)} growth records")

    # ── OUTPUT DIR ────────────────────────────────────────────────────────────
    out_dir = Path(args.output) if args.output else _make_output_dir(farm_name, paddock_name)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── CHARTS ───────────────────────────────────────────────────────────────
    print(f"\n  Generating charts for {len(animals)} animals...")
    charts = {}
    for i, animal in enumerate(animals, 1):
        charts[animal.eid] = animal_chart(animal)
        if i % 20 == 0 or i == len(animals):
            print(f"    {i}/{len(animals)}")

    # ── REPORT ────────────────────────────────────────────────────────────────
    print("  Building report...")
    meta = {
        "farm":      farm_name,
        "paddock":   paddock_name,
        "start":     start_date or "N/A",
        "end":       end_date,
        "generated": datetime.now().strftime("%d %b %Y %H:%M"),
    }
    html = generate_report(animals, weight_records, growth_records, charts, meta)

    report_path = out_dir / "report.html"
    report_path.write_text(html, encoding="utf-8")
    print(f"\n  Report saved → {report_path}\n")

    try:
        webbrowser.open(report_path.as_uri())
    except Exception:
        pass


if __name__ == "__main__":
    main()
