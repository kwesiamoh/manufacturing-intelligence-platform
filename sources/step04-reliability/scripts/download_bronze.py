from __future__ import annotations

import io
import pathlib
import sys
import zipfile
import requests

URL = "https://archive.ics.uci.edu/static/public/447/condition%2Bmonitoring%2Bof%2Bhydraulic%2Bsystems.zip"
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
from _shared.bronze_guard import install_bytes, reuse_complete_set_or_raise
OUT = ROOT / "bronze" / "hydraulic_condition_monitoring"

REQUIRED = [
    "PS1.txt", "PS2.txt", "PS3.txt", "PS4.txt", "PS5.txt", "PS6.txt",
    "EPS1.txt", "FS1.txt", "FS2.txt", "TS1.txt", "TS2.txt", "TS3.txt",
    "TS4.txt", "VS1.txt", "CE.txt", "CP.txt", "SE.txt", "profile.txt",
]

OUT.mkdir(parents=True, exist_ok=True)

if reuse_complete_set_or_raise([OUT / name for name in REQUIRED]):
    raise SystemExit(0)

print(f"Downloading official UCI source: {URL}")
with requests.get(URL, timeout=180) as response:
    response.raise_for_status()
    payload = response.content

with zipfile.ZipFile(io.BytesIO(payload)) as zf:
    names = {
        pathlib.PurePosixPath(name).name: name
        for name in zf.namelist()
        if not name.endswith("/")
    }
    missing = sorted(set(REQUIRED) - set(names))
    if missing:
        raise RuntimeError(f"Official UCI archive lacks required files: {missing}")
    for member in zf.infolist():
        if member.is_dir():
            continue
        relative = pathlib.PurePosixPath(member.filename)
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError(f"Unsafe UCI archive member: {member.filename}")
        target = OUT.joinpath(*relative.parts)
        install_bytes(target, zf.read(member))

print(f"Extracted official source to: {OUT}")
print("Bronze files are preserved as downloaded; no row-level transformations were applied.")
