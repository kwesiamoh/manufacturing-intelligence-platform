"""Validate the accepted Eurostat nrg_pc_205 JSON-stat Bronze response."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "sources"
    / "step14-eu-energy-prices"
    / "bronze"
    / "eurostat_energy_prices"
    / "nrg_pc_205__full.json"
)


def validate(source: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"Missing canonical Eurostat Bronze response: {source}")

    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid Eurostat JSON: {exc}") from exc

    required = {"id", "size", "dimension", "value"}
    missing = sorted(required - set(payload))
    if missing:
        raise RuntimeError(f"Eurostat JSON-stat response lacks fields: {missing}")
    if payload.get("class") != "dataset":
        raise RuntimeError("Eurostat JSON-stat response class is not 'dataset'")
    if len(payload["id"]) != len(payload["size"]):
        raise RuntimeError("Eurostat id/size dimensionality mismatch")
    if "geo" not in payload["id"] or "time" not in payload["id"]:
        raise RuntimeError("Eurostat response lacks required geo/time dimensions")
    if not isinstance(payload["value"], dict) or not payload["value"]:
        raise RuntimeError("Eurostat response contains no observations")

    print(
        "PASS: canonical Eurostat nrg_pc_205 JSON-stat Bronze validated "
        f"({len(payload['value']):,} non-null observations)."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Eurostat nrg_pc_205 JSON-stat")
    parser.add_argument("--source", type=Path, default=SOURCE)
    source = parser.parse_args().source
    try:
        validate(source)
        return 0
    except (FileNotFoundError, OSError, RuntimeError) as exc:
        print(f"FAIL: Eurostat Bronze validation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
