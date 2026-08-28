# Stage 16A.10 disposable clean-build proof

## Result

`PASS_AFTER_FAIL_FAST_RESUME` against disposable database
`manufacturing_intelligence_stage16a10_20260828_proof1` on PostgreSQL
`18.6`.

Build-log interval: `2026-08-28 06:25:06.725329+02:00` to
`2026-08-28 12:38:57.183119+02:00`. Evidence was
captured at `2026-08-28 12:50:33.186525+02:00`.

The canonical build completed through all 19
mandatory fail-fast validations. The initial runner correctly stopped when SQL
623 was canceled; execution resumed from that first incomplete step without
recreating the database or rerunning completed loaders.

## Canonical populations

- Production: 65,790
- Downtime: 170,408
- Quality: 257,794
- Maintenance: 46,670
- Energy: 65,790
- Gold shift / line-day / site-day / site summary:
  65,790 /
  21,930 /
  4,386 /
  6

## DQ and utility amendment

- DQ: 24 PASS,
  0 WARN,
  0 FAIL.
- CAN: 6,579 rows, zero positive-production nulls,
  intensity 5 Nm3/1,000 cans,
  total 12,805,152.250 Nm3.
- PET total: 331,230,504.302 Nm3.
- Enterprise total: 344,035,656.552 Nm3.
- Electricity and cost totals/order matched the retained Stage 3H snapshot and
  mandatory Stage 6 gates.

## Reliability and advanced bridge

- Failures: 46,670; downtime:
  14,856.652017 h; repair:
  13,207.527188 h; MTTR:
  0.282998226 h.
- Corrected trend: 720 rows across
  24 months; SQL 740 was not run.
- Forecast: 720 rows; energy anomaly:
  32,850 rows; reliability bridge:
  720 rows.
- Loader audit hashes matched the accepted Stage 12D/12E snapshots.

## SQL 623 finding

The interrupted/original SQL 623 repeatedly expanded the nested accepted Laney
p-prime view and its section-4 aggregation ran for more than 40 minutes. The
validation now materializes the unchanged accepted view once into a session-local
temporary table. Its optional ordinary-p-chart comparison is skipped when the
noncanonical SQL 620 view is absent. All mandatory Laney calculations and gates
are unchanged and passed.

## Power BI and safety

All required operational and advanced `gold_bi` views passed SQL validation.
The PBIX was not modified or refreshed. Pointing it at
`manufacturing_intelligence_stage16a10_20260828_proof1` and visually checking forecasts, anomaly,
reliability, compressed air, and GWh/MWh presentation remains manual.

The disposable database is retained for that check. The existing
`manufacturing_intelligence` database was never the build or resume target.
