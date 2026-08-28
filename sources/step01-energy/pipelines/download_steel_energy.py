from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import Request, urlopen

MANIFEST_NAME = "steel_energy_source_manifest.json"


def find_repo_root(start: Path) -> Path:
    """Find the repository root without depending on the caller's working directory."""
    for candidate in [start, *start.parents]:
        if (candidate / "sources").exists() and (candidate / "config").exists():
            return candidate
    raise RuntimeError(
        "Could not locate repository root. Expected an ancestor containing "
        "'sources/' and 'config/'."
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    required = {
        "dataset_id",
        "official_source",
        "retrieval_url",
        "file",
        "sha256",
        "rows",
        "columns",
        "column_names",
        "missing_cells",
        "duplicate_rows",
    }
    missing = sorted(required.difference(manifest))
    if missing:
        raise ValueError(f"Manifest missing required fields: {', '.join(missing)}")
    return manifest


def validate_csv(path: Path, manifest: dict, *, verify_hash: bool = True) -> dict:
    """Validate the governed file identity and material CSV contract."""
    expected_sha = str(manifest["sha256"]).lower()
    observed_sha = sha256_file(path)
    if verify_hash and observed_sha != expected_sha:
        raise RuntimeError(
            "Steel-energy file failed SHA-256 verification.\n"
            f"Path: {path}\nExpected: {expected_sha}\nObserved: {observed_sha}"
        )

    expected_columns = list(manifest["column_names"])
    expected_column_count = int(manifest["columns"])
    if len(expected_columns) != expected_column_count:
        raise ValueError(
            "Manifest column_names length does not match the governed columns value."
        )

    row_count = 0
    missing_cells = 0
    duplicate_rows = 0
    seen_rows: set[tuple[str, ...]] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            observed_columns = next(reader)
        except StopIteration as exc:
            raise RuntimeError(f"Steel-energy CSV is empty: {path}") from exc

        if observed_columns != expected_columns:
            raise RuntimeError(
                "Steel-energy CSV schema mismatch.\n"
                f"Expected: {expected_columns}\nObserved: {observed_columns}"
            )

        for line_number, row in enumerate(reader, start=2):
            if len(row) != expected_column_count:
                raise RuntimeError(
                    f"Steel-energy CSV row {line_number} has {len(row)} columns; "
                    f"expected {expected_column_count}."
                )
            row_count += 1
            missing_cells += sum(value == "" for value in row)
            row_key = tuple(row)
            if row_key in seen_rows:
                duplicate_rows += 1
            else:
                seen_rows.add(row_key)

    expectations = {
        "rows": row_count,
        "missing_cells": missing_cells,
        "duplicate_rows": duplicate_rows,
    }
    for field, observed in expectations.items():
        expected = int(manifest[field])
        if observed != expected:
            raise RuntimeError(
                f"Steel-energy CSV {field} mismatch: expected {expected}, "
                f"observed {observed}."
            )

    return {
        "sha256": observed_sha,
        "rows": row_count,
        "columns": len(observed_columns),
        "missing_cells": missing_cells,
        "duplicate_rows": duplicate_rows,
    }


def download_to_temp(url: str, destination_dir: Path) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)

    request = Request(
        url,
        headers={
            "User-Agent": "manufacturing-intelligence-platform/step01-downloader"
        },
    )

    temp_path: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="wb",
            prefix=".steel_energy_",
            suffix=".download",
            dir=destination_dir,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            with urlopen(request, timeout=120) as response:
                shutil_copyfileobj(response, temp_file)
        return temp_path
    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise


def shutil_copyfileobj(src, dst, length: int = 1024 * 1024) -> None:
    while True:
        buf = src.read(length)
        if not buf:
            break
        dst.write(buf)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Acquire the governed UCI Steel Industry Energy Consumption Bronze file "
            "from the recorded public retrieval mirror and verify its canonical SHA-256."
        )
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to steel_energy_source_manifest.json.",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=None,
        help="Optional target override used for isolated immutability testing.",
    )
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = find_repo_root(script_path.parent)

    package_root = script_path.parent.parent
    manifest_path = args.manifest
    if manifest_path is None:
        manifest_path = package_root / "docs" / "data_sources" / MANIFEST_NAME
    elif not manifest_path.is_absolute():
        manifest_path = repo_root / manifest_path

    manifest = load_manifest(manifest_path.resolve())
    if args.target is None:
        # The source manifest's file path is package-relative by contract.
        target = (package_root / manifest["file"]).resolve()
    else:
        target = args.target
        if not target.is_absolute():
            target = repo_root / target
        target = target.resolve()
    expected_sha = manifest["sha256"].lower()

    if target.exists():
        existing_sha = sha256_file(target)
        if existing_sha == expected_sha:
            validation = validate_csv(target, manifest, verify_hash=False)
            print(
                f"REUSED: canonical Bronze file already exists and matches SHA-256: {target}"
            )
            print(
                f"VALIDATED: rows={validation['rows']} columns={validation['columns']} "
                f"missing_cells={validation['missing_cells']} "
                f"duplicate_rows={validation['duplicate_rows']}"
            )
            return 0
        if existing_sha != expected_sha:
            raise RuntimeError(
                "Refusing to overwrite an existing Bronze file whose SHA-256 differs "
                f"from the governed manifest.\nPath: {target}\n"
                f"Expected: {expected_sha}\nObserved: {existing_sha}"
            )

    retrieval_url = manifest["retrieval_url"]
    print(f"Official dataset reference: {manifest['official_source']}")
    print(f"Recorded retrieval route: {retrieval_url}")

    temp_path = download_to_temp(retrieval_url, target.parent)
    try:
        downloaded_sha = sha256_file(temp_path)
        if downloaded_sha != expected_sha:
            raise RuntimeError(
                "Downloaded file failed SHA-256 verification.\n"
                f"Expected: {expected_sha}\nObserved: {downloaded_sha}"
            )

        validation = validate_csv(temp_path, manifest, verify_hash=False)

        # Never stream directly over Bronze. Promote only after hash/schema checks.
        if target.exists():
            current_sha = sha256_file(target)
            if current_sha != expected_sha:
                raise RuntimeError(
                    "Refusing to overwrite a Bronze file that changed during "
                    f"acquisition.\nPath: {target}\nExpected: {expected_sha}\n"
                    f"Observed: {current_sha}"
                )
        os.replace(temp_path, target)
        print(f"DOWNLOADED_AND_VERIFIED: {target}")
        print(f"SHA-256: {downloaded_sha}")
        print(
            f"VALIDATED: rows={validation['rows']} columns={validation['columns']} "
            f"missing_cells={validation['missing_cells']} "
            f"duplicate_rows={validation['duplicate_rows']}"
        )
        return 0
    finally:
        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
