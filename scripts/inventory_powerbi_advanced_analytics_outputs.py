from pathlib import Path
import json
import pandas as pd
import pyarrow.parquet as pq

KEYWORDS = (
    "forecast",
    "prediction",
    "anomaly",
    "energy",
    "production",
    "reliability",
)

def find_repo_root():
    here = Path.cwd()
    for p in [here, *here.parents]:
        if (p / "data").exists() and (p / "reports").exists():
            return p
    raise FileNotFoundError("Could not locate repository root.")

def profile_csv(path):
    df = pd.read_csv(path, nrows=20)
    return {
        "format": "csv",
        "columns": [str(c) for c in df.columns],
    }

def profile_parquet(path):
    pf = pq.ParquetFile(path)
    return {
        "format": "parquet",
        "rows": int(pf.metadata.num_rows),
        "columns": [f.name for f in pf.schema_arrow],
    }

def main():
    repo = find_repo_root()

    search_roots = [
        repo / "data" / "gold" / "advanced_analytics",
        repo / "reports" / "advanced_analytics",
    ]

    candidates = []

    for base in search_roots:
        if not base.exists():
            continue

        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".csv", ".parquet"}:
                continue

            low = str(path).lower()

            # Exclude external benchmark outputs from Velora BI integration
            # candidates while still listing them separately later.
            is_external = any(
                token in low
                for token in (
                    "metropt",
                    "hydraulic_condition",
                    "hydraulic-condition",
                )
            )

            if not any(k in low for k in KEYWORDS):
                continue

            try:
                if path.suffix.lower() == ".csv":
                    info = profile_csv(path)
                    # Count rows efficiently enough for these Gold/report outputs.
                    with path.open("r", encoding="utf-8", errors="ignore") as f:
                        rows = max(sum(1 for _ in f) - 1, 0)
                    info["rows"] = rows
                else:
                    info = profile_parquet(path)

                candidates.append({
                    "path": str(path.relative_to(repo)),
                    "size_bytes": path.stat().st_size,
                    "external_benchmark": is_external,
                    **info,
                })
            except Exception as e:
                candidates.append({
                    "path": str(path.relative_to(repo)),
                    "size_bytes": path.stat().st_size,
                    "external_benchmark": is_external,
                    "error": f"{type(e).__name__}: {e}",
                })

    print("=== Power BI advanced-analytics integration preflight ===")

    enterprise = [x for x in candidates if not x.get("external_benchmark")]
    external = [x for x in candidates if x.get("external_benchmark")]

    print("\n=== A. Velora / synthetic-enterprise integration candidates ===")
    if not enterprise:
        print("No candidate files found.")
    else:
        for i, item in enumerate(enterprise, 1):
            print(f"\n[{i}] {item['path']}")
            print(f"    format: {item.get('format')}")
            print(f"    rows:   {item.get('rows')}")
            if "columns" in item:
                print("    columns:")
                for col in item["columns"]:
                    print(f"      - {col}")
            if "error" in item:
                print(f"    ERROR: {item['error']}")

    print("\n=== B. External benchmark outputs (do NOT blend into Velora operations) ===")
    if not external:
        print("No external benchmark candidate files found.")
    else:
        for item in external:
            print(f"- {item['path']}")

    out_dir = repo / "reports" / "powerbi"
    out_dir.mkdir(parents=True, exist_ok=True)

    report_path = out_dir / "advanced_analytics_integration_inventory.json"
    report_path.write_text(
        json.dumps(
            {
                "enterprise_candidates": enterprise,
                "external_benchmark_candidates": external,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\nReport:")
    print(report_path.relative_to(repo))
    print("=== Preflight complete ===")

if __name__ == "__main__":
    main()
