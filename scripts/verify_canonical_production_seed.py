"""Verify the immutable canonical production seed used by the Velora build.

This verifier is intentionally read-only.  It validates both the physical
Parquet file hash and a logical, row-order-independent content fingerprint so
that an equivalent table can be distinguished from a changed production
population even when Parquet writer metadata differs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "config" / "canonical_production_seed.json"
FINGERPRINT_ALGORITHM = "velora-tabular-sha256-v1"


class SeedVerificationError(RuntimeError):
    """Raised when the governed production boundary fails verification."""


def _length_prefix(payload: bytes) -> bytes:
    return struct.pack(">Q", len(payload)) + payload


def _encoded_value(value: Any, logical_type: str) -> bytes:
    if pd.isna(value):
        return b"N" + _length_prefix(b"")

    if logical_type == "string":
        marker = b"S"
        payload = str(value).encode("utf-8")
    elif logical_type == "timestamp[ns]":
        marker = b"T"
        payload = str(pd.Timestamp(value).value).encode("ascii")
    elif logical_type == "int64":
        marker = b"I"
        payload = str(int(value)).encode("ascii")
    elif logical_type == "double":
        marker = b"F"
        number = float(value)
        if math.isnan(number):
            payload = bytes.fromhex("7ff8000000000000")
        else:
            # Canonicalize negative zero while preserving every other IEEE-754
            # double exactly.
            if number == 0.0:
                number = 0.0
            payload = struct.pack(">d", number)
    else:
        raise SeedVerificationError(
            f"Unsupported logical type in seed manifest: {logical_type}"
        )

    return marker + _length_prefix(payload)


def logical_content_fingerprint(
    frame: pd.DataFrame,
    schema: list[dict[str, str]],
    schema_version: str,
    sort_key: list[str],
) -> str:
    """Return a deterministic fingerprint independent of Parquet metadata/order."""

    ordered_columns = [field["name"] for field in schema]
    ordered = frame.sort_values(sort_key, kind="mergesort")[ordered_columns]

    digest = hashlib.sha256()
    digest.update(_length_prefix(FINGERPRINT_ALGORITHM.encode("ascii")))
    digest.update(_length_prefix(schema_version.encode("utf-8")))
    for field in schema:
        digest.update(_length_prefix(field["name"].encode("utf-8")))
        digest.update(_length_prefix(field["logical_type"].encode("ascii")))

    for row in ordered.itertuples(index=False, name=None):
        digest.update(b"R")
        for value, field in zip(row, schema):
            digest.update(_encoded_value(value, field["logical_type"]))

    return digest.hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def _assert_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise SeedVerificationError(
            f"{label} mismatch: expected {expected!r}, observed {actual!r}"
        )


def _assert_close(label: str, actual: float, expected: float, tolerance: float) -> None:
    if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=tolerance):
        raise SeedVerificationError(
            f"{label} mismatch: expected {expected!r} +/- {tolerance}, "
            f"observed {actual!r}"
        )


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SeedVerificationError(f"Canonical production seed manifest is missing: {path}")
    try:
        with path.open("r", encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise SeedVerificationError(
            f"Canonical production seed manifest could not be parsed: {path}: {exc}"
        ) from exc


def inspect_artifact(path: Path, manifest: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    if not path.is_file():
        raise SeedVerificationError(f"Canonical production seed is missing: {path}")

    expected = manifest["artifact"]
    physical_hash = file_sha256(path)
    if physical_hash != expected["sha256"]:
        raise SeedVerificationError(
            "Canonical production seed SHA-256 mismatch: "
            f"expected {expected['sha256']}, observed {physical_hash}, path {path}"
        )

    arrow_schema = pq.read_schema(path)
    observed_schema = [
        {"name": field.name, "logical_type": str(field.type)} for field in arrow_schema
    ]
    _assert_equal("Parquet schema", observed_schema, expected["schema"])

    frame = pd.read_parquet(path)
    fingerprint = logical_content_fingerprint(
        frame=frame,
        schema=expected["schema"],
        schema_version=expected["schema_version"],
        sort_key=expected["content_fingerprint"]["sort_key"],
    )
    observed = {
        "sha256": physical_hash,
        "content_fingerprint": fingerprint,
        "row_count": int(len(frame)),
        "schema": observed_schema,
    }
    return frame, observed


def verify(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    expected = manifest["artifact"]
    frame, observed = inspect_artifact(path, manifest)

    _assert_equal("row count", observed["row_count"], expected["expected_row_count"])
    _assert_equal(
        "logical content fingerprint",
        observed["content_fingerprint"],
        expected["content_fingerprint"]["sha256"],
    )

    primary_key = expected["primary_key"]
    business_grain = expected["business_grain"]
    _assert_equal(
        "primary-key duplicate row count",
        int(frame.duplicated(primary_key, keep=False).sum()),
        0,
    )
    _assert_equal(
        "business-grain duplicate row count",
        int(frame.duplicated(business_grain, keep=False).sum()),
        0,
    )

    null_profile = {column: int(frame[column].isna().sum()) for column in frame.columns}
    _assert_equal("null profile", null_profile, expected["null_profile"])

    coverage = expected["coverage"]
    for label, column in (
        ("sites", "site_code"),
        ("lines", "line_code"),
        ("products", "product_code"),
        ("shifts", "shift_code"),
    ):
        actual_values = sorted(str(value) for value in frame[column].unique())
        _assert_equal(f"{label} coverage", actual_values, coverage[label])

    dates = expected["date_coverage"]
    _assert_equal(
        "timestamp_start minimum",
        frame["timestamp_start"].min().isoformat(),
        dates["timestamp_start_min"],
    )
    _assert_equal(
        "timestamp_start maximum",
        frame["timestamp_start"].max().isoformat(),
        dates["timestamp_start_max"],
    )
    _assert_equal(
        "timestamp_end minimum",
        frame["timestamp_end"].min().isoformat(),
        dates["timestamp_end_min"],
    )
    _assert_equal(
        "timestamp_end maximum",
        frame["timestamp_end"].max().isoformat(),
        dates["timestamp_end_max"],
    )
    _assert_equal(
        "calendar-date count",
        int(frame["timestamp_start"].dt.date.nunique()),
        dates["timestamp_start_calendar_dates"],
    )

    for column, values in expected["constant_values"].items():
        actual_values = sorted(
            int(value) if isinstance(values[0], int) else str(value)
            for value in frame[column].unique()
        )
        _assert_equal(f"{column} values", actual_values, values)

    checks = expected["reconciliation"]
    _assert_equal(
        "quantity-reconciliation failure count",
        int((frame["actual_quantity"] != frame["good_quantity"] + frame["reject_quantity"]).sum()),
        checks["quantity_mismatch_rows"],
    )
    _assert_equal(
        "invalid timestamp-interval count",
        int((frame["timestamp_end"] <= frame["timestamp_start"]).sum()),
        checks["invalid_timestamp_interval_rows"],
    )
    for column, specification in checks["column_totals"].items():
        actual_total = frame[column].sum()
        expected_total = specification["value"]
        tolerance = specification.get("absolute_tolerance", 0)
        if tolerance:
            _assert_close(column + " total", float(actual_total), float(expected_total), tolerance)
        else:
            _assert_equal(column + " total", int(actual_total), int(expected_total))

    return observed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify the immutable canonical Velora production seed."
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help="Manifest path (default: config/canonical_production_seed.json).",
    )
    parser.add_argument(
        "--artifact-path",
        help="Testing override for the artifact path; the manifest remains authoritative.",
    )
    parser.add_argument(
        "--print-observed",
        action="store_true",
        help="Print observed hash/fingerprint/schema after physical hash validation.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifest_path = _resolve_repo_path(args.manifest)
        manifest = load_manifest(manifest_path)
        artifact_path = _resolve_repo_path(
            args.artifact_path or manifest["artifact"]["path"]
        )
        observed = verify(artifact_path, manifest)
        if args.print_observed:
            print(json.dumps(observed, indent=2))
        print(
            "PASS: canonical production seed verified "
            f"({observed['row_count']:,} rows; "
            f"SHA-256 {observed['sha256']}; "
            f"content {observed['content_fingerprint']})."
        )
        return 0
    except (KeyError, TypeError, SeedVerificationError, OSError) as exc:
        print(f"FAIL: canonical production seed verification failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
