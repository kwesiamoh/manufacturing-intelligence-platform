#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import zipfile

base = Path("bronze/industrial_park_ies")
metadata = json.loads(Path("provenance/files.json").read_text(encoding="utf-8"))

for item in metadata:
    p = base / item["filename"]
    if not p.exists():
        raise SystemExit(f"Missing Bronze file: {p}")

    # XLSX files are ZIP containers.
    if not zipfile.is_zipfile(p):
        raise SystemExit(f"Invalid XLSX container: {p}")

    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    if h.hexdigest() != item["md5"]:
        raise SystemExit(f"MD5 mismatch: {p.name}")

    print(f"{p.name}: valid XLSX, MD5 verified")

print("Bronze validation passed.")
