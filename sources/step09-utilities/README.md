# Step 9 — Real Industrial Utilities: Steam & Compressed Air

## Domain
Plant/industrial-park utility telemetry for steam and compressed air.

## Source
**Data for an IES from a real industrial park**  
Zenodo record: https://zenodo.org/records/13927178  
DOI: https://doi.org/10.5281/zenodo.13927178  
Published: 2024-10-14, version v2

The Zenodo description states that this dataset contains historical operational data from an
Integrated Energy System (IES) in a real industrial park in China. The published Excel files
contain flow-rate and pressure data for steam and compressed air.

## Files used in this step

| Utility | Published file | Published MD5 |
|---|---|---|
| Compressed air flow | `preair_G.xlsx` | `a70d5d322672df8be938a850c6d79ffb` |
| Compressed air pressure | `preair_P.xlsx` | `2f5aff2892f4d64ea0d1a163aa5c76b4` |
| Steam flow | `steam_G.xlsx` | `8a6ac97f3907f1bc6391bd4c98a73794` |
| Steam pressure | `steam_P.xlsx` | `0b73ec7035a2149543dff6f48bc85b06` |

## Important data-integrity rule
These measurements belong to the real industrial park represented by the Zenodo source.

They MUST NOT be relabelled as measurements from the fictional beverage sites and MUST NOT be
row-level joined to unrelated public datasets unless a genuine common identifier exists.

This source can be used for:
- steam-network pressure/flow analytics;
- compressed-air pressure/flow analytics;
- utility anomaly detection;
- utility load profiling;
- time-series data engineering;
- later calibration of synthetic utility behavior, if explicitly documented.

## License note
The retrieved Zenodo page did not expose a readable license value in the accessible metadata.
Therefore this package deliberately does **not** state a license. Verify the Zenodo record's rights
metadata before redistributing the original files outside the project.

## Storage workflow
1. Download and preserve the four source `.xlsx` files unchanged in `bronze/industrial_park_ies/`.
2. Validate each file's MD5 against the checksums published on Zenodo.
3. Normalize sheet/column names only.
4. Write cleaned tables to Parquet under `silver/industrial_park_ies/`.
5. Do not fill missing values or fabricate timestamps/units without source evidence.

No synthetic records are included in this step.
