# Repository Release, Licensing, and Redistribution

## Purpose

This document defines the release-packaging rules for the Manufacturing Performance & Energy Intelligence Platform.

The objective is to publish a portfolio repository that is technically reproducible, clear about provenance, and free of local credentials, caches, oversized public-source artifacts, and ambiguous redistribution claims.

---

## Release status

Stage 16A technical hardening is complete.

The accepted reproducibility result is:

```text
PASS_AFTER_FAIL_FAST_RESUME
```

All 19 mandatory validations passed in the retained disposable proof database.

Stage 16B release work is limited to:

- documentation
- presentation
- licensing
- redistribution review
- repository packaging
- final consistency checks

No new analytical development should be introduced during release packaging unless a genuine reproducibility or release defect is found.

---

## Root code license

A root code license has **not yet been selected**.

This decision should be made explicitly by the repository owner before the public release.

For a public portfolio repository, two common choices are:

### MIT License

Suitable when the priority is:

- simple permissive reuse
- minimal license text
- broad compatibility
- low administrative overhead

### Apache License 2.0

Suitable when the priority is:

- permissive reuse
- explicit patent-license language
- more detailed contribution and redistribution terms

The repository should not claim a root license until a `LICENSE` file has actually been added.

Third-party datasets remain governed by their own source licenses regardless of the repository's code license.

---

## What the root license would cover

The root repository license should apply only to materials owned by the repository author, such as:

- Python source code
- SQL source code
- PowerShell orchestration
- Terraform source
- original documentation
- original configuration files
- original diagrams
- original project structure

It should not be interpreted as relicensing third-party datasets, third-party publications, external benchmark data, or other material governed by separate terms.

---

## Third-party data principle

Public and third-party data should be handled according to the terms of the original provider.

The repository must not imply that a project-level code license grants redistribution rights over third-party source artifacts.

Where redistribution is uncertain, the release should include:

- acquisition instructions
- source metadata
- provenance
- expected filenames
- validation logic
- transformation scripts

rather than distributing the source artifact itself.

---

## Public-source acquisition model

The canonical source runner supports explicit acquisition states such as:

- automated
- automated from a recorded verified public mirror
- authenticated user acquisition
- manual input required
- unavailable

These states should remain visible in source manifests and acquisition documentation.

The release should not silently substitute a different source or make a manual source appear automated.

---

## Step 01: Steel Energy

The authoritative source is the UCI Machine Learning Repository.

Recorded authoritative metadata includes:

```text
Dataset ID: 851
DOI: 10.24432/C52G8C
License: CC BY 4.0
```

The accepted retrieval route uses a recorded verified public mirror because the original UCI binary endpoint was unavailable in the development environment.

The release should preserve this distinction:

- UCI remains the authoritative source
- the public mirror is only the retrieval route
- the Bronze artifact is validated against the recorded expected content

---

## Step 09 redistribution status

The Step 09 source redistribution/license status remains unresolved.

Until it is explicitly verified, the release should **not redistribute the Step 09 source artifact**.

The repository may still include:

- source metadata
- acquisition notes
- expected local path
- transformation logic
- schema expectations
- validation code

The final release documentation should state that users must obtain the source under the original provider's terms.

This item must remain on the final release checklist until resolved or intentionally documented as non-redistributable.

---

## Step 12: EU ETS

Step 12 is a manual-acquisition source.

The source runner correctly returns:

```text
MANUAL_INPUT_REQUIRED
```

with a non-success acquisition status when the source is not present.

Redistribution/license status remains unresolved.

Until that status is explicitly verified, the release should **not redistribute the Step 12 source artifact**.

The repository should instead provide:

- source/provenance information
- acquisition instructions
- expected local placement
- validation and transformation logic

This preserves reproducibility without making an unsupported redistribution claim.

---

## Step 13: ERA5

ERA5 acquisition requires user-owned credentials and acceptance of the applicable provider terms.

The release should not include user credentials.

Users are expected to configure their own authenticated environment before running the acquisition step.

The source should be described as:

```text
automated authenticated acquisition
```

rather than as a broken or unavailable source.

---

## Step 14: Eurostat

The canonical Eurostat route is the later structured JSON-stat pipeline.

The older metadata-only route is not the canonical transformation path.

Release documentation should point users to the accepted structured route and should not present superseded logic as the final source pipeline.

---

## Canonical governed production seed

The canonical production seed is intentionally retained in the release because the original first-principles production generator could not be recovered defensibly.

Accepted file:

```text
data/silver/synthetic_enterprise/production/
production_operations_2024_2025.parquet
```

The seed is small enough for repository distribution and is required for downstream reproducibility.

It is governed through:

```text
config/canonical_production_seed.json
```

The canonical bootstrap verifies the seed before loading downstream data.

---

## Accepted compact analytical artifacts

Compact accepted analytics may be retained where they are required for reproducibility and Power BI reconstruction.

Examples include accepted:

- forecasting outputs
- anomaly outputs
- reliability bridge outputs
- business-case evidence
- reproducibility evidence

Superseded or bulky intermediate analytics should remain excluded where they are not required for the accepted build.

---

## Files and directories that should remain excluded

The release should exclude:

- bulk public Bronze datasets
- bulk public Silver datasets
- local PostgreSQL database files
- PostgreSQL credentials
- `pgpass.conf`
- `.env` files containing secrets
- AWS access keys
- Terraform state files
- Terraform local cache directories
- Python virtual environments
- Python caches
- notebook checkpoints
- transient runtime logs
- local temporary files
- large model binaries not required for accepted reproduction
- superseded bulky analytical outputs
- machine-specific editor or OS artifacts

---

## Large-file release policy

The Stage 16A.9 repository audit identified several very large local artifacts, including:

- FMUCD Bronze CSV
- MetroPT archive
- MetroPT CSV
- FMUCD Silver Parquet
- hydraulic benchmark sensor data

These are intentionally excluded from the Git release.

The release should use source acquisition and local reconstruction rather than GitHub as bulk dataset storage.

No file larger than GitHub's normal practical repository limit should be committed unless it is explicitly required and intentionally managed.

---

## PBIX packaging

The final Power BI file may be retained in the repository if it remains within the hosting platform's file-size limits.

The PBIX should:

- use the accepted final report pages
- contain no embedded credentials
- contain no temporary test visuals
- reflect the final proof-database refresh
- be accompanied by static screenshots in `powerbi/screenshots/`

The repository should explain that users rebuild their own PostgreSQL database and then repoint/refresh the PBIX.

The local proof database itself is not distributed.

---

## Screenshot packaging

Final screenshots should be retained under:

```text
powerbi/screenshots/
```

Expected files:

```text
01_executive_overview.png
02_production_performance.png
03_loss_opportunity.png
04_energy_utilities.png
05_data_quality.png
06_reliability_maintenance.png
```

The root README should use relative links only.

---

## Terraform packaging

Retain:

- Terraform source files
- provider configuration
- reusable module/source definitions
- lock file where appropriate
- example variable files that contain no secrets

Exclude:

- `.terraform/`
- `terraform.tfstate`
- `terraform.tfstate.*`
- secret `.tfvars`
- local plan output containing sensitive values
- local provider caches

Terraform should be presented as the AWS-ready target infrastructure definition, not evidence of a live deployed AWS environment.

---

## Credential handling

Credentials must remain outside the repository.

For local PostgreSQL, standard libpq credential resolution may use a user-owned file such as:

```text
%APPDATA%\postgresql\pgpass.conf
```

This file must never be committed.

For a future AWS deployment, credentials and secrets should be handled through managed services such as AWS Secrets Manager and IAM rather than source-controlled plaintext.

---

## Secrets scan

Stage 16A.9 scanned the relevant repository text files and found:

```text
0 high-confidence secret findings
```

The secret scan should be repeated once more immediately before public release.

A clean scan is a release requirement.

---

## Release evidence to retain

The following files should be retained as principal reproducibility evidence:

```text
reports/reproducibility/stage16a10_build_evidence.json
docs/reproducibility/stage16a10_clean_build_proof.md
docs/reproducibility/canonical_build_order.md
config/artifact_manifest.json
config/canonical_production_seed.json
config/stage3h_energy_artifact_manifest.json
```

The generated local orchestration log itself remains excluded from the release.

Its cryptographic hash is captured in the machine-readable build evidence.

---

## Artifact manifest

`config/artifact_manifest.json` is the canonical release-classification reference.

Artifacts should remain classified according to their accepted role, such as:

- accepted
- superseded
- diagnostic
- supporting
- manual
- excluded

A file should not be promoted into the public release simply because it exists locally.

---

## Superseded analytical material

Superseded analytical implementations should not be presented as canonical results.

Examples include:

- ordinary p-chart analytical output superseded by Laney p′
- superseded reliability SQL paths where corrected source-qualified logic exists
- older Eurostat route superseded by the structured pipeline
- legacy partial PostgreSQL orchestration

Where superseded files are retained for development history, they should be clearly labeled and kept out of the primary run path.

---

## Recommended public repository structure

```text
manufacturing-intelligence-platform/
├── config/
├── data/
│   └── silver/
│       └── synthetic_enterprise/
│           └── production/
│               └── production_operations_2024_2025.parquet
├── docs/
│   ├── architecture/
│   ├── governance/
│   ├── methodology/
│   ├── powerbi/
│   └── reproducibility/
├── infrastructure/
│   └── terraform/
├── pipelines/
├── powerbi/
│   └── screenshots/
├── reports/
│   └── reproducibility/
├── scripts/
├── sql/
├── .gitignore
├── requirements.txt
├── LICENSE
└── README.md
```

The exact source tree may contain additional accepted directories, but the public repository should remain navigable and should avoid exposing development clutter.

---

## Final release checks

Before public release, verify:

- root `README.md` renders correctly on GitHub
- Mermaid diagrams render
- screenshot links resolve
- Power BI screenshots are final
- PBIX is the accepted final version
- canonical production seed is included
- artifact manifests are included
- reproducibility proof files are included
- local runtime logs are excluded
- bulk public data is excluded where intended
- `.terraform/` is excluded
- Terraform state is excluded
- credentials are excluded
- a final secrets scan passes
- Step 09 redistribution wording is explicit
- Step 12 redistribution wording is explicit
- root code license is selected and added
- third-party data is not implicitly relicensed
- repository file sizes are acceptable
- no superseded analytical path is presented as canonical

---

## Release blockers still requiring owner decision

The following items must be explicitly closed before the final public release:

1. **Root code license**
   - select and add the project license

2. **Step 09 redistribution**
   - verify redistribution terms, or retain acquisition-only handling

3. **Step 12 redistribution**
   - verify redistribution terms, or retain manual acquisition-only handling

These are release-governance decisions. They do not invalidate the completed technical reproducibility proof.
