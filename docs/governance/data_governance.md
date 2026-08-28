# Data Governance Framework

## Purpose

The platform integrates public real-world datasets, synthetic enterprise
integration data, reference data, derived analytics, and reporting outputs.

Governance must therefore preserve:

- provenance;
- reproducibility;
- separation of real and synthetic sources;
- traceability from Bronze through Silver and Gold;
- clear ownership of data-quality and analytical outputs.

## Data zones

### Bronze

Bronze is immutable source capture.

Rules:

- preserve original file contents;
- record source dataset, publisher, access date, licence/reference information,
  and checksum where available;
- do not overwrite source files;
- do not apply business transformations in Bronze.

### Silver

Silver contains validated and standardized analytical source tables.

Rules:

- normalize data types and schemas;
- retain source identifiers;
- document transformations;
- record validation results;
- preserve a direct lineage path back to Bronze.

### Gold

Gold contains business-ready analytical views and reporting models.

Rules:

- metrics must have documented definitions;
- calculations must reference known source fields;
- synthetic and real-source metrics must not be blended in ways that imply a
  shared physical plant;
- Power BI-facing compatibility views may cast data types but must not silently
  alter business meaning.

## Provenance classes

### Real external data

Examples include MetroPT telemetry and the hydraulic condition-monitoring
benchmark.

These may be described as real source data, but not as data from Velora
Beverage Group or from the synthetic enterprise.

### Synthetic enterprise integration

`SYNTHETIC_ENTERPRISE` is the fictional six-site beverage integration layer.

It exists to demonstrate:

- enterprise modelling;
- cross-domain integration;
- KPI pipelines;
- Power BI reporting;
- operational analytics.

Results from this source must be labelled as synthetic workflow demonstration
where the distinction matters.

### Benchmark/reference data

External benchmark datasets such as FMUCD must remain clearly separated from
the fictional enterprise operational history.

## Data ownership model

| Domain | Logical owner | Stewardship responsibility |
|---|---|---|
| Production | Manufacturing Operations | production completeness, line/shift mapping |
| Quality | Quality Engineering | defect definitions, quality-rule ownership |
| Energy | Energy / Utilities Management | utility definitions, intensity metrics |
| Maintenance | Maintenance / Reliability | equipment hierarchy, failure taxonomy |
| Enterprise master data | Data Engineering | keys, dimensions, integration mappings |
| Reporting | BI / Analytics | semantic consistency, KPI definitions |
| Data quality | Data Engineering + domain owner | rule design, exception review |

These are project role definitions, not claims about an actual organization.

## Data-quality governance

Each DQ rule should contain:

- domain;
- rule ID;
- rule description;
- severity;
- evaluated rows;
- failed rows;
- status;
- owner;
- remediation guidance where relevant.

Current reporting distinguishes PASS, WARN, and FAIL. WARN findings must not be
reported as passes.

## Lineage

Minimum lineage chain:

`source dataset -> Bronze -> Silver -> PostgreSQL fact/dimension -> Gold view -> Power BI`

Advanced-analytics lineage should additionally record:

`Gold/Silver source -> feature engineering -> model -> evaluation output`

## Metric governance

Metric definitions must distinguish:

- measured value;
- calculated KPI;
- proxy;
- synthetic demonstration result;
- benchmark result.

Examples:

- operating-hours MTBF is explicitly a **proxy** because line operating hours
  are used rather than direct asset runtime;
- hydraulic condition classification is not remaining-useful-life prediction;
- MetroPT anomaly detection is not claimed as a two-hour predictive-maintenance
  warning model.

## Change control

Changes to:

- source mappings;
- dimension keys;
- KPI formulas;
- DQ thresholds;
- model evaluation design;
- provenance wording

should be documented in version control with a clear commit message and, for
material changes, an architecture/analytics decision note.
