# Repository release policy

## Purpose

This policy defines the Stage 16A.9 Git release boundary. It does not authorize
deletion of the local working data lake. The public repository should favor
code, source manifests, governed checksums, acquisition instructions, compact
accepted evidence, and the canonical production seed over bundled copies of
reacquirable public datasets or generated caches.

The demonstrated implementation is local Python, PostgreSQL, and Power BI. The
AWS material describes an AWS-ready target deployment architecture for future
production deployment; it is not evidence of a live AWS deployment.

## Size inventory

The pre-cleanup workspace contained 1,038 files totaling 4,131,783,966 bytes
(3.848 GiB). Stage 16A.9 removed only the 920,634,362-byte reproducible local
Terraform provider cache. After that removal and the Stage 16A.9 documentation
additions, the workspace contains 1,037 files totaling 3,211,172,127 bytes
(2.991 GiB). No source data, derived data, models, PBIX, logs, or analytical
evidence was deleted.

The largest pre-cleanup items were:

| Artifact | Size | Release treatment |
|---|---:|---|
| Step 06 FMUCD Bronze CSV | 1,372.89 MiB | External/reacquirable; exclude |
| Terraform AWS provider executable | 860.25 MiB | Local provider cache; exclude/remove safely |
| Step 02 MetroPT archive | 208.27 MiB | External/reacquirable; exclude |
| Step 02 MetroPT CSV | 208.19 MiB | External/reacquirable; exclude |
| Step 06 FMUCD Silver Parquet | 101.82 MiB | Generated from external source; exclude |
| Step 04 hydraulic PS1 sensor file | 87.16 MiB | External/reacquirable; exclude |
| Synthetic quality Bronze CSV | 55.82 MiB | Generated; exclude |
| Final Power BI PBIX | 42.14 MiB | Accepted release artifact; include |
| Canonical production Silver seed | 3.20 MiB | Governed required input; include |

## Artifact-class policy

| Class | Version-control treatment | Rationale |
|---|---|---|
| Source code, SQL, DAX source, configuration, manifests, checksums, documentation | Include | Reproducibility and review boundary |
| Canonical production Silver seed and its manifest | Include | Small governed upstream boundary; no first-principles generator exists |
| Other synthetic Bronze/Silver facts | Generated; exclude | Regenerated downstream from the governed seed and configuration |
| Accepted compact Gold evidence and business-case evidence | Include | Supports accepted conclusions and portfolio review |
| Superseded Gold outputs | Exclude outputs; retain scripts and documentation | Preserves technical history without presenting stale conclusions |
| Model `joblib` binaries | Generated; exclude | Reproducible from retained scripts; not consumed by the canonical database/BI build |
| Final PBIX | Include | Accepted manual report artifact; below GitHub's single-file limit |
| Power BI temporary/autorecovery files | Exclude | Local working state |
| Timestamped orchestration logs | Generated; exclude | Machine-specific paths and repeated runs add little reproducibility value |
| Terraform `.tf` and `.terraform.lock.hcl` | Include | Versioned AWS-ready target architecture and dependency selections |
| `.terraform/`, state, local tfvars, crash files | Local/generated; exclude | Provider cache, deployment state, local configuration, or possible sensitive state |
| Public-source Bronze and derived Silver data | External; exclude | Prefer manifests/checksums/acquisition instructions and avoid unsupported redistribution claims |

## Canonical production seed

`data/silver/synthetic_enterprise/production/production_operations_2024_2025.parquet`
is retained in version control. It is 3.20 MiB, has 65,790 rows, and remains
governed by `config/canonical_production_seed.json`. The root `.gitignore`
explicitly exempts it from the generated-Silver rule. Its supporting Bronze CSV
is a non-canonical serialization source and is excluded as generated data.

## Public-source data

All public-source code, provenance documents, checksums, and acquisition
instructions remain versioned. Materialized Bronze and derived Silver files are
local/external release artifacts unless a later release decision explicitly
documents a redistribution basis.

| Step | Acquisition status | Public-release treatment |
|---|---|---|
| 01 UCI steel energy | Automated from recorded checksum-verified public mirror; UCI remains authoritative | Exclude materialized data; retain downloader, UCI metadata, DOI, CC BY 4.0 record, URL, and SHA-256 |
| 02 MetroPT | Automated official UCI route | Exclude bulk data; retain source/acquisition manifests and compact failure-window reference |
| 03 SECOM | Automated official UCI route | Exclude materialized data; retain code and CC BY 4.0 provenance |
| 04 Hydraulic | Automated official UCI route | Exclude materialized data; retain code and CC BY 4.0 provenance |
| 05 Beverage production | Automated Zenodo route | Exclude materialized data; retain code and recorded CC BY 4.0 provenance |
| 06 FMUCD | Automated public API route | Exclude 1.37 GiB Bronze and derived Silver; retain code and recorded CC BY 4.0 provenance |
| 07 CNC production | Automated Zenodo route | Exclude materialized data; retain code and recorded CC BY 4.0 provenance |
| 08 ITAC | Automated source route | Exclude archive/extraction/Silver; retain code and manifest |
| 09 Industrial-park utilities | Automated source route | Exclude all materialized data; redistribution/license status unresolved |
| 10 Statistics Canada water | Automated source route | Exclude materialized data; retain code and source record without inferring additional rights |
| 11 EIA MECS fuels | Automated source route | Exclude materialized data; retain code and source record without inferring additional rights |
| 12 EEA EU ETS | Manual official acquisition | Exclude all materialized data; redistribution/license review unresolved |
| 13 ERA5-Land | Automated authenticated CDS route | Exclude materialized data; users must supply their own CDS credentials and complete required terms acceptance |
| 14 Eurostat prices | Automated structured route | Exclude materialized data; retain code, download metadata, and source record without inferring additional rights |

Step 01 is not an outstanding acquisition limitation. Steps 09 and 12 remain
explicit release blockers for bundling their source data. Step 13 is reproducible
only after user-owned authentication and external terms requirements are met.

## Dependencies

The root `requirements.txt` is the complete installation entry point:

```powershell
python -m pip install -r .\requirements.txt
```

For narrower work, use `pipelines/postgres/requirements-stage4.txt` for the
canonical PostgreSQL build, `sources/requirements.txt` for public-source routes,
or the accepted Stage 12/13 requirements files under `scripts/`. Historical and
package-specific requirement files remain available; no new packaging framework
is introduced.

## Logs and evidence

All current files under `logs/orchestration/` are generated, timestamped local
runs. Several contain absolute machine paths, and earlier failed/passed attempts
are superseded by the fail-fast bootstrap and validation definitions. They remain
in the local workspace but are excluded from release. Versioned SQL validations,
manifests, checksums, business-case evidence, and compact accepted Gold outputs
are the reproducibility evidence retained in Git.

## Secrets and credentials

Local environment files, key/certificate formats, CDS credentials, Terraform
state, and non-example tfvars are excluded. Static scanning is required before
release and must report only finding type and path, never values. Runtime secrets
belong in environment-specific secret management and are not repository assets.

## Deferred release decisions

- Select and add a root code/repository license during Stage 16B; none currently exists.
- Resolve Step 09 source redistribution/license status before bundling any of its data.
- Resolve Step 12 source redistribution/license status before bundling any of its data.
- Decide final PBIX distribution presentation and GitHub release packaging in Stage 16B.
- Write the final root README and portfolio narrative in Stage 16B.
