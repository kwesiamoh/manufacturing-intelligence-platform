from __future__ import annotations

from pathlib import Path
import sys
import requests

SOURCE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SOURCE_ROOT))
from _shared.bronze_guard import install_chunks, reuse_complete_set_or_raise

URL = "https://zenodo.org/records/18146866/files/production_raw.xlsx?download=1"
EXPECTED_MD5 = "d9c095d5eba8706ac7dda92af63f5c35"

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "bronze" / "production_downtime" / "production_raw.xlsx"
OUT.parent.mkdir(parents=True, exist_ok=True)

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    )
}

if reuse_complete_set_or_raise(
    [OUT], expected={OUT: ("md5", EXPECTED_MD5)}
):
    raise SystemExit(0)

with requests.get(URL, headers=headers, stream=True, timeout=120) as response:
    response.raise_for_status()
    md5, _ = install_chunks(
        OUT,
        response.iter_content(chunk_size=1024 * 1024),
        expected_digest=EXPECTED_MD5,
        algorithm="md5",
    )

print(f"Downloaded: {OUT}")
print(f"Size: {OUT.stat().st_size:,} bytes")
print(f"MD5 verified: {md5}")
