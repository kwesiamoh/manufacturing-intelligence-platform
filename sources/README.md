# Public-source orchestration

The 14 source packages are real external operational, benchmark, or contextual
datasets. They are separate from the synthetic Velora enterprise build.

Install the consolidated source dependencies with:

```powershell
python -m pip install -r .\requirements.txt
```

Run the explicit manifest-driven source workflow from any directory:

```powershell
& "<repository>\sources\run_all_sources.ps1"
```

Use `-DryRun` to resolve and report every declared action without executing a
download, validator, or transform. `-Phase Acquire|Validate|Transform` and
`-Source steel-energy,metropt3-telemetry` select narrower runs. The runner resolves paths from its own
location, sets each package's working directory explicitly, reports action mode
and status, stops on the first blocking failure by default, and supports
`-ContinueOnError` when a full inventory is preferable. `-OutputFormat Json`
provides a machine-readable summary.

The runner is the canonical portfolio-level Bronze safeguard. When every
declared immutable Bronze artifact already exists, acquisition skips
network work and the existing files are checksummed/reused. A source can opt
into its downloader's stronger governed reuse verification; Steel Energy does this
without making a network request. A partial declared artifact set fails instead
of permitting a downloader to overwrite it. Source validators then enforce
available hash, container, row, and schema expectations.

Important acquisition limits:

- Steel Energy uses the recorded verified public mirror as its automated retrieval
  route while retaining UCI dataset 851 as the authoritative source. Its
  downloader validates and reuses the existing governed Bronze CSV without a
  network request when the SHA-256 and CSV contract match, and refuses a
  differing existing file.
- EU ETS is an instruction-only EEA Datahub route and requires manual source
  acquisition. It is never reported as an automated download.
- ERA5-Land uses the authenticated CDS API. A CDS account, credentials, and any
  externally required terms acceptance remain prerequisites.
- Industrial Utilities is acquisition-only: its four utility workbooks are not redistributed.
- EU ETS is manual acquisition with `MANUAL_INPUT_REQUIRED`; its source
  workbook is not redistributed.

The exact actions, canonical Silver contracts, and acquisition limits are
recorded in `source_pipeline_manifest.json`.

Rerun isolation is also explicit: MetroPT partitioned Silver output is staged
and published atomically as one complete directory, ITAC workbook extraction
uses a fresh temporary directory, and each ERA5 NetCDF extraction is published
atomically from its immutable site ZIP. These routes cannot retain fragments
from another extraction or partition set.
