# Stage 10A source-model inventory

Stage 10 will create the final curated analytical layer used by the later Power BI stage.

Before creating Gold models, this inventory confirms the exact view names, columns, data types and row counts already present in PostgreSQL.

This prevents the Gold layer from being built against assumed column names or guessed join keys.

## Run

From the repository root:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres `
  -d manufacturing_intelligence `
  -f .\sql\validation\400_inventory_stage10_sources.sql
```

## What to send back

Send the terminal output from:

1. the FOUND/MISSING view list;
2. the column inventory;
3. the row-count notices.

The next Stage 10 step will use that actual schema to build the final Gold analytical models.
