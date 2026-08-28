#!/usr/bin/env python3
from pathlib import Path
import json

for ds in ["nrg_pc_205","nrg_pc_203"]:
    p=Path("bronze/eurostat_energy_prices")/f"{ds}.json"
    if not p.exists():
        raise SystemExit(f"Missing {p}")
    obj=json.loads(p.read_text(encoding="utf-8"))
    if "id" not in obj or "value" not in obj:
        raise SystemExit(f"Unexpected Eurostat JSON structure for {ds}")
    print(ds, "validated")
