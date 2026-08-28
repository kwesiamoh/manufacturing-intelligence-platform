from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = pd.read_csv(ROOT / "metadata" / "source_manifest.csv")
SRC = ROOT / "bronze" / "series_production_cnc"
DST = ROOT / "silver" / "series_production_cnc"
DST.mkdir(parents=True, exist_ok=True)

for row in MANIFEST.itertuples(index=False):
    src = SRC / row.file_name
    if not src.exists():
        raise FileNotFoundError(f"Run download_bronze.py first: {src}")
    df = pd.read_csv(src)

    # Preserve all original source columns. Only add provenance columns.
    first_col = df.columns[0]
    parsed = pd.to_datetime(df[first_col], errors="coerce")
    if parsed.notna().mean() > 0.95:
        df[first_col] = parsed

    df.insert(0, "source_session_id", int(row.session_id))
    df.insert(1, "source_file", row.file_name)

    out = DST / f"session_id={int(row.session_id):02d}.parquet"
    df.to_parquet(out, index=False, engine="pyarrow", compression="snappy")
    print(f"Wrote {out.name}: {len(df):,} rows")
