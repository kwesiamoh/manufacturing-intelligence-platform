from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
from _shared.bronze_guard import replace_derived_directory
RAW = ROOT / "data" / "bronze" / "metropt3" / "MetroPT3(AirCompressor).csv"
OUT_DIR = ROOT / "data" / "silver" / "telemetry" / "metropt3"
CHUNK_SIZE = 250_000


def snake(name: str) -> str:
    value = name.strip().replace(" ", "_").replace("-", "_")
    value = re.sub(r"[^A-Za-z0-9_]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value.lower()


if not RAW.exists():
    raise FileNotFoundError(
        f"Raw source not found: {RAW}\nRun ingestion/batch/download_metropt3.py first."
    )

OUT_DIR.parent.mkdir(parents=True, exist_ok=True)

with tempfile.TemporaryDirectory(
    prefix=".metropt3-silver-", dir=OUT_DIR.parent
) as temporary_root:
    staged = Path(temporary_root) / OUT_DIR.name
    staged.mkdir()

    for i, chunk in enumerate(pd.read_csv(RAW, chunksize=CHUNK_SIZE)):
        chunk.columns = [snake(c) for c in chunk.columns]
        if "timestamp" not in chunk.columns:
            raise ValueError(
                f"No timestamp column after normalization: {list(chunk.columns)}"
            )
        chunk["timestamp"] = pd.to_datetime(chunk["timestamp"], errors="raise")
        chunk["source_dataset"] = "UCI MetroPT-3 (ID 791)"
        chunk["source_record_type"] = "real_measured"
        chunk["year"] = chunk["timestamp"].dt.year.astype("int16")
        chunk["month"] = chunk["timestamp"].dt.month.astype("int8")

        out = staged / f"part-{i:03d}.parquet"
        chunk.to_parquet(out, index=False, compression="snappy", engine="pyarrow")
        print(f"Staged {len(chunk):,} rows -> {out.name}")

    if not list(staged.glob("part-*.parquet")):
        raise RuntimeError("MetroPT-3 transformation produced no Silver parts")
    replace_derived_directory(staged, OUT_DIR)

print(f"Replaced Silver dataset as one complete unit: {OUT_DIR}")
