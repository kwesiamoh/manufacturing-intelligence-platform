from __future__ import annotations

import argparse
import hashlib
from io import StringIO
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import Json

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines" / "postgres"))
from connection_auth import connection_parameters


LOADER_VERSION = "16A.4"
FORECAST_TARGET_DOMAINS = {
    "daily_actual_quantity": "PRODUCTION",
    "daily_site_total_electricity_kwh": "ENERGY",
}
FORECAST_COLUMNS = [
    "calendar_date",
    "site_code",
    "site_name",
    "actual_value",
    "ml_forecast_value",
    "seasonal_naive_value",
    "selected_forecast_value",
    "forecast_target",
    "forecast_domain",
    "absolute_error",
    "absolute_pct_error",
]
ANOMALY_COLUMNS = [
    "production_id",
    "timestamp_start",
    "date_id",
    "site_code",
    "site_name",
    "line_code",
    "line_name",
    "product_code",
    "product_name",
    "shift_code",
    "shift_name",
    "actual_quantity",
    "operating_time_min",
    "line_total_electricity_kwh",
    "line_idle_electricity_kwh",
    "idle_energy_share",
    "expected_kwh",
    "residual_kwh",
    "residual_pct",
    "low_threshold",
    "high_threshold",
    "energy_anomaly_status",
    "is_high_energy_anomaly",
    "is_low_energy_anomaly",
]
ANOMALY_STATUSES = {"NORMAL", "HIGH_ENERGY", "LOW_ENERGY"}
EXPECTED_FORECAST_DOMAIN_ROWS = {"PRODUCTION": 360, "ENERGY": 360}
EXPECTED_FORECAST_START = pd.Timestamp("2025-11-02").date()
EXPECTED_FORECAST_END = pd.Timestamp("2025-12-31").date()
EXPECTED_ANOMALY_START = pd.Timestamp("2025-01-01").date()
EXPECTED_ANOMALY_END = pd.Timestamp("2025-12-31").date()
EXPECTED_RELIABILITY_DOWNTIME_HOURS = 14856.65
RELIABILITY_DOWNTIME_TOLERANCE_HOURS = 0.01
EXPECTED_FORECAST_SHA256 = (
    "270b091a9f60e207652d7d0fe3e727ad019ea45ef3ba86c4d9f8381b50887da5"
)
EXPECTED_ANOMALY_SHA256 = (
    "8a7c6407b565edea05da4757e8d401ec343f5f0ffe3d67da67da5ff44c193999"
)


class AcceptanceError(ValueError):
    """Raised when an accepted materialized input fails snapshot checks."""


def repo_root() -> Path:
    root = Path(__file__).resolve().parents[1]
    if not (root / "data" / "gold" / "advanced_analytics").exists():
        raise FileNotFoundError("Could not locate advanced-analytics outputs.")
    return root


def resolve_input_path(repo: Path, supplied: Path | None, default: Path) -> Path:
    path = default if supplied is None else supplied
    if not path.is_absolute():
        path = repo / path
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_columns(frame: pd.DataFrame, required: list[str], label: str) -> None:
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise AcceptanceError(f"{label} is missing required columns: {missing}")


def require_non_null(frame: pd.DataFrame, columns: list[str], label: str) -> None:
    null_counts = frame[columns].isna().sum()
    bad = {name: int(count) for name, count in null_counts.items() if count}
    if bad:
        raise AcceptanceError(f"{label} has missing required values: {bad}")


def require_nonblank(frame: pd.DataFrame, columns: list[str], label: str) -> None:
    for column in columns:
        frame[column] = frame[column].astype("string").str.strip()
        if frame[column].eq("").any():
            raise AcceptanceError(f"{label}.{column} contains blank values")


def normalize_boolean(series: pd.Series, label: str) -> pd.Series:
    if pd.api.types.is_bool_dtype(series.dtype):
        result = series.astype("boolean")
    else:
        normalized = series.astype("string").str.strip().str.lower()
        mapping = {"true": True, "false": False, "1": True, "0": False}
        values = normalized.dropna()
        unknown = sorted(values[~values.isin(mapping)].unique())
        if unknown:
            raise AcceptanceError(f"{label} has invalid boolean values: {unknown}")
        result = normalized.map(mapping).astype("boolean")
    if result.isna().any():
        raise AcceptanceError(f"{label} contains null boolean values")
    return result


def validate_forecast(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    label = "Forecast Parquet"
    source_columns = [c for c in FORECAST_COLUMNS if c != "forecast_domain"]
    require_columns(frame, source_columns, label)
    forecast = frame.copy()

    parsed_dates = pd.to_datetime(forecast["calendar_date"], errors="coerce")
    if parsed_dates.isna().any():
        raise AcceptanceError(f"{label}.calendar_date contains invalid dates")
    forecast["calendar_date"] = parsed_dates.dt.date
    require_non_null(forecast, ["calendar_date", "site_code", "forecast_target"], label)
    require_nonblank(forecast, ["site_code", "forecast_target"], label)

    unknown_targets = sorted(
        set(forecast["forecast_target"]) - set(FORECAST_TARGET_DOMAINS)
    )
    if unknown_targets:
        raise AcceptanceError(
            "Unknown forecast_target value(s); no domain mapping exists: "
            f"{unknown_targets}"
        )
    forecast["forecast_domain"] = forecast["forecast_target"].map(
        FORECAST_TARGET_DOMAINS
    )

    numeric_columns = [
        "actual_value",
        "ml_forecast_value",
        "seasonal_naive_value",
        "selected_forecast_value",
        "absolute_error",
        "absolute_pct_error",
    ]
    for column in numeric_columns:
        forecast[column] = pd.to_numeric(forecast[column], errors="coerce")
    require_non_null(forecast, numeric_columns, label)
    if not np.isfinite(forecast[numeric_columns].to_numpy(dtype=float)).all():
        raise AcceptanceError(f"{label} contains non-finite numeric values")
    if (forecast["absolute_error"] < 0).any() or (
        forecast["absolute_pct_error"] < 0
    ).any():
        raise AcceptanceError(f"{label} contains negative error values")

    if len(forecast) != 720:
        raise AcceptanceError(f"{label} has {len(forecast)} rows; expected 720")
    domain_rows = forecast["forecast_domain"].value_counts().to_dict()
    if domain_rows != EXPECTED_FORECAST_DOMAIN_ROWS:
        raise AcceptanceError(
            f"{label} domain rows are {domain_rows}; expected "
            f"{EXPECTED_FORECAST_DOMAIN_ROWS}"
        )
    if forecast["site_code"].nunique() != 6:
        raise AcceptanceError(f"{label} must contain exactly 6 sites")
    if (
        forecast["calendar_date"].min() != EXPECTED_FORECAST_START
        or forecast["calendar_date"].max() != EXPECTED_FORECAST_END
    ):
        raise AcceptanceError(
            f"{label} date range must be {EXPECTED_FORECAST_START} through "
            f"{EXPECTED_FORECAST_END}"
        )
    for domain in EXPECTED_FORECAST_DOMAIN_ROWS:
        domain_frame = forecast.loc[forecast["forecast_domain"] == domain]
        if domain_frame["calendar_date"].nunique() != 60:
            raise AcceptanceError(f"{label} {domain} must contain 60 dates")
        if domain_frame["site_code"].nunique() != 6:
            raise AcceptanceError(f"{label} {domain} must contain 6 sites")

    duplicate_key = ["calendar_date", "site_code", "forecast_domain"]
    duplicate_count = int(forecast.duplicated(duplicate_key).sum())
    if duplicate_count:
        raise AcceptanceError(
            f"{label} has {duplicate_count} duplicate Date+Site+Domain rows"
        )

    expected_absolute_error = (
        forecast["actual_value"] - forecast["selected_forecast_value"]
    ).abs()
    if not np.allclose(
        forecast["absolute_error"], expected_absolute_error, rtol=1e-10, atol=1e-8
    ):
        raise AcceptanceError(f"{label}.absolute_error does not reconcile")
    if forecast["actual_value"].eq(0).any():
        raise AcceptanceError(f"{label} contains zero actual values; APE is undefined")
    expected_ape = expected_absolute_error / forecast["actual_value"].abs()
    if not np.allclose(
        forecast["absolute_pct_error"], expected_ape, rtol=1e-10, atol=1e-12
    ):
        raise AcceptanceError(
            f"{label}.absolute_pct_error is not stored as a fractional ratio"
        )

    mape_fraction = (
        forecast.groupby("forecast_domain")["absolute_pct_error"].mean().to_dict()
    )
    return forecast[FORECAST_COLUMNS], {
        "rows": len(forecast),
        "domain_rows": domain_rows,
        "dates_per_domain": {
            domain: int(group["calendar_date"].nunique())
            for domain, group in forecast.groupby("forecast_domain")
        },
        "sites": int(forecast["site_code"].nunique()),
        "min_date": str(forecast["calendar_date"].min()),
        "max_date": str(forecast["calendar_date"].max()),
        "mape_fraction": {key: float(value) for key, value in mape_fraction.items()},
    }


def validate_anomaly(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    label = "Energy-anomaly Parquet"
    require_columns(frame, ANOMALY_COLUMNS, label)
    anomaly = frame.copy()
    anomaly["timestamp_start"] = pd.to_datetime(
        anomaly["timestamp_start"], errors="coerce"
    )
    anomaly["date_id"] = pd.to_numeric(anomaly["date_id"], errors="coerce")
    require_non_null(
        anomaly,
        [
            "production_id",
            "timestamp_start",
            "date_id",
            "site_code",
            "line_code",
            "shift_code",
            "energy_anomaly_status",
        ],
        label,
    )
    if not np.equal(anomaly["date_id"], np.floor(anomaly["date_id"])).all():
        raise AcceptanceError(f"{label}.date_id contains non-integer values")
    anomaly["date_id"] = anomaly["date_id"].astype("int64")
    require_nonblank(
        anomaly,
        [
            "production_id",
            "site_code",
            "line_code",
            "shift_code",
            "energy_anomaly_status",
        ],
        label,
    )

    numeric_columns = [
        "actual_quantity",
        "operating_time_min",
        "line_total_electricity_kwh",
        "line_idle_electricity_kwh",
        "idle_energy_share",
        "expected_kwh",
        "residual_kwh",
        "residual_pct",
        "low_threshold",
        "high_threshold",
    ]
    for column in numeric_columns:
        anomaly[column] = pd.to_numeric(anomaly[column], errors="coerce")
    require_non_null(anomaly, numeric_columns, label)
    if not np.isfinite(anomaly[numeric_columns].to_numpy(dtype=float)).all():
        raise AcceptanceError(f"{label} contains non-finite numeric values")

    for column in ["is_high_energy_anomaly", "is_low_energy_anomaly"]:
        anomaly[column] = normalize_boolean(anomaly[column], f"{label}.{column}")

    statuses = set(anomaly["energy_anomaly_status"])
    unknown_statuses = sorted(statuses - ANOMALY_STATUSES)
    if unknown_statuses:
        raise AcceptanceError(
            f"{label} contains invalid energy_anomaly_status values: {unknown_statuses}"
        )
    expected_high = anomaly["energy_anomaly_status"].eq("HIGH_ENERGY")
    expected_low = anomaly["energy_anomaly_status"].eq("LOW_ENERGY")
    if not anomaly["is_high_energy_anomaly"].eq(expected_high).all():
        raise AcceptanceError(f"{label} high-anomaly flags conflict with status")
    if not anomaly["is_low_energy_anomaly"].eq(expected_low).all():
        raise AcceptanceError(f"{label} low-anomaly flags conflict with status")

    if len(anomaly) != 32850:
        raise AcceptanceError(f"{label} has {len(anomaly)} rows; expected 32,850")
    if anomaly["site_code"].nunique() != 6 or anomaly["line_code"].nunique() != 30:
        raise AcceptanceError(f"{label} must contain 6 sites and 30 lines")
    high_count = int(anomaly["is_high_energy_anomaly"].sum())
    low_count = int(anomaly["is_low_energy_anomaly"].sum())
    if high_count != 254 or low_count != 282:
        raise AcceptanceError(
            f"{label} anomaly counts are high={high_count}, low={low_count}; "
            "expected high=254, low=282"
        )

    timestamp_dates = anomaly["timestamp_start"].dt.date
    if (
        timestamp_dates.min() != EXPECTED_ANOMALY_START
        or timestamp_dates.max() != EXPECTED_ANOMALY_END
    ):
        raise AcceptanceError(
            f"{label} date range must be {EXPECTED_ANOMALY_START} through "
            f"{EXPECTED_ANOMALY_END}"
        )
    expected_date_ids = anomaly["timestamp_start"].dt.strftime("%Y%m%d").astype("int64")
    if not anomaly["date_id"].eq(expected_date_ids).all():
        raise AcceptanceError(f"{label}.date_id does not match timestamp_start")

    if anomaly["production_id"].duplicated().any():
        raise AcceptanceError(f"{label} has duplicate production_id values")
    shift_key = ["date_id", "site_code", "line_code", "shift_code"]
    duplicate_shift_rows = int(anomaly.duplicated(shift_key).sum())
    if duplicate_shift_rows:
        raise AcceptanceError(
            f"{label} has {duplicate_shift_rows} duplicate Date+Site+Line+Shift rows"
        )

    return anomaly[ANOMALY_COLUMNS], {
        "rows": len(anomaly),
        "high_energy_anomalies": high_count,
        "low_energy_anomalies": low_count,
        "sites": int(anomaly["site_code"].nunique()),
        "lines": int(anomaly["line_code"].nunique()),
        "min_date": str(timestamp_dates.min()),
        "max_date": str(timestamp_dates.max()),
        "physical_grain": "production_id (Date+Site+Line+Shift)",
        "power_bi_relationship_keys": ["Date", "Site", "Line"],
    }


def copy_dataframe(
    conn, frame: pd.DataFrame, table: str, columns: list[str]
) -> None:
    buffer = StringIO()
    frame[columns].to_csv(
        buffer,
        index=False,
        header=False,
        na_rep="\\N",
        date_format="%Y-%m-%d %H:%M:%S.%f",
    )
    buffer.seek(0)
    columns_sql = ", ".join(columns)
    statement = (
        f"COPY {table} ({columns_sql}) "
        "FROM STDIN WITH (FORMAT CSV, NULL '\\N')"
    )
    with conn.cursor() as cursor:
        cursor.copy_expert(statement, buffer)


def create_stable_tables(cursor) -> None:
    cursor.execute(
        """
        CREATE SCHEMA IF NOT EXISTS analytics;

        CREATE TABLE IF NOT EXISTS analytics.bi_site_daily_forecast (
            calendar_date date NOT NULL,
            site_code text NOT NULL,
            site_name text,
            actual_value double precision NOT NULL,
            ml_forecast_value double precision NOT NULL,
            seasonal_naive_value double precision NOT NULL,
            selected_forecast_value double precision NOT NULL,
            forecast_target text NOT NULL,
            forecast_domain text NOT NULL,
            absolute_error double precision NOT NULL,
            absolute_pct_error double precision NOT NULL,
            CONSTRAINT ck_bi_forecast_domain
                CHECK (forecast_domain IN ('PRODUCTION', 'ENERGY')),
            CONSTRAINT ck_bi_forecast_target_domain
                CHECK (
                    (forecast_target = 'daily_actual_quantity'
                     AND forecast_domain = 'PRODUCTION')
                    OR
                    (forecast_target = 'daily_site_total_electricity_kwh'
                     AND forecast_domain = 'ENERGY')
                )
        );

        CREATE TABLE IF NOT EXISTS analytics.bi_shift_energy_anomaly (
            production_id text NOT NULL,
            timestamp_start timestamp NOT NULL,
            date_id integer NOT NULL,
            site_code text NOT NULL,
            site_name text,
            line_code text NOT NULL,
            line_name text,
            product_code text,
            product_name text,
            shift_code text NOT NULL,
            shift_name text,
            actual_quantity double precision,
            operating_time_min double precision,
            line_total_electricity_kwh double precision,
            line_idle_electricity_kwh double precision,
            idle_energy_share double precision,
            expected_kwh double precision,
            residual_kwh double precision,
            residual_pct double precision,
            low_threshold double precision,
            high_threshold double precision,
            energy_anomaly_status text NOT NULL,
            is_high_energy_anomaly boolean NOT NULL,
            is_low_energy_anomaly boolean NOT NULL,
            CONSTRAINT ck_bi_energy_anomaly_status
                CHECK (energy_anomaly_status IN ('NORMAL', 'HIGH_ENERGY', 'LOW_ENERGY')),
            CONSTRAINT ck_bi_energy_anomaly_flags
                CHECK (
                    is_high_energy_anomaly = (energy_anomaly_status = 'HIGH_ENERGY')
                    AND is_low_energy_anomaly = (energy_anomaly_status = 'LOW_ENERGY')
                )
        );

        CREATE TABLE IF NOT EXISTS analytics.bi_advanced_analytics_load_audit (
            load_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            loaded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            loader_version text NOT NULL,
            forecast_input_path text NOT NULL,
            forecast_sha256 text NOT NULL,
            anomaly_input_path text NOT NULL,
            anomaly_sha256 text NOT NULL,
            forecast_row_count integer NOT NULL,
            anomaly_row_count integer NOT NULL,
            reliability_row_count integer NOT NULL,
            acceptance_summary jsonb NOT NULL
        );
        """
    )


def truncate_and_enforce_schema(cursor) -> None:
    cursor.execute(
        """
        TRUNCATE TABLE
            analytics.bi_site_daily_forecast,
            analytics.bi_shift_energy_anomaly;

        ALTER TABLE analytics.bi_site_daily_forecast
            ALTER COLUMN calendar_date SET NOT NULL,
            ALTER COLUMN site_code SET NOT NULL,
            ALTER COLUMN actual_value SET NOT NULL,
            ALTER COLUMN ml_forecast_value SET NOT NULL,
            ALTER COLUMN seasonal_naive_value SET NOT NULL,
            ALTER COLUMN selected_forecast_value SET NOT NULL,
            ALTER COLUMN forecast_target SET NOT NULL,
            ALTER COLUMN forecast_domain SET NOT NULL,
            ALTER COLUMN absolute_error SET NOT NULL,
            ALTER COLUMN absolute_pct_error SET NOT NULL;

        ALTER TABLE analytics.bi_shift_energy_anomaly
            ALTER COLUMN production_id SET NOT NULL,
            ALTER COLUMN timestamp_start SET NOT NULL,
            ALTER COLUMN date_id SET NOT NULL,
            ALTER COLUMN site_code SET NOT NULL,
            ALTER COLUMN line_code SET NOT NULL,
            ALTER COLUMN shift_code SET NOT NULL,
            ALTER COLUMN energy_anomaly_status SET NOT NULL,
            ALTER COLUMN is_high_energy_anomaly SET NOT NULL,
            ALTER COLUMN is_low_energy_anomaly SET NOT NULL;

        DO $constraints$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conrelid = 'analytics.bi_site_daily_forecast'::regclass
                  AND conname = 'ck_bi_forecast_domain'
            ) THEN
                ALTER TABLE analytics.bi_site_daily_forecast
                    ADD CONSTRAINT ck_bi_forecast_domain
                    CHECK (forecast_domain IN ('PRODUCTION', 'ENERGY'));
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conrelid = 'analytics.bi_site_daily_forecast'::regclass
                  AND conname = 'ck_bi_forecast_target_domain'
            ) THEN
                ALTER TABLE analytics.bi_site_daily_forecast
                    ADD CONSTRAINT ck_bi_forecast_target_domain
                    CHECK (
                        (forecast_target = 'daily_actual_quantity'
                         AND forecast_domain = 'PRODUCTION')
                        OR
                        (forecast_target = 'daily_site_total_electricity_kwh'
                         AND forecast_domain = 'ENERGY')
                    );
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conrelid = 'analytics.bi_shift_energy_anomaly'::regclass
                  AND conname = 'ck_bi_energy_anomaly_status'
            ) THEN
                ALTER TABLE analytics.bi_shift_energy_anomaly
                    ADD CONSTRAINT ck_bi_energy_anomaly_status
                    CHECK (energy_anomaly_status IN ('NORMAL', 'HIGH_ENERGY', 'LOW_ENERGY'));
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conrelid = 'analytics.bi_shift_energy_anomaly'::regclass
                  AND conname = 'ck_bi_energy_anomaly_flags'
            ) THEN
                ALTER TABLE analytics.bi_shift_energy_anomaly
                    ADD CONSTRAINT ck_bi_energy_anomaly_flags
                    CHECK (
                        is_high_energy_anomaly = (energy_anomaly_status = 'HIGH_ENERGY')
                        AND is_low_energy_anomaly = (energy_anomaly_status = 'LOW_ENERGY')
                    );
            END IF;
        END
        $constraints$;

        CREATE UNIQUE INDEX IF NOT EXISTS uq_bi_forecast_date_site_domain
            ON analytics.bi_site_daily_forecast
            (calendar_date, site_code, forecast_domain);
        CREATE INDEX IF NOT EXISTS idx_bi_forecast_date_site
            ON analytics.bi_site_daily_forecast (calendar_date, site_code);
        CREATE INDEX IF NOT EXISTS idx_bi_forecast_domain
            ON analytics.bi_site_daily_forecast (forecast_domain);

        CREATE UNIQUE INDEX IF NOT EXISTS uq_bi_energy_anomaly_production
            ON analytics.bi_shift_energy_anomaly (production_id);
        CREATE UNIQUE INDEX IF NOT EXISTS uq_bi_energy_anomaly_shift_grain
            ON analytics.bi_shift_energy_anomaly
            (date_id, site_code, line_code, shift_code);
        CREATE INDEX IF NOT EXISTS idx_bi_energy_anomaly_date_site_line
            ON analytics.bi_shift_energy_anomaly
            (date_id, site_code, line_code);
        CREATE INDEX IF NOT EXISTS idx_bi_energy_anomaly_high
            ON analytics.bi_shift_energy_anomaly (is_high_energy_anomaly);
        """
    )


def validate_reliability_source(cursor) -> dict:
    cursor.execute(
        """
        SELECT
            COUNT(*),
            COUNT(DISTINCT month_start),
            COUNT(DISTINCT site_code),
            COUNT(DISTINCT line_code),
            COALESCE(SUM(corrective_failure_count), 0),
            COALESCE(SUM(corrective_downtime_hours), 0),
            MIN(month_start),
            MAX(month_start)
        FROM analytics.vw_monthly_reliability_trend
        """
    )
    row = cursor.fetchone()
    summary = {
        "rows": int(row[0]),
        "months": int(row[1]),
        "sites": int(row[2]),
        "lines": int(row[3]),
        "corrective_failures": int(row[4]),
        "corrective_downtime_hours": float(row[5]),
        "min_month": str(row[6]),
        "max_month": str(row[7]),
        "downtime_tolerance_hours": RELIABILITY_DOWNTIME_TOLERANCE_HOURS,
    }
    expected = {
        "rows": 720,
        "months": 24,
        "sites": 6,
        "lines": 30,
        "corrective_failures": 46670,
        "min_month": "2024-01-01",
        "max_month": "2025-12-01",
    }
    mismatches = {
        key: (summary[key], value)
        for key, value in expected.items()
        if summary[key] != value
    }
    if mismatches:
        raise AcceptanceError(f"Reliability bridge acceptance failed: {mismatches}")
    if abs(summary["corrective_downtime_hours"] - EXPECTED_RELIABILITY_DOWNTIME_HOURS) > (
        RELIABILITY_DOWNTIME_TOLERANCE_HOURS
    ):
        raise AcceptanceError(
            "Reliability corrective downtime is "
            f"{summary['corrective_downtime_hours']:.6f} hours; expected "
            f"{EXPECTED_RELIABILITY_DOWNTIME_HOURS:.2f} +/- "
            f"{RELIABILITY_DOWNTIME_TOLERANCE_HOURS:.2f}"
        )

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM analytics.vw_monthly_reliability_trend r
        LEFT JOIN public.dim_time t ON t.calendar_date = r.month_start
        LEFT JOIN public.dim_site s ON s.site_code = r.site_code
        LEFT JOIN public.dim_line l ON l.line_code = r.line_code
        WHERE r.month_start IS NULL OR r.site_code IS NULL OR r.line_code IS NULL
           OR t.date_id IS NULL OR s.site_id IS NULL OR l.line_id IS NULL
        """
    )
    if cursor.fetchone()[0] != 0:
        raise AcceptanceError("Reliability bridge has missing Date/Site/Line keys")
    cursor.execute(
        """
        SELECT COUNT(*) FROM (
            SELECT month_start, site_code, line_code
            FROM analytics.vw_monthly_reliability_trend
            GROUP BY month_start, site_code, line_code
            HAVING COUNT(*) <> 1
        ) duplicates
        """
    )
    if cursor.fetchone()[0] != 0:
        raise AcceptanceError("Reliability bridge has duplicate Date+Site+Line rows")

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM analytics.vw_monthly_equipment_type_reliability_trend r
        LEFT JOIN public.dim_time t ON t.calendar_date = r.month_start
        LEFT JOIN public.dim_site s ON s.site_code = r.site_code
        WHERE r.month_start IS NULL OR r.site_code IS NULL
           OR r.equipment_type IS NULL OR t.date_id IS NULL OR s.site_id IS NULL
        """
    )
    if cursor.fetchone()[0] != 0:
        raise AcceptanceError(
            "Equipment-type reliability has missing Date/Site/equipment-type keys"
        )
    cursor.execute(
        """
        SELECT COUNT(*) FROM (
            SELECT month_start, site_code, equipment_type
            FROM analytics.vw_monthly_equipment_type_reliability_trend
            GROUP BY month_start, site_code, equipment_type
            HAVING COUNT(*) <> 1
        ) duplicates
        """
    )
    if cursor.fetchone()[0] != 0:
        raise AcceptanceError(
            "Equipment-type reliability has duplicate Date+Site+EquipmentType rows"
        )
    return summary


def validate_loaded_tables(cursor) -> None:
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM analytics.bi_site_daily_forecast f
        LEFT JOIN public.dim_time t ON t.calendar_date = f.calendar_date
        LEFT JOIN public.dim_site s ON s.site_code = f.site_code
        WHERE t.date_id IS NULL OR s.site_id IS NULL
        """
    )
    if cursor.fetchone()[0] != 0:
        raise AcceptanceError("Loaded forecast rows have missing Date/Site keys")

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM analytics.bi_shift_energy_anomaly a
        LEFT JOIN public.dim_time t ON t.date_id = a.date_id
        LEFT JOIN public.dim_site s ON s.site_code = a.site_code
        LEFT JOIN public.dim_line l ON l.line_code = a.line_code
        WHERE t.date_id IS NULL OR s.site_id IS NULL OR l.line_id IS NULL
        """
    )
    if cursor.fetchone()[0] != 0:
        raise AcceptanceError("Loaded anomaly rows have missing Date/Site/Line keys")

    cursor.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM analytics.bi_site_daily_forecast),
            (SELECT COUNT(*) FROM analytics.bi_site_daily_forecast
             WHERE forecast_domain = 'PRODUCTION'),
            (SELECT COUNT(*) FROM analytics.bi_site_daily_forecast
             WHERE forecast_domain = 'ENERGY'),
            (SELECT COUNT(*) FROM analytics.bi_shift_energy_anomaly),
            (SELECT COUNT(*) FROM analytics.bi_shift_energy_anomaly
             WHERE is_high_energy_anomaly),
            (SELECT COUNT(*) FROM analytics.bi_shift_energy_anomaly
             WHERE is_low_energy_anomaly)
        """
    )
    observed = tuple(int(value) for value in cursor.fetchone())
    expected = (720, 360, 360, 32850, 254, 282)
    if observed != expected:
        raise AcceptanceError(
            f"Post-load database acceptance is {observed}; expected {expected}"
        )


def display_input_summary(
    forecast_summary: dict,
    anomaly_summary: dict,
    forecast_hash: str,
    anomaly_hash: str,
) -> None:
    print("Forecast acceptance:", forecast_summary)
    print("Energy-anomaly acceptance:", anomaly_summary)
    print("Forecast SHA-256:", forecast_hash)
    print("Energy-anomaly SHA-256:", anomaly_hash)
    print(
        "MAPE storage semantics: fractional ratios; Power BI should average "
        "the value directly and apply Percentage formatting."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5433)
    parser.add_argument("--dbname", default="manufacturing_intelligence")
    parser.add_argument("--user", default="postgres")
    parser.add_argument("--forecast-path", type=Path)
    parser.add_argument("--anomaly-path", type=Path)
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate and hash Parquet inputs without connecting to PostgreSQL.",
    )
    args = parser.parse_args()

    repo = repo_root()
    advanced = repo / "data" / "gold" / "advanced_analytics"
    forecast_path = resolve_input_path(
        repo,
        args.forecast_path,
        advanced / "forecasting" / "daily_site_forecast_holdout_2025.parquet",
    )
    anomaly_path = resolve_input_path(
        repo,
        args.anomaly_path,
        advanced / "energy_anomaly" / "energy_anomaly_shift_monitoring_2025.parquet",
    )

    print("=== Power BI advanced-analytics PostgreSQL loader ===")
    forecast, forecast_summary = validate_forecast(pd.read_parquet(forecast_path))
    anomaly, anomaly_summary = validate_anomaly(pd.read_parquet(anomaly_path))
    forecast_hash = sha256_file(forecast_path)
    anomaly_hash = sha256_file(anomaly_path)
    if forecast_hash != EXPECTED_FORECAST_SHA256:
        raise AcceptanceError(
            "Forecast Parquet SHA-256 does not match the accepted production and energy forecasting snapshot"
        )
    if anomaly_hash != EXPECTED_ANOMALY_SHA256:
        raise AcceptanceError(
            "Energy-anomaly Parquet SHA-256 does not match the accepted energy anomaly snapshot"
        )
    display_input_summary(
        forecast_summary, anomaly_summary, forecast_hash, anomaly_hash
    )

    if args.validate_only:
        print("=== Input validation complete; PostgreSQL was not contacted ===")
        return

    conn = psycopg2.connect(**connection_parameters(args))
    conn.autocommit = False

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))",
                ("velora_powerbi_advanced_analytics_load",),
            )
            create_stable_tables(cursor)
            reliability_summary = validate_reliability_source(cursor)
            truncate_and_enforce_schema(cursor)

        copy_dataframe(
            conn,
            forecast,
            "analytics.bi_site_daily_forecast",
            FORECAST_COLUMNS,
        )
        copy_dataframe(
            conn,
            anomaly,
            "analytics.bi_shift_energy_anomaly",
            ANOMALY_COLUMNS,
        )

        acceptance_summary = {
            "forecast": forecast_summary,
            "energy_anomaly": anomaly_summary,
            "reliability": reliability_summary,
        }
        with conn.cursor() as cursor:
            validate_loaded_tables(cursor)
            cursor.execute(
                """
                INSERT INTO analytics.bi_advanced_analytics_load_audit (
                    loader_version,
                    forecast_input_path,
                    forecast_sha256,
                    anomaly_input_path,
                    anomaly_sha256,
                    forecast_row_count,
                    anomaly_row_count,
                    reliability_row_count,
                    acceptance_summary
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    LOADER_VERSION,
                    str(forecast_path),
                    forecast_hash,
                    str(anomaly_path),
                    anomaly_hash,
                    forecast_summary["rows"],
                    anomaly_summary["rows"],
                    reliability_summary["rows"],
                    Json(acceptance_summary),
                ),
            )
        conn.commit()

        print("Reliability acceptance:", reliability_summary)
        print("Transactional TRUNCATE + reload committed.")
        print("=== Loader complete ===")
    except Exception:
        conn.rollback()
        print("Loader failed; transaction rolled back and prior bridge rows were preserved.")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
