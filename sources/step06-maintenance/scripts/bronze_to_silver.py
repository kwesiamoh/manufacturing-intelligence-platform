"""Convert FMUCD Bronze CSV to compressed Silver Parquet using Polars streaming.

The script preserves source context and adds provenance flags. It does not relabel
facility data as manufacturing data.
"""
from pathlib import Path
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
bronze_files = list((ROOT / "bronze").glob("*.csv"))
if not bronze_files:
    raise SystemExit("No Bronze CSV found. Run download_fmucd.py first.")

src = bronze_files[0]
out = ROOT / "silver" / "fmucd_maintenance.parquet"
out.parent.mkdir(parents=True, exist_ok=True)

rename_map = {
    "UniversityID": "source_organization_id",
    "Country": "country",
    "State/Province": "state_province",
    "BuildingID": "source_asset_group_id",
    "BuildingName": "source_asset_group_name",
    "SystemCode": "system_code",
    "SystemDescription": "system_description",
    "SubsystemCode": "subsystem_code",
    "SubsystemDescription": "subsystem_description",
    "ComponentCode": "component_code",
    "ComponentDescription": "component_description",
    "WOID": "work_order_id",
    "WODescription": "work_order_description",
    "WOPriority": "work_order_priority",
    "WOStartDate": "work_order_start_date",
    "WOEnd Date": "work_order_end_date",
    "WODuration": "work_order_duration_days",
    "PPM/UPM": "maintenance_class",
    "LaborCost": "labor_cost_usd",
    "MaterialCost": "material_cost_usd",
    "OtherCosts": "other_cost_usd",
    "TotalCost": "total_cost_usd",
    "Labor hours": "labor_hours",
}

lf = pl.scan_csv(src, infer_schema_length=10000, ignore_errors=True)
existing = set(lf.collect_schema().names())
lf = lf.rename({k: v for k, v in rename_map.items() if k in existing})

# Add explicit provenance so downstream users cannot confuse this domain with factory data.
lf = lf.with_columns(
    pl.lit("FMUCD").alias("source_dataset"),
    pl.lit("real").alias("data_origin"),
    pl.lit("building_facilities").alias("source_industry_context"),
    pl.lit(False).alias("manufacturing_specific"),
)

# Parse dates only if columns exist after rename.
schema = set(lf.collect_schema().names())
exprs = []
for c in ["work_order_start_date", "work_order_end_date"]:
    if c in schema:
        exprs.append(pl.col(c).cast(pl.Utf8).str.strptime(pl.Date, "%m/%d/%Y", strict=False).alias(c))
if exprs:
    lf = lf.with_columns(exprs)

lf.sink_parquet(out, compression="zstd")
print(out)
