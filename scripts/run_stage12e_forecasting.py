from __future__ import annotations

from getpass import getpass
from pathlib import Path
import json
import joblib

import numpy as np
import pandas as pd
import psycopg2

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

HOLDOUT_DAYS = 60
LAGS = [1, 7, 14, 28]
ROLLING_WINDOWS = [7, 28]
RANDOM_STATE = 42


def find_repo_root() -> Path:
    here = Path.cwd()
    for c in [here, *here.parents]:
        if (c / "sources").exists():
            return c
    raise FileNotFoundError("Run from the repository root or a subdirectory.")


def load_daily() -> pd.DataFrame:
    password = getpass("PostgreSQL password for user postgres: ")
    conn = psycopg2.connect(
        host="localhost",
        port=5433,
        dbname="manufacturing_intelligence",
        user="postgres",
        password=password,
    )
    q = """
    SELECT
        d.calendar_date,
        s.site_code,
        s.site_name,
        SUM(g.actual_quantity)::double precision AS actual_quantity,
        SUM(g.site_total_electricity_kwh)::double precision AS site_total_electricity_kwh
    FROM gold_bi.vw_site_daily_performance g
    JOIN public.dim_time d
      ON d.date_id = g.date_id
    JOIN public.dim_site s
      ON s.site_code = g.site_code
    WHERE d.calendar_date >= DATE '2024-01-01'
      AND d.calendar_date <= DATE '2025-12-31'
    GROUP BY d.calendar_date, s.site_code, s.site_name
    ORDER BY s.site_code, d.calendar_date
    """
    try:
        return pd.read_sql_query(q, conn, parse_dates=["calendar_date"])
    finally:
        conn.close()


def add_features(df: pd.DataFrame, target: str) -> pd.DataFrame:
    out = df.sort_values(["site_code", "calendar_date"]).copy()
    g = out.groupby("site_code", group_keys=False)

    for lag in LAGS:
        out[f"{target}__lag_{lag}"] = g[target].shift(lag)

    for win in ROLLING_WINDOWS:
        # strictly causal: shift(1) before rolling
        out[f"{target}__roll_mean_{win}"] = (
            g[target].shift(1).rolling(win).mean().reset_index(level=0, drop=True)
        )
        out[f"{target}__roll_std_{win}"] = (
            g[target].shift(1).rolling(win).std(ddof=0).reset_index(level=0, drop=True)
        )

    out["day_of_week"] = out["calendar_date"].dt.dayofweek
    out["day_of_month"] = out["calendar_date"].dt.day
    out["month"] = out["calendar_date"].dt.month
    out["week_of_year"] = out["calendar_date"].dt.isocalendar().week.astype(int)
    out["is_weekend"] = out["day_of_week"].isin([5, 6]).astype(int)

    return out


def metrics(y, p) -> dict:
    y = np.asarray(y, float)
    p = np.asarray(p, float)
    mask = np.abs(y) > 1e-9
    mape = float(np.mean(np.abs((y[mask]-p[mask])/y[mask]))*100) if mask.any() else None
    return {
        "mae": float(mean_absolute_error(y, p)),
        "rmse": float(mean_squared_error(y, p) ** 0.5),
        "r2": float(r2_score(y, p)),
        "mape_pct": mape,
    }


def fit_and_score(base: pd.DataFrame, target: str, holdout_start: pd.Timestamp):
    feat = add_features(base, target).dropna().copy()

    train = feat.loc[feat["calendar_date"] < holdout_start].copy()
    test = feat.loc[feat["calendar_date"] >= holdout_start].copy()

    feature_cols = [
        "site_code",
        "day_of_week",
        "day_of_month",
        "month",
        "week_of_year",
        "is_weekend",
        *[f"{target}__lag_{x}" for x in LAGS],
        *[f"{target}__roll_mean_{w}" for w in ROLLING_WINDOWS],
        *[f"{target}__roll_std_{w}" for w in ROLLING_WINDOWS],
    ]

    categorical = ["site_code"]
    numeric = [c for c in feature_cols if c not in categorical]

    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical),
        ("num", "passthrough", numeric),
    ])

    model = HistGradientBoostingRegressor(
        learning_rate=0.05,
        max_iter=300,
        max_leaf_nodes=31,
        l2_regularization=1.0,
        random_state=RANDOM_STATE,
    )

    pipe = Pipeline([
        ("preprocessor", pre),
        ("model", model),
    ])
    pipe.fit(train[feature_cols], train[target])

    test["ml_forecast"] = pipe.predict(test[feature_cols])
    # Seasonal-naive reference: same site, same weekday one week earlier.
    test["seasonal_naive_7d"] = test[f"{target}__lag_7"]

    ml_metrics = metrics(test[target], test["ml_forecast"])
    naive_metrics = metrics(test[target], test["seasonal_naive_7d"])

    if ml_metrics["mae"] <= naive_metrics["mae"]:
        winner = "hist_gradient_boosting"
        test["selected_forecast"] = test["ml_forecast"]
    else:
        winner = "seasonal_naive_7d"
        test["selected_forecast"] = test["seasonal_naive_7d"]

    return pipe, test, {
        "target": target,
        "train_rows": int(len(train)),
        "holdout_rows": int(len(test)),
        "hist_gradient_boosting": ml_metrics,
        "seasonal_naive_7d": naive_metrics,
        "selected_model_by_mae": winner,
    }


def main():
    repo = find_repo_root()
    out = repo/"data"/"gold"/"advanced_analytics"/"forecasting"
    rep = repo/"reports"/"advanced_analytics"
    mod = repo/"models"/"advanced_analytics"/"forecasting"
    for p in [out, rep, mod]:
        p.mkdir(parents=True, exist_ok=True)

    print("=== Stage 12E production and energy forecasting ===")
    daily = load_daily()
    print(f"Rows loaded: {len(daily):,}")
    print(f"Coverage: {daily.calendar_date.min().date()} -> {daily.calendar_date.max().date()}")
    print(f"Sites: {daily.site_code.nunique()}")

    max_date = daily["calendar_date"].max()
    holdout_start = max_date - pd.Timedelta(days=HOLDOUT_DAYS - 1)
    print(f"Holdout: {holdout_start.date()} -> {max_date.date()}")

    prod_model, prod_test, prod_report = fit_and_score(
        daily, "actual_quantity", holdout_start
    )
    energy_model, energy_test, energy_report = fit_and_score(
        daily, "site_total_electricity_kwh", holdout_start
    )

    prod_out = prod_test[[
        "calendar_date", "site_code", "site_name", "actual_quantity",
        "ml_forecast", "seasonal_naive_7d", "selected_forecast"
    ]].rename(columns={
        "actual_quantity": "actual_value",
        "ml_forecast": "ml_forecast_value",
        "seasonal_naive_7d": "seasonal_naive_value",
        "selected_forecast": "selected_forecast_value",
    })
    prod_out["forecast_target"] = "daily_actual_quantity"

    energy_out = energy_test[[
        "calendar_date", "site_code", "site_name", "site_total_electricity_kwh",
        "ml_forecast", "seasonal_naive_7d", "selected_forecast"
    ]].rename(columns={
        "site_total_electricity_kwh": "actual_value",
        "ml_forecast": "ml_forecast_value",
        "seasonal_naive_7d": "seasonal_naive_value",
        "selected_forecast": "selected_forecast_value",
    })
    energy_out["forecast_target"] = "daily_site_total_electricity_kwh"

    combined = pd.concat([prod_out, energy_out], ignore_index=True)
    combined["absolute_error"] = (
        combined["actual_value"] - combined["selected_forecast_value"]
    ).abs()
    combined["absolute_pct_error"] = (
        combined["absolute_error"] / combined["actual_value"].replace(0, np.nan)
    )

    combined.to_parquet(out/"daily_site_forecast_holdout_2025.parquet", index=False)
    combined.to_csv(out/"daily_site_forecast_holdout_2025.csv", index=False)

    report = {
        "source": {
            "source_code": "SYNTHETIC_ENTERPRISE",
            "is_real_data": False,
            "reference_period": "2024-2025",
        },
        "forecast_design": {
            "forecast_horizon": "one day ahead",
            "evaluation_holdout_days": HOLDOUT_DAYS,
            "holdout_start": str(holdout_start.date()),
            "holdout_end": str(max_date.date()),
            "forecast_grain": "site-day",
            "lags_days": LAGS,
            "rolling_windows_days": ROLLING_WINDOWS,
            "baseline": "seasonal naive, 7-day lag",
            "selection_metric": "MAE",
            "causality_note": (
                "All lag and rolling features use prior observations only. "
                "This is an operational one-day-ahead forecast evaluation, not a "
                "60-day recursive forecast made at the start of the holdout."
            ),
        },
        "production_forecast": prod_report,
        "energy_forecast": energy_report,
        "interpretation_note": (
            "The source is synthetic enterprise integration data. Forecast "
            "performance demonstrates the workflow and must not be presented as "
            "measured-plant forecast accuracy."
        ),
    }

    with open(rep/"stage12e_forecasting_metrics.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    joblib.dump(prod_model, mod/"daily_production_forecast_model.joblib")
    joblib.dump(energy_model, mod/"daily_energy_forecast_model.joblib")

    def show(label, r):
        print(f"\n=== {label} ===")
        a = r["hist_gradient_boosting"]
        b = r["seasonal_naive_7d"]
        print(f"HGBR MAE:  {a['mae']:.4f}")
        print(f"HGBR RMSE: {a['rmse']:.4f}")
        print(f"HGBR R2:   {a['r2']:.6f}")
        print(f"HGBR MAPE: {a['mape_pct']:.4f}%")
        print(f"Naive MAE:  {b['mae']:.4f}")
        print(f"Naive RMSE: {b['rmse']:.4f}")
        print(f"Naive R2:   {b['r2']:.6f}")
        print(f"Naive MAPE: {b['mape_pct']:.4f}%")
        print(f"Selected by MAE: {r['selected_model_by_mae']}")

    show("Production one-day-ahead forecast", prod_report)
    show("Energy one-day-ahead forecast", energy_report)

    print("\nOutputs:")
    print(out.relative_to(repo))
    print((rep/"stage12e_forecasting_metrics.json").relative_to(repo))
    print("=== Stage 12E complete ===")


if __name__ == "__main__":
    main()
