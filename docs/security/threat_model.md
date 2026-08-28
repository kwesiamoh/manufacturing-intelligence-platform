# Lightweight Threat Model

## Assets

Primary assets:

- source datasets;
- Bronze/Silver/Gold files;
- PostgreSQL database;
- transformation code;
- analytical models;
- Power BI semantic model;
- credentials and connection secrets.

## Threats and mitigations

| Threat | Example | Control |
|---|---|---|
| Credential leakage | password committed to Git | prompts/env vars, secret scanning |
| Unauthorized DB access | broad database credentials | RBAC, network restriction, TLS |
| Data tampering | Bronze file overwritten | immutable Bronze, checksums |
| Lineage loss | derived result cannot be traced | source IDs, documented pipeline lineage |
| Misleading provenance | synthetic KPI presented as real | provenance labels and documentation |
| Model misuse | anomaly detector called predictive maintenance | explicit model-scope statements |
| Dependency compromise | vulnerable Python package | dependency review/scanning |
| Unapproved cloud deployment | target architecture mistaken for deployed resources | documentation-only Terraform configuration and explicit deployment status |
| BI overexposure | users see unauthorized sites | workspace controls / RLS in target state |

## Trust boundaries

1. External source acquisition
2. Local filesystem
3. PostgreSQL analytical database
4. Power BI Desktop / semantic layer
5. Future cloud boundary

Each transition should preserve provenance and use the minimum required access.

## Out of scope

This portfolio does not claim:

- production SOC monitoring;
- penetration testing;
- formal ISO 27001 certification;
- validated disaster-recovery objectives;
- live cloud security controls.

Those would require a deployed organizational environment.
