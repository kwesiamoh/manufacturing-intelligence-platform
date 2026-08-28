# Stage 11B setup steps in Power BI Desktop

1. Load the five dimensions and six Gold views in Import mode.
2. Open Model view.
3. Create the relationships exactly as listed in `stage11b_relationship_map.md`.
4. Set every relationship to one-to-many and single-direction from dimension to fact.
5. Mark `dim_time` as the Date table using `calendar_date`.
6. Sort `dim_time[month_name]` by `dim_time[month]`.
7. Create a blank Measures table if you want all measures kept in one place.
8. Add the measures from `stage11b_core_measures.dax`.
9. Format:
   - percentage measures as Percentage, usually 1 or 2 decimals
   - EUR measures as Currency
   - kWh and units with thousands separators
10. Hide technical ID columns from report view where they are not intended for users.

## Important

Do not use the stored row-level `oee`, `availability`, `performance`, or intensity columns as SUM fields in visuals.

For report-period values, use the DAX measures supplied here. They recompute the ratios from additive numerators and denominators rather than summing or averaging precomputed ratios.
