#!/usr/bin/env python3
from pathlib import Path
import sys
import requests

FILES = {
    "preair_G.xlsx": ("https://zenodo.org/records/13927178/files/preair_G.xlsx?download=1",
                      "a70d5d322672df8be938a850c6d79ffb"),
    "preair_P.xlsx": ("https://zenodo.org/records/13927178/files/preair_P.xlsx?download=1",
                      "2f5aff2892f4d64ea0d1a163aa5c76b4"),
    "steam_G.xlsx": ("https://zenodo.org/records/13927178/files/steam_G.xlsx?download=1",
                     "8a6ac97f3907f1bc6391bd4c98a73794"),
    "steam_P.xlsx": ("https://zenodo.org/records/13927178/files/steam_P.xlsx?download=1",
                     "0b73ec7035a2149543dff6f48bc85b06"),
}

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
from _shared.bronze_guard import install_chunks, reuse_complete_set_or_raise

out_dir = ROOT / "bronze" / "industrial_park_ies"
out_dir.mkdir(parents=True, exist_ok=True)

targets = [out_dir / filename for filename in FILES]
expected = {
    out_dir / filename: ("md5", expected_md5)
    for filename, (_, expected_md5) in FILES.items()
}
if reuse_complete_set_or_raise(targets, expected=expected):
    raise SystemExit(0)

session = requests.Session()
session.headers.update({"User-Agent": "manufacturing-intelligence-portfolio/1.0"})

for filename, (url, expected_md5) in FILES.items():
    out = out_dir / filename
    print(f"Downloading {filename} ...")
    with session.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        actual, _ = install_chunks(
            out,
            r.iter_content(1024 * 1024),
            expected_digest=expected_md5,
            algorithm="md5",
        )

    print(f"  verified MD5={actual}")

print("All Bronze utility files downloaded and verified.")
