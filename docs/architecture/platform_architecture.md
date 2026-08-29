# Platform Architecture

## Purpose

The Manufacturing Performance & Energy Intelligence Platform is a batch-oriented analytical system designed to integrate production, downtime, maintenance, quality, energy, utility, and external benchmark data into a common manufacturing intelligence model.

The demonstrated implementation runs locally using Python, PostgreSQL, PowerShell, SQL, Parquet, and Power BI.

The repository also contains an AWS-ready target architecture and Terraform infrastructure definitions for future cloud deployment.

---

## Current implementation

```mermaid
flowchart LR
    A[Public Data Sources] --> B[Bronze Layer]
    C[Governed Enterprise Inputs] --> B
    B --> D[Python Acquisition and Transformation]
    D --> E[Silver Parquet]
    E --> F[PostgreSQL]
    F --> G[Enterprise Dimensions]
    F --> H[Operational Facts]
    G --> I[Analytics Layer]
    H --> I
    I --> J[Gold Views]
    J --> K[gold_bi Views]
    K --> L[Power BI]
    I --> M[SPC]
    I --> N[Forecasting]
    I --> O[Energy Anomaly Detection]
    I --> P[Reliability Analytics]
    I --> Q[Data Quality]
    I --> R[Compressor Predictive Maintenance]
```

The principal processing path is:

**Source acquisition → Bronze → Silver → PostgreSQL → Analytics → Gold → `gold_bi` → Power BI**

---

## Architecture principles

The platform separates source acquisition, transformation, operational modelling, analytical logic, and reporting.

Bronze preserves acquired source artifacts as closely as practical to their original form.

Silver contains cleaned and transformed Parquet datasets suitable for downstream loading.

PostgreSQL provides the integrated enterprise model, analytical views, data-quality controls, and reporting outputs.

The Gold layer exposes business-facing manufacturing metrics.

The `gold_bi` layer provides stable reporting interfaces for Power BI so that dashboard logic does not depend directly on lower-level analytical implementation details.

---

## Data-source architecture

Public datasets are used for different purposes, including reference data, method development, benchmark analytics, and source-specific transformation exercises.

They are not treated as if they originated from the same manufacturing company.

The integrated enterprise backbone represents the fictional **Velora Beverage Group** and provides a controlled six-site structure for cross-domain analysis.

| Object | Population |
|---|---:|
| Sites | 6 |
| Manufacturing areas | 12 |
| Production lines | 30 |
| Equipment assets | 255 |
| Products | 6 |
| Shifts | 3 |
| Failure reasons | 23 |
| Utilities | 7 |
| Time rows | 8,035 |

Principal operational facts:

| Domain | Rows |
|---|---:|
| Production | 65,790 |
| Downtime | 170,408 |
| Quality | 257,794 |
| Maintenance | 46,670 |
| Energy | 65,790 |
| Line energy detail | 65,790 |
| Site energy detail | 13,158 |

---

## Bronze layer

The Bronze layer stores acquired source artifacts and preserves source provenance.

Depending on the source, acquisition may be automated, authenticated, manually supplied, or obtained through a verified public retrieval route.

Bulk public-source artifacts are generally excluded from the Git release where redistribution, file size, or repository hygiene makes direct inclusion unsuitable.

Source manifests record the expected acquisition route and validation status.

---

## Silver layer

The Silver layer contains transformed datasets in analysis-ready form, primarily using Parquet.

Typical processing includes:

- schema normalization
- type conversion
- identifier standardization
- timestamp normalization
- validation
- source lineage preservation
- derived fields required for downstream modelling

The Silver layer is the main boundary between source-specific transformations and enterprise database loading.

---

## Governed production seed

The accepted production population is the governed upstream boundary for
downstream synthetic regeneration:

```text
data/silver/synthetic_enterprise/production/production_operations_2024_2025.parquet
```

The canonical bootstrap verifies its physical and logical identity before
database mutation. The detailed boundary evidence is documented in the
[canonical build order](../reproducibility/canonical_build_order.md).

---

## PostgreSQL enterprise model

PostgreSQL is the central integration and analytical platform.

Core dimensions include:

- source dataset
- time
- site
- manufacturing area
- line
- equipment
- product
- shift
- failure reason
- utility

Operational facts include:

- production
- downtime
- quality
- maintenance
- energy
- line energy detail
- site energy detail

Shared dimensions allow different operational domains to be analysed consistently across site, line, product, shift, and time.

---

## Analytical layer

The analytical layer covers manufacturing performance, Laney p′ SPC,
source-qualified reliability, data quality, forecasting, contextual energy
anomalies, and compressor condition monitoring. Real MetroPT telemetry remains
source-qualified external data; its governed enterprise adaptation maps only to
an existing compressed-air utility asset and publishes warning-event and KPI
views in Gold without changing maintenance facts or reliability KPIs. That
adaptation participates in the canonical DQ layer through completeness,
uniqueness, enterprise-mapping, lineage, and cadence checks. The
hydraulic-condition workflow remains a separate benchmark. Method definitions and
limitations are maintained in the
[analytics methodology](../methodology/analytics_methodology_and_limitations.md).

---

## Gold reporting layer

| Gold object | Rows |
|---|---:|
| Shift manufacturing performance | 65,790 |
| Line daily performance | 21,930 |
| Site daily performance | 4,386 |
| Site executive summary | 6 |

Gold views provide the principal business-facing operational metrics consumed by reporting.

---

## Power BI compatibility layer

Power BI consumes views exposed through the `gold_bi` schema.

This gives the dashboard a stable reporting contract while separating it from lower-level SQL implementation details.

The compatibility layer covers:

- production
- loss analysis
- energy and utilities
- data quality
- reliability
- production forecasts
- energy forecasts
- energy anomalies

---

## Power BI reporting

The six-page import-mode dashboard consumes the stable `gold_bi` contract and
uses batch refresh. Page purposes, relationships, measures, and refresh rules
are documented in the [Power BI report guide](../powerbi/final_powerbi_presentation.md).

---

## Reproducibility architecture

The database can be reconstructed through:

```text
pipelines/postgres/bootstrap_database.ps1
```

```mermaid
flowchart TD
    A[Governed Input Preflight] --> B[DDL and Migrations]
    B --> C[Dimension Loads]
    C --> D[Operational Fact Loads]
    D --> E[Analytics]
    E --> F[Data Quality]
    F --> G[Gold Layer]
    G --> H[Reliability]
    H --> I[Advanced Analytics Bridge]
    I --> J[Mandatory Validations]
```

Mandatory SQL execution uses PostgreSQL fail-fast behaviour:

```text
ON_ERROR_STOP=1
```

The accepted disposable clean-build proof passed all 19 mandatory validations.

The proof database itself is not distributed through GitHub. Reproducibility is demonstrated through governed inputs, scripts, manifests, hashes, validation logic, and captured build evidence.

---

## AWS-ready target architecture

```mermaid
flowchart LR
    A[Source Systems / Public Sources] --> B[Amazon S3 Bronze]
    B --> C[AWS Glue / Managed Processing]
    C --> D[Amazon S3 Silver]
    D --> E[Amazon RDS for PostgreSQL]
    E --> F[Analytics and Gold]
    F --> G[BI Consumption]
    H[AWS Secrets Manager] --> C
    H --> E
    I[Amazon CloudWatch] --> C
    I --> E
    J[IAM] --> B
    J --> C
    J --> E
    K[Terraform] --> B
    K --> C
    K --> E
    K --> H
    K --> I
```

| Current implementation | AWS target |
|---|---|
| Local Bronze storage | Amazon S3 |
| Local Silver Parquet | Amazon S3 |
| Python processing | AWS Glue or managed compute |
| PostgreSQL | Amazon RDS for PostgreSQL |
| Batch scheduling | EventBridge / Step Functions / managed jobs |
| Local credentials | AWS Secrets Manager |
| Local monitoring | Amazon CloudWatch |
| Local access configuration | AWS IAM |
| Infrastructure definitions | Terraform |

The cloud architecture is a target deployment design. The portfolio implementation demonstrated in the repository runs locally.

---

## Why the architecture is batch-oriented

The demonstrated use cases do not require sub-second or real-time processing.

Production performance, reliability trends, energy analysis, data-quality checks, forecasting, and executive reporting can be refreshed on scheduled batch cycles.

A future industrial deployment could increase refresh frequency where source-system availability and business requirements justify it.

---

## Security and validation controls

Credentials remain outside source control, local artifacts are excluded by the
release boundary, and AWS mappings use Secrets Manager and IAM. Governed hashes,
database constraints, lineage, DQ rules, fail-fast execution, and mandatory
validators protect the build. See [cybersecurity controls](../security/cybersecurity_controls.md),
the [threat model](../security/threat_model.md), and the
[clean-build proof](../reproducibility/clean_build_proof.md).

---

## Architecture limitations

The current implementation is a portfolio-scale analytical platform rather than a production manufacturing execution system.

It does not implement:

- real-time PLC or SCADA ingestion
- streaming event processing
- closed-loop process control
- real-time alarm handling
- production-grade high availability
- enterprise identity federation
- live AWS hosting

Those capabilities would require additional operational infrastructure beyond the demonstrated portfolio scope.

---

## Related documentation

- [Canonical build order](../reproducibility/canonical_build_order.md)
- [Clean-build proof](../reproducibility/clean_build_proof.md)
- [Third-party data policy](../governance/third_party_data_redistribution.md)
