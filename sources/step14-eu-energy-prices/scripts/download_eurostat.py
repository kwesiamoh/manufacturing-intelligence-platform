#!/usr/bin/env python3
# Uses Eurostat's dissemination API in TSV format.
from pathlib import Path
import requests

datasets = ["nrg_pc_205", "nrg_pc_203"]
out = Path("bronze/eurostat_energy_prices")
out.mkdir(parents=True, exist_ok=True)

for ds in datasets:
    url = f"https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{ds}?lang=en"
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    (out/f"{ds}.json").write_bytes(r.content)
    print(ds, len(r.content))
