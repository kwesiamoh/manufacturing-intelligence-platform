# Production generation configuration

- generator seed: `20260825`
- period: `2024-01-01` through `2025-12-31`
- sites: 6
- production lines: 30
- shifts per day: 3
- scheduled shift duration: 480 minutes
- scheduled breaks excluded from planned production time: 30 minutes
- base planned production time: 450 minutes
- multi-product line campaigns: 2-3 day blocks
- planned changeovers: 25-35 minutes
- all rows: `SYNTHETIC_OPERATIONAL` / `SYNTHETIC_INTEGRATION`

The retained loss-driver columns are the source for later detailed downtime and quality generation, preventing independent inconsistent datasets.
