from pathlib import Path
import pandas as pd
import numpy as np

SEED = 20260825
rng = np.random.default_rng(SEED)

ROOT = Path(__file__).resolve().parents[2]
PRODUCTION = ROOT / "data" / "silver" / "synthetic_enterprise" / "production" / "production_operations_2024_2025.parquet"
BRONZE = ROOT / "data" / "bronze" / "synthetic_enterprise" / "downtime"
SILVER = ROOT / "data" / "silver" / "synthetic_enterprise" / "downtime"

# Beverage-line failure families kept deliberately compact.
FAILURE_WEIGHTS = {
    "BLOW_MOULDER": [
        ("MECHANICAL", "Mould handling / stretch-blow fault", 0.45),
        ("PROCESS", "Bottle formation instability", 0.30),
        ("ELECTRICAL", "Drive / sensor fault", 0.25),
    ],
    "FILLER_CAPPER": [
        ("MECHANICAL", "Filler / capper mechanical fault", 0.40),
        ("PROCESS", "Filling process interruption", 0.35),
        ("ELECTRICAL", "Control / sensor fault", 0.25),
    ],
    "FILLER_SEAMER": [
        ("MECHANICAL", "Filler / seamer mechanical fault", 0.45),
        ("PROCESS", "Filling / seaming process interruption", 0.35),
        ("ELECTRICAL", "Control / sensor fault", 0.20),
    ],
    "CONVEYOR": [
        ("MECHANICAL", "Conveyor jam", 0.65),
        ("ELECTRICAL", "Conveyor drive / sensor fault", 0.35),
    ],
    "INSPECTION_SYSTEM": [
        ("QUALITY", "Inspection system stop", 0.55),
        ("ELECTRICAL", "Inspection sensor / control fault", 0.45),
    ],
    "LABELLER": [
        ("MECHANICAL", "Label feed / applicator fault", 0.60),
        ("MATERIAL", "Label material interruption", 0.40),
    ],
    "PACKER": [
        ("MECHANICAL", "Packing machine jam", 0.55),
        ("MATERIAL", "Packaging material interruption", 0.45),
    ],
    "PALLETISER": [
        ("MECHANICAL", "Palletiser handling fault", 0.65),
        ("ELECTRICAL", "Palletiser control fault", 0.35),
    ],
    "DEPALLETISER": [
        ("MECHANICAL", "Can depalletiser handling fault", 0.70),
        ("ELECTRICAL", "Depalletiser control fault", 0.30),
    ],
    "RINSER": [
        ("PROCESS", "Can rinser interruption", 0.60),
        ("MECHANICAL", "Can rinser mechanical fault", 0.40),
    ],
}

LINE_ASSETS = {
    "PET_WATER_STILL_500": [
        ("BLW","BLOW_MOULDER",0.18),
        ("AIR","CONVEYOR",0.10),
        ("FIL","FILLER_CAPPER",0.24),
        ("INS","INSPECTION_SYSTEM",0.08),
        ("LAB","LABELLER",0.10),
        ("PKR","PACKER",0.12),
        ("CNV","CONVEYOR",0.08),
        ("PAL","PALLETISER",0.10),
    ],
    "PET_CARBONATED_500": [
        ("BLW","BLOW_MOULDER",0.16),
        ("AIR","CONVEYOR",0.09),
        ("FIL","FILLER_CAPPER",0.27),
        ("INS","INSPECTION_SYSTEM",0.08),
        ("LAB","LABELLER",0.09),
        ("PKR","PACKER",0.12),
        ("CNV","CONVEYOR",0.08),
        ("PAL","PALLETISER",0.11),
    ],
    "PET_JUICE_1000": [
        ("BLW","BLOW_MOULDER",0.15),
        ("AIR","CONVEYOR",0.08),
        ("FIL","FILLER_CAPPER",0.30),
        ("INS","INSPECTION_SYSTEM",0.09),
        ("LAB","LABELLER",0.08),
        ("PKR","PACKER",0.11),
        ("CNV","CONVEYOR",0.08),
        ("PAL","PALLETISER",0.11),
    ],
    "CAN_ENERGY_250": [
        ("DEP","DEPALLETISER",0.12),
        ("RIN","RINSER",0.08),
        ("FIL","FILLER_SEAMER",0.33),
        ("INS","INSPECTION_SYSTEM",0.09),
        ("PKR","PACKER",0.14),
        ("CNV","CONVEYOR",0.10),
        ("PAL","PALLETISER",0.14),
    ],
}

def choose_weighted(items):
    weights = np.array([x[-1] for x in items], dtype=float)
    weights = weights / weights.sum()
    idx = rng.choice(len(items), p=weights)
    return items[idx]

def split_duration(total_min):
    """Split a shift-level downtime total into a small number of events whose durations sum exactly."""
    total_min = float(total_min)
    if total_min <= 0.001:
        return []

    if total_min < 8:
        n = 1
    elif total_min < 22:
        n = int(rng.integers(1, 3))
    elif total_min < 45:
        n = int(rng.integers(2, 4))
    else:
        n = int(rng.integers(3, 6))

    raw = rng.gamma(shape=1.6, scale=1.0, size=n)
    parts = raw / raw.sum() * total_min
    parts = np.round(parts, 3)
    # Force exact reconciliation after rounding.
    parts[-1] = round(total_min - float(parts[:-1].sum()), 3)
    return [float(x) for x in parts if x > 0]

def main():
    if not PRODUCTION.exists():
        raise FileNotFoundError(f"Missing production Silver production file: {PRODUCTION}")

    BRONZE.mkdir(parents=True, exist_ok=True)
    SILVER.mkdir(parents=True, exist_ok=True)

    prod = pd.read_parquet(PRODUCTION)
    prod["timestamp_start"] = pd.to_datetime(prod["timestamp_start"])
    prod["timestamp_end"] = pd.to_datetime(prod["timestamp_end"])

    events = []
    event_id = 1

    for row in prod.itertuples(index=False):
        shift_start = pd.Timestamp(row.timestamp_start)
        shift_end = pd.Timestamp(row.timestamp_end)

        # Planned changeover event, if present.
        chg = float(row.planned_changeover_min)
        if chg > 0.001:
            start = shift_start + pd.Timedelta(minutes=30)
            end = start + pd.Timedelta(minutes=chg)
            events.append({
                "downtime_event_id": f"DT-{event_id:09d}",
                "production_record_id": row.production_record_id,
                "site_code": row.site_code,
                "line_code": row.line_code,
                "equipment_code": f"{row.line_code}-FIL",
                "shift_code": row.shift_code,
                "product_code": row.product_code,
                "event_start": start,
                "event_end": end,
                "duration_min": round(chg, 3),
                "planned_flag": True,
                "failure_category": "CHANGEOVER",
                "failure_reason": "Planned product changeover",
                "source_event_code": "PLANNED_CHANGEOVER",
                "data_class": "SYNTHETIC_OPERATIONAL",
                "integration_role": "SYNTHETIC_INTEGRATION",
                "generator_seed": SEED,
            })
            event_id += 1

        total_unplanned = float(row.unplanned_downtime_min)
        parts = split_duration(total_unplanned)

        if parts:
            # Place events inside the shift without overlap. We distribute candidate start positions
            # across the available window, then step forward by the event durations.
            window_start = shift_start + pd.Timedelta(minutes=45 + chg)
            max_window = max((shift_end - window_start).total_seconds()/60.0 - sum(parts) - 10, 1)
            gaps = rng.dirichlet(np.ones(len(parts)+1)) * max_window

            cursor = window_start + pd.Timedelta(minutes=float(gaps[0]))

            for i, dur in enumerate(parts):
                suffix, equipment_type, _ = choose_weighted(LINE_ASSETS[row.line_class_code])
                category, reason, _ = choose_weighted(FAILURE_WEIGHTS[equipment_type])

                start = cursor
                end = start + pd.Timedelta(minutes=dur)

                events.append({
                    "downtime_event_id": f"DT-{event_id:09d}",
                    "production_record_id": row.production_record_id,
                    "site_code": row.site_code,
                    "line_code": row.line_code,
                    "equipment_code": f"{row.line_code}-{suffix}",
                    "shift_code": row.shift_code,
                    "product_code": row.product_code,
                    "event_start": start,
                    "event_end": end,
                    "duration_min": round(dur, 3),
                    "planned_flag": False,
                    "failure_category": category,
                    "failure_reason": reason,
                    "source_event_code": "UNPLANNED_STOP",
                    "data_class": "SYNTHETIC_OPERATIONAL",
                    "integration_role": "SYNTHETIC_INTEGRATION",
                    "generator_seed": SEED,
                })
                event_id += 1
                cursor = end + pd.Timedelta(minutes=float(gaps[i+1]))

    dt = pd.DataFrame(events)

    # Validate exact reconciliation by production record.
    agg = (
        dt.groupby(["production_record_id","planned_flag"], as_index=False)["duration_min"]
          .sum()
    )
    planned = agg[agg["planned_flag"]].set_index("production_record_id")["duration_min"]
    unplanned = agg[~agg["planned_flag"]].set_index("production_record_id")["duration_min"]

    check = prod[["production_record_id","planned_changeover_min","unplanned_downtime_min"]].copy()
    check["event_planned_changeover_min"] = check["production_record_id"].map(planned).fillna(0.0)
    check["event_unplanned_downtime_min"] = check["production_record_id"].map(unplanned).fillna(0.0)
    check["planned_diff_min"] = (check["planned_changeover_min"] - check["event_planned_changeover_min"]).abs()
    check["unplanned_diff_min"] = (check["unplanned_downtime_min"] - check["event_unplanned_downtime_min"]).abs()

    max_planned_diff = float(check["planned_diff_min"].max())
    max_unplanned_diff = float(check["unplanned_diff_min"].max())

    if max_planned_diff > 0.002 or max_unplanned_diff > 0.002:
        raise RuntimeError(
            f"Downtime reconciliation failed: planned max diff {max_planned_diff}, "
            f"unplanned max diff {max_unplanned_diff}"
        )

    # Bronze source is CSV for transparency; Silver is Parquet for analytics.
    bronze_out = BRONZE / "downtime_events_2024_2025.csv"
    silver_out = SILVER / "downtime_events_2024_2025.parquet"
    dt.to_csv(bronze_out, index=False)
    dt.to_parquet(silver_out, index=False)

    summary = pd.DataFrame({
        "metric": [
            "event_rows",
            "planned_changeover_events",
            "unplanned_stop_events",
            "lines",
            "sites",
            "planned_minutes_total",
            "unplanned_minutes_total",
            "max_planned_reconciliation_diff_min",
            "max_unplanned_reconciliation_diff_min",
        ],
        "value": [
            len(dt),
            int(dt["planned_flag"].sum()),
            int((~dt["planned_flag"]).sum()),
            dt["line_code"].nunique(),
            dt["site_code"].nunique(),
            round(dt.loc[dt["planned_flag"], "duration_min"].sum(), 3),
            round(dt.loc[~dt["planned_flag"], "duration_min"].sum(), 3),
            max_planned_diff,
            max_unplanned_diff,
        ]
    })
    summary.to_csv(BRONZE / "downtime_events_summary.csv", index=False)

    print(f"Wrote {len(dt):,} downtime events")
    print(f"Bronze -> {bronze_out}")
    print(f"Silver -> {silver_out}")
    print(f"Planned reconciliation max diff: {max_planned_diff:.6f} min")
    print(f"Unplanned reconciliation max diff: {max_unplanned_diff:.6f} min")

if __name__ == "__main__":
    main()
