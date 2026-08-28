# Stage 3E — Detailed Downtime Events

## Purpose
Generate detailed downtime events from the Stage 3D shift-level production source.

## Core rule
The Stage 3D production records remain the source of truth.

For every production shift:
- the sum of generated planned-changeover event minutes must equal `planned_changeover_min`;
- the sum of generated unplanned-stop event minutes must equal `unplanned_downtime_min`.

The generator validates both relationships before writing output.

## Event scope
Only beverage-line assets already created in Stage 3C are used.

The event taxonomy is intentionally small:
- mechanical
- electrical
- process
- material
- quality
- changeover

No new equipment classes or operational domains are introduced.

## Outputs
Bronze:
`data/bronze/synthetic_enterprise/downtime/downtime_events_2024_2025.csv`

Silver:
`data/silver/synthetic_enterprise/downtime/downtime_events_2024_2025.parquet`

## Data classification
All generated events are:
- `SYNTHETIC_OPERATIONAL`
- `SYNTHETIC_INTEGRATION`

They are not claimed to be real records from the public beverage dataset.
