"""Download the public FMUCD dataset from Mendeley Data.

Uses the public dataset API so the current file UUID/download URL can be discovered
instead of hard-coding an expiring binary URL.
"""
from pathlib import Path
import sys
import requests

DATASET_ID = "cb8d2nsjss"
VERSION = 1
API = "https://api.data.mendeley.com"
OUT = Path(__file__).resolve().parents[1] / "bronze"
sys.path.insert(0, str(OUT.parents[1]))
from _shared.bronze_guard import install_chunks, reuse_complete_set_or_raise
OUT.mkdir(parents=True, exist_ok=True)

existing_csvs = sorted(OUT.glob("*.csv"))
if existing_csvs and reuse_complete_set_or_raise(existing_csvs):
    raise SystemExit(0)

headers = {"Accept": "application/json"}
files_url = f"{API}/datasets/publics/{DATASET_ID}/files"
r = requests.get(files_url, params={"version": VERSION, "$limit": 100}, headers=headers, timeout=60)
r.raise_for_status()
files = r.json()

csv_files = [f for f in files if str(f.get("filename", "")).lower().endswith(".csv")]
if not csv_files:
    raise RuntimeError("No CSV file was returned by the Mendeley public dataset API.")

for meta in csv_files:
    file_id = meta["id"]
    name = meta["filename"]
    detail_url = f"{API}/datasets/publics/{DATASET_ID}/files/{file_id}"
    d = requests.get(detail_url, params={"version": VERSION}, headers=headers, timeout=60)
    d.raise_for_status()
    detail = d.json()
    download_url = detail.get("content_details", {}).get("download_url")
    if not download_url:
        # Fallback to the documented redirect endpoint.
        download_url = f"{API}/datasets/{DATASET_ID}/files/{file_id}/file_downloaded?version={VERSION}"

    target = OUT / name
    print(f"Downloading {name} -> {target}")
    with requests.get(download_url, stream=True, allow_redirects=True, timeout=120) as src:
        src.raise_for_status()
        install_chunks(target, src.iter_content(chunk_size=8 * 1024 * 1024))
    print(f"Saved {target.stat().st_size:,} bytes")
