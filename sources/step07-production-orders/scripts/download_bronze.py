from pathlib import Path
import sys
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
from _shared.bronze_guard import install_chunks, reuse_complete_set_or_raise
MANIFEST = pd.read_csv(ROOT / "metadata" / "source_manifest.csv")
OUT = ROOT / "bronze" / "series_production_cnc"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "https://zenodo.org/records/10853254/files"

for row in MANIFEST.itertuples(index=False):
    target = OUT / row.file_name
    if reuse_complete_set_or_raise(
        [target], expected={target: ("md5", row.md5)}
    ):
        continue
    url = f"{BASE}/{row.file_name}?download=1"
    print(f"Downloading {row.file_name}")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        actual, _ = install_chunks(
            target,
            r.iter_content(chunk_size=1024 * 1024),
            expected_digest=row.md5,
            algorithm="md5",
        )
    print(f"Verified: {row.file_name}")
