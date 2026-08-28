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

### Release decision

**Do not redistribute these source workbooks in the public repository.**

Repository evidence does not grant redistribution rights for these files, so the public treatment is acquisition-only.

The repository may include:

- source metadata
- provenance notes
- expected local filenames and paths
- schema expectations
- validation logic
- transformation scripts
- downstream derived logic where redistribution is permitted

Users who want to reproduce this source route must obtain the original files separately under the terms of the source provider.

---

## EU ETS source workbook

The EU ETS source is:

```text
ETS_Database_July_2026.xlsx
```

### Acquisition status

EU ETS is a **manual acquisition** source.

The canonical source runner correctly reports:

```text
MANUAL_INPUT_REQUIRED
```

when the workbook is absent.

### Release decision

**Do not redistribute the EU ETS workbook in the public repository.**

Repository evidence does not grant redistribution rights for direct inclusion of the workbook, so the public treatment is manual acquisition with no source redistribution.

The repository may include:

- source and provenance information
- expected local filename and path
- manual acquisition instructions
- validation logic
- transformation scripts
- downstream analytical logic where redistribution is permitted

Users must obtain the workbook separately from the original provider and place it in the documented local path before running validation and transformation.

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

For public release:

- do not commit third-party source files where redistribution rights are unclear
- do not imply that the MIT code license applies to third-party data
- retain source provenance and acquisition instructions
- retain validation and transformation code
- use original-provider terms for all external data
- keep bulk public Bronze/Silver artifacts out of the Git repository unless intentionally approved for redistribution

---

## Final release status

Industrial Utilities uses **acquisition-only / no-source-redistribution** handling. EU ETS uses **manual acquisition / no-source-redistribution** handling.

This is a release-governance decision and does not change the completed technical reproducibility proof.
