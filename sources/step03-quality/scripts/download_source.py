from __future__ import annotations

import io
import pathlib
import sys
import zipfile

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
from _shared.bronze_guard import install_bytes, reuse_complete_set_or_raise
OUT = ROOT / "bronze" / "secom"
OUT.mkdir(parents=True, exist_ok=True)

ARCHIVE_URL = "https://archive.ics.uci.edu/static/public/179/secom.zip"
LEGACY = "https://archive.ics.uci.edu/ml/machine-learning-databases/secom/"
FILES = ["secom.data", "secom_labels.data", "secom.names"]


def download(url: str, timeout: int = 60) -> bytes:
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.content


def try_archive() -> bool:
    try:
        payload = download(ARCHIVE_URL, timeout=120)
        with zipfile.ZipFile(io.BytesIO(payload)) as zf:
            names = set(zf.namelist())
            extracted = {}
            for filename in FILES:
                candidates = [n for n in names if n.endswith(filename)]
                if not candidates:
                    raise RuntimeError(f"{filename} not found in archive")
                extracted[filename] = zf.read(candidates[0])
            for filename, content in extracted.items():
                install_bytes(OUT / filename, content)
        return True
    except Exception as exc:
        print(f"Current UCI archive attempt failed: {exc}")
        return False


def try_legacy() -> bool:
    try:
        downloaded = {filename: download(LEGACY + filename) for filename in FILES}
        for filename, content in downloaded.items():
            install_bytes(OUT / filename, content)
        return True
    except Exception as exc:
        print(f"Legacy UCI file attempt failed: {exc}")
        return False


if __name__ == "__main__":
    if reuse_complete_set_or_raise([OUT / filename for filename in FILES]):
        raise SystemExit(0)
    if not (try_archive() or try_legacy()):
        sys.exit("Unable to download UCI SECOM files. No synthetic fallback was used.")
    print("Downloaded authoritative UCI SECOM source files to", OUT)
