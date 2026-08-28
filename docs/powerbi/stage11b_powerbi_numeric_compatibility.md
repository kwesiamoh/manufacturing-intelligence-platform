# Stage 11B Power BI compatibility fix

Power BI reported:

`Numeric value does not fit in a System.Decimal.`

The PostgreSQL Gold views expose many calculated columns as unconstrained
`NUMERIC` (`numeric_precision` and `numeric_scale` are NULL). PostgreSQL itself
handles those values correctly, but the .NET provider used by Power BI can
fail while materializing them as `System.Decimal`.

This patch deliberately does **not** rewrite or weaken the validated Gold
business logic.

It creates a thin schema named `gold_bi` with four Power BI-facing wrapper
views. Only unconstrained NUMERIC columns are cast to `double precision`.

## Run

From the repository root:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres `
  -d manufacturing_intelligence `
  -f .\sql\analytics\410_create_powerbi_compat_views.sql
```

## Expected row counts

- shift: 65,790
- line daily: 21,930
- site daily: 4,386
- site executive: 6

## Power BI

After the SQL succeeds:

1. In Power BI, remove the four errored `gold.vw_*` performance queries.
2. Get Data -> PostgreSQL again.
3. Select the matching four `gold_bi.vw_*` views.
4. Keep the two existing Gold DQ views and the five public dimensions.
5. Load.

You may rename the four imported Power BI tables to remove the `gold_bi`
prefix if you want cleaner field names. The underlying database object remains
in `gold_bi`.

The source Gold views remain unchanged and retain exact PostgreSQL numeric
semantics. The cast exists only at the BI presentation boundary.
