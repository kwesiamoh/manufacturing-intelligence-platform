from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq

repo = Path.cwd()

candidates = []
for base in [repo / "data" / "silver", repo / "sources"]:
    if base.exists():
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".parquet", ".csv"}:
                name = p.name.lower()
                parts = " ".join(x.lower() for x in p.parts)
                if any(k in name or k in parts for k in ["telemetry", "metropt", "sensor"]):
                    candidates.append(p)

print("=== Stage 12C.1 telemetry Silver/source inventory ===")
print(f"Candidates found: {len(candidates)}")

if not candidates:
    print("No telemetry-like Parquet/CSV files found under data/silver or sources.")
    raise SystemExit(0)

for p in sorted(set(candidates)):
    print("\n---")
    print(f"Path: {p.relative_to(repo) if p.is_relative_to(repo) else p}")
    print(f"Size bytes: {p.stat().st_size}")

    try:
        if p.suffix.lower() == ".parquet":
            pf = pq.ParquetFile(p)
            schema = pf.schema_arrow
            print(f"Rows: {pf.metadata.num_rows}")
            print(f"Row groups: {pf.metadata.num_row_groups}")
            print("Columns:")
            for field in schema:
                print(f"  - {field.name}: {field.type}")

            # Small metadata/sample profile only; do not print raw rows.
            names = schema.names
            timestamp_candidates = [
                c for c in names
                if any(k in c.lower() for k in ["timestamp", "datetime", "date", "time"])
            ]
            if timestamp_candidates:
                tscol = timestamp_candidates[0]
                try:
                    s = pd.read_parquet(p, columns=[tscol])[tscol]
                    print(f"Timestamp candidate: {tscol}")
                    print(f"Timestamp min: {s.min()}")
                    print(f"Timestamp max: {s.max()}")
                    print(f"Timestamp nulls: {int(s.isna().sum())}")
                except Exception as e:
                    print(f"Timestamp profile warning: {e}")

        else:
            df = pd.read_csv(p, nrows=1000)
            print("CSV detected; first 1000 rows used for schema-only profile.")
            print("Columns:")
            for c, dt in df.dtypes.items():
                print(f"  - {c}: {dt}")
    except Exception as e:
        print(f"Profile error: {type(e).__name__}: {e}")

print("\n=== Inventory complete ===")
