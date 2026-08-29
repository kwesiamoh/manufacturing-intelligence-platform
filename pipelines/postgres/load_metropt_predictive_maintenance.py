from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd
import psycopg

from connection_auth import connection_parameters


ROOT = Path(__file__).resolve().parents[2]
TELEMETRY_PATH = (
    ROOT
    / "data"
    / "silver"
    / "synthetic_enterprise"
    / "telemetry"
    / "metropt_enterprise_telemetry.parquet"
)
WARNING_PATH = (
    ROOT
    / "data"
    / "gold"
    / "advanced_analytics"
    / "metropt_predictive_maintenance"
    / "metropt_enterprise_warning_events.csv"
)
KPI_PATH = (
    ROOT
    / "data"
    / "gold"
    / "advanced_analytics"
    / "metropt_predictive_maintenance"
    / "metropt_predictive_maintenance_kpis.csv"
)
SOURCE_SEED = ROOT / "data_model" / "source_mapping" / "source_dataset_seed.csv"

SITE_CODE = "SITE-DE-01"
EQUIPMENT_CODE = "SITE-DE-01-U-AIR-01"
EXPECTED_LINEAGE = {
    "source_dataset_code": "METROPT3",
    "source_data_origin": "EXTERNAL_REAL",
    "scenario_type": "SYNTHETIC_ENTERPRISE_ADAPTATION",
    "transformation_basis": "METROPT_INFORMED",
    "degradation_signal_origin": "SYNTHETIC_CONTROLLED",
}


def nullable(value):
    return None if pd.isna(value) else value


def timestamp(value):
    if pd.isna(value):
        return None
    result = pd.Timestamp(value)
    if result.tzinfo is not None:
        result = result.tz_convert("UTC").tz_localize(None)
    return result.to_pydatetime(warn=False)


def validate_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    missing = [path for path in (TELEMETRY_PATH, WARNING_PATH, KPI_PATH, SOURCE_SEED) if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing MetroPT PdM inputs: " + ", ".join(str(path) for path in missing))

    telemetry = pd.read_parquet(TELEMETRY_PATH)
    warnings = pd.read_csv(WARNING_PATH, parse_dates=["warning_timestamp", "fault_onset_timestamp", "fault_end_timestamp"])
    kpis = pd.read_csv(KPI_PATH)

    if telemetry.empty or warnings.empty or kpis.empty:
        raise ValueError("MetroPT PdM inputs must all be non-empty")
    if telemetry.duplicated(["equipment_code", "event_timestamp"]).any():
        raise ValueError("Enterprise telemetry contains duplicate equipment/timestamp keys")
    if not telemetry["event_timestamp"].is_monotonic_increasing:
        raise ValueError("Enterprise telemetry timestamps are not ordered")
    if not (pd.to_datetime(telemetry["event_timestamp"]) > pd.to_datetime(telemetry["source_event_timestamp"])).all():
        raise ValueError("Enterprise calendar mapping is invalid")
    if set(telemetry["site_code"].unique()) != {SITE_CODE}:
        raise ValueError("Unexpected enterprise site mapping")
    if set(telemetry["equipment_code"].unique()) != {EQUIPMENT_CODE}:
        raise ValueError("Unexpected enterprise equipment mapping")
    for column, expected in EXPECTED_LINEAGE.items():
        if set(telemetry[column].dropna().unique()) != {expected}:
            raise ValueError(f"Telemetry lineage mismatch for {column}")
        if set(warnings[column].dropna().unique()) != {expected}:
            raise ValueError(f"Warning-event lineage mismatch for {column}")
    if not (warnings["warning_timestamp"] < warnings["fault_onset_timestamp"]).all():
        raise ValueError("Every warning timestamp must precede its fault onset")
    if not (warnings["warning_lead_time_hours"] >= 0).all():
        raise ValueError("Warning lead times must be non-negative")
    if not set(kpis["warning_horizon_hours"].unique()).issubset({2, 4, 6}):
        raise ValueError("Unexpected warning horizon in KPI input")
    if kpis.loc[kpis["is_selected"]].shape[0] != 2:
        raise ValueError("Expected one selected real policy and one selected synthetic policy")

    return telemetry, warnings, kpis


def seed_metropt_sources(cursor) -> tuple[int, int]:
    with SOURCE_SEED.open(newline="", encoding="utf-8-sig") as stream:
        rows = {
            row["source_code"]: row
            for row in csv.DictReader(stream)
            if row["source_code"] in {"METROPT3", "METROPT3_ENTERPRISE_PDM"}
        }
    if set(rows) != {"METROPT3", "METROPT3_ENTERPRISE_PDM"}:
        raise RuntimeError("MetroPT source seed rows are incomplete")

    for row in rows.values():
        cursor.execute(
            """
            INSERT INTO public.dim_source_dataset (
                source_code, source_name, publisher, source_domain,
                integration_role, is_real_data, source_url, reference_period, notes
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (source_code) DO UPDATE SET
                source_name = EXCLUDED.source_name,
                publisher = EXCLUDED.publisher,
                source_domain = EXCLUDED.source_domain,
                integration_role = EXCLUDED.integration_role,
                is_real_data = EXCLUDED.is_real_data,
                source_url = EXCLUDED.source_url,
                reference_period = EXCLUDED.reference_period,
                notes = EXCLUDED.notes
            """,
            (
                row["source_code"],
                row["source_name"],
                nullable(row["publisher"]),
                row["source_domain"],
                row["integration_role"],
                row["is_real_data"].strip().lower() == "true",
                nullable(row["source_url"]),
                nullable(row["reference_period"]),
                nullable(row["notes"]),
            ),
        )

    cursor.execute(
        "SELECT source_code, source_dataset_id FROM public.dim_source_dataset WHERE source_code IN ('METROPT3','METROPT3_ENTERPRISE_PDM')"
    )
    source_ids = dict(cursor.fetchall())
    return source_ids["METROPT3"], source_ids["METROPT3_ENTERPRISE_PDM"]


def resolve_mapping(cursor) -> tuple[int, int]:
    cursor.execute(
        """
        SELECT s.site_id, e.equipment_id
        FROM public.dim_site s
        JOIN public.dim_area a ON a.site_id = s.site_id
        JOIN public.dim_equipment e ON e.area_id = a.area_id
        WHERE s.site_code = %s
          AND e.equipment_code = %s
          AND e.equipment_type = 'COMPRESSED_AIR_SYSTEM'
        """,
        (SITE_CODE, EQUIPMENT_CODE),
    )
    rows = cursor.fetchall()
    if len(rows) != 1:
        raise RuntimeError("Expected exactly one governed compressed-air equipment mapping")
    return rows[0]


def load_telemetry(cursor, frame, site_id, equipment_id, source_id, scenario_source_id):
    statement = """
        INSERT INTO analytics.metropt_enterprise_telemetry (
            event_timestamp, source_event_timestamp, site_id, equipment_id,
            source_dataset_id, scenario_source_dataset_id, tp2_pressure_bar,
            tp3_pressure_bar, reservoir_pressure_bar, oil_temperature_c,
            motor_current_a, pressure_delta_bar, reservoir_pressure_slope_60m,
            oil_temperature_slope_60m, motor_current_slope_60m, anomaly_score,
            degradation_index, condition_score, precursor_failure_id,
            source_fault_event_id, fault_state, condition_state,
            selected_warning_state, selected_warning_horizon_hours,
            source_data_origin, scenario_type, transformation_basis,
            degradation_signal_origin
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    batch = []
    for row in frame.itertuples(index=False):
        batch.append(
            (
                timestamp(row.event_timestamp), timestamp(row.source_event_timestamp),
                site_id, equipment_id, source_id, scenario_source_id,
                row.tp2_pressure_bar, row.tp3_pressure_bar, row.reservoir_pressure_bar,
                row.oil_temperature_c, row.motor_current_a, row.pressure_delta_bar,
                row.reservoir_pressure_slope_60m, row.oil_temperature_slope_60m,
                row.motor_current_slope_60m, row.anomaly_score, row.degradation_index,
                row.condition_score, nullable(row.precursor_failure_id),
                nullable(row.source_fault_event_id), bool(row.fault_state), row.condition_state,
                bool(row.selected_warning_state), int(row.selected_warning_horizon_hours),
                row.source_data_origin, row.scenario_type, row.transformation_basis,
                row.degradation_signal_origin,
            )
        )
        if len(batch) == 2000:
            cursor.executemany(statement, batch)
            batch.clear()
    if batch:
        cursor.executemany(statement, batch)


def load_warnings(cursor, frame, site_id, equipment_id, source_id, scenario_source_id):
    statement = """
        INSERT INTO analytics.metropt_pdm_warning_event (
            failure_id, scenario_scope, site_id, equipment_id, source_dataset_id,
            scenario_source_dataset_id, warning_timestamp, fault_onset_timestamp,
            fault_end_timestamp, warning_horizon_hours, warning_lead_time_hours,
            warning_outcome, warning_persistence, source_data_origin, scenario_type,
            transformation_basis, degradation_signal_origin
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    rows = [
        (
            str(row.failure_id), row.scenario_scope, site_id, equipment_id, source_id,
            scenario_source_id, timestamp(row.warning_timestamp),
            timestamp(row.fault_onset_timestamp), timestamp(row.fault_end_timestamp),
            int(row.warning_horizon_hours), nullable(row.warning_lead_time_hours),
            row.warning_outcome, row.warning_persistence, row.source_data_origin,
            row.scenario_type, row.transformation_basis, row.degradation_signal_origin,
        )
        for row in frame.itertuples(index=False)
    ]
    cursor.executemany(statement, rows)


def load_kpis(cursor, frame):
    statement = """
        INSERT INTO analytics.metropt_pdm_policy_kpi (
            scenario_scope, model_name, policy_name, evaluation_split,
            warning_horizon_hours, events_evaluated, events_warned, events_missed,
            warning_success_rate, average_lead_time_hours, median_lead_time_hours,
            precision_value, recall_value, false_alerts,
            false_alerts_per_operating_day, alert_episodes, operating_days, is_selected
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    rows = [
        (
            row.scenario_scope, row.model_name, row.policy, row.split,
            int(row.warning_horizon_hours), int(row.events_evaluated),
            int(row.events_warned), int(row.events_missed), row.warning_success_rate,
            nullable(row.average_lead_time_hours), nullable(row.median_lead_time_hours),
            row.precision, row.recall, int(row.false_alerts),
            row.false_alerts_per_operating_day, int(row.alert_episodes),
            row.operating_days, bool(row.is_selected),
        )
        for row in frame.itertuples(index=False)
    ]
    cursor.executemany(statement, rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5433)
    parser.add_argument("--dbname", default="manufacturing_intelligence")
    parser.add_argument("--user", default="postgres")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    telemetry, warnings, kpis = validate_inputs()
    print(f"Validated enterprise telemetry: {len(telemetry):,} rows")
    print(f"Validated warning events: {len(warnings):,} rows")
    print(f"Validated policy KPI rows: {len(kpis):,} rows")
    if args.validate_only:
        return

    with psycopg.connect(**connection_parameters(args)) as connection:
        with connection.cursor() as cursor:
            source_id, scenario_source_id = seed_metropt_sources(cursor)
            site_id, equipment_id = resolve_mapping(cursor)
            cursor.execute("TRUNCATE analytics.metropt_enterprise_telemetry")
            cursor.execute("TRUNCATE analytics.metropt_pdm_warning_event")
            cursor.execute("TRUNCATE analytics.metropt_pdm_policy_kpi")
            load_telemetry(cursor, telemetry, site_id, equipment_id, source_id, scenario_source_id)
            load_warnings(cursor, warnings, site_id, equipment_id, source_id, scenario_source_id)
            load_kpis(cursor, kpis)

            cursor.execute("SELECT COUNT(*) FROM analytics.metropt_enterprise_telemetry")
            telemetry_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM analytics.metropt_pdm_warning_event")
            warning_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM analytics.metropt_pdm_policy_kpi")
            kpi_count = cursor.fetchone()[0]
            if (telemetry_count, warning_count, kpi_count) != (len(telemetry), len(warnings), len(kpis)):
                raise RuntimeError("PostgreSQL row counts do not match the validated inputs")

    print(f"Loaded mapping: {SITE_CODE} / {EQUIPMENT_CODE}")
    print("MetroPT predictive-maintenance PostgreSQL load complete")


if __name__ == "__main__":
    main()
