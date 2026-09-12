# Third-Party Data Acquisition and Redistribution

## Purpose

This document records the final public-release treatment of third-party source data used by the Manufacturing Performance & Energy Intelligence Platform.

The repository code license does **not** relicense third-party datasets. Each external source remains subject to the terms of its original provider.

Where redistribution rights are unestablished, the public package consists of
acquisition guidance, expected local paths, validation logic, provenance, and
transformation code; the source artifact stays with the provider or authorized
user.

---

## Industrial Utilities workbooks

The Industrial Utilities inputs are:

```text
preair_G.xlsx
preair_P.xlsx
steam_G.xlsx
steam_P.xlsx
```

Their release classification is acquisition-only, so the public repository
excludes all four workbooks. Reproduction uses copies supplied by users who
obtained them under the provider's terms; metadata, expected paths, schemas,
validation, and transformation code remain available here.

---

## EU ETS source workbook

The EU ETS source is:

```text
ETS_Database_July_2026.xlsx
```

This source follows a manual-acquisition, no-redistribution policy. The runner
reports `MANUAL_INPUT_REQUIRED` when the workbook is absent. Validation and
transformation begin after the user places an authorized copy in the documented
local path.

---

## Steel Energy reference

The authoritative source remains the UCI Machine Learning Repository.

Recorded metadata:

```text
Dataset ID: 851
DOI: 10.24432/C52G8C
License: CC BY 4.0
```

Acquisition uses a recorded, checksum-verified public mirror while UCI remains the authoritative dataset publisher:

- UCI is the authoritative source
- the mirror is only the retrieval route
- the downloaded artifact is validated against the recorded expected content

---

## ERA5-Land

ERA5 is handled as authenticated acquisition.

Users must provide their own credentials and accept the relevant provider terms.

No user credentials are distributed or committed.

Its acquisition classification is:

```text
automated authenticated acquisition
```

---

## Eurostat energy prices

The Eurostat route uses the structured JSON-stat acquisition, validation, and transformation pipeline.

---

## General third-party data policy

- Provider terms govern every external dataset; MIT covers only repository-owned
  code and documentation.
- Source artifacts remain out of Git when redistribution rights are unclear.
- Provenance, acquisition instructions, validation, and transformation code
  remain versioned.
- Bulk Bronze/Silver materializations remain local unless redistribution is
  explicitly approved.

Package-level commands and paths are documented in the
[source catalog](../../sources/README.md).
