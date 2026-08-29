# Third-Party Data Acquisition and Redistribution

## Purpose

This document records the final public-release treatment of third-party source data used by the Manufacturing Performance & Energy Intelligence Platform.

The repository code license does **not** relicense third-party datasets. Each external source remains subject to the terms of its original provider.

Where redistribution rights are not established, the repository provides acquisition guidance, expected local paths, validation logic, provenance, and transformation code rather than redistributing the source artifact itself.

---

## Industrial Utilities workbooks

The Industrial Utilities inputs are:

```text
preair_G.xlsx
preair_P.xlsx
steam_G.xlsx
steam_P.xlsx
```

They are acquisition-only and must not be redistributed. Reproduction requires
user-supplied copies obtained under the provider's terms; the repository retains
metadata, expected paths, schemas, validation, and transformation code.

---

## EU ETS source workbook

The EU ETS source is:

```text
ETS_Database_July_2026.xlsx
```

This source requires manual acquisition and must not be redistributed. The
runner reports `MANUAL_INPUT_REQUIRED` when the workbook is absent. Users place
an authorized copy in the documented local path before validation and
transformation.

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
