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
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from getpass import getpass

LOW_Q, HIGH_Q = 0.005, 0.995


def repo_root():
    p = Path.cwd()
    for c in [p, *p.parents]:
        if (c/"sources").exists():
            return c
    raise FileNotFoundError("Run from the repository.")


def load_data():
    password = getpass("PostgreSQL password for user postgres: ")

    conn = psycopg2.connect(
        host="localhost",
        port=5433,
        dbname="manufacturing_intelligence",
        user="postgres",
        password=password,
    )
    q = """
    SELECT production_id,timestamp_start,date_id,site_code,site_name,
           line_code,line_name,product_code,product_name,shift_code,shift_name,
           actual_quantity,operating_time_min,planned_production_time_min,
           nominal_rate,actual_rate,line_total_electricity_kwh,
           line_idle_electricity_kwh,idle_energy_share,shift_mean_air_temperature_c
    FROM gold_bi.vw_shift_manufacturing_performance
    WHERE timestamp_start >= '2024-01-01' AND timestamp_start < '2026-01-01'
      AND line_total_electricity_kwh > 0
      AND actual_quantity IS NOT NULL
      AND operating_time_min IS NOT NULL
    ORDER BY timestamp_start,site_code,line_code,shift_code
    """
    try:
        return pd.read_sql_query(q, conn, parse_dates=["timestamp_start"])
    finally:
        conn.close()


def mape(y, p):
    y = np.asarray(y, float)
    p = np.asarray(p, float)
    m = np.abs(y) > 1e-9
    return float(np.mean(np.abs((y[m]-p[m])/y[m]))*100)


def main():
    repo = repo_root()
    out = repo/"data"/"gold"/"advanced_analytics"/"energy_anomaly"
    rep = repo/"reports"/"advanced_analytics"
    mod = repo/"models"/"advanced_analytics"/"energy"
    for p in [out, rep, mod]:
        p.mkdir(parents=True, exist_ok=True)

    print("=== energy anomaly contextual energy anomaly analytics ===")
    d = load_data()
    d["year"] = d["timestamp_start"].dt.year
    print(f"Rows loaded: {len(d):,}")
    print(f"Coverage: {d.timestamp_start.min()} -> {d.timestamp_start.max()}")

    cat = ["site_code", "line_code", "product_code", "shift_code"]
    num = ["actual_quantity", "operating_time_min", "planned_production_time_min",
           "nominal_rate", "actual_rate", "shift_mean_air_temperature_c"]
    target = "line_total_electricity_kwh"

    base = d[d.year == 2024].sort_values("timestamp_start").copy()
    test = d[d.year == 2025].sort_values("timestamp_start").copy()
    cut = int(len(base)*0.80)
    train = base.iloc[:cut].copy()
    cal = base.iloc[cut:].copy()

    print(f"Training rows: {len(train):,}")
    print(f"Calibration rows: {len(cal):,}")
    print(f"2025 holdout rows: {len(test):,}")

    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat),
        ("num", StandardScaler(), num)
    ])
    reg = HistGradientBoostingRegressor(learning_rate=.05, max_iter=300,
                                        max_leaf_nodes=31, l2_regularization=1.0, random_state=42)
    pipe = Pipeline([("preprocessor", pre), ("model", reg)])
    pipe.fit(train[cat+num], train[target])

    for x in [cal, test]:
        x["expected_kwh"] = pipe.predict(x[cat+num])
        x["residual_kwh"] = x[target]-x["expected_kwh"]
        x["residual_pct"] = x["residual_kwh"] / \
            x["expected_kwh"].replace(0, np.nan)

    th = (cal.groupby("line_code")["residual_pct"].quantile([LOW_Q, HIGH_Q])
          .unstack().rename(columns={LOW_Q: "low_threshold", HIGH_Q: "high_threshold"})
          .reset_index())
    test = test.merge(th, on="line_code", how="left")
    test["low_threshold"] = test["low_threshold"].fillna(
        cal.residual_pct.quantile(LOW_Q))
    test["high_threshold"] = test["high_threshold"].fillna(
        cal.residual_pct.quantile(HIGH_Q))
    test["energy_anomaly_status"] = np.select(
        [test.residual_pct > test.high_threshold,
            test.residual_pct < test.low_threshold],
        ["HIGH_ENERGY", "LOW_ENERGY"], default="NORMAL")
    test["is_high_energy_anomaly"] = test.energy_anomaly_status.eq(
        "HIGH_ENERGY")
    test["is_low_energy_anomaly"] = test.energy_anomaly_status.eq("LOW_ENERGY")

    y = test[target].astype(float).to_numpy()
    p = test.expected_kwh.astype(float).to_numpy()
    metrics = {
        "source": {"source_code": "SYNTHETIC_ENTERPRISE", "is_real_data": False,
                   "role": "SYNTHETIC_INTEGRATION", "reference_period": "2024-2025"},
        "design": {"train": "first 80% of 2024", "calibration": "last 20% of 2024",
                   "holdout": "2025", "model": "HistGradientBoostingRegressor",
                   "high_quantile": HIGH_Q, "low_quantile": LOW_Q,
                   "features": cat+num},
        "model_quality_2025": {
            "mae_kwh": float(mean_absolute_error(y, p)),
            "rmse_kwh": float(mean_squared_error(y, p)**.5),
            "r2": float(r2_score(y, p)),
            "mape_pct": mape(y, p)},
        "anomaly_summary_2025": {
            "rows": int(len(test)),
            "high_count": int(test.is_high_energy_anomaly.sum()),
            "low_count": int(test.is_low_energy_anomaly.sum()),
            "high_pct": float(100*test.is_high_energy_anomaly.mean()),
            "low_pct": float(100*test.is_low_energy_anomaly.mean()),
            "excess_kwh_high": float(test.loc[test.is_high_energy_anomaly, "residual_kwh"].clip(lower=0).sum())}
    }

    site = (test.groupby(["site_code", "site_name"], as_index=False)
            .agg(monitored_shifts=("production_id", "count"),
                 high_energy_anomalies=("is_high_energy_anomaly", "sum"),
                 low_energy_anomalies=("is_low_energy_anomaly", "sum"),
                 residual_energy_kwh=("residual_kwh", "sum")))
    site["high_energy_anomaly_pct"] = 100 * \
        site.high_energy_anomalies/site.monitored_shifts

    keep = ["production_id", "timestamp_start", "date_id", "site_code", "site_name",
            "line_code", "line_name", "product_code", "product_name", "shift_code", "shift_name",
            "actual_quantity", "operating_time_min", "line_total_electricity_kwh",
            "line_idle_electricity_kwh", "idle_energy_share", "expected_kwh",
            "residual_kwh", "residual_pct", "low_threshold", "high_threshold",
            "energy_anomaly_status", "is_high_energy_anomaly", "is_low_energy_anomaly"]
    test[keep].to_parquet(
        out/"energy_anomaly_shift_monitoring_2025.parquet", index=False)
    site.to_csv(out/"energy_anomaly_site_summary_2025.csv", index=False)
    th.to_csv(out/"energy_anomaly_calibration_thresholds.csv", index=False)
    with open(rep/"energy_anomaly_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    joblib.dump(pipe, mod/"expected_line_energy_model.joblib")

    q = metrics["model_quality_2025"]
    a = metrics["anomaly_summary_2025"]
    print("\n=== 2025 expected-energy model quality ===")
    print(f"MAE: {q['mae_kwh']:.4f} kWh")
    print(f"RMSE: {q['rmse_kwh']:.4f} kWh")
    print(f"R2: {q['r2']:.6f}")
    print(f"MAPE: {q['mape_pct']:.4f}%")
    print("\n=== 2025 anomaly summary ===")
    print(f"High-energy anomalies: {a['high_count']:,} ({a['high_pct']:.4f}%)")
    print(f"Low-energy anomalies: {a['low_count']:,} ({a['low_pct']:.4f}%)")
    print(f"Excess kWh in high-energy anomalies: {a['excess_kwh_high']:,.2f}")
    print("\n=== High-energy anomaly rate by site ===")
    print(site[["site_code", "monitored_shifts", "high_energy_anomalies",
                "high_energy_anomaly_pct"]].sort_values(
        "high_energy_anomaly_pct", ascending=False).to_string(index=False))
    print("\n=== energy anomaly complete ===")


if __name__ == "__main__":
    main()
