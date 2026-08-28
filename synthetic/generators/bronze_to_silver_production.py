from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
SRC = BASE / "data" / "bronze" / "synthetic_enterprise" / "production" / "production_operations_2024_2025.csv"
OUT = BASE / "data" / "silver" / "synthetic_enterprise" / "production" / "production_operations_2024_2025.parquet"
OUT.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(SRC, parse_dates=["timestamp_start", "timestamp_end"])
required = ["production_record_id","site_code","line_code","shift_code","product_code","planned_quantity","actual_quantity","good_quantity","reject_quantity","data_class","integration_role"]
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")
if (df["good_quantity"] + df["reject_quantity"] != df["actual_quantity"]).any():
    raise ValueError("Production quantity reconciliation failed")
if not (df["data_class"] == "SYNTHETIC_OPERATIONAL").all():
    raise ValueError("Unexpected data_class found")

df.to_parquet(OUT, index=False)
print(f"Wrote {len(df):,} rows -> {OUT}")
