from pathlib import Path
import pandas as pd
import numpy as np

SEED = 20260825
GENERATOR_VERSION = "stage3h-energy-utilities-v2-can-air-5nm3-per-1000"
rng = np.random.default_rng(SEED)

ROOT = Path(__file__).resolve().parents[2]
PRODUCTION = ROOT / "data" / "silver" / "synthetic_enterprise" / \
    "production" / "production_operations_2024_2025.parquet"
WEATHER = ROOT / "sources" / "step13-weather" / "data" / "silver" / \
    "weather" / "enterprise_weather_context_2024_2025.parquet"

BRONZE = ROOT / "data" / "bronze" / "synthetic_enterprise" / "energy"
SILVER = ROOT / "data" / "silver" / "synthetic_enterprise" / "energy"

# Stage 3H is intentionally compact.
#
# PET production power is anchored to a peer-reviewed measured PET bottling-plant
# average of 245.3 kW during production and 12.327 kW during an unproductive period.
# The can line uses a conservative synthetic 250 kW production-power design point,
# within a published 120-450 kW range for 12,000-60,000 cans/h lines.
#
# These are synthetic enterprise design assumptions, not claims about a real plant.
POWER_CLASS = {
    "PET_WATER_STILL_500": {
        "production_kw": 245.3,
        "idle_kw": 12.327,
        "compressed_air_nm3_per_1000_units": 20.0,
    },
    "PET_CARBONATED_500": {
        "production_kw": 252.0,
        "idle_kw": 12.5,
        "compressed_air_nm3_per_1000_units": 22.0,
    },
    "PET_JUICE_1000": {
        "production_kw": 260.0,
        "idle_kw": 13.0,
        "compressed_air_nm3_per_1000_units": 30.0,
    },
    "CAN_ENERGY_250": {
        "production_kw": 250.0,
        "idle_kw": 15.0,
        # Synthetic can-line compressed-air design assumption.
        # 5.0 Nm3/1,000 cans is anchored to published canning-line
        # pneumatic-demand specifications and is substantially below
        # PET blow-moulding air intensity.
        "compressed_air_nm3_per_1000_units": 5.0,
    },
}

# Small site auxiliary base load used only to make a site-level energy view possible.
# This is synthetic and intentionally simple.
SITE_AUX_BASE_KW = 180.0


def main():
    if not PRODUCTION.exists():
        raise FileNotFoundError(
            f"Missing Stage 3D production file: {PRODUCTION}")
    if not WEATHER.exists():
        raise FileNotFoundError(
            f"Missing Stage 2E ERA5-Land Silver weather file: {WEATHER}")

    BRONZE.mkdir(parents=True, exist_ok=True)
    SILVER.mkdir(parents=True, exist_ok=True)

    prod = pd.read_parquet(PRODUCTION)
    prod["timestamp_start"] = pd.to_datetime(prod["timestamp_start"], utc=True)
    prod["timestamp_end"] = pd.to_datetime(prod["timestamp_end"], utc=True)

    weather = pd.read_parquet(WEATHER)
    weather["timestamp_utc"] = pd.to_datetime(
        weather["timestamp_utc"], utc=True)

    # Weather is hourly. Aggregate temperature over each shift by site.
    weather = weather[["site_code", "timestamp_utc",
                       "air_temperature_c"]].copy()
    weather["shift_date"] = weather["timestamp_utc"].dt.floor("D")

    # Create shift labels matching Stage 3D.
    h = weather["timestamp_utc"].dt.hour
    weather["shift_code"] = np.select(
        [(h >= 6) & (h < 14), (h >= 14) & (h < 22)],
        ["SHIFT-A", "SHIFT-B"],
        default="SHIFT-C"
    )
    # Hours 00:00-05:59 belong to the previous day's night shift.
    weather["production_date"] = weather["shift_date"]
    night_early = h < 6
    weather.loc[night_early, "production_date"] = weather.loc[night_early,
                                                              "shift_date"] - pd.Timedelta(days=1)

    wt = (
        weather.groupby(["site_code", "production_date",
                        "shift_code"], as_index=False)
        ["air_temperature_c"].mean()
        .rename(columns={"air_temperature_c": "shift_mean_air_temperature_c"})
    )

    prod["production_date"] = prod["timestamp_start"].dt.floor("D")
    df = prod.merge(
        wt,
        on=["site_code", "production_date", "shift_code"],
        how="left",
        validate="many_to_one"
    )

    rows = []
    for row in df.itertuples(index=False):
        cfg = POWER_CLASS[row.line_class_code]

        operating_h = float(row.operating_time_min) / 60.0
        planned_changeover_h = float(row.planned_changeover_min) / 60.0
        unplanned_h = float(row.unplanned_downtime_min) / 60.0
        scheduled_break_h = float(row.scheduled_break_min) / 60.0

        # Beverage bottling power does not decrease linearly with speed.
        # Keep production power mostly fixed, with only a modest performance response.
        perf = float(row.performance_driver)
        production_power_factor = 0.80 + 0.20 * perf
        production_kw = cfg["production_kw"] * production_power_factor

        production_kwh = production_kw * operating_h
        idle_hours = planned_changeover_h + unplanned_h + scheduled_break_h
        idle_kwh = cfg["idle_kw"] * idle_hours
        line_electricity_kwh = production_kwh + idle_kwh

        units = max(float(row.actual_quantity), 0.0)
        energy_intensity = (
            line_electricity_kwh / (units / 1000.0)
            if units > 0 else np.nan
        )

        air_intensity = cfg["compressed_air_nm3_per_1000_units"]
        compressed_air_nm3 = (
            air_intensity * (units / 1000.0)
            if np.isfinite(air_intensity) and units > 0 else np.nan
        )

        temp = getattr(row, "shift_mean_air_temperature_c")
        # Simple site auxiliary effect: cooling rises above 22 C and heating/support
        # load rises below 5 C. This is contextual, not a detailed HVAC model.
        weather_aux_kw = 0.0
        if pd.notna(temp):
            if temp > 22:
                weather_aux_kw = (float(temp) - 22.0) * 3.0
            elif temp < 5:
                weather_aux_kw = (5.0 - float(temp)) * 2.0

        rows.append({
            "energy_record_id": f"ENE-{len(rows)+1:08d}",
            "production_record_id": row.production_record_id,
            "site_code": row.site_code,
            "line_code": row.line_code,
            "line_class_code": row.line_class_code,
            "shift_code": row.shift_code,
            "product_code": row.product_code,
            "timestamp_start": row.timestamp_start,
            "timestamp_end": row.timestamp_end,
            "actual_quantity": int(row.actual_quantity),
            "line_production_electricity_kwh": round(production_kwh, 6),
            "line_idle_electricity_kwh": round(idle_kwh, 6),
            "line_total_electricity_kwh": round(line_electricity_kwh, 6),
            "energy_intensity_kwh_per_1000_units": round(energy_intensity, 6),
            "compressed_air_nm3": round(compressed_air_nm3, 6) if pd.notna(compressed_air_nm3) else np.nan,
            "compressed_air_nm3_per_1000_units": air_intensity,
            "shift_mean_air_temperature_c": round(float(temp), 4) if pd.notna(temp) else np.nan,
            "site_auxiliary_base_kw": SITE_AUX_BASE_KW,
            "site_weather_auxiliary_kw": round(weather_aux_kw, 6),
            "data_class": "SYNTHETIC_OPERATIONAL",
            "integration_role": "SYNTHETIC_INTEGRATION",
            "weather_data_class": "REAL_EXTERNAL_CONTEXT",
            "generator_seed": SEED,
        })

    energy = pd.DataFrame(rows)

    # Site-shift rollup, allocating the site auxiliary base/weather load once per site-shift.
    site_shift = (
        energy.groupby(["site_code", "shift_code",
                       "timestamp_start", "timestamp_end"], as_index=False)
        .agg(
            line_electricity_kwh=("line_total_electricity_kwh", "sum"),
            production_units=("actual_quantity", "sum"),
            mean_air_temperature_c=("shift_mean_air_temperature_c", "mean"),
            site_auxiliary_base_kw=("site_auxiliary_base_kw", "first"),
            site_weather_auxiliary_kw=("site_weather_auxiliary_kw", "first"),
        )
    )
    site_shift["shift_hours"] = (
        (pd.to_datetime(site_shift["timestamp_end"]) -
         pd.to_datetime(site_shift["timestamp_start"]))
        .dt.total_seconds() / 3600.0
    )
    site_shift["site_auxiliary_electricity_kwh"] = (
        (site_shift["site_auxiliary_base_kw"] +
         site_shift["site_weather_auxiliary_kw"])
        * site_shift["shift_hours"]
    )
    site_shift["site_total_electricity_kwh"] = (
        site_shift["line_electricity_kwh"] +
        site_shift["site_auxiliary_electricity_kwh"]
    )
    site_shift["site_energy_intensity_kwh_per_1000_units"] = np.where(
        site_shift["production_units"] > 0,
        site_shift["site_total_electricity_kwh"] /
        (site_shift["production_units"] / 1000.0),
        np.nan
    )
    site_shift["data_class"] = "SYNTHETIC_OPERATIONAL"
    site_shift["integration_role"] = "SYNTHETIC_INTEGRATION"
    site_shift["weather_data_class"] = "REAL_EXTERNAL_CONTEXT"

    # Validation
    orphan_prod = int((~energy["production_record_id"].isin(
        set(prod["production_record_id"]))).sum())
    missing_weather = int(energy["shift_mean_air_temperature_c"].isna().sum())
    invalid_energy = int((energy["line_total_electricity_kwh"] <= 0).sum())

    if orphan_prod or invalid_energy:
        raise RuntimeError(
            f"Validation failed: orphan_prod={orphan_prod}, invalid_energy={invalid_energy}"
        )

    # Outputs
    line_bronze = BRONZE / "line_energy_utility_2024_2025.csv"
    line_silver = SILVER / "line_energy_utility_2024_2025.parquet"
    site_bronze = BRONZE / "site_energy_2024_2025.csv"
    site_silver = SILVER / "site_energy_2024_2025.parquet"

    energy.to_csv(line_bronze, index=False)
    energy.to_parquet(line_silver, index=False)
    site_shift.to_csv(site_bronze, index=False)
    site_shift.to_parquet(site_silver, index=False)

    pet_air_total = float(energy.loc[
        energy["line_class_code"].str.startswith("PET_"),
        "compressed_air_nm3",
    ].sum(skipna=True))
    can_air_total = float(energy.loc[
        energy["line_class_code"].eq("CAN_ENERGY_250"),
        "compressed_air_nm3",
    ].sum(skipna=True))
    enterprise_air_total = float(
        energy["compressed_air_nm3"].sum(skipna=True))

    summary = pd.DataFrame({
        "metric": [
            "generator_version",
            "generator_seed",
            "line_shift_energy_rows",
            "site_shift_energy_rows",
            "sites",
            "lines",
            "line_electricity_kwh_total",
            "line_idle_electricity_kwh_total",
            "site_total_electricity_kwh",
            "pet_compressed_air_nm3_total",
            "can_compressed_air_nm3_total",
            "enterprise_compressed_air_nm3_total",
            "can_compressed_air_nm3_per_1000_units",
            "missing_weather_matches",
            "orphan_production_links",
            "nonpositive_energy_rows",
        ],
        "value": [
            GENERATOR_VERSION,
            SEED,
            len(energy),
            len(site_shift),
            energy["site_code"].nunique(),
            energy["line_code"].nunique(),
            round(float(energy["line_total_electricity_kwh"].sum()), 3),
            round(float(energy["line_idle_electricity_kwh"].sum()), 3),
            round(float(site_shift["site_total_electricity_kwh"].sum()), 3),
            round(pet_air_total, 3),
            round(can_air_total, 3),
            round(enterprise_air_total, 3),
            POWER_CLASS["CAN_ENERGY_250"]["compressed_air_nm3_per_1000_units"],
            missing_weather,
            orphan_prod,
            invalid_energy,
        ]
    })
    summary.to_csv(BRONZE / "energy_utility_summary.csv", index=False)

    print(f"Wrote {len(energy):,} line-shift energy records")
    print(f"Wrote {len(site_shift):,} site-shift energy records")
    print(f"Line Silver -> {line_silver}")
    print(f"Site Silver -> {site_silver}")
    print(f"Missing weather matches: {missing_weather}")
    print(f"Orphan production links: {orphan_prod}")
    print(f"Nonpositive energy rows: {invalid_energy}")
    print("Can-line compressed air generated using the documented 5.0 Nm3/1,000-can synthetic design assumption.")


if __name__ == "__main__":
    main()
