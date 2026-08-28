from pathlib import Path
import pandas as pd
import numpy as np

SEED = 20260825
rng = np.random.default_rng(SEED)

ROOT = Path(__file__).resolve().parents[2]
DOWNTIME = ROOT / "data" / "silver" / "synthetic_enterprise" / "downtime" / "downtime_events_2024_2025.parquet"
BRONZE = ROOT / "data" / "bronze" / "synthetic_enterprise" / "maintenance"
SILVER = ROOT / "data" / "silver" / "synthetic_enterprise" / "maintenance"

def maintenance_required(row):
    if bool(row.planned_flag):
        return False
    if row.failure_category not in ("MECHANICAL", "ELECTRICAL"):
        return False

    # Short stops are normally cleared operationally; longer failures are more
    # likely to require a maintenance intervention.
    d = float(row.duration_min)
    if d >= 30:
        return True
    if d >= 15:
        return rng.random() < 0.75
    if d >= 8:
        return rng.random() < 0.35
    return False

def main():
    if not DOWNTIME.exists():
        raise FileNotFoundError(f"Missing downtime Silver downtime file: {DOWNTIME}")

    BRONZE.mkdir(parents=True, exist_ok=True)
    SILVER.mkdir(parents=True, exist_ok=True)

    dt = pd.read_parquet(DOWNTIME)
    dt["event_start"] = pd.to_datetime(dt["event_start"])
    dt["event_end"] = pd.to_datetime(dt["event_end"])

    rows = []
    work_order_no = 1

    for row in dt.itertuples(index=False):
        if not maintenance_required(row):
            continue

        event_duration = float(row.duration_min)

        # Maintenance begins shortly after the stop is identified.
        response_delay = min(float(rng.uniform(1.0, 4.0)), max(event_duration * 0.15, 0.5))
        maintenance_duration = max(event_duration - response_delay, 0.5)

        start = pd.Timestamp(row.event_start) + pd.Timedelta(minutes=response_delay)
        end = min(
            start + pd.Timedelta(minutes=maintenance_duration),
            pd.Timestamp(row.event_end)
        )
        maintenance_duration = max((end - start).total_seconds() / 60.0, 0.0)

        if event_duration < 20:
            technicians = 1
        elif event_duration < 45:
            technicians = int(rng.choice([1, 2], p=[0.35, 0.65]))
        else:
            technicians = int(rng.choice([2, 3], p=[0.75, 0.25]))

        labor_hours = maintenance_duration / 60.0 * technicians

        if row.failure_category == "MECHANICAL":
            maintenance_type = "CORRECTIVE_MECHANICAL"
        else:
            maintenance_type = "CORRECTIVE_ELECTRICAL"

        rows.append({
            "maintenance_id": f"MWO-{work_order_no:09d}",
            "downtime_event_id": row.downtime_event_id,
            "production_record_id": row.production_record_id,
            "site_code": row.site_code,
            "line_code": row.line_code,
            "equipment_code": row.equipment_code,
            "shift_code": row.shift_code,
            "product_code": row.product_code,
            "maintenance_type": maintenance_type,
            "failure_category": row.failure_category,
            "failure_reason": row.failure_reason,
            "start_timestamp": start,
            "end_timestamp": end,
            "duration_hours": round(maintenance_duration / 60.0, 6),
            "technician_count": technicians,
            "labor_hours": round(labor_hours, 6),
            "labor_cost": np.nan,
            "material_cost": np.nan,
            "other_cost": np.nan,
            "total_cost": np.nan,
            "planned_flag": False,
            "work_order_status": "COMPLETED",
            "data_class": "SYNTHETIC_OPERATIONAL",
            "integration_role": "SYNTHETIC_INTEGRATION",
            "generator_seed": SEED,
        })
        work_order_no += 1

    maint = pd.DataFrame(rows)

    if maint.empty:
        raise RuntimeError("No maintenance work orders generated.")

    # Referential and timing validation.
    downtime_ids = set(dt["downtime_event_id"])
    orphan_count = int((~maint["downtime_event_id"].isin(downtime_ids)).sum())
    invalid_time_count = int((maint["end_timestamp"] < maint["start_timestamp"]).sum())

    # Maintenance interval must remain inside the linked downtime interval.
    linked = maint.merge(
        dt[["downtime_event_id","event_start","event_end","duration_min"]],
        on="downtime_event_id",
        how="left",
        validate="one_to_one"
    )
    outside_count = int(
        (
            (linked["start_timestamp"] < linked["event_start"]) |
            (linked["end_timestamp"] > linked["event_end"])
        ).sum()
    )

    if orphan_count or invalid_time_count or outside_count:
        raise RuntimeError(
            f"Validation failed: orphan={orphan_count}, invalid_time={invalid_time_count}, "
            f"outside_downtime={outside_count}"
        )

    bronze_out = BRONZE / "maintenance_work_orders_2024_2025.csv"
    silver_out = SILVER / "maintenance_work_orders_2024_2025.parquet"

    maint.to_csv(bronze_out, index=False)
    maint.to_parquet(silver_out, index=False)

    summary = pd.DataFrame({
        "metric": [
            "maintenance_work_orders",
            "sites",
            "lines",
            "equipment_assets",
            "mechanical_work_orders",
            "electrical_work_orders",
            "labor_hours_total",
            "orphan_downtime_links",
            "invalid_time_intervals",
            "maintenance_intervals_outside_downtime",
        ],
        "value": [
            len(maint),
            maint["site_code"].nunique(),
            maint["line_code"].nunique(),
            maint["equipment_code"].nunique(),
            int((maint["failure_category"] == "MECHANICAL").sum()),
            int((maint["failure_category"] == "ELECTRICAL").sum()),
            round(float(maint["labor_hours"].sum()), 3),
            orphan_count,
            invalid_time_count,
            outside_count,
        ],
    })
    summary.to_csv(BRONZE / "maintenance_work_orders_summary.csv", index=False)

    print(f"Wrote {len(maint):,} maintenance work orders")
    print(f"Bronze -> {bronze_out}")
    print(f"Silver -> {silver_out}")
    print(f"Linked downtime orphans: {orphan_count}")
    print(f"Invalid time intervals: {invalid_time_count}")
    print(f"Maintenance intervals outside downtime: {outside_count}")
    print("Maintenance cost fields intentionally left null until the financial-parameter step.")

if __name__ == "__main__":
    main()
