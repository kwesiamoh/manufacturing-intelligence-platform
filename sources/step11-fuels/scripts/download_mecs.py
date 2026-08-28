#!/usr/bin/env python3
from pathlib import Path
import sys
import requests

FILES = {
    "Table3_1.xlsx": "https://www.eia.gov/consumption/manufacturing/data/2022/xls/Table3_1.xlsx",
    "Table7_3.xlsx": "https://www.eia.gov/consumption/manufacturing/data/2022/xls/Table7_3.xlsx",
    "Table7_7.xlsx": "https://www.eia.gov/consumption/manufacturing/data/2022/xls/Table7_7.xlsx",
    "Table7_10.xlsx": "https://www.eia.gov/consumption/manufacturing/data/2022/xls/Table7_10.xlsx",
}

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
from _shared.bronze_guard import install_chunks, reuse_complete_set_or_raise

out_dir = ROOT / "bronze" / "eia_mecs_2022"
out_dir.mkdir(parents=True, exist_ok=True)

if reuse_complete_set_or_raise([out_dir / filename for filename in FILES]):
    raise SystemExit(0)

session = requests.Session()
session.headers.update({"User-Agent": "manufacturing-intelligence-portfolio/1.0"})

for filename, url in FILES.items():
    out = out_dir / filename
    print(f"Downloading {filename} ...")
    with session.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        install_chunks(out, r.iter_content(1024 * 1024))
    print(f"  saved {out.stat().st_size:,} bytes")

print("All MECS Bronze files downloaded.")
