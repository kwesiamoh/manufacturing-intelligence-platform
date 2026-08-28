# Architecture Decision Record

## ADR-001 — Bronze/Silver/Gold data architecture

Decision:
Use an immutable Bronze layer, standardized Silver Parquet layer, and
business-ready Gold analytical layer.

Reason:
Preserves provenance and supports reproducible transformation.

## ADR-002 — PostgreSQL analytical integration layer

Decision:
Use PostgreSQL as the integrated local analytical database.

Reason:
Provides relational modelling, SQL analytics, Power BI connectivity, and
portfolio-friendly local operation.

## ADR-003 — Synthetic enterprise anchor

Decision:
Use a clearly labelled synthetic six-site beverage enterprise to bridge public
datasets that do not originate from one physical organization.

Reason:
Avoids falsely claiming unrelated public datasets came from the same plant.

## ADR-004 — Real-source separation

Decision:
MetroPT and hydraulic condition-monitoring datasets remain separate from the
synthetic enterprise operational history.

Reason:
Protects provenance and prevents misleading cross-source claims.

## ADR-005 — AWS target architecture only

Decision:
Document AWS-ready infrastructure and IaC patterns without live deployment.

Reason:
Hard €0 AWS-spend requirement.

## ADR-006 — Power BI compatibility views

Decision:
Use `gold_bi` wrapper views to cast unconstrained PostgreSQL numerics for Power
BI compatibility while preserving original Gold logic.

Reason:
Avoids decimal import failures without changing analytical meaning.

## ADR-007 — Reliability KPI proxy wording

Decision:
Label operating-hours MTBF and derived availability as proxies when line
operating time is used instead of direct equipment runtime.

Reason:
Avoids overstating measurement precision.
