# Manufacturing Intelligence Platform

## Project scope

* Build an **enterprise digital manufacturing performance and energy intelligence platform** for a fictional multinational manufacturer.

* Model approximately **6 manufacturing sites and 30 production lines**.

* Integrate real/public industrial datasets covering:

  * production
  * downtime
  * machine and process telemetry
  * quality
  * maintenance
  * electricity
  * natural gas
  * steam
  * compressed air
  * water
  * emissions
  * energy prices and costs
  * weather context

* Use **real industrial data wherever possible** and generate synthetic data only where required to fill integration gaps.

* Implement a **Bronze / Silver / Gold** data architecture.

* Store large datasets primarily in **Parquet**, with PostgreSQL used for structured analytics and business-layer tables.

* Build a canonical manufacturing hierarchy:

  * Company
  * Site
  * Area
  * Production line
  * Equipment
  * Sensor / tag

* Calculate manufacturing KPIs including:

  * OEE
  * Availability
  * Performance
  * Quality
  * throughput
  * production attainment
  * capacity utilization
  * scrap rate
  * first-pass yield
  * changeover duration
  * MTBF
  * MTTR
  * energy intensity

* Build **production-loss accounting** for:

  * planned downtime
  * unplanned downtime
  * equipment failures
  * reduced speed
  * micro-stops
  * changeovers
  * material shortages
  * quality losses

* Translate manufacturing and energy losses into **financial impact and improvement opportunities**.

* Build **energy and utility analytics** covering:

  * consumption
  * energy intensity
  * utility intensity
  * idle energy
  * abnormal consumption
  * energy cost
  * benchmarking
  * potential savings

* Implement **data-quality monitoring** for:

  * missing values
  * duplicate records
  * invalid timestamps
  * sensor gaps
  * impossible measurements
  * spikes
  * frozen sensors
  * inconsistent records

* Add selected advanced analytics:

  * statistical process analysis
  * anomaly detection
  * energy anomaly detection
  * reliability analysis
  * production forecasting

* Support benchmarking across:

  * sites
  * production lines
  * shifts
  * products
  * operating periods
  * historical baselines
  * best demonstrated performance

* Define an **AWS-ready target deployment architecture** for future production
  deployment, using selected services such as:

  * Amazon S3
  * AWS Glue
  * Glue Data Catalog
  * Amazon Athena
  * Amazon RDS / PostgreSQL
  * AWS Lambda
  * Kinesis or IoT Core where required
  * CloudWatch
  * Secrets Manager

* Build the final reporting layer in **Power BI** with report areas for:

  * Corporate Manufacturing Overview
  * Site Performance
  * Production Loss Analysis
  * Energy Intelligence
  * Reliability & Maintenance
  * Data Quality

* Include essential enterprise documentation:

  * architecture
  * requirements
  * data model
  * data dictionary
  * KPI definitions
  * source-to-target mappings
  * data-quality rules
  * governance
  * cybersecurity considerations
  * project-management documentation
  * digital-transformation roadmap
  * business case

* Finish with a polished **GitHub portfolio repository, technical documentation, architecture diagrams, dashboards, analytics outputs, and business case**.

* Keep the project controlled and avoid unnecessary scope expansion. The objective is a **complete end-to-end manufacturing intelligence portfolio project**, not a full commercial MES, ERP, CMMS, SCADA, or industrial cybersecurity platform.

---

## Original target folder tree

The following is the original planned layout, not a current filesystem
inventory. Stage 16A.9 defines the actual public release boundary in
`docs/governance/repository_release_policy.md`; the final root README remains a
Stage 16B deliverable.

```text
manufacturing-intelligence-platform/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── docs/
│   ├── architecture/
│   ├── requirements/
│   ├── data_dictionary/
│   ├── kpi_definitions/
│   ├── source_to_target/
│   ├── governance/
│   ├── cybersecurity/
│   ├── project_management/
│   └── business_case/
│
├── sources/
│   ├── step01-energy/
│   ├── step02-telemetry/
│   ├── step03-quality/
│   ├── step04-reliability/
│   ├── step05-production-downtime/
│   ├── step06-maintenance/
│   ├── step07-production-orders/
│   ├── step08-energy-cost/
│   ├── step09-utilities/
│   ├── step10-water/
│   ├── step11-fuels/
│   ├── step12-emissions/
│   ├── step13-weather/
│   ├── step14-eu-energy-prices/
│   └── step15-source-inventory/
│
├── data/
│   ├── bronze/
│   │   ├── energy/
│   │   ├── telemetry/
│   │   ├── quality/
│   │   ├── reliability/
│   │   ├── production/
│   │   ├── downtime/
│   │   ├── maintenance/
│   │   ├── production_orders/
│   │   ├── utilities/
│   │   ├── water/
│   │   ├── fuels/
│   │   ├── emissions/
│   │   ├── weather/
│   │   └── energy_prices/
│   │
│   ├── silver/
│   │   ├── energy/
│   │   ├── telemetry/
│   │   ├── quality/
│   │   ├── reliability/
│   │   ├── production/
│   │   ├── downtime/
│   │   ├── maintenance/
│   │   ├── production_orders/
│   │   ├── utilities/
│   │   ├── water/
│   │   ├── fuels/
│   │   ├── emissions/
│   │   ├── weather/
│   │   └── energy_prices/
│   │
│   └── gold/
│       ├── manufacturing_performance/
│       ├── production_loss/
│       ├── energy_intelligence/
│       ├── reliability/
│       ├── maintenance/
│       ├── financial_opportunity/
│       ├── benchmarking/
│       └── data_quality/
│
├── data_model/
│   ├── dimensions/
│   ├── facts/
│   ├── source_mapping/
│   └── erd/
│
├── pipelines/
│   ├── bronze/
│   ├── silver/
│   ├── gold/
│   └── orchestration/
│
├── sql/
│   ├── ddl/
│   ├── dimensions/
│   ├── facts/
│   ├── transformations/
│   ├── marts/
│   └── analytics/
│
├── analytics/
│   ├── production/
│   ├── oee/
│   ├── production_loss/
│   ├── energy/
│   ├── reliability/
│   ├── anomaly_detection/
│   ├── forecasting/
│   └── benchmarking/
│
├── data_quality/
│   ├── rules/
│   ├── validation/
│   └── reports/
│
├── dashboards/
│   ├── powerbi/
│   └── documentation/
│
├── infrastructure/
│   ├── aws/
│   └── terraform/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── data_quality/
│
└── docker/
```

## Current project stage

```text
Stage 1 — Real-data acquisition and provenance       COMPLETE
Stage 2 — Enterprise data model and source mapping   COMPLETE
Stage 3 — Synthetic integration for remaining gaps   COMPLETE
Stage 4 — Local Python + PostgreSQL pipelines        COMPLETE
Stage 5 — Production / OEE / loss analytics          COMPLETE
Stage 6 — Energy and utility analytics               COMPLETE
Stage 7 — Data-quality framework                     COMPLETE
Stage 8 — AWS-ready target architecture             COMPLETE
Stage 9 — Automated ingestion / orchestration        COMPLETE
Stage 10 — Final Silver / Gold business models       COMPLETE
Stage 11 — Power BI semantic model and dashboards    COMPLETE
Stage 12 — Advanced analytics                        COMPLETE
Stage 13 — Maintenance / reliability analytics       COMPLETE
Stage 14 — Governance / cybersecurity / PM docs      COMPLETE
Stage 15 — Digital roadmap and business case         COMPLETE
Stage 16 — Hardening and GitHub release preparation   IN PROGRESS (through 16A.9)
```
