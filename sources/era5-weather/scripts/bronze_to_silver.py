from pathlib import Path
import csv
import math
import numpy as np
import pandas as pd
import xarray as xr

BASE = Path(__file__).resolve().parents[1]
CONFIG = BASE / "config" / "era5_land_sites.csv"
BRONZE = BASE / "data" / "bronze" / "era5_land"
SILVER = BASE / "data" / "silver" / "weather"

ALIASES = {
    "air_temperature_k": ["t2m", "2m_temperature"],
    "dewpoint_temperature_k": ["d2m", "2m_dewpoint_temperature"],
    "wind_u_10m_ms": ["u10", "10m_u_component_of_wind"],
    "wind_v_10m_ms": ["v10", "10m_v_component_of_wind"],
    "surface_pressure_pa": ["sp", "surface_pressure"],
    "solar_radiation_j_m2": ["ssrd", "surface_solar_radiation_downwards"],
    "precipitation_m": ["tp", "total_precipitation"],
}

def choose_var(ds, aliases):
    for name in aliases:
        if name in ds.data_vars:
            return name
    return None

def dataframe_from_nc(nc_path):
    ds = xr.open_dataset(nc_path)

    # Point time-series may retain single latitude/longitude dimensions.
    for dim in list(ds.dims):
        if dim != "time" and dim != "valid_time" and ds.sizes.get(dim, 0) == 1:
            ds = ds.squeeze(dim=dim, drop=True)

    time_name = "time" if "time" in ds.coords else ("valid_time" if "valid_time" in ds.coords else None)
    if time_name is None:
        ds.close()
        raise RuntimeError(f"No time coordinate in {nc_path}")

    pieces = {}
    for out_name, aliases in ALIASES.items():
        src = choose_var(ds, aliases)
        if src:
            values = ds[src]
            for dim in list(values.dims):
                if dim != time_name and values.sizes.get(dim, 0) == 1:
                    values = values.squeeze(dim=dim, drop=True)
            pieces[out_name] = pd.Series(values.values, index=pd.to_datetime(ds[time_name].values, utc=True))

    ds.close()

    if not pieces:
        return pd.DataFrame()

    frame = pd.DataFrame(pieces)
    frame.index.name = "timestamp_utc"
    return frame

def main():
    SILVER.mkdir(parents=True, exist_ok=True)

    with CONFIG.open(newline="", encoding="utf-8") as f:
        sites = list(csv.DictReader(f))

    all_sites = []

    for site in sites:
        site_code = site["site_code"]
        nc_files = sorted((BRONZE / site_code / "netcdf").rglob("*.nc"))
        if not nc_files:
            raise FileNotFoundError(f"{site_code}: no Bronze NetCDF files found")

        frames = [dataframe_from_nc(p) for p in nc_files]
        frames = [f for f in frames if not f.empty]
        if not frames:
            raise RuntimeError(f"{site_code}: no usable variables found")

        # Combine variable groups by timestamp.
        df = pd.concat(frames, axis=1)
        df = df.loc[:, ~df.columns.duplicated()]
        df = df.sort_index()

        # Standardized Silver units.
        if "air_temperature_k" in df:
            df["air_temperature_c"] = df["air_temperature_k"] - 273.15
        if "dewpoint_temperature_k" in df:
            df["dewpoint_temperature_c"] = df["dewpoint_temperature_k"] - 273.15
        if "surface_pressure_pa" in df:
            df["surface_pressure_hpa"] = df["surface_pressure_pa"] / 100.0
        if "wind_u_10m_ms" in df and "wind_v_10m_ms" in df:
            df["wind_speed_ms"] = np.sqrt(df["wind_u_10m_ms"]**2 + df["wind_v_10m_ms"]**2)
        if "solar_radiation_j_m2" in df:
            df["solar_radiation_wh_m2"] = df["solar_radiation_j_m2"] / 3600.0
        if "precipitation_m" in df:
            df["precipitation_mm"] = df["precipitation_m"] * 1000.0

        df = df.reset_index()
        df.insert(0, "site_code", site_code)
        df.insert(1, "country_code", site["country_code"])
        df.insert(2, "reference_city", site["reference_city"])
        df.insert(3, "requested_latitude", float(site["latitude"]))
        df.insert(4, "requested_longitude", float(site["longitude"]))
        df["source_dataset_code"] = "ERA5_LAND_TS"
        df["integration_role"] = "EXTERNAL_CONTEXT"

        keep = [
            "site_code",
            "country_code",
            "reference_city",
            "requested_latitude",
            "requested_longitude",
            "timestamp_utc",
            "air_temperature_c",
            "dewpoint_temperature_c",
            "surface_pressure_hpa",
            "wind_u_10m_ms",
            "wind_v_10m_ms",
            "wind_speed_ms",
            "solar_radiation_wh_m2",
            "precipitation_mm",
            "source_dataset_code",
            "integration_role",
        ]
        keep = [c for c in keep if c in df.columns]
        df = df[keep]

        out = SILVER / f"{site_code}_weather_2024_2025.parquet"
        df.to_parquet(out, index=False)
        print(f"{site_code}: {len(df):,} rows -> {out}")
        all_sites.append(df)

    combined = pd.concat(all_sites, ignore_index=True)
    combined_out = SILVER / "enterprise_weather_context_2024_2025.parquet"
    combined.to_parquet(combined_out, index=False)
    print(f"Combined: {len(combined):,} rows -> {combined_out}")

if __name__ == "__main__":
    main()
