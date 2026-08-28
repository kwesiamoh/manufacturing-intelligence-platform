from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq

repo = Path.cwd()

bases = [
    repo / "sources" / "step04-reliability",
    repo / "data" / "silver",
]

print("=== Stage 13A file inventory ===")

candidates = []
for base in bases:
    if not base.exists():
        continue
    for p in base.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".parquet", ".csv"}:
            candidates.append(p)

print(f"Candidate files: {len(candidates)}")

for p in sorted(candidates):
    rel = p.relative_to(repo) if p.is_relative_to(repo) else p
    print("\n---")
    print(f"Path: {rel}")
    print(f"Size bytes: {p.stat().st_size}")

    try:
        if p.suffix.lower() == ".parquet":
            pf = pq.ParquetFile(p)
            print(f"Rows: {pf.metadata.num_rows}")
            print("Columns:")
            for f in pf.schema_arrow:
                print(f"  - {f.name}: {f.type}")
        else:
            d = pd.read_csv(p, nrows=250)
            print("CSV schema sample only (first 250 rows).")
            print("Columns:")
            for c, dt in d.dtypes.items():
                print(f"  - {c}: {dt}")
    except Exception as e:
        print(f"Profile error: {type(e).__name__}: {e}")

print("\n=== Stage 13A file inventory complete ===")
