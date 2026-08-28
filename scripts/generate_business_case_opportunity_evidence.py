"""Generate and validate business-case business-case opportunity evidence.

The canonical database result is public.vw_site_loss_summary, created by
sql/analytics/110_create_production_loss_views.sql.  This script reproduces its
total_technical_opportunity_eur formula from the governed production seed and
the product values seeded by SQL 005, allowing evidence generation without
changing or requiring a live database.

The output is modeled technical opportunity.  It is not realized savings.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, getcontext
from pathlib import Path
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_MANIFEST = REPO_ROOT / "config" / "canonical_production_seed.json"
LOSS_VALUE_SQL = REPO_ROOT / "sql" / "ddl" / "005_create_loss_value_config.sql"
OEE_SQL = REPO_ROOT / "sql" / "analytics" / "100_create_oee_views.sql"
OPPORTUNITY_SQL = (
    REPO_ROOT / "sql" / "analytics" / "110_create_production_loss_views.sql"
)
SITE_REGISTRY = (
    REPO_ROOT / "data_model" / "dimensions" / "fictional_site_registry.csv"
)
OUTPUT_DIR = REPO_ROOT / "data" / "gold" / "business_case"
SITE_EXPORT = OUTPUT_DIR / "technical_opportunity_2024_2025.csv"
SENSITIVITY_EXPORT = OUTPUT_DIR / "annual_realization_sensitivity_2024_2025.csv"
EVIDENCE_MANIFEST = OUTPUT_DIR / "business_case_evidence_manifest.json"

EVIDENCE_VERSION = "stage16a7-v1"
CURRENCY = "EUR"
EXPECTED_PERIOD_START = "2024-01-01"
EXPECTED_PERIOD_END = "2025-12-31"
EXPECTED_PERIOD_LABEL = "2024-2025"
CENT = Decimal("0.01")
TWO = Decimal("2")
REALIZATION_RATES = (
    ("0.5", Decimal("0.005")),
    ("1.0", Decimal("0.010")),
    ("2.0", Decimal("0.020")),
    ("5.0", Decimal("0.050")),
)

getcontext().prec = 40


class EvidenceValidationError(RuntimeError):
    """Raised when generated or retained evidence fails reconciliation."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def quantize_eur(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceValidationError(f"Cannot parse JSON {path}: {exc}") from exc


def governed_production_path() -> tuple[Path, dict[str, Any]]:
    manifest = load_json(PRODUCTION_MANIFEST)
    artifact = manifest["artifact"]
    path = REPO_ROOT / artifact["path"]
    if not path.is_file():
        raise EvidenceValidationError(f"Governed production seed is missing: {path}")
    observed_hash = sha256_file(path)
    if observed_hash != artifact["sha256"]:
        raise EvidenceValidationError(
            "Governed production seed hash mismatch: "
            f"expected {artifact['sha256']}, observed {observed_hash}"
        )
    return path, manifest


def product_values_from_canonical_sql() -> dict[str, Decimal]:
    text = LOSS_VALUE_SQL.read_text(encoding="utf-8")
    matches = re.findall(
        r"\('([^']+)'\s*,\s*([0-9]+(?:\.[0-9]+)?)\s*,"
        r"\s*'STANDARD_UNIT_OPPORTUNITY_VALUE'",
        text,
    )
    values = {product_code: Decimal(value) for product_code, value in matches}
    if len(values) != 6:
        raise EvidenceValidationError(
            f"Expected six product opportunity values in {LOSS_VALUE_SQL}, found {len(values)}"
        )
    if any(value < 0 for value in values.values()):
        raise EvidenceValidationError("Canonical product opportunity values must be nonnegative")
    return values


def site_names() -> dict[str, str]:
    with SITE_REGISTRY.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    names = {row["site_code"]: row["site_name"] for row in rows}
    if len(names) != 6:
        raise EvidenceValidationError(
            f"Expected six sites in {SITE_REGISTRY}, found {len(names)}"
        )
    return names


def canonical_site_calculation() -> tuple[list[dict[str, str]], Decimal]:
    production_path, _ = governed_production_path()
    production = pd.read_parquet(production_path)
    required = {
        "site_code",
        "product_code",
        "timestamp_start",
        "planned_production_time_min",
        "operating_time_min",
        "nominal_rate",
        "actual_quantity",
        "reject_quantity",
    }
    missing = sorted(required - set(production.columns))
    if missing:
        raise EvidenceValidationError(
            f"Governed production seed lacks opportunity fields: {missing}"
        )

    starts = pd.to_datetime(production["timestamp_start"])
    period_start = starts.min().date().isoformat()
    period_end = starts.max().date().isoformat()
    if period_start != EXPECTED_PERIOD_START or period_end != EXPECTED_PERIOD_END:
        raise EvidenceValidationError(
            "Canonical production period mismatch: "
            f"expected {EXPECTED_PERIOD_START} through {EXPECTED_PERIOD_END}, "
            f"observed {period_start} through {period_end}"
        )

    values = product_values_from_canonical_sql()
    names = site_names()
    totals = {site_code: Decimal("0") for site_code in names}

    for row in production.itertuples(index=False):
        if row.site_code not in totals:
            raise EvidenceValidationError(f"Unknown production site: {row.site_code}")
        if row.product_code not in values:
            raise EvidenceValidationError(
                f"No canonical opportunity value for product {row.product_code}"
            )

        nominal_rate = Decimal(int(row.nominal_rate))
        planned_capacity = (
            Decimal(str(row.planned_production_time_min)) * nominal_rate / Decimal("60")
        )
        operating_capacity = (
            Decimal(str(row.operating_time_min)) * nominal_rate / Decimal("60")
        )
        availability_loss = max(planned_capacity - operating_capacity, Decimal("0"))
        performance_loss = max(
            operating_capacity - Decimal(int(row.actual_quantity)), Decimal("0")
        )
        quality_loss = Decimal(int(row.reject_quantity))
        technical_loss = availability_loss + performance_loss + quality_loss
        totals[row.site_code] += technical_loss * values[row.product_code]

    records = []
    for site_code, opportunity in sorted(
        totals.items(), key=lambda item: (-item[1], item[0])
    ):
        records.append(
            {
                "site_code": site_code,
                "site_name": names[site_code],
                "analysis_period_start": period_start,
                "analysis_period_end": period_end,
                "analysis_period": EXPECTED_PERIOD_LABEL,
                "technical_opportunity_eur": f"{quantize_eur(opportunity):.2f}",
                "currency": CURRENCY,
                "opportunity_type": "MODELED_TECHNICAL_OPPORTUNITY",
                "realization_status": "NOT_REALIZED",
                "calculation_source_reference": (
                    "public.vw_site_loss_summary.total_technical_opportunity_eur; "
                    "sql/analytics/110_create_production_loss_views.sql"
                ),
                "evidence_version": EVIDENCE_VERSION,
            }
        )

    total = quantize_eur(sum(totals.values(), Decimal("0")))
    validate_site_records(records, records, total)
    return records, total


def sensitivity_records(two_year_total: Decimal) -> tuple[list[dict[str, str]], Decimal]:
    annualized_base = quantize_eur(two_year_total / TWO)
    records = []
    for rate_label, rate in REALIZATION_RATES:
        records.append(
            {
                "realization_rate_pct": rate_label,
                "annualized_technical_opportunity_base_eur": f"{annualized_base:.2f}",
                "illustrative_annual_value_eur": f"{quantize_eur(annualized_base * rate):.2f}",
                "currency": CURRENCY,
                "scenario_type": "ILLUSTRATIVE_REALIZATION_SENSITIVITY",
                "realization_status": "NOT_REALIZED",
                "analysis_period_basis": (
                    "Simple annualization of 2024-2025 modeled technical opportunity"
                ),
                "evidence_version": EVIDENCE_VERSION,
            }
        )
    return records, annualized_base


def read_csv_records(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise EvidenceValidationError(f"Evidence CSV is missing: {path}")
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def validate_site_records(
    observed: list[dict[str, str]],
    expected: list[dict[str, str]],
    expected_total: Decimal,
) -> None:
    if len(observed) != 6:
        raise EvidenceValidationError(f"Expected six site rows, observed {len(observed)}")
    site_codes = [row.get("site_code", "") for row in observed]
    if len(set(site_codes)) != 6 or any(not value for value in site_codes):
        raise EvidenceValidationError("Site export contains duplicate or null site codes")
    required = {
        "site_code",
        "site_name",
        "analysis_period_start",
        "analysis_period_end",
        "analysis_period",
        "technical_opportunity_eur",
        "currency",
        "opportunity_type",
        "realization_status",
        "calculation_source_reference",
        "evidence_version",
    }
    for row in observed:
        missing = sorted(column for column in required if not row.get(column))
        if missing:
            raise EvidenceValidationError(
                f"Site {row.get('site_code')!r} has null required values: {missing}"
            )
        try:
            value = Decimal(row["technical_opportunity_eur"])
        except InvalidOperation as exc:
            raise EvidenceValidationError(
                f"Site {row['site_code']} has a nonnumeric technical opportunity"
            ) from exc
        if not value.is_finite() or value < 0:
            raise EvidenceValidationError(
                f"Site {row['site_code']} has an invalid technical opportunity"
            )
        if (
            row["analysis_period_start"] != EXPECTED_PERIOD_START
            or row["analysis_period_end"] != EXPECTED_PERIOD_END
            or row["analysis_period"] != EXPECTED_PERIOD_LABEL
        ):
            raise EvidenceValidationError(
                f"Site {row['site_code']} has an incorrect analysis period"
            )
        if row["currency"] != CURRENCY:
            raise EvidenceValidationError(f"Site {row['site_code']} is not denominated in EUR")

    observed_by_site = {row["site_code"]: row for row in observed}
    expected_by_site = {row["site_code"]: row for row in expected}
    if observed_by_site != expected_by_site:
        raise EvidenceValidationError(
            "Site evidence does not match the canonical SQL-equivalent calculation"
        )
    observed_total = sum(
        (Decimal(row["technical_opportunity_eur"]) for row in observed),
        Decimal("0"),
    )
    if observed_total != expected_total:
        raise EvidenceValidationError(
            f"Site sum {observed_total} does not reconcile to {expected_total}"
        )


def validate_sensitivity_records(
    observed: list[dict[str, str]],
    expected: list[dict[str, str]],
) -> None:
    if len(observed) != len(REALIZATION_RATES):
        raise EvidenceValidationError(
            f"Expected {len(REALIZATION_RATES)} sensitivity rows, observed {len(observed)}"
        )
    if observed != expected:
        raise EvidenceValidationError(
            "Annual sensitivity export does not reconcile to the annualized base"
        )


def atomic_write_csv(path: Path, records: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(records[0])
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="",
        delete=False,
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".tmp",
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
        temporary = Path(stream.name)
    temporary.replace(path)


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".tmp",
    ) as stream:
        json.dump(payload, stream, indent=2)
        stream.write("\n")
        temporary = Path(stream.name)
    temporary.replace(path)


def generate() -> None:
    site_records, two_year_total = canonical_site_calculation()
    scenarios, annualized_base = sensitivity_records(two_year_total)

    atomic_write_csv(SITE_EXPORT, site_records)
    atomic_write_csv(SENSITIVITY_EXPORT, scenarios)

    production_path, production_manifest = governed_production_path()
    payload = {
        "manifest_version": "1.0",
        "evidence_version": EVIDENCE_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_period": {
            "start": EXPECTED_PERIOD_START,
            "end": EXPECTED_PERIOD_END,
            "label": EXPECTED_PERIOD_LABEL,
            "years": 2,
        },
        "provenance": {
            "data_class": "SYNTHETIC_OPERATIONAL",
            "opportunity_type": "MODELED_TECHNICAL_OPPORTUNITY",
            "realization_status": "NOT_REALIZED",
            "statement": (
                "Technical/model-derived opportunity for prioritization; not "
                "realized savings, revenue, margin, forecast, ROI, or payback."
            ),
        },
        "canonical_calculation": {
            "database_view": "public.vw_site_loss_summary",
            "field": "total_technical_opportunity_eur",
            "upstream_view": "public.vw_shift_production_loss",
            "sql_path": str(OPPORTUNITY_SQL.relative_to(REPO_ROOT)).replace("\\", "/"),
            "sql_sha256": sha256_file(OPPORTUNITY_SQL),
            "upstream_sql_path": str(OEE_SQL.relative_to(REPO_ROOT)).replace("\\", "/"),
            "upstream_sql_sha256": sha256_file(OEE_SQL),
            "loss_value_sql_path": str(LOSS_VALUE_SQL.relative_to(REPO_ROOT)).replace("\\", "/"),
            "loss_value_sql_sha256": sha256_file(LOSS_VALUE_SQL),
            "formula": (
                "(availability_loss_units_exact + performance_loss_units_exact + "
                "quality_loss_units_exact) * standard_loss_value_eur_per_unit"
            ),
        },
        "source_artifacts": {
            "production_path": str(production_path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "production_sha256": sha256_file(production_path),
            "production_content_fingerprint": production_manifest["artifact"][
                "content_fingerprint"
            ]["sha256"],
            "site_registry_path": str(SITE_REGISTRY.relative_to(REPO_ROOT)).replace("\\", "/"),
            "site_registry_sha256": sha256_file(SITE_REGISTRY),
        },
        "results": {
            "site_rows": len(site_records),
            "enterprise_two_year_technical_opportunity_eur": f"{two_year_total:.2f}",
            "simple_annualized_technical_opportunity_base_eur": f"{annualized_base:.2f}",
            "currency": CURRENCY,
        },
        "annualization": {
            "method": "SIMPLE_TWO_YEAR_AVERAGE",
            "base_formula": "enterprise_two_year_technical_opportunity_eur / 2",
            "scenario_formula": (
                "simple_annualized_technical_opportunity_base_eur * "
                "realization_rate"
            ),
            "interpretation": (
                "Illustrative arithmetic sensitivity; not a forecast or "
                "realized savings."
            ),
        },
        "outputs": {
            "site_export": {
                "path": str(SITE_EXPORT.relative_to(REPO_ROOT)).replace("\\", "/"),
                "sha256": sha256_file(SITE_EXPORT),
            },
            "annual_sensitivity_export": {
                "path": str(SENSITIVITY_EXPORT.relative_to(REPO_ROOT)).replace("\\", "/"),
                "sha256": sha256_file(SENSITIVITY_EXPORT),
            },
        },
    }
    atomic_write_json(EVIDENCE_MANIFEST, payload)
    validate_existing()


def validate_existing() -> None:
    expected_sites, two_year_total = canonical_site_calculation()
    expected_sensitivity, annualized_base = sensitivity_records(two_year_total)
    observed_sites = read_csv_records(SITE_EXPORT)
    observed_sensitivity = read_csv_records(SENSITIVITY_EXPORT)
    validate_site_records(observed_sites, expected_sites, two_year_total)
    validate_sensitivity_records(observed_sensitivity, expected_sensitivity)

    manifest = load_json(EVIDENCE_MANIFEST)
    if manifest.get("evidence_version") != EVIDENCE_VERSION:
        raise EvidenceValidationError("Evidence manifest version mismatch")
    results = manifest.get("results", {})
    if Decimal(results.get("enterprise_two_year_technical_opportunity_eur", "NaN")) != two_year_total:
        raise EvidenceValidationError("Manifest two-year total does not reconcile")
    if Decimal(results.get("simple_annualized_technical_opportunity_base_eur", "NaN")) != annualized_base:
        raise EvidenceValidationError("Manifest annualized base does not reconcile")

    for key, path in (
        ("site_export", SITE_EXPORT),
        ("annual_sensitivity_export", SENSITIVITY_EXPORT),
    ):
        expected_hash = manifest.get("outputs", {}).get(key, {}).get("sha256")
        if expected_hash != sha256_file(path):
            raise EvidenceValidationError(f"Manifest hash mismatch for {path}")

    print(
        "PASS: business-case evidence validated "
        f"(6 sites; 2024-2025 total EUR {two_year_total:.2f}; "
        f"annualized base EUR {annualized_base:.2f})."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate or validate canonical business-case opportunity evidence."
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate retained exports without rewriting them.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.validate_only:
            validate_existing()
        else:
            generate()
            print(f"Wrote {SITE_EXPORT.relative_to(REPO_ROOT)}")
            print(f"Wrote {SENSITIVITY_EXPORT.relative_to(REPO_ROOT)}")
            print(f"Wrote {EVIDENCE_MANIFEST.relative_to(REPO_ROOT)}")
        return 0
    except (EvidenceValidationError, InvalidOperation, KeyError, OSError, ValueError) as exc:
        print(f"FAIL: business-case evidence validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
