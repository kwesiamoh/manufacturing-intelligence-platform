from __future__ import annotations

import pathlib
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = pathlib.Path(__file__).resolve().parents[1]
BRONZE = ROOT / "bronze" / "hydraulic_condition_monitoring"
SILVER = ROOT / "silver" / "reliability"
SILVER.mkdir(parents=True, exist_ok=True)
CHUNK_CYCLES = 100

SENSOR_META = {
    "PS1": ("pressure", "bar", 100), "PS2": ("pressure", "bar", 100),
    "PS3": ("pressure", "bar", 100), "PS4": ("pressure", "bar", 100),
    "PS5": ("pressure", "bar", 100), "PS6": ("pressure", "bar", 100),
    "EPS1": ("motor_power", "W", 100),
    "FS1": ("volume_flow", "L/min", 10), "FS2": ("volume_flow", "L/min", 10),
    "TS1": ("temperature", "degC", 1), "TS2": ("temperature", "degC", 1),
    "TS3": ("temperature", "degC", 1), "TS4": ("temperature", "degC", 1),
    "VS1": ("vibration", "mm/s", 1),
    "CE": ("cooling_efficiency", "percent", 1),
    "CP": ("cooling_power", "kW", 1),
    "SE": ("efficiency_factor", "percent", 1),
}


def resolve(name: str) -> pathlib.Path:
    matches = list(BRONZE.rglob(name))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one {name}; found {len(matches)}")
    return matches[0]

profile = pd.read_csv(resolve("profile.txt"), sep=r"\s+", header=None)
profile.columns = [
    "cooler_condition_pct", "valve_condition_pct", "internal_pump_leakage_class",
    "hydraulic_accumulator_bar", "stable_flag",
]
profile.insert(0, "cycle_id", range(1, len(profile) + 1))
profile.to_parquet(SILVER / "condition_labels.parquet", index=False)

# Stream each sensor file in cycle chunks so high-frequency matrices never need to be
# expanded into tens of millions of long-form rows in RAM at once.
for sensor_id, (quantity, unit, hz) in SENSOR_META.items():
    src = resolve(f"{sensor_id}.txt")
    out_dir = SILVER / "telemetry" / f"sensor_id={sensor_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    cycle_offset = 0
    part = 0
    for matrix in pd.read_csv(
        src, sep=r"\s+", header=None, dtype="float32", chunksize=CHUNK_CYCLES
    ):
        first_cycle = cycle_offset + 1
        matrix.index = pd.RangeIndex(first_cycle, first_cycle + len(matrix), name="cycle_id")
        long = matrix.stack().rename("value").reset_index()
        long.columns = ["cycle_id", "sample_index", "value"]
        long["cycle_id"] = long["cycle_id"].astype("int32")
        long["sample_index"] = long["sample_index"].astype("int32")
        long["seconds_from_cycle_start"] = (long["sample_index"] / float(hz)).astype("float32")
        long.insert(1, "sensor_id", sensor_id)
        long["physical_quantity"] = quantity
        long["unit"] = unit
        long["sampling_rate_hz"] = hz

        table = pa.Table.from_pandas(long, preserve_index=False)
        pq.write_table(table, out_dir / f"part-{part:05d}.parquet", compression="zstd")
        cycle_offset += len(matrix)
        part += 1

    print(f"Wrote {sensor_id}: {cycle_offset} cycles in {part} Parquet parts")

print(f"Silver reliability dataset written to: {SILVER}")
print("No synthetic measurements or labels were created.")
