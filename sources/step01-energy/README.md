# Step 01 — steel-industry energy consumption

This package contains the real measured UCI Steel Industry Energy Consumption
dataset (UCI dataset ID 851, DOI `10.24432/C52G8C`, CC BY 4.0). UCI remains the
authoritative publisher and metadata source. The public GitHub URL recorded in
the source manifest is only the retrieval route used after the official UCI
binary endpoint was unavailable in the original execution environment.

The canonical route is:

1. `pipelines/download_steel_energy.py` — retrieve to a temporary sibling,
   verify the governed SHA-256 and CSV contract, then promote atomically; an
   identical existing Bronze file is validated and reused without network
   access, while a differing file is never overwritten.
2. `pipelines/validate_steel_energy.py` — independently recheck SHA-256, exact
   headers, row/column counts, missing cells, and duplicate rows.
3. `pipelines/transform_steel_energy.py` — create the accepted Silver Parquet
   using the existing transformation and assertions.

Run the route through the repository source runner:

```powershell
& .\sources\run_all_sources.ps1 -Step 01
```

The governed source identity and retrieval URL are in
`docs/data_sources/steel_energy_source_manifest.json`. This real external
dataset is separate from the synthetic Velora operational database/BI build.
