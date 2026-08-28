from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
BRONZE = ROOT / "bronze" / "hydraulic_condition_monitoring"
EXPECTED_CYCLES = 2205

SENSORS = {
    "PS1.txt": 6000,
    "PS2.txt": 6000,
    "PS3.txt": 6000,
    "PS4.txt": 6000,
    "PS5.txt": 6000,
    "PS6.txt": 6000,
    "EPS1.txt": 6000,
    "FS1.txt": 600,
    "FS2.txt": 600,
    "TS1.txt": 60,
    "TS2.txt": 60,
    "TS3.txt": 60,
    "TS4.txt": 60,
    "VS1.txt": 60,
    "CE.txt": 60,
    "CP.txt": 60,
    "SE.txt": 60,
}


def resolve(name: str) -> pathlib.Path:
    matches = list(BRONZE.rglob(name))
    if not matches:
        raise FileNotFoundError(f"Required Bronze file not found: {name}")
    if len(matches) > 1:
        raise RuntimeError(f"Multiple matches for {name}: {matches}")
    return matches[0]


def inspect_matrix(path: pathlib.Path, expected_cols: int) -> None:
    rows = 0
    first_cols = None
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not line.strip():
                continue
            rows += 1
            if first_cols is None:
                first_cols = len(line.split())
    if rows != EXPECTED_CYCLES:
        raise ValueError(f"{path.name}: expected {EXPECTED_CYCLES} cycles, found {rows}")
    if first_cols != expected_cols:
        raise ValueError(f"{path.name}: expected {expected_cols} samples/cycle, found {first_cols}")
    print(f"OK  {path.name}: {rows} cycles × {first_cols} samples")

for filename, cols in SENSORS.items():
    inspect_matrix(resolve(filename), cols)

profile = resolve("profile.txt")
profile_rows = [line for line in profile.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
if len(profile_rows) != EXPECTED_CYCLES:
    raise ValueError(f"profile.txt: expected {EXPECTED_CYCLES} rows, found {len(profile_rows)}")
if len(profile_rows[0].split()) != 5:
    raise ValueError("profile.txt: expected 5 target columns")

print(f"OK  profile.txt: {len(profile_rows)} cycles × 5 target labels")
print("Bronze validation passed.")
