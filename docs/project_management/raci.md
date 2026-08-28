# Project RACI

The roles below are conceptual enterprise roles used to demonstrate governance.

| Activity | Data Engineering | Manufacturing Ops | Quality | Energy | Maintenance | BI/Analytics | Security |
|---|---|---|---|---|---|---|---|
| Source ingestion | R/A | C | C | C | C | I | I |
| Master-data mapping | R | C | C | C | C | I | I |
| Production KPI definitions | C | A/R | I | I | I | C | I |
| Quality rules | C | I | A/R | I | I | C | I |
| Energy KPI definitions | C | I | I | A/R | I | C | I |
| Reliability definitions | C | I | I | I | A/R | C | I |
| Gold model | A/R | C | C | C | C | R | I |
| Power BI semantic model | C | C | C | C | C | A/R | I |
| Access controls | C | I | I | I | I | C | A/R |
| DQ issue remediation | R | R | R | R | R | C | I |
| Provenance governance | A/R | C | C | C | C | C | I |

Legend:
- R = Responsible
- A = Accountable
- C = Consulted
- I = Informed
