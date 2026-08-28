from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "config" / "stage3h_energy_artifact_manifest.json"

LINE_COLUMNS = [
    "energy_record_id",
    "production_record_id",
    "site_code",
    "line_code",
    "line_class_code",
    "shift_code",
    "product_code",
    "timestamp_start",
    "timestamp_end",
    "actual_quantity",
    "line_production_electricity_kwh",
    "line_idle_electricity_kwh",
    "line_total_electricity_kwh",
    "energy_intensity_kwh_per_1000_units",
    "compressed_air_nm3",
    "compressed_air_nm3_per_1000_units",
    "shift_mean_air_temperature_c",
    "site_auxiliary_base_kw",
    "site_weather_auxiliary_kw",
    "data_class",
    "integration_role",
    "weather_data_class",
    "generator_seed",
]

SITE_COLUMNS = [
    "site_code",
    "shift_code",
    "timestamp_start",
    "timestamp_end",
    "line_electricity_kwh",
    "production_units",
    "mean_air_temperature_c",
    "site_auxiliary_base_kw",
    "site_weather_auxiliary_kw",
    "shift_hours",
    "site_auxiliary_electricity_kwh",
    "site_total_electricity_kwh",
    "site_energy_intensity_kwh_per_1000_units",
    "data_class",
    "integration_role",
    "weather_data_class",
]


class VerificationError(ValueError):
    """Raised when the governed Stage 3H snapshot no longer matches."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_path(relative_path: str) -> Path:
    path = (REPO_ROOT / relative_path).resolve()
    try:
        path.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise VerificationError(
            f"Manifest path escapes the repository: {relative_path}"
        ) from exc
    if not path.is_file():
        raise VerificationError(f"Required Stage 3H artifact is missing: {path}")
    return path


def require_hash(path: Path, expected: str, label: str) -> None:
    actual = sha256_file(path)
    if actual != expected:
        raise VerificationError(
            f"{label} SHA-256 mismatch: expected {expected}, observed {actual}"
        )


def output_record(manifest: dict, suffix: str) -> dict:
    matches = [
        record
        for record in manifest["outputs"]
        if record["path"].replace("\\", "/").endswith(suffix)
    ]
    if len(matches) != 1:
        raise VerificationError(
            f"Expected exactly one Stage 3H manifest output ending in {suffix}"
        )
    return matches[0]


def require_close(observed: float, expected: float, label: str) -> None:
    if not np.isclose(observed, expected, rtol=0.0, atol=0.001):
        raise VerificationError(
            f"{label} mismatch: expected {expected:.3f}, observed {observed:.3f}"
        )


def validate() -> None:
    with MANIFEST_PATH.open("r", encoding="utf-8") as source:
        manifest = json.load(source)

    if manifest.get("stage") != "16A.9A":
        raise VerificationError("Unexpected Stage 3H artifact manifest stage")

    generator = manifest["generator"]
    require_hash(
        repository_path(generator["path"]),
        generator["sha256"],
        "Stage 3H generator",
    )
    for input_record in manifest["inputs"]:
        require_hash(
            repository_path(input_record["path"]),
            input_record["sha256"],
            f"Stage 3H input {input_record['path']}",
        )
    for output in manifest["outputs"]:
        require_hash(
            repository_path(output["path"]),
            output["sha256"],
            f"Stage 3H output {output['path']}",
        )

    line_record = output_record(
        manifest, "silver/synthetic_enterprise/energy/line_energy_utility_2024_2025.parquet"
    )
    site_record = output_record(
        manifest, "silver/synthetic_enterprise/energy/site_energy_2024_2025.parquet"
    )
    line = pd.read_parquet(repository_path(line_record["path"]))
    site = pd.read_parquet(repository_path(site_record["path"]))

    if list(line.columns) != LINE_COLUMNS:
        raise VerificationError("Stage 3H line-energy schema/order mismatch")
    if list(site.columns) != SITE_COLUMNS:
        raise VerificationError("Stage 3H site-energy schema/order mismatch")
    if len(line) != 65790 or len(line) != line_record["rows"]:
        raise VerificationError(f"Line-energy rows are {len(line)}; expected 65,790")
    if len(site) != 13158 or len(site) != site_record["rows"]:
        raise VerificationError(f"Site-energy rows are {len(site)}; expected 13,158")
    if line["energy_record_id"].duplicated().any():
        raise VerificationError("Line-energy energy_record_id is not unique")
    if line["production_record_id"].duplicated().any():
        raise VerificationError("Line-energy production_record_id is not unique")

    required_line = [
        "energy_record_id",
        "production_record_id",
        "site_code",
        "line_code",
        "line_class_code",
        "shift_code",
        "product_code",
        "timestamp_start",
        "timestamp_end",
        "actual_quantity",
        "line_production_electricity_kwh",
        "line_idle_electricity_kwh",
        "line_total_electricity_kwh",
        "energy_intensity_kwh_per_1000_units",
    ]
    if line[required_line].isna().any().any():
        raise VerificationError("Line-energy contains required null values")

    if not np.allclose(
        line["line_total_electricity_kwh"],
        line["line_production_electricity_kwh"]
        + line["line_idle_electricity_kwh"],
        rtol=0.0,
        atol=0.001,
    ):
        raise VerificationError("Line electricity no longer reconciles")
    if not np.allclose(
        site["site_total_electricity_kwh"],
        site["line_electricity_kwh"] + site["site_auxiliary_electricity_kwh"],
        rtol=0.0,
        atol=0.001,
    ):
        raise VerificationError("Site electricity no longer reconciles")

    can = line.loc[line["line_class_code"].eq("CAN_ENERGY_250")].copy()
    if len(can) != 6579:
        raise VerificationError(f"CAN line-energy rows are {len(can)}; expected 6,579")
    positive_can = can.loc[can["actual_quantity"] > 0]
    if len(positive_can) != 6579:
        raise VerificationError("Not all accepted CAN rows have positive production")
    if positive_can[
        ["compressed_air_nm3", "compressed_air_nm3_per_1000_units"]
    ].isna().any().any():
        raise VerificationError("Positive-production CAN rows contain compressed-air nulls")
    if not positive_can["compressed_air_nm3_per_1000_units"].eq(5.0).all():
        raise VerificationError("CAN compressed-air intensity is not exactly 5.0")
    if not np.allclose(
        positive_can["compressed_air_nm3"],
        positive_can["actual_quantity"] * 5.0 / 1000.0,
        rtol=0.0,
        atol=0.000001,
    ):
        raise VerificationError("CAN compressed-air values violate the generic formula")

    reconciliation = manifest["reconciliation"]
    can_total = float(can["compressed_air_nm3"].sum())
    pet_total = float(
        line.loc[
            line["line_class_code"].str.startswith("PET_"), "compressed_air_nm3"
        ].sum()
    )
    enterprise_total = float(line["compressed_air_nm3"].sum())
    require_close(
        can_total,
        float(reconciliation["new_can_compressed_air_nm3"]),
        "CAN compressed-air total",
    )
    require_close(
        pet_total,
        float(reconciliation["new_pet_compressed_air_nm3"]),
        "PET compressed-air total",
    )
    require_close(
        enterprise_total,
        float(reconciliation["new_enterprise_compressed_air_nm3"]),
        "Enterprise compressed-air total",
    )

    print("PASS: governed Stage 3H energy artifact verified")
    print(f"  line rows: {len(line):,}; site rows: {len(site):,}")
    print(
        "  CAN rows: "
        f"{len(can):,}; intensity: 5.0 Nm3/1,000 cans; nulls: 0"
    )
    print(
        "  compressed air Nm3: "
        f"CAN={can_total:.3f}; PET={pet_total:.3f}; enterprise={enterprise_total:.3f}"
    )
    print("  generator, input, and output SHA-256 values match the manifest")


def main() -> int:
    try:
        validate()
        return 0
    except (KeyError, OSError, TypeError, VerificationError, ValueError) as exc:
        print(f"FAIL: governed Stage 3H energy artifact verification failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
