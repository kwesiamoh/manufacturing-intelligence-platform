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

Controls:

- preserve original file contents;
- record source dataset, publisher, access date, licence/reference information,
  and checksum where available;
- source files remain immutable;
- business transformations begin in Silver.

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

Controls:

- every metric has a documented definition;
- calculations reference known source fields;
- synthetic and real-source metrics remain distinct wherever blending could
  imply a shared physical plant;
- Power BI-facing compatibility views may cast data types while preserving
  business meaning.

## Provenance classes

### Real external data

Examples include MetroPT telemetry and the hydraulic condition-monitoring
benchmark.

These retain real-source status while remaining outside Velora Beverage Group
and the synthetic enterprise.

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
| Telemetry / PdM | Maintenance / Reliability + Data Engineering | telemetry completeness, equipment mapping, lineage, cadence exceptions |
| Enterprise master data | Data Engineering | keys, dimensions, integration mappings |
| Reporting | BI / Analytics | semantic consistency, KPI definitions |
| Data quality | Data Engineering + domain owner | rule design, exception review |

These roles define repository governance responsibilities; they do not assert
the structure of an actual organization.

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

Current reporting distinguishes PASS, WARN, and FAIL. A WARN is a separate,
nonfatal outcome and never counts as a pass.

The governed MetroPT-informed enterprise telemetry is subject to the canonical
DQ framework. Its checks cover structural integrity, required fields,
enterprise mapping, lineage, and source-supported cadence. Untouched MetroPT
records remain external real data, and physical faults or analytical warning
states are not classified as data defects merely because they are abnormal.

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

- operating-hours MTBF is explicitly a **proxy** because direct asset runtime
  is unavailable and line operating hours supply the exposure basis;
- hydraulic condition analysis addresses state classification only;
  remaining-useful-life prediction lies outside its scope;
- real MetroPT evaluation is reported separately from the MetroPT-informed
  synthetic enterprise degradation scenario;
- synthetic precursor performance is reported solely as controlled scenario
  behavior, without a measured MetroPT or Velora performance claim.

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
