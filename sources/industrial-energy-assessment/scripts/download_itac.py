#!/usr/bin/env python3
from pathlib import Path
import sys
import requests

URL = "https://itac.university/storage/ITAC_Database.zip"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
from _shared.bronze_guard import install_chunks, reuse_complete_set_or_raise

OUT = ROOT / "bronze" / "itac" / "ITAC_Database.zip"
OUT.parent.mkdir(parents=True, exist_ok=True)

if reuse_complete_set_or_raise([OUT]):
    raise SystemExit(0)

with requests.get(URL, stream=True, timeout=120) as r:
    r.raise_for_status()
    observed, _ = install_chunks(OUT, r.iter_content(chunk_size=1024 * 1024))

print(f"saved={OUT}")
print(f"bytes={OUT.stat().st_size}")
print(f"sha256={observed}")
