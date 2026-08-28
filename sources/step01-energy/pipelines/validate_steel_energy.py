from __future__ import annotations

from pathlib import Path

from download_steel_energy import find_repo_root, load_manifest, validate_csv


def main() -> int:
    script_path = Path(__file__).resolve()
    package_root = script_path.parent.parent
    find_repo_root(script_path.parent)

    manifest_path = (
        package_root
        / "docs"
        / "data_sources"
        / "steel_energy_source_manifest.json"
    )
    manifest = load_manifest(manifest_path)
    bronze_path = (package_root / manifest["file"]).resolve()
    if not bronze_path.is_file():
        raise FileNotFoundError(f"Required Step 01 Bronze file is missing: {bronze_path}")

    validation = validate_csv(bronze_path, manifest)
    print(f"VALID: {bronze_path}")
    print(
        f"SHA-256={validation['sha256']} rows={validation['rows']} "
        f"columns={validation['columns']} missing_cells={validation['missing_cells']} "
        f"duplicate_rows={validation['duplicate_rows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
