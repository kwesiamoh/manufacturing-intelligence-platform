from pathlib import Path
import pandas as pd
import numpy as np

SEED = 20260825
rng = np.random.default_rng(SEED)

ROOT = Path(__file__).resolve().parents[2]
PRODUCTION = ROOT / "data" / "silver" / "synthetic_enterprise" / "production" / "production_operations_2024_2025.parquet"
BRONZE = ROOT / "data" / "bronze" / "synthetic_enterprise" / "quality"
SILVER = ROOT / "data" / "silver" / "synthetic_enterprise" / "quality"

# Small beverage-relevant defect taxonomy only.
PRODUCT_DEFECTS = {
    "BEV-WAT-STILL": [
        ("FILL_VOLUME", "Underfill / overfill", 0.35),
        ("CAP_CLOSURE", "Cap torque / closure defect", 0.25),
        ("LABEL", "Label placement / print defect", 0.20),
        ("BOTTLE", "Bottle deformation / visual defect", 0.20),
    ],
    "BEV-WAT-SPARK": [
        ("FILL_VOLUME", "Underfill / overfill", 0.25),
        ("CAP_CLOSURE", "Cap torque / closure defect", 0.30),
        ("CARBONATION", "Carbonation out of target", 0.25),
        ("LABEL", "Label placement / print defect", 0.20),
    ],
    "BEV-CSD-COLA": [
        ("FILL_VOLUME", "Underfill / overfill", 0.20),
        ("CAP_CLOSURE", "Cap torque / closure defect", 0.25),
        ("CARBONATION", "Carbonation out of target", 0.30),
        ("LABEL", "Label placement / print defect", 0.15),
        ("BOTTLE", "Bottle deformation / visual defect", 0.10),
    ],
    "BEV-CSD-CITRUS": [
        ("FILL_VOLUME", "Underfill / overfill", 0.20),
        ("CAP_CLOSURE", "Cap torque / closure defect", 0.25),
        ("CARBONATION", "Carbonation out of target", 0.30),
        ("LABEL", "Label placement / print defect", 0.15),
        ("BOTTLE", "Bottle deformation / visual defect", 0.10),
    ],
    "BEV-JUI-ORANGE": [
        ("FILL_VOLUME", "Underfill / overfill", 0.30),
        ("CAP_CLOSURE", "Cap torque / closure defect", 0.20),
        ("LABEL", "Label placement / print defect", 0.15),
        ("BOTTLE", "Bottle deformation / visual defect", 0.15),
        ("PROCESS_QUALITY", "Product quality out of target", 0.20),
    ],
    "BEV-ENE-CLASSIC": [
        ("FILL_VOLUME", "Underfill / overfill", 0.25),
        ("SEAM", "Can seam defect", 0.35),
        ("CAN_DAMAGE", "Can damage / deformation", 0.20),
        ("CODING", "Date / lot coding defect", 0.20),
    ],
}

def choose_weighted(items):
    w = np.array([x[2] for x in items], dtype=float)
    w = w / w.sum()
    return items[int(rng.choice(len(items), p=w))]

def split_count(total):
    total = int(total)
    if total <= 0:
        return []
    if total < 20:
        n = 1
    elif total < 100:
        n = int(rng.integers(1, 3))
    elif total < 500:
        n = int(rng.integers(2, 4))
    else:
        n = int(rng.integers(3, 6))

    raw = rng.gamma(shape=1.5, scale=1.0, size=n)
    shares = raw / raw.sum()
    counts = np.floor(shares * total).astype(int)
    remainder = total - counts.sum()

    for i in range(remainder):
        counts[i % n] += 1

    return [int(x) for x in counts if x > 0]

def main():
    if not PRODUCTION.exists():
        raise FileNotFoundError(f"Missing Stage 3D production file: {PRODUCTION}")

    BRONZE.mkdir(parents=True, exist_ok=True)
    SILVER.mkdir(parents=True, exist_ok=True)

    prod = pd.read_parquet(PRODUCTION)
    prod["timestamp_start"] = pd.to_datetime(prod["timestamp_start"])
    prod["timestamp_end"] = pd.to_datetime(prod["timestamp_end"])

    events = []
    quality_event_id = 1

    for row in prod.itertuples(index=False):
        reject_qty = int(row.reject_quantity)
        parts = split_count(reject_qty)

        if not parts:
            continue

        shift_start = pd.Timestamp(row.timestamp_start)
        shift_end = pd.Timestamp(row.timestamp_end)
        total_shift_min = max((shift_end - shift_start).total_seconds() / 60.0, 1.0)

        for rejected_units in parts:
            defect_code, defect_reason, _ = choose_weighted(PRODUCT_DEFECTS[row.product_code])

            # Place quality observation within the production shift.
            offset_min = float(rng.uniform(20, max(total_shift_min - 20, 21)))
            event_ts = shift_start + pd.Timedelta(minutes=offset_min)

            if row.line_class_code == "CAN_ENERGY_250":
                equipment_code = f"{row.line_code}-FIL" if defect_code in ("FILL_VOLUME","SEAM") else f"{row.line_code}-INS"
            else:
                equipment_code = f"{row.line_code}-FIL" if defect_code in ("FILL_VOLUME","CAP_CLOSURE","CARBONATION","PROCESS_QUALITY") else f"{row.line_code}-INS"

            events.append({
                "quality_event_id": f"QLT-{quality_event_id:09d}",
                "production_record_id": row.production_record_id,
                "site_code": row.site_code,
                "line_code": row.line_code,
                "equipment_code": equipment_code,
                "shift_code": row.shift_code,
                "product_code": row.product_code,
                "event_timestamp": event_ts,
                "defect_code": defect_code,
                "defect_reason": defect_reason,
                "rejected_units": rejected_units,
                "rework_units": 0,
                "quality_result": "FAIL",
                "data_class": "SYNTHETIC_OPERATIONAL",
                "integration_role": "SYNTHETIC_INTEGRATION",
                "generator_seed": SEED,
            })
            quality_event_id += 1

    q = pd.DataFrame(events)

    # Exact reconciliation to Stage 3D reject quantities.
    reject_by_prod = q.groupby("production_record_id")["rejected_units"].sum()
    check = prod[["production_record_id","reject_quantity"]].copy()
    check["event_reject_quantity"] = check["production_record_id"].map(reject_by_prod).fillna(0).astype(int)
    check["difference"] = check["reject_quantity"].astype(int) - check["event_reject_quantity"]
    max_abs_diff = int(check["difference"].abs().max())

    if max_abs_diff != 0:
        raise RuntimeError(f"Quality reconciliation failed. Max reject-unit difference = {max_abs_diff}")

    bronze_out = BRONZE / "quality_events_2024_2025.csv"
    silver_out = SILVER / "quality_events_2024_2025.parquet"

    q.to_csv(bronze_out, index=False)
    q.to_parquet(silver_out, index=False)

    summary = pd.DataFrame({
        "metric": [
            "quality_event_rows",
            "production_records_with_rejects",
            "rejected_units_total",
            "sites",
            "lines",
            "products",
            "max_reject_reconciliation_difference"
        ],
        "value": [
            len(q),
            q["production_record_id"].nunique(),
            int(q["rejected_units"].sum()),
            q["site_code"].nunique(),
            q["line_code"].nunique(),
            q["product_code"].nunique(),
            max_abs_diff,
        ]
    })
    summary.to_csv(BRONZE / "quality_events_summary.csv", index=False)

    print(f"Wrote {len(q):,} quality events")
    print(f"Bronze -> {bronze_out}")
    print(f"Silver -> {silver_out}")
    print(f"Rejected units total: {int(q['rejected_units'].sum()):,}")
    print(f"Reject reconciliation max difference: {max_abs_diff}")

if __name__ == "__main__":
    main()
