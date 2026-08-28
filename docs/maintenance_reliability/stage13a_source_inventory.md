# Stage 13A — Maintenance & Reliability Source Inventory

Stage 13 begins with a read-only inventory before any MTBF, MTTR, availability,
failure-frequency, or reliability calculations are created.

## Why this inventory is needed

The project contains more than one maintenance/reliability-related source:

- enterprise maintenance/downtime facts;
- Step 04 reliability Silver data;
- cycle-based sensor telemetry.

These sources must not be silently mixed. Stage 13A confirms which objects
represent real external reliability data and which belong to the synthetic
enterprise integration layer.

## Intended Stage 13 sequence

### 13A — Source inventory and provenance
Confirm exact maintenance/reliability tables, Silver files, grains, timestamps,
equipment identifiers, failure fields, and provenance.

### 13B — Reliability KPI layer
Where supported by the event data:
- failure count
- downtime hours
- MTBF
- MTTR
- inherent/operational availability proxy
- maintenance burden

### 13C — Failure mode / downtime analysis
Failure-mode and equipment ranking, Pareto, recurrence, and downtime burden.

### 13D — Reliability trends
Time-based reliability trends and equipment comparison.

### 13E — Optional condition analytics
Only if the Step 04 cycle telemetry has labels or event alignment sufficient to
support a defensible condition indicator. No model will be added merely for
portfolio volume.

## Run

Database inventory:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres `
  -d manufacturing_intelligence `
  -f .\sql\validation\700_inventory_stage13_reliability_sources.sql
```

File inventory:

```powershell
python .\scripts\inventory_stage13_reliability_files.py
```

Both are read-only.
