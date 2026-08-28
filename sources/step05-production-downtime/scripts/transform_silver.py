from __future__ import annotations

from pathlib import Path
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "bronze" / "production_downtime" / "production_raw.xlsx"
OUT = ROOT / "silver" / "production_downtime"
DATASET_ID = "zenodo_18146866"


def combine_date_time(date_expr: pl.Expr, time_expr: pl.Expr) -> pl.Expr:
    # Excel readers may return dates/times in slightly different scalar types.
    # Formatting to strings first keeps the transformation deterministic.
    return (
        date_expr.cast(pl.String)
        + pl.lit(" ")
        + time_expr.cast(pl.String)
    ).str.to_datetime(strict=False)


def add_source(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(pl.lit(DATASET_ID).alias("source_dataset_id"))


def transform_processed_hourly() -> None:
    df = pl.read_excel(SRC, sheet_name="processed_hourly", engine="calamine")
    df = add_source(df).with_columns(
        combine_date_time(pl.col("date"), pl.col("hour_start")).alias("interval_start_utc"),
        combine_date_time(pl.col("date"), pl.col("hour_end")).alias("interval_end_utc"),
        pl.col("production_gallons").cast(pl.Float64, strict=False),
    ).select(
        "source_dataset_id", "interval_start_utc", "interval_end_utc", "production_gallons"
    )
    df.write_parquet(OUT / "production_hourly.parquet", compression="zstd")


def transform_daily() -> None:
    df = pl.read_excel(SRC, sheet_name="daily_operation_summary", engine="calamine")
    df = add_source(df).with_columns(
        pl.col("date").cast(pl.Date, strict=False).alias("production_date"),
        combine_date_time(pl.col("date"), pl.col("production_start_time")).alias("production_start_timestamp"),
        combine_date_time(pl.col("date"), pl.col("production_end_time")).alias("production_end_timestamp"),
        pl.col("efficiency").cast(pl.Float64, strict=False).alias("efficiency_pct"),
        pl.col("monitored_time_dec").cast(pl.Float64, strict=False).alias("monitored_time_h"),
        pl.col("operation_time_dec").cast(pl.Float64, strict=False).alias("operation_time_h"),
        pl.col("pause_time_dec").cast(pl.Float64, strict=False).alias("downtime_h"),
    ).select(
        "source_dataset_id", "production_date", "product_type_l", "production_units",
        "liters_produced", "production_start_timestamp", "production_end_timestamp",
        "efficiency_pct", "gallons_per_hour", "monitored_time_h", "operation_time_h",
        "downtime_h"
    )
    df.write_parquet(OUT / "production_daily.parquet", compression="zstd")


def transform_hourly_operation() -> None:
    df = pl.read_excel(SRC, sheet_name="hourly_operation_breakdown", engine="calamine")
    df = add_source(df).with_columns(
        combine_date_time(pl.col("date"), pl.col("hour_start")).alias("interval_start_utc"),
        combine_date_time(pl.col("date"), pl.col("hour_end")).alias("interval_end_utc"),
        pl.col("efficiency").cast(pl.Float64, strict=False).alias("efficiency_pct"),
    ).select(
        "source_dataset_id", "interval_start_utc", "interval_end_utc",
        "monitored_time_h", "operation_time_h", "downtime_h", "efficiency_pct"
    )
    df.write_parquet(OUT / "operation_hourly.parquet", compression="zstd")


def transform_downtime() -> None:
    df = pl.read_excel(SRC, sheet_name="downtime_event_log", engine="calamine")
    df = add_source(df).with_columns(
        combine_date_time(pl.col("date"), pl.col("downtime_start_time")).alias("downtime_start_timestamp"),
        combine_date_time(pl.col("date"), pl.col("downtime_end_time")).alias("downtime_end_timestamp"),
        pl.col("downtime_time").cast(pl.Float64, strict=False).alias("downtime_h"),
        pl.col("downtime_id").cast(pl.String),
    ).select(
        "source_dataset_id", "downtime_id", "downtime_start_timestamp",
        "downtime_end_timestamp", "downtime_h"
    )
    df.write_parquet(OUT / "downtime_events.parquet", compression="zstd")


def main() -> None:
    if not SRC.exists():
        raise FileNotFoundError(
            f"Bronze source not found: {SRC}. Run scripts/download_source.py first."
        )
    OUT.mkdir(parents=True, exist_ok=True)
    transform_processed_hourly()
    transform_daily()
    transform_hourly_operation()
    transform_downtime()
    print(f"Silver production/downtime files written to: {OUT}")


if __name__ == "__main__":
    main()
