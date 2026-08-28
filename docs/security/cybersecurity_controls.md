# Cybersecurity Controls

## Current local portfolio environment

The implementation runs locally using:

- Python;
- PostgreSQL 18;
- Power BI Desktop;
- local source / Bronze / Silver / Gold files.

The project is not a live production system.

## Credential controls

- credentials must not be hard-coded;
- PostgreSQL password prompts are acceptable for the local portfolio workflow;
- `.env` or local secret files must be excluded from Git;
- AWS access keys must not be created or committed solely for this portfolio.

## Least privilege

Target-state access should separate:

- ingestion/write roles;
- transformation roles;
- read-only BI roles;
- administrative roles.

Power BI should use a read-oriented database identity in a deployed
environment, not the PostgreSQL superuser.

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
- generated Silver/Gold outputs should be created by controlled pipelines;
- source checksums should be retained where available;
- local secrets and transient logs containing sensitive values must be excluded
  from Git.

## Dependency controls

Python dependencies should be pinned or constrained through requirements files.

Recommended future CI controls:

- dependency vulnerability scanning;
- static code checks;
- SQL linting;
- secret scanning.

## Power BI controls

For a production deployment:

- dataset access should follow least privilege;
- row-level security should be used if site access must be segmented;
- workspace permissions should be role-based;
- published semantic models should use controlled refresh credentials.

## Backup and recovery

Target recovery controls:

- scheduled PostgreSQL backups;
- documented restore procedure;
- source/metadata backups;
- version-controlled SQL and Python;
- reproducible Gold views.

The portfolio does not claim tested enterprise RTO/RPO values.
