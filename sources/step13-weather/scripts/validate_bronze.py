from pathlib import Path
import csv
import zipfile
import xarray as xr

BASE = Path(__file__).resolve().parents[1]
CONFIG = BASE / "config" / "era5_land_sites.csv"
BRONZE = BASE / "data" / "bronze" / "era5_land"

EXPECTED_MIN_HOURS = 17544  # 2024 leap year + 2025, per site

def main():
    failures = []

    with CONFIG.open(newline="", encoding="utf-8") as f:
        sites = list(csv.DictReader(f))

    for site in sites:
        site_code = site["site_code"]
        site_dir = BRONZE / site_code
        zips = list(site_dir.glob("*.zip"))
        nc_files = sorted((site_dir / "netcdf").rglob("*.nc"))

        if not zips:
            failures.append(f"{site_code}: missing Bronze ZIP")
            continue
        if not nc_files:
            failures.append(f"{site_code}: no NetCDF files")
            continue

        timestamps = set()
        variables = set()

        for nc in nc_files:
            ds = xr.open_dataset(nc)
            variables.update(ds.data_vars)
            time_name = "time" if "time" in ds.coords else ("valid_time" if "valid_time" in ds.coords else None)
            if time_name:
                timestamps.update(str(v) for v in ds[time_name].values)
            ds.close()

        print(f"{site_code}: {len(nc_files)} NetCDF file(s), {len(timestamps):,} unique hourly timestamps")
        print(f"{site_code}: variables found = {sorted(variables)}")

        if len(timestamps) < EXPECTED_MIN_HOURS:
            failures.append(
                f"{site_code}: expected at least {EXPECTED_MIN_HOURS:,} hourly timestamps, found {len(timestamps):,}"
            )

    if failures:
        print("\nVALIDATION FAILED")
        for item in failures:
            print(" -", item)
        raise SystemExit(1)

    print("\nBronze ERA5-Land validation passed.")

if __name__ == "__main__":
    main()
