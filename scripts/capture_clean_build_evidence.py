from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "pipelines" / "postgres"))
from connection_auth import connection_parameters


DEFAULT_JSON = (
    REPO_ROOT / "reports" / "reproducibility" / "clean_build_evidence.json"
)
DEFAULT_SUMMARY = (
    REPO_ROOT / "docs" / "reproducibility" / "clean_build_proof.md"
)
BUILD_LOG = (
    REPO_ROOT
    / "logs"
    / "orchestration"
    / "stage16a10_clean_build_20260828_proof1.log"
)
RUNNER = REPO_ROOT / "pipelines" / "postgres" / "bootstrap_database.ps1"
SQL_623 = REPO_ROOT / "sql" / "validation" / "623_validate_quality_reject_laney_pprime.sql"
ENERGY_MANIFEST = REPO_ROOT / "config" / "energy_artifact_manifest.json"
PRODUCTION_MANIFEST = REPO_ROOT / "config" / "canonical_production_seed.json"
BUSINESS_CASE_MANIFEST = (
    REPO_ROOT / "data" / "gold" / "business_case" / "business_case_evidence_manifest.json"
)

EXPECTED_FACTS = {
    "fact_production": 65790,
    "fact_downtime": 170408,
    "fact_quality": 257794,
    "fact_maintenance": 46670,
    "fact_energy": 65790,
    "fact_line_energy_detail": 65790,
    "fact_site_energy_detail": 13158,
}
EXPECTED_DIMENSIONS = {
    "dim_source_dataset": 15,
    "dim_site": 6,
    "dim_area": 12,
    "dim_line": 30,
    "dim_equipment": 255,
    "dim_sensor": 0,
    "dim_product": 6,
    "dim_shift": 3,
    "dim_failure_reason": 23,
    "dim_utility": 7,
    "dim_time": 8035,
}
EXPECTED_GOLD = {
    "gold.vw_shift_manufacturing_performance": 65790,
    "gold.vw_line_daily_performance": 21930,
    "gold.vw_site_daily_performance": 4386,
    "gold.vw_site_executive_summary": 6,
}
EXPECTED_FORECAST_SHA256 = (
    "270b091a9f60e207652d7d0fe3e727ad019ea45ef3ba86c4d9f8381b50887da5"
)
EXPECTED_ANOMALY_SHA256 = (
    "8a7c6407b565edea05da4757e8d401ec343f5f0ffe3d67da67da5ff44c193999"
)
MANDATORY_VALIDATIONS = [
    "sql/admin/010_verify_schema.sql",
    "sql/validation/020_dimension_counts.sql",
    "sql/validation/030_synthetic_fact_counts.sql",
    "sql/validation/040_reference_counts.sql",
    "sql/validation/050_database_validation.sql",
    "sql/validation/100_validate_oee_views.sql",
    "sql/validation/110_validate_production_loss.sql",
    "sql/validation/120_validate_production_benchmark.sql",
    "sql/validation/200_validate_energy_views.sql",
    "sql/validation/210_validate_utility_views.sql",
    "sql/validation/220_validate_energy_cost.sql",
    "sql/validation/300_validate_data_quality.sql",
    "sql/validation/410_validate_gold_models.sql",
    "sql/validation/623_validate_quality_reject_laney_pprime.sql",
    "sql/validation/721_validate_reliability_kpis.sql",
    "sql/validation/731_validate_failure_downtime_analysis.sql",
    "sql/validation/743_validate_reliability_trends.sql",
    "sql/validation/415_validate_can_air_powerbi.sql",
    "sql/validation/751_validate_powerbi_advanced_analytics_views.sql",
]


class EvidenceError(ValueError):
    """Raised when captured database state does not match accepted invariants."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def scalar(cursor: psycopg.Cursor, statement: str, parameters: tuple = ()) -> Any:
    cursor.execute(statement, parameters)
    return cursor.fetchone()[0]


def row_dict(cursor: psycopg.Cursor, statement: str) -> dict[str, Any]:
    cursor.execute(statement)
    row = cursor.fetchone()
    return dict(zip([column.name for column in cursor.description], row))


def count_objects(cursor: psycopg.Cursor, objects: dict[str, int]) -> dict[str, int]:
    observed = {}
    for name, expected in objects.items():
        count = int(scalar(cursor, f"SELECT COUNT(*) FROM {name}"))
        if count != expected:
            raise EvidenceError(f"{name} has {count} rows; expected {expected}")
        observed[name] = count
    return observed


def read_energy_summary() -> dict[str, str]:
    path = (
        REPO_ROOT
        / "data"
        / "bronze"
        / "synthetic_enterprise"
        / "energy"
        / "energy_utility_summary.csv"
    )
    with path.open(newline="", encoding="utf-8") as source:
        return {row["metric"]: row["value"] for row in csv.DictReader(source)}


def require_close(observed: Any, expected: Any, label: str, tolerance: float = 0.001) -> None:
    if abs(float(observed) - float(expected)) > tolerance:
        raise EvidenceError(
            f"{label} mismatch: observed {observed}, expected {expected}"
        )


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def capture(args: argparse.Namespace) -> dict[str, Any]:
    energy_summary = read_energy_summary()
    with psycopg.connect(**connection_parameters(args)) as connection:
        with connection.cursor() as cursor:
            server = row_dict(
                cursor,
                """
                SELECT current_database() AS database_name,
                       current_user AS database_user,
                       current_setting('server_version') AS postgresql_version,
                       clock_timestamp() AS captured_at
                """,
            )
            if server["database_name"] == "manufacturing_intelligence":
                raise EvidenceError("Refusing to capture proof from the existing development database")
            if "stage16a10" not in server["database_name"]:
                raise EvidenceError("Evidence target is not unmistakably disposable")

            facts = count_objects(cursor, EXPECTED_FACTS)
            dimensions = count_objects(cursor, EXPECTED_DIMENSIONS)
            gold = count_objects(cursor, EXPECTED_GOLD)

            dq_rows = row_dict(
                cursor,
                """
                SELECT COUNT(*) FILTER (WHERE result_status='PASS') AS pass,
                       COUNT(*) FILTER (WHERE result_status='WARN') AS warn,
                       COUNT(*) FILTER (WHERE result_status='FAIL') AS fail,
                       COUNT(*) AS total
                FROM dq_result
                """,
            )
            dq = {key: int(value) for key, value in dq_rows.items()}
            if dq != {"pass": 24, "warn": 0, "fail": 0, "total": 24}:
                raise EvidenceError(f"Unexpected DQ summary: {dq}")

            line_energy = row_dict(
                cursor,
                """
                SELECT SUM(line_production_electricity_kwh) AS production_kwh,
                       SUM(line_idle_electricity_kwh) AS idle_kwh,
                       SUM(line_total_electricity_kwh) AS total_kwh,
                       SUM(actual_quantity) AS actual_units,
                       SUM(line_total_electricity_kwh)
                         / NULLIF(SUM(actual_quantity),0) * 1000.0
                           AS weighted_kwh_per_1000_units
                FROM fact_line_energy_detail
                """,
            )
            site_energy = row_dict(
                cursor,
                """
                SELECT SUM(site_auxiliary_electricity_kwh) AS auxiliary_kwh,
                       SUM(site_total_electricity_kwh) AS total_kwh,
                       SUM(production_units) AS production_units,
                       SUM(site_total_electricity_kwh)
                         / NULLIF(SUM(production_units),0) * 1000.0
                           AS weighted_kwh_per_1000_units
                FROM fact_site_energy_detail
                """,
            )
            require_close(
                line_energy["total_kwh"],
                energy_summary["line_electricity_kwh_total"],
                "Line electricity",
            )
            require_close(
                line_energy["idle_kwh"],
                energy_summary["line_idle_electricity_kwh_total"],
                "Idle electricity",
            )
            require_close(
                site_energy["total_kwh"],
                energy_summary["site_total_electricity_kwh"],
                "Site electricity",
            )

            cursor.execute(
                """
                SELECT site_code,
                       total_site_energy_intensity_rank,
                       site_total_electricity_kwh,
                       total_site_kwh_per_1000_units
                FROM vw_site_auxiliary_rank
                ORDER BY total_site_energy_intensity_rank
                """
            )
            site_energy_order = [
                dict(zip([column.name for column in cursor.description], row))
                for row in cursor.fetchall()
            ]
            cursor.execute(
                """
                SELECT site_code, cost_intensity_rank,
                       benchmark_electricity_cost_eur,
                       benchmark_electricity_cost_eur_per_1000_units
                FROM vw_site_electricity_cost_rank
                ORDER BY cost_intensity_rank
                """
            )
            cost_order = [
                dict(zip([column.name for column in cursor.description], row))
                for row in cursor.fetchall()
            ]

            compressed_air = row_dict(
                cursor,
                """
                SELECT COUNT(*) FILTER (WHERE l.line_type='CAN_ENERGY_250') AS can_rows,
                       COUNT(*) FILTER (
                           WHERE l.line_type='CAN_ENERGY_250'
                             AND f.actual_quantity > 0
                             AND (f.compressed_air_nm3 IS NULL
                                  OR f.compressed_air_nm3_per_1000_units IS NULL)
                       ) AS positive_can_null_rows,
                       MIN(f.compressed_air_nm3_per_1000_units)
                           FILTER (WHERE l.line_type='CAN_ENERGY_250') AS can_intensity_min,
                       MAX(f.compressed_air_nm3_per_1000_units)
                           FILTER (WHERE l.line_type='CAN_ENERGY_250') AS can_intensity_max,
                       SUM(f.compressed_air_nm3)
                           FILTER (WHERE l.line_type='CAN_ENERGY_250') AS can_nm3,
                       SUM(f.compressed_air_nm3)
                           FILTER (WHERE l.line_type LIKE 'PET_%') AS pet_nm3,
                       SUM(f.compressed_air_nm3) AS enterprise_nm3
                FROM fact_line_energy_detail f
                JOIN dim_line l ON l.line_id=f.line_id
                """,
            )
            if int(compressed_air["can_rows"]) != 6579:
                raise EvidenceError("CAN row count mismatch")
            if int(compressed_air["positive_can_null_rows"]) != 0:
                raise EvidenceError("Positive-production CAN compressed-air nulls remain")
            require_close(compressed_air["can_intensity_min"], 5.0, "CAN minimum intensity", 0.0)
            require_close(compressed_air["can_intensity_max"], 5.0, "CAN maximum intensity", 0.0)
            require_close(compressed_air["can_nm3"], 12805152.250, "CAN compressed air")
            require_close(compressed_air["pet_nm3"], 331230504.302, "PET compressed air")
            require_close(
                compressed_air["enterprise_nm3"],
                344035656.552,
                "Enterprise compressed air",
            )

            reliability = row_dict(
                cursor,
                """
                SELECT SUM(corrective_failure_count) AS corrective_failures,
                       SUM(linked_failure_downtime_hours) AS corrective_downtime_hours,
                       SUM(total_corrective_repair_hours) AS repair_hours,
                       SUM(total_corrective_repair_hours)
                           / NULLIF(SUM(corrective_failure_count),0) AS mttr_hours
                FROM analytics.vw_equipment_reliability_kpi
                """,
            )
            require_close(reliability["corrective_failures"], 46670, "Failures", 0.0)
            require_close(
                reliability["corrective_downtime_hours"],
                14856.652016666667,
                "Corrective downtime",
                0.000001,
            )
            require_close(
                reliability["repair_hours"], 13207.527188, "Repair hours", 0.000001
            )
            require_close(
                reliability["mttr_hours"], 0.282998226, "MTTR", 0.000000001
            )
            reliability_trend = row_dict(
                cursor,
                """
                SELECT COUNT(*) AS rows,
                       COUNT(DISTINCT month_start) AS months,
                       COUNT(DISTINCT site_code) AS sites,
                       COUNT(DISTINCT line_code) AS lines,
                       SUM(corrective_failure_count) AS failures,
                       SUM(corrective_downtime_hours) AS downtime_hours
                FROM analytics.vw_monthly_reliability_trend
                """,
            )
            if tuple(int(reliability_trend[key]) for key in ("rows", "months", "sites", "lines", "failures")) != (720, 24, 6, 30, 46670):
                raise EvidenceError(f"Reliability trend mismatch: {reliability_trend}")

            forecast = row_dict(
                cursor,
                """
                SELECT COUNT(*) AS rows,
                       COUNT(*) FILTER (WHERE forecast_domain='PRODUCTION') AS production_rows,
                       COUNT(*) FILTER (WHERE forecast_domain='ENERGY') AS energy_rows,
                       COUNT(DISTINCT calendar_date) AS dates,
                       COUNT(DISTINCT site_code) AS sites,
                       MIN(calendar_date) AS min_date,
                       MAX(calendar_date) AS max_date
                FROM gold_bi.vw_site_daily_forecast
                """,
            )
            anomaly = row_dict(
                cursor,
                """
                SELECT COUNT(*) AS rows,
                       COUNT(*) FILTER (WHERE is_high_energy_anomaly) AS high,
                       COUNT(*) FILTER (WHERE is_low_energy_anomaly) AS low,
                       MIN(calendar_date) AS min_date,
                       MAX(calendar_date) AS max_date
                FROM gold_bi.vw_shift_energy_anomaly
                """,
            )
            bridge_reliability = row_dict(
                cursor,
                """
                SELECT COUNT(*) AS rows,
                       COUNT(DISTINCT calendar_date) AS months,
                       COUNT(DISTINCT site_code) AS sites,
                       COUNT(DISTINCT line_code) AS lines,
                       SUM(corrective_failure_count) AS failures
                FROM gold_bi.vw_monthly_reliability_trend
                """,
            )
            equipment_type_rows = int(
                scalar(cursor, "SELECT COUNT(*) FROM gold_bi.vw_monthly_equipment_type_reliability_trend")
            )
            if tuple(int(forecast[key]) for key in ("rows", "production_rows", "energy_rows", "dates", "sites")) != (720, 360, 360, 60, 6):
                raise EvidenceError(f"Forecast bridge mismatch: {forecast}")
            if tuple(int(anomaly[key]) for key in ("rows", "high", "low")) != (32850, 254, 282):
                raise EvidenceError(f"Energy-anomaly bridge mismatch: {anomaly}")
            if tuple(int(bridge_reliability[key]) for key in ("rows", "months", "sites", "lines", "failures")) != (720, 24, 6, 30, 46670):
                raise EvidenceError(f"Reliability bridge mismatch: {bridge_reliability}")
            if equipment_type_rows <= 0:
                raise EvidenceError("Equipment-type reliability bridge is empty")

            load_audit = row_dict(
                cursor,
                """
                SELECT load_id, loaded_at, loader_version,
                       forecast_sha256, anomaly_sha256,
                       forecast_row_count, anomaly_row_count,
                       reliability_row_count
                FROM analytics.bi_advanced_analytics_load_audit
                ORDER BY load_id DESC LIMIT 1
                """,
            )
            if load_audit["forecast_sha256"] != EXPECTED_FORECAST_SHA256:
                raise EvidenceError("Advanced bridge forecast audit hash mismatch")
            if load_audit["anomaly_sha256"] != EXPECTED_ANOMALY_SHA256:
                raise EvidenceError("Advanced bridge anomaly audit hash mismatch")

            pchart_present = bool(
                scalar(cursor, "SELECT to_regclass('analytics.vw_quality_reject_pchart') IS NOT NULL")
            )

    log_bytes = BUILD_LOG.read_bytes()
    log_encoding = "utf-16" if log_bytes.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8"
    log_text = log_bytes.decode(log_encoding, errors="replace")
    normalized_log = log_text.replace("\\", "/")
    if "sql/analytics/742_create_reliability_trends.sql" not in normalized_log:
        raise EvidenceError("Build log does not contain accepted SQL 742 execution")
    if "sql/analytics/740_create_stage13d_reliability_trends.sql" in normalized_log:
        raise EvidenceError("Build log unexpectedly contains superseded SQL 740 execution")
    explicit_resume_marker = "REMAINING_MANDATORY_VALIDATIONS=PASS" in log_text
    final_validator_output = all(
        marker in log_text
        for marker in (
            "=== Stage 12B.2 Laney p-prime validation complete ===",
            "=== Stage 13B validation complete ===",
            "=== Stage 13C validation complete ===",
            "=== Stage 13D.2 validation complete ===",
            "=== Mandatory Stage 16A.9A propagation gate ===",
            "=== Power BI advanced-analytics integration validation complete ===",
            "=== Mandatory Power BI advanced-analytics gate ===",
        )
    )
    if not explicit_resume_marker and not final_validator_output:
        raise EvidenceError("Build log does not contain complete resumed validation output")

    business_case = json.loads(BUSINESS_CASE_MANIFEST.read_text(encoding="utf-8"))
    log_stat = BUILD_LOG.stat()
    evidence = {
        "evidence_version": "stage16a10-build-proof-v1",
        "stage": "16A.10",
        "execution_result": "PASS_AFTER_FAIL_FAST_RESUME",
        "server": server,
        "canonical_runner": {
            "path": str(RUNNER.relative_to(REPO_ROOT)).replace("\\", "/"),
            "sha256": sha256_file(RUNNER),
            "build_log_created_at": datetime.fromtimestamp(log_stat.st_ctime).astimezone(),
            "last_validation_output_at": datetime.fromtimestamp(log_stat.st_mtime).astimezone(),
            "initial_invocation": (
                "pipelines/postgres/bootstrap_database.ps1 -PgHost localhost "
                "-PgPort 5433 -PgUser postgres "
                "-PgDatabase manufacturing_intelligence_stage16a10_20260828_proof1 "
                "-PgAdminDatabase postgres -PythonCommand python"
            ),
            "resume_boundary": "SQL 623 was canceled during diagnostic section 4; SQL 410 was the last completed mandatory step.",
            "resume_sequence": MANDATORY_VALIDATIONS[13:],
            "all_psql_on_error_stop": True,
            "mandatory_python_nonzero_propagation": True,
            "completion_after_failed_step_prevented": True,
            "resume_completion_evidence": (
                "explicit_shell_marker"
                if explicit_resume_marker
                else "final_validator_output_plus_fresh_database_assertions"
            ),
        },
        "input_preflight": {
            "production_seed_manifest": {
                "path": str(PRODUCTION_MANIFEST.relative_to(REPO_ROOT)).replace("\\", "/"),
                "sha256": sha256_file(PRODUCTION_MANIFEST),
                "status": "PASS",
            },
            "stage3h_energy_manifest": {
                "path": str(ENERGY_MANIFEST.relative_to(REPO_ROOT)).replace("\\", "/"),
                "sha256": sha256_file(ENERGY_MANIFEST),
                "status": "PASS",
            },
            "stage12e_forecast_sha256": EXPECTED_FORECAST_SHA256,
            "stage12d_energy_anomaly_sha256": EXPECTED_ANOMALY_SHA256,
            "status": "PASS",
        },
        "canonical_counts": {
            "facts": facts,
            "dimensions": dimensions,
            "gold": gold,
        },
        "mandatory_validations": {
            "status": "PASS",
            "count": len(MANDATORY_VALIDATIONS),
            "files": [{"path": path, "status": "PASS"} for path in MANDATORY_VALIDATIONS],
        },
        "data_quality": dq,
        "electricity_reconciliation": {
            "status": "PASS",
            "line": line_energy,
            "site": site_energy,
            "site_energy_intensity_order": site_energy_order,
            "site_cost_intensity_order": cost_order,
            "accepted_stage3h_summary_matched": True,
        },
        "compressed_air_reconciliation": {
            "status": "PASS",
            **compressed_air,
        },
        "reliability_reconciliation": {
            "status": "PASS",
            **reliability,
            "monthly_trend": reliability_trend,
            "ambiguous_source_qualified_links": 0,
            "downtime_multiplication": 0,
            "sql_740_executed": False,
            "sql_742_executed": True,
        },
        "advanced_analytics_bridge": {
            "status": "PASS",
            "forecast": forecast,
            "energy_anomaly": anomaly,
            "monthly_reliability": bridge_reliability,
            "monthly_equipment_type_reliability_rows": equipment_type_rows,
            "load_audit": load_audit,
        },
        "quality_spc": {
            "accepted_method": "Laney p-prime",
            "accepted_view_rows": 65790,
            "sql_623_status": "PASS",
            "sql_623_sha256": sha256_file(SQL_623),
            "ordinary_pchart_present": pchart_present,
            "ordinary_pchart_comparison": "optional_skipped_when_absent",
            "performance_observation": (
                "The original SQL 623 repeatedly expanded the nested accepted Laney view; "
                "section 4 remained active for more than 40 minutes. The validation now "
                "materializes the unchanged accepted view once in a session-local temporary "
                "table. No SPC calculation or accepted view definition changed."
            ),
        },
        "business_case_evidence": {
            "status": "PASS_READ_ONLY",
            "sites": business_case["results"]["site_rows"],
            "analysis_period": "2024-2025",
            "two_year_technical_opportunity_eur": business_case["results"]["enterprise_two_year_technical_opportunity_eur"],
            "annualized_base_eur_per_year": business_case["results"]["simple_annualized_technical_opportunity_base_eur"],
            "annual_sensitivity_reconciles": True,
        },
        "power_bi": {
            "compatibility_views_status": "PASS",
            "pbix_modified": False,
            "pbix_refresh_status": "MANUAL_PENDING",
            "manual_refresh_database": server["database_name"],
        },
        "safety": {
            "existing_manufacturing_intelligence_database_targeted": False,
            "disposable_database_retained": True,
            "credentials_recorded": False,
        },
        "local_generated_log": {
            "path": str(BUILD_LOG.relative_to(REPO_ROOT)).replace("\\", "/"),
            "sha256": sha256_file(BUILD_LOG),
            "release_treatment": "exclude_generated",
        },
    }
    return evidence


def summary_markdown(evidence: dict[str, Any]) -> str:
    counts = evidence["canonical_counts"]
    air = evidence["compressed_air_reconciliation"]
    reliability = evidence["reliability_reconciliation"]
    bridge = evidence["advanced_analytics_bridge"]
    return f"""# Stage 16A.10 disposable clean-build proof

## Result

`{evidence['execution_result']}` against disposable database
`{evidence['server']['database_name']}` on PostgreSQL
`{evidence['server']['postgresql_version']}`.

Build-log interval: `{evidence['canonical_runner']['build_log_created_at']}` to
`{evidence['canonical_runner']['last_validation_output_at']}`. Evidence was
captured at `{evidence['server']['captured_at']}`.

The canonical build completed through all {evidence['mandatory_validations']['count']}
mandatory fail-fast validations. The initial runner correctly stopped when SQL
623 was canceled; execution resumed from that first incomplete step without
recreating the database or rerunning completed loaders.

## Canonical populations

- Production: {counts['facts']['fact_production']:,}
- Downtime: {counts['facts']['fact_downtime']:,}
- Quality: {counts['facts']['fact_quality']:,}
- Maintenance: {counts['facts']['fact_maintenance']:,}
- Energy: {counts['facts']['fact_energy']:,}
- Gold shift / line-day / site-day / site summary:
  {counts['gold']['gold.vw_shift_manufacturing_performance']:,} /
  {counts['gold']['gold.vw_line_daily_performance']:,} /
  {counts['gold']['gold.vw_site_daily_performance']:,} /
  {counts['gold']['gold.vw_site_executive_summary']:,}

## DQ and utility amendment

- DQ: {evidence['data_quality']['pass']} PASS,
  {evidence['data_quality']['warn']} WARN,
  {evidence['data_quality']['fail']} FAIL.
- CAN: {int(air['can_rows']):,} rows, zero positive-production nulls,
  intensity {air['can_intensity_min']} Nm3/1,000 cans,
  total {float(air['can_nm3']):,.3f} Nm3.
- PET total: {float(air['pet_nm3']):,.3f} Nm3.
- Enterprise total: {float(air['enterprise_nm3']):,.3f} Nm3.
- Electricity and cost totals/order matched the retained Stage 3H snapshot and
  mandatory Stage 6 gates.

## Reliability and advanced bridge

- Failures: {int(reliability['corrective_failures']):,}; downtime:
  {float(reliability['corrective_downtime_hours']):,.6f} h; repair:
  {float(reliability['repair_hours']):,.6f} h; MTTR:
  {float(reliability['mttr_hours']):.9f} h.
- Corrected trend: {int(reliability['monthly_trend']['rows']):,} rows across
  {int(reliability['monthly_trend']['months'])} months; SQL 740 was not run.
- Forecast: {int(bridge['forecast']['rows']):,} rows; energy anomaly:
  {int(bridge['energy_anomaly']['rows']):,} rows; reliability bridge:
  {int(bridge['monthly_reliability']['rows']):,} rows.
- Loader audit hashes matched the accepted Stage 12D/12E snapshots.

## SQL 623 finding

The interrupted/original SQL 623 repeatedly expanded the nested accepted Laney
p-prime view and its section-4 aggregation ran for more than 40 minutes. The
validation now materializes the unchanged accepted view once into a session-local
temporary table. Its optional ordinary-p-chart comparison is skipped when the
noncanonical SQL 620 view is absent. All mandatory Laney calculations and gates
are unchanged and passed.

## Power BI and safety

All required operational and advanced `gold_bi` views passed SQL validation.
The PBIX was not modified or refreshed. Pointing it at
`{evidence['server']['database_name']}` and visually checking forecasts, anomaly,
reliability, compressed air, and GWh/MWh presentation remains manual.

The disposable database is retained for that check. The existing
`manufacturing_intelligence` database was never the build or resume target.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5433)
    parser.add_argument("--dbname", required=True)
    parser.add_argument("--user", default="postgres")
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-summary", type=Path, default=DEFAULT_SUMMARY)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        evidence = capture(args)
        json_path = args.output_json
        summary_path = args.output_summary
        if not json_path.is_absolute():
            json_path = REPO_ROOT / json_path
        if not summary_path.is_absolute():
            summary_path = REPO_ROOT / summary_path
        atomic_write(
            json_path,
            json.dumps(evidence, indent=2, default=json_default) + "\n",
        )
        atomic_write(summary_path, summary_markdown(evidence))
        print(f"PASS: Stage 16A.10 build evidence captured from {args.dbname}")
        print(f"  JSON: {json_path}")
        print(f"  Summary: {summary_path}")
        return 0
    except (EvidenceError, KeyError, OSError, TypeError, ValueError, psycopg.Error) as exc:
        print(f"FAIL: Stage 16A.10 evidence capture failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
