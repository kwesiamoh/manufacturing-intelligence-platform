# Public-source orchestration

The 14 source packages are real external operational, benchmark, or contextual
datasets. They are separate from the synthetic Velora enterprise build.

Install the consolidated source dependencies with:

```powershell
python -m pip install -r .\sources\requirements.txt
```

Run the explicit manifest-driven source workflow from any directory:

```powershell
& "<repository>\sources\run_all_sources.ps1"
```

Use `-DryRun` to resolve and report every declared action without executing a
download, validator, or transform. `-Phase Acquire|Validate|Transform` and
`-Step 01,02` select narrower runs. The runner resolves paths from its own
location, sets each package's working directory explicitly, reports action mode
and status, stops on the first blocking failure by default, and supports
`-ContinueOnError` when a full inventory is preferable. `-OutputFormat Json`
provides a machine-readable summary.

The runner is the canonical portfolio-level Bronze safeguard. When every
declared immutable Bronze artifact already exists, acquisition normally skips
network work and the existing files are checksummed/reused. A source can opt
into its downloader's stronger governed reuse verification; Step 01 does this
without making a network request. A partial declared artifact set fails instead
of permitting a downloader to overwrite it. Source validators then enforce
available hash, container, row, and schema expectations.

Important acquisition limits:

- Step 01 uses the recorded verified public mirror as its automated retrieval
  route while retaining UCI dataset 851 as the authoritative source. Its
  downloader validates and reuses the existing governed Bronze CSV without a
  network request when the SHA-256 and CSV contract match, and refuses a
  differing existing file.
- Step 12 is an instruction-only EEA Datahub route and requires manual source
  acquisition. It is never reported as an automated download.
- Step 13 uses the authenticated CDS API. A CDS account, credentials, and any
  externally required terms acceptance remain prerequisites.
- Step 09's source license remains unresolved, so its materialized data is
  excluded from the public release boundary pending a Stage 16B decision. Step
  12 redistribution/license status is also unresolved and its manually acquired
  materialized data is likewise excluded; no license is inferred.

The exact actions, canonical Silver contracts, retained legacy routes, and
limitations are recorded in `source_pipeline_manifest.json`.

Rerun isolation is also explicit: MetroPT partitioned Silver output is staged
and replaced as one complete directory, ITAC workbook extraction uses a fresh
temporary directory, and each ERA5 NetCDF extraction is staged and cleanly
replaced from its immutable site ZIP. These routes cannot retain fragments from
an older extraction or partition set.
