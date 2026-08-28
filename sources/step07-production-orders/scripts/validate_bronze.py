from pathlib import Path
import hashlib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = pd.read_csv(ROOT / "metadata" / "source_manifest.csv")
SRC = ROOT / "bronze" / "series_production_cnc"


def md5sum(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


failures = []
for row in MANIFEST.itertuples(index=False):
    p = SRC / row.file_name
    if not p.exists():
        failures.append(f"missing: {row.file_name}")
        continue
    if md5sum(p) != row.md5:
        failures.append(f"md5 mismatch: {row.file_name}")
        continue
    df = pd.read_csv(p)
    if len(df) != int(row.expected_rows):
        failures.append(
            f"row-count mismatch {row.file_name}: {len(df)} != {row.expected_rows}")
    if df.shape[1] < 22:
        failures.append(
            f"unexpectedly few columns {row.file_name}: {df.shape[1]}")
    if not any(str(c).lower().startswith("time") or "date" in str(c).lower() for c in df.columns[:2]):
        print(
            f"NOTE: inspect timestamp heading manually in {row.file_name}: {df.columns[0]}")

if failures:
    raise SystemExit("\n".join(failures))
print("Bronze validation passed for all 13 source files.")
