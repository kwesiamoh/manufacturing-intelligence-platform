# Final Power BI Presentation and Screenshot Packaging

## Purpose

This document defines the final presentation state for the Power BI component of the Manufacturing Performance & Energy Intelligence Platform.

The final screenshots should be captured from the validated Stage 16A.10 proof database:

```text
manufacturing_intelligence_stage16a10_20260828_proof1
```

This database passed all 19 mandatory validations and represents the accepted portfolio state.

---

## Final dashboard pages

The Power BI report contains six pages:

1. Executive Overview
2. Production Performance
3. Loss & Opportunity
4. Energy & Utilities
5. Data Quality
6. Reliability & Maintenance

All final screenshots should be captured after a successful refresh against the proof database.

---

## Screenshot folder

Store the final screenshots in:

```text
powerbi/screenshots/
```

Use the following filenames:

```text
01_executive_overview.png
02_production_performance.png
03_loss_opportunity.png
04_energy_utilities.png
05_data_quality.png
06_reliability_maintenance.png
```

These filenames match the image links already used in the root `README.md`.

---

## Final presentation checks

Before capturing the screenshots:

- refresh the full Power BI model against the proof database
- click a blank area of each report page so no visual remains selected
- hide visual-header icons where possible
- confirm no edit-mode selection borders are visible
- confirm slicers show the intended default state
- use consistent zoom across all six pages
- ensure no Power BI warning banner or refresh error is visible
- capture the complete report canvas without unnecessary application chrome where practical

---

## Executive Overview

Verify the following:

- Enterprise OEE displays correctly
- production volume is populated
- downtime is populated
- technical opportunity displays approximately **€573.91M**
- site comparison remains consistent with the accepted six-site model
- electricity intensity reflects the accepted site-level total electricity basis
- no visual is selected when the screenshot is taken

Recommended terminology:

```text
Electricity Intensity, kWh/1,000 units
```

if the current label can be changed without disturbing the layout.

---

## Production Performance

Verify:

- production performance measures are populated
- site and line comparisons work
- production forecast is visible
- forecast actual and predicted series are present
- forecast MAPE displays approximately **0.72%**
- forecast MAE displays approximately **28,869 units**
- only intended slicers interact with the forecast visual

The forecast should be presented as a rolling one-day-ahead evaluation over the final 60-day holdout, not as a recursive 60-day forecast.

---

## Loss & Opportunity

Verify:

- downtime and loss visuals are populated
- Pareto structure is visible
- site/line opportunity visuals reconcile with the accepted Gold layer
- technical opportunity is presented as model-derived
- no label suggests that the opportunity is realized savings

Accepted enterprise values:

```text
Two-year technical opportunity: €573,908,429.76
Simple annualized equivalent:   €286,954,214.88/year
```

---

## Energy & Utilities

This page is particularly important because it confirms the Stage 16A.9A compressed-air amendment.

Verify:

- total electricity displays approximately **132.84 GWh**
- electricity intensity displays approximately **7.58 kWh/1,000 units**
- compressed air displays approximately **344.04M Nm³**
- Energy Drink Can Line compressed air is nonblank
- CAN compressed-air total is approximately **12.81M Nm³**
- PET compressed-air contribution remains populated
- production/energy forecast visual is populated
- energy forecast MAPE displays approximately **0.51%**
- energy forecast MAE displays approximately **154 kWh**
- high-energy anomaly visual is populated

Preferred units:

- enterprise/site/line total electricity: **GWh**
- idle electricity: **MWh**
- shift/anomaly/forecast electricity: **kWh**
- compressed air: **Nm³**

Recommended label:

```text
Total Electricity, GWh
```

rather than a generic `Total Energy` label if the measure is electricity-specific.

---

## Data Quality

The canonical Stage 16A.10 DQ result is:

| Status | Rules |
|---|---:|
| PASS | 24 |
| WARN | 0 |
| FAIL | 0 |

Verify:

- overall DQ score displays **100.00%**
- warning-rule card displays `0`, not blank or `--`
- failed-rule card displays `0`
- failed-row card displays an integer `0`
- rule-status and domain visuals are populated
- the page does not imply that a 100% score means the datasets are universally error-free

The intended interpretation is:

> All 24 active canonical data-quality rules passed in the accepted reproducibility build.

Optional external benchmark DQ rules are not part of this canonical score.

---

## Reliability & Maintenance

Verify the accepted KPI values:

| KPI | Accepted value |
|---|---:|
| Corrective failures | 46,670 |
| Corrective downtime | 14,856.7 h |
| Weighted MTTR | 0.28 h |
| Aggregate operating-hours MTBF proxy | 9.74 h |
| Failures per 1,000 operating h | 102.65 |
| Corrective downtime ratio | 3.27% |

Also verify:

- site reliability burden is populated
- equipment-type reliability trend is populated
- monthly reliability trend is populated
- the page does not confuse the 9.74 h aggregate Power BI MTBF proxy with the separate equipment-level MTBF proxy used elsewhere in the analytical layer

---

## Final screenshot links

The root `README.md` expects these relative paths:

```markdown
![Executive Overview](powerbi/screenshots/01_executive_overview.png)

![Production Performance](powerbi/screenshots/02_production_performance.png)

![Loss & Opportunity](powerbi/screenshots/03_loss_opportunity.png)

![Energy & Utilities](powerbi/screenshots/04_energy_utilities.png)

![Data Quality](powerbi/screenshots/05_data_quality.png)

![Reliability & Maintenance](powerbi/screenshots/06_reliability_maintenance.png)
```

Do not use absolute local Windows paths in the README.

---

## PBIX source for final screenshots

The final portfolio screenshots should use the proof database because it contains the accepted post-hardening state, including:

- validated canonical DQ scope
- Stage 16A.9A compressed-air amendment
- validated reliability lineage
- accepted advanced-analytics bridge
- final Gold and `gold_bi` views

The older working `manufacturing_intelligence` database can be rebuilt later to match the validated state.

Until that rebuild is complete, it should not be used as the source for final screenshots.

---

## Final PBIX release state

Before packaging the PBIX for GitHub:

- save it after the final proof-database refresh
- confirm no broken source references
- confirm all six pages render correctly
- confirm screenshot values match the report
- remove temporary test visuals or temporary display measures that are no longer required
- retain only the accepted final pages and measures
- do not embed local credentials in the PBIX

The PBIX may remain connected to the proof database during final screenshot capture. The repository documentation should make clear that GitHub users reconstruct their own PostgreSQL database rather than receiving this local database instance.

---

## Portfolio screenshot selection

All six screenshots should be retained in `powerbi/screenshots/`.

For the root README, the strongest pages for first-glance portfolio review are:

1. Executive Overview
2. Production Performance
3. Energy & Utilities
4. Reliability & Maintenance

The remaining two pages should still be retained and linked in the repository because they demonstrate loss analysis and data-quality governance.

---

## Completion criteria

Stage 16B.5 is complete when:

- the PBIX has been refreshed against the proof database
- all six pages have been visually verified
- DQ warning and fail cards display numeric zeros where appropriate
- electricity and compressed-air units are consistent
- no screenshot contains selected-visual borders or edit artifacts
- all six final PNG files are saved under `powerbi/screenshots/`
- the README image links render correctly on GitHub
- the PBIX is saved in its final accepted presentation state
