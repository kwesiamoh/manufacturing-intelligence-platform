from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT.parent))
from _shared.bronze_guard import install_chunks, reuse_complete_set_or_raise
BRONZE = ROOT / "data" / "bronze" / "metropt3"
ARCHIVE = BRONZE / "metropt3_dataset.zip"
CSV_NAME = "MetroPT3(AirCompressor).csv"
CSV_PATH = BRONZE / CSV_NAME
URL = "https://archive.ics.uci.edu/static/public/791/metropt%2B3%2Bdataset.zip"
EXPECTED_ARCHIVE_SHA256 = "aab991a970e58210de853bb8078ce0e63abb4d9412fdc5c79792dae3d8e1721a"


def sha256(path: Path, block_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            h.update(block)
    return h.hexdigest()


def download() -> None:
    BRONZE.mkdir(parents=True, exist_ok=True)
    archive_reused = reuse_complete_set_or_raise(
        [ARCHIVE], expected={ARCHIVE: ("sha256", EXPECTED_ARCHIVE_SHA256)}
    )
    if not archive_reused:
        with urllib.request.urlopen(URL) as response:
            install_chunks(
                ARCHIVE,
                iter(lambda: response.read(1024 * 1024), b""),
                expected_digest=EXPECTED_ARCHIVE_SHA256,
            )

    archive_hash = sha256(ARCHIVE)
    if archive_hash != EXPECTED_ARCHIVE_SHA256:
        raise RuntimeError(
            "Archive SHA-256 differs from the reproducibility reference. "
            f"Expected {EXPECTED_ARCHIVE_SHA256}, received {archive_hash}. "
            "Verify the current UCI archive before proceeding."
        )

    with zipfile.ZipFile(ARCHIVE) as zf:
        with zf.open(CSV_NAME) as src:
            install_chunks(
                CSV_PATH,
                iter(lambda: src.read(1024 * 1024), b""),
            )

    acquisition = {
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": URL,
        "archive_file": str(ARCHIVE.relative_to(ROOT)),
        "archive_sha256": archive_hash,
        "csv_file": str(CSV_PATH.relative_to(ROOT)),
        "csv_sha256": sha256(CSV_PATH),
        "csv_bytes": CSV_PATH.stat().st_size,
    }
    (BRONZE / "acquisition_manifest.json").write_text(
        json.dumps(acquisition, indent=2), encoding="utf-8"
    )
    print(f"Bronze source ready: {CSV_PATH}")


if __name__ == "__main__":
    download()
