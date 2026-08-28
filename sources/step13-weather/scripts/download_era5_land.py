from pathlib import Path
import csv
import os
import sys
import tempfile
import cdsapi

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE.parent))
from _shared.bronze_guard import (
    install_chunks,
    refresh_zip_extraction,
    reuse_complete_set_or_raise,
)
CONFIG = BASE / "config" / "era5_land_sites.csv"
PERIOD = BASE / "config" / "weather_period.csv"
BRONZE = BASE / "data" / "bronze" / "era5_land"

DATASET = "reanalysis-era5-land-timeseries"
VARIABLES = [
    "2m_temperature",
    "2m_dewpoint_temperature",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "surface_pressure",
    "surface_solar_radiation_downwards",
    "total_precipitation",
]

def read_period():
    with PERIOD.open(newline="", encoding="utf-8") as f:
        row = next(csv.DictReader(f))
    return row["start_date"], row["end_date"]

def main():
    BRONZE.mkdir(parents=True, exist_ok=True)

    start_date, end_date = read_period()
    date_range = f"{start_date}/{end_date}"

    client = None

    with CONFIG.open(newline="", encoding="utf-8") as f:
        sites = list(csv.DictReader(f))

    for site in sites:
        site_code = site["site_code"]
        lat = float(site["latitude"])
        lon = float(site["longitude"])

        site_dir = BRONZE / site_code
        site_dir.mkdir(parents=True, exist_ok=True)

        zip_path = site_dir / f"{site_code}_era5_land_2024_2025.zip"

        if reuse_complete_set_or_raise([zip_path]):
            print(f"{site_code}: verified and reused immutable Bronze ZIP.")
        else:
            if client is None:
                client = cdsapi.Client()
            request = {
                "variable": VARIABLES,
                "location": {"longitude": lon, "latitude": lat},
                "date": [date_range],
                "data_format": "netcdf",
            }
            print(f"{site_code}: requesting ERA5-Land {date_range} at ({lat}, {lon})")
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=zip_path.name + ".", suffix=".incoming", dir=site_dir
            )
            os.close(descriptor)
            Path(temporary_name).unlink(missing_ok=True)
            try:
                # cdsapi owns the temporary destination; the canonical path is
                # installed only after retrieval completes.
                client.retrieve(DATASET, request, temporary_name)
                temporary = Path(temporary_name)
                with temporary.open("rb") as stream:
                    install_chunks(
                        zip_path,
                        iter(lambda: stream.read(1024 * 1024), b""),
                    )
            finally:
                Path(temporary_name).unlink(missing_ok=True)
            print(f"{site_code}: wrote {zip_path}")

        extract_dir = site_dir / "netcdf"
        # Replace the derived directory as one staged unit so files from an
        # older extraction cannot survive.
        refresh_zip_extraction(zip_path, extract_dir, required_suffix=".nc")
        nc_files = sorted(extract_dir.rglob("*.nc"))
        print(f"{site_code}: {len(nc_files)} NetCDF group file(s) ready.")

if __name__ == "__main__":
    main()
