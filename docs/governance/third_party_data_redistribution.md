# Third-Party Data Acquisition and Redistribution

## Purpose

This document records the final public-release treatment of third-party source data used by the Manufacturing Performance & Energy Intelligence Platform.

The repository code license does **not** relicense third-party datasets. Each external source remains subject to the terms of its original provider.

Where redistribution rights are not established, the repository provides acquisition guidance, expected local paths, validation logic, provenance, and transformation code rather than redistributing the source artifact itself.

---

## Step 09: Utilities source workbooks

The Step 09 utilities inputs are:

```text
preair_G.xlsx
preair_P.xlsx
steam_G.xlsx
steam_P.xlsx
```

### Release decision

**Do not redistribute these source workbooks in the public repository.**

The project does not currently establish sufficient redistribution rights for these files.

The repository may include:

- source metadata
- provenance notes
- expected local filenames and paths
- schema expectations
- validation logic
- transformation scripts
- downstream derived logic where redistribution is permitted

Users who want to reproduce this source step must obtain the original files separately under the terms of the source provider.

### Public repository wording

> Step 09 utility workbooks are not redistributed with this repository because redistribution rights have not been established. The repository retains the expected filenames, source metadata, validation logic, and transformation code required to process user-obtained copies.

---

## Step 12: EU ETS source workbook

The Step 12 source is:

```text
ETS_Database_July_2026.xlsx
```

### Acquisition status

Step 12 remains a **manual acquisition** source.

The canonical source runner correctly reports:

```text
MANUAL_INPUT_REQUIRED
```

when the workbook is absent.

### Release decision

**Do not redistribute the EU ETS workbook in the public repository.**

The project does not currently establish sufficient redistribution rights for direct inclusion of the workbook.

The repository may include:

- source and provenance information
- expected local filename and path
- manual acquisition instructions
- validation logic
- transformation scripts
- downstream analytical logic where redistribution is permitted

Users must obtain the workbook separately from the original provider and place it in the documented local path before running the source step.

### Public repository wording

> Step 12 EU ETS data is handled as a manual-input source. The original workbook is not redistributed with this repository. Users must obtain it from the original provider under the applicable terms, place it in the documented local path, and then run the included validation and transformation workflow.

---

## Step 01: Steel Energy reference

The authoritative source remains the UCI Machine Learning Repository.

Recorded metadata:

```text
Dataset ID: 851
DOI: 10.24432/C52G8C
License: CC BY 4.0
```

The accepted project retrieval route uses a recorded verified public mirror because the original UCI binary endpoint was unavailable in the development environment.

The release should preserve this distinction:

- UCI is the authoritative source
- the mirror is only the retrieval route
- the downloaded artifact is validated against the recorded expected content

---

## Step 13: ERA5

ERA5 is handled as authenticated acquisition.

Users must provide their own credentials and accept the relevant provider terms.

No user credentials are distributed or committed.

The source should be described as:

```text
automated authenticated acquisition
```

---

## Step 14: Eurostat

The accepted Eurostat route is the structured JSON-stat pipeline.

Older metadata-only logic is not the canonical transformation path.

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

The unresolved redistribution questions for Steps 09 and 12 are closed by adopting **acquisition-only / no-source-redistribution** handling.

This is a release-governance decision and does not change the completed technical reproducibility proof.
