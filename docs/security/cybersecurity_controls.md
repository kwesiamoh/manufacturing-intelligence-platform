# Security Controls and Threat Model

## Implementation boundary

The implemented platform uses:

- Python;
- PostgreSQL 18;
- Power BI Desktop;
- repository-managed source metadata and local Bronze, Silver, and Gold data
  layers.

The included Terraform defines an AWS-ready target architecture; it does not
represent a live cloud deployment or an operational production system.

## Credential controls

- PostgreSQL authentication uses standard libpq mechanisms such as password
  prompts or a user-managed `pgpass.conf`;
- secrets and credentials are kept outside version control;
- the repository contains no AWS access keys or local secret files.

## Least privilege

Target-state access separates:

- ingestion/write roles;
- transformation roles;
- read-only BI roles;
- administrative roles.

A deployed Power BI service uses a read-oriented database identity with no
superuser privileges.

## Database controls

Recommended target controls:

- TLS for client connections;
- network restriction to approved hosts/subnets;
- role-based privileges;
- schema-level separation;
- audit logging for privileged actions;
- backups and restore tests.

## File controls

- Bronze files are immutable;
- controlled pipelines create generated Silver and Gold outputs;
- source checksums are retained where available;
- `.gitignore` keeps local secrets and transient sensitive logs outside Git.

## Dependency controls

The root requirements file constrains Python dependencies used by the supported
workflows.

Recommended CI controls for a deployed implementation:

- dependency vulnerability scanning;
- static code checks;
- SQL linting;
- secret scanning.

## Threat model

### Protected assets

- source datasets and Bronze, Silver, and Gold materializations;
- the PostgreSQL database;
- transformation and analytical code;
- analytical models and the Power BI semantic model;
- credentials and connection secrets.

### Threats and mitigations

| Threat | Example | Control |
|---|---|---|
| Credential leakage | Password committed to Git | External credential handling, `.gitignore`, and secret scanning |
| Unauthorized database access | Overly broad database credentials | Role-based access, network restriction, and TLS |
| Data tampering | Bronze file overwritten | Immutable-file behavior and governed checksums |
| Lineage loss | Derived result cannot be traced | Source IDs, manifests, and documented pipeline lineage |
| Misleading provenance | Synthetic KPI presented as real | Explicit provenance labels and separate operational and benchmark scopes |
| Model misuse | Synthetic scenario performance presented as real predictive performance | Separate real/synthetic evaluations and lineage fields |
| Dependency compromise | Vulnerable Python package | Dependency review and vulnerability scanning |
| Unapproved cloud deployment | Target architecture mistaken for deployed infrastructure | Explicit deployment status and source-only Terraform treatment |
| BI overexposure | Users see unauthorized sites | Workspace permissions and row-level security in a deployed environment |

### Trust boundaries

1. External source acquisition
2. Local filesystem
3. PostgreSQL analytical database
4. Power BI Desktop and semantic layer
5. AWS target environment

Each transition preserves provenance and uses the minimum required access.

## Power BI controls

Target controls for a production deployment include:

- least-privilege dataset access;
- row-level security where site access requires segmentation;
- role-based workspace permissions;
- controlled refresh credentials for published semantic models.

## Backup and recovery

Target recovery controls:

- scheduled PostgreSQL backups;
- documented restore procedure;
- source/metadata backups;
- version-controlled SQL and Python;
- reproducible Gold views.

Recovery objectives require validation in a deployed organizational
environment before RTO or RPO commitments can be stated.
