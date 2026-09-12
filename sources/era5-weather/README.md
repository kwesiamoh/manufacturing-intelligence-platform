# ERA5-Land weather context

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

Weather joins the fictional enterprise layer only through governed `site_code`
and timestamp relationships. ERA5-Land remains external gridded context; the
join creates no shared-site provenance with other public industrial datasets
and never represents an on-site weather station.

## Authenticated acquisition

`scripts/download_era5_land.py` uses the authenticated CDS API. A configured
CDS account (`.cdsapirc` or the supported CDS environment variables) and any
required external terms acceptance are prerequisites. Existing immutable site
ZIPs are checksummed and reused. NetCDF files are derived extraction artifacts:
each extraction is staged and replaces the site's `netcdf/` directory as one
unit so stale fragments cannot be mixed across reruns.
