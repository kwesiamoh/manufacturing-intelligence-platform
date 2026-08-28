from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]

RAW = BASE / "data" / "bronze" / "steel_energy" / "Steel_industry_data.csv"
OUT = BASE / "data" / "silver" / "steel_energy" / "steel_energy.parquet"

OUT.parent.mkdir(parents=True, exist_ok=True)

COLUMN_MAP = {
    "date": "timestamp",
    "Usage_kWh": "usage_kwh",
    "Lagging_Current_Reactive.Power_kVarh": "lagging_reactive_power_kvarh",
    "Leading_Current_Reactive_Power_kVarh": "leading_reactive_power_kvarh",
    "CO2(tCO2)": "co2_tco2",
    "Lagging_Current_Power_Factor": "lagging_power_factor_pct",
    "Leading_Current_Power_Factor": "leading_power_factor_pct",
    "NSM": "seconds_from_midnight",
    "WeekStatus": "week_status",
    "Day_of_week": "day_of_week",
    "Load_Type": "load_type",
}

df = pd.read_csv(RAW, encoding="utf-8-sig")
assert len(df) == 35040
assert df.isna().sum().sum() == 0

df = df.rename(columns=COLUMN_MAP)
df["timestamp"] = pd.to_datetime(df["timestamp"], format="%d/%m/%Y %H:%M")
df["source_dataset"] = "UCI Steel Industry Energy Consumption (ID 851)"

OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(OUT, index=False, compression="snappy")
print(f"Wrote {len(df):,} rows to {OUT}")
