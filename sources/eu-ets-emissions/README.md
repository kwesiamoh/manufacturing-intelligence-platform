# Real industrial greenhouse-gas and CO2 emissions data

## Domain
Verified greenhouse-gas emissions and EU ETS compliance data for real European industrial installations.

## Authoritative source
European Environment Agency (EEA) — European Union Emissions Trading System (EU ETS) data from the Union Registry.

Latest dataset page checked: 2026-08-24
Dataset release: July 2026
Published: 2026-07-08
Temporal coverage: 2005-2025
Underlying Union Registry extraction date: 2026-07-01

Official datahub:
https://www.eea.europa.eu/en/datahub/datahubitem-view/98f04097-26de-4fca-86c4-63834818c0c0/folder_contents

Official viewer:
https://www.eea.europa.eu/en/analysis/maps-and-charts/emissions-trading-viewer-1-dashboards

## Source characteristics
The EU ETS dataset contains verified emissions and allowance/compliance information from the European Commission Union Registry. The EEA viewer reports coverage of more than 16,000 stationary installations, as well as aviation and maritime operators.

The stationary-installation records serve as a real European industrial-emissions benchmark.

## Important integration rule
These records describe real EU ETS installations and retain that identity.
Fictional beverage-site labels and row-level joins to unrelated public datasets
would require a genuine common identifier that is absent here.

Valid uses include:
- industrial CO2/GHG benchmarking;
- sector and country comparisons;
- verified-emissions trend analysis;
- calibration of emissions-intensity scenarios where clearly documented;
- corporate sustainability / carbon-cost Gold marts.

Invalid uses include:
- assigning verified emissions to fictional DE01/NL01/etc.;
- inferring hourly stack emissions from annual verified emissions;
- claiming product-level carbon intensity without production denominators;
- fabricating allowance prices or carbon costs.

No synthetic rows are included in this package.

## Acquisition and validation state

Acquisition is manual. `scripts/download_eea_eu_ets.py` prints the official EEA
Datahub instructions and exits with status 2 (`MANUAL_INPUT_REQUIRED`); it does
not download a file or claim automated success. Place the selected official
release unchanged under `bronze/eea_eu_ets/`, then run
`scripts/validate_bronze.py` and `scripts/bronze_to_silver.py`.

The validator fails for a missing, empty, or invalid required XLSX container.
It emits a warning—without weakening those failures—that release-specific
worksheet semantics require source-aware review. The source workbook is not
redistributed. Users must obtain the official file
under the provider's terms; the public package retains manual acquisition,
validation, and transformation instructions.
