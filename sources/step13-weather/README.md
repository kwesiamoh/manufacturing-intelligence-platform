# Step 13 — ERA5-Land Weather Context

Purpose: add external weather context for the six fictional enterprise sites without creating false relationships with the real industrial source datasets.

## Period
2024-01-01 through 2025-12-31, hourly.

## Variables
- 2 m air temperature
- 2 m dewpoint temperature
- 10 m U wind component
- 10 m V wind component
- surface pressure
- surface solar radiation downwards
- total precipitation

## Silver standard units
- air temperature: °C
- dewpoint temperature: °C
- surface pressure: hPa
- wind components and wind speed: m/s
- hourly solar radiation: Wh/m²
- hourly precipitation: mm

The source-native NetCDF files remain unchanged in Bronze. The ERA5-Land time-series service provides de-accumulated hourly precipitation and solar-radiation values before the Silver unit conversions.

## Integration rule
`integration_role = EXTERNAL_CONTEXT`

Weather may later be joined to the fictional enterprise layer through valid `site_code` and timestamp relationships. It must not be used to imply that unrelated public industrial datasets came from these fictional sites.

## Authenticated acquisition

`scripts/download_era5_land.py` uses the authenticated CDS API. A configured
CDS account (`.cdsapirc` or the supported CDS environment variables) and any
required external terms acceptance are prerequisites. Existing immutable site
ZIPs are checksummed and reused. NetCDF files are derived extraction artifacts:
each extraction is staged and replaces the site's `netcdf/` directory as one
unit so stale fragments cannot be mixed across reruns.
