from pathlib import Path
import json
import pandas as pd
import pyarrow.parquet as pq


def repo_root():
    here = Path.cwd()
    for c in [here, *here.parents]:
        if (c / "sources" / "step04-reliability").exists():
            return c
    raise FileNotFoundError("Could not locate sources/step04-reliability.")


def profile_file(path: Path):
    out = {
        "path": str(path),
        "suffix": path.suffix.lower(),
        "size_bytes": path.stat().st_size,
    }

    try:
        if path.suffix.lower() == ".parquet":
            pf = pq.ParquetFile(path)
            out["rows"] = pf.metadata.num_rows
            out["columns"] = [
                {"name": f.name, "type": str(f.type)}
                for f in pf.schema_arrow
            ]

            if pf.metadata.num_rows <= 10000:
                d = pf.read().to_pandas()
                out["distinct_cycle_id"] = (
                    int(d["cycle_id"].nunique())
                    if "cycle_id" in d.columns else None
                )
                out["null_counts"] = {
                    c: int(d[c].isna().sum()) for c in d.columns
                }
                out["distinct_counts"] = {
                    c: int(d[c].nunique(dropna=True))
                    for c in d.columns
                    if d[c].nunique(dropna=True) <= 50
                }
                out["value_samples"] = {
                    c: [str(x) for x in d[c].dropna().unique()[:20]]
                    for c in d.columns
                    if d[c].nunique(dropna=True) <= 20
                }

        elif path.suffix.lower() == ".csv":
            d = pd.read_csv(path)
            out["rows"] = len(d)
            out["columns"] = [
                {"name": c, "type": str(dt)}
                for c, dt in d.dtypes.items()
            ]
            out["distinct_cycle_id"] = (
                int(d["cycle_id"].nunique())
                if "cycle_id" in d.columns else None
            )
            out["null_counts"] = {
                c: int(d[c].isna().sum()) for c in d.columns
            }
            out["distinct_counts"] = {
                c: int(d[c].nunique(dropna=True))
                for c in d.columns
                if d[c].nunique(dropna=True) <= 50
            }
            out["value_samples"] = {
                c: [str(x) for x in d[c].dropna().unique()[:20]]
                for c in d.columns
                if d[c].nunique(dropna=True) <= 20
            }

    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"

    return out


def main():
    repo = repo_root()
    base = repo / "sources" / "step04-reliability"
    silver = base / "silver" / "reliability"

    print("=== Stage 13E.1 condition-monitoring feasibility ===")
    print(f"Base: {base}")

    candidates = []
    for p in silver.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in {".parquet", ".csv"}:
            continue

        parts_lower = [x.lower() for x in p.parts]
        if "telemetry" in parts_lower:
            continue

        candidates.append(p)

    for p in base.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in {".csv", ".txt"}:
            continue
        name = p.name.lower()
        if any(k in name for k in [
            "profile", "label", "condition", "target", "cycle",
            "metadata", "class"
        ]):
            if p not in candidates:
                candidates.append(p)

    print(f"Non-telemetry candidate files: {len(candidates)}")

    profiles = []
    for p in sorted(set(candidates)):
        rel = p.relative_to(repo)
        print("\n---")
        print(f"Path: {rel}")

        if p.suffix.lower() == ".txt":
            print(f"Text file size: {p.stat().st_size} bytes")
            profiles.append({
                "path": str(rel),
                "suffix": ".txt",
                "size_bytes": p.stat().st_size,
                "note": "Text/reference file; inspect manually if it is a label/profile source."
            })
            continue

        prof = profile_file(p)
        prof["path"] = str(rel)
        profiles.append(prof)

        print(f"Rows: {prof.get('rows')}")
        print("Columns:")
        for c in prof.get("columns", []):
            print(f"  - {c['name']}: {c['type']}")

        if prof.get("distinct_cycle_id") is not None:
            print(f"Distinct cycles: {prof['distinct_cycle_id']}")

        dc = prof.get("distinct_counts", {})
        if dc:
            print("Low-cardinality fields:")
            for k, v in dc.items():
                print(f"  - {k}: {v} distinct")
                vals = prof.get("value_samples", {}).get(k, [])
                if vals:
                    print(f"    values: {vals}")

    tel = silver / "telemetry"
    sensor_dirs = sorted([p for p in tel.glob("sensor_id=*") if p.is_dir()])

    sensor_summary = []
    all_cycles = set()

    print("\n=== Telemetry cycle/sensor coverage ===")
    for sd in sensor_dirs:
        sensor = sd.name.split("=", 1)[1]
        files = sorted(sd.glob("*.parquet"))
        cycle_ids = set()
        rows = 0

        for p in files:
            pf = pq.ParquetFile(p)
            rows += pf.metadata.num_rows

            # IMPORTANT:
            # Read the individual Parquet file directly. Using pq.read_table(p)
            # under a directory named sensor_id=... invokes Hive partition
            # inference, which clashes with the sensor_id column stored inside
            # the file.
            table = pf.read(columns=["cycle_id"])
            vals = table.column("cycle_id").to_pylist()
            cycle_ids.update(int(x) for x in vals if x is not None)

        all_cycles.update(cycle_ids)
        sensor_summary.append({
            "sensor_id": sensor,
            "files": len(files),
            "rows": rows,
            "cycles": len(cycle_ids),
            "min_cycle": min(cycle_ids) if cycle_ids else None,
            "max_cycle": max(cycle_ids) if cycle_ids else None,
        })

        print(
            f"{sensor}: files={len(files)}, rows={rows:,}, "
            f"cycles={len(cycle_ids)}, "
            f"range={min(cycle_ids) if cycle_ids else None}-"
            f"{max(cycle_ids) if cycle_ids else None}"
        )

    print(f"\nUnion of telemetry cycle IDs: {len(all_cycles)}")
    if all_cycles:
        print(f"Cycle range: {min(all_cycles)} -> {max(all_cycles)}")

    labels_path = silver / "condition_labels.parquet"
    alignment = {}
    if labels_path.exists():
        labels = pq.ParquetFile(labels_path).read().to_pandas()
        label_cycles = set(labels["cycle_id"].astype(int))

        alignment = {
            "label_cycles": len(label_cycles),
            "telemetry_cycles": len(all_cycles),
            "matched_cycles": len(label_cycles & all_cycles),
            "label_cycles_missing_telemetry": len(label_cycles - all_cycles),
            "telemetry_cycles_missing_labels": len(all_cycles - label_cycles),
            "alignment_pct_of_labels": (
                100.0 * len(label_cycles & all_cycles) / len(label_cycles)
                if label_cycles else None
            ),
        }

        print("\n=== Cycle-label alignment ===")
        for k, v in alignment.items():
            print(f"{k}: {v}")

    report = {
        "non_telemetry_profiles": profiles,
        "telemetry_sensor_summary": sensor_summary,
        "telemetry_union_cycle_count": len(all_cycles),
        "telemetry_cycle_min": min(all_cycles) if all_cycles else None,
        "telemetry_cycle_max": max(all_cycles) if all_cycles else None,
        "cycle_label_alignment": alignment,
    }

    out = repo / "reports" / "advanced_analytics"
    out.mkdir(parents=True, exist_ok=True)
    path = out / "stage13e1_condition_monitoring_feasibility.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\nReport:")
    print(path.relative_to(repo))
    print("=== Stage 13E.1 complete ===")


if __name__ == "__main__":
    main()
