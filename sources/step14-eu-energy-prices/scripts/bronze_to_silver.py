#!/usr/bin/env python3
# Conservative normalization scaffold. Full dimension expansion will be performed in Stage 2 after
# the enterprise site/country/consumption-band mapping is finalized.
from pathlib import Path
import json
import pandas as pd

src=Path("bronze/eurostat_energy_prices")
dst=Path("silver/eurostat_energy_prices")
dst.mkdir(parents=True, exist_ok=True)

for ds in ["nrg_pc_205","nrg_pc_203"]:
    obj=json.loads((src/f"{ds}.json").read_text(encoding="utf-8"))
    pd.DataFrame([{
        "dataset_code":ds,
        "source_label":obj.get("label"),
        "source_href":obj.get("href"),
        "updated":obj.get("updated"),
        "raw_value_count":len(obj.get("value",{}))
    }]).to_parquet(dst/f"{ds}__metadata.parquet", index=False)
    print(ds, "metadata written; dimension expansion deferred")
