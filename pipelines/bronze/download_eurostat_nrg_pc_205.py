from pathlib import Path
import json
import sys
import requests
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "sources" / "step14-eu-energy-prices" / "bronze" / "eurostat_energy_prices"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "sources"))
from _shared.bronze_guard import install_bytes, reuse_complete_set_or_raise

URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_pc_205"
TARGET_GEOS = {"DE", "NL", "PL", "CZ", "FR", "ES"}

def main():
    raw_path = OUT / "nrg_pc_205__full.json"
    if reuse_complete_set_or_raise([raw_path]):
        return

    print("Downloading Eurostat nrg_pc_205 ...")
    r = requests.get(URL, params={"lang": "en"}, timeout=180)
    r.raise_for_status()
    payload = r.json()

    install_bytes(raw_path, json.dumps(payload).encode("utf-8"))

    metadata = {
        "dataset_code": "nrg_pc_205",
        "source_url": r.url,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "http_status": r.status_code,
        "target_geographies": sorted(TARGET_GEOS),
        "data_class": "REAL_EXTERNAL_BENCHMARK",
        "integration_role": "BENCHMARK",
        "notes": "Official Eurostat non-household electricity-price dataset. No fictional-site observations."
    }
    install_bytes(
        OUT / "nrg_pc_205__download_metadata.json",
        (json.dumps(metadata, indent=2) + "\n").encode("utf-8"),
    )

    print(f"Wrote: {raw_path}")
    print(f"Response dimensions: {payload.get('id')}")
    print(f"Dimension sizes: {payload.get('size')}")
    print(f"Raw non-null value count: {len(payload.get('value', {}))}")

if __name__ == "__main__":
    main()
