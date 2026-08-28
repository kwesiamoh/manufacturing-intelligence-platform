from pathlib import Path

DATAHUB = "https://www.eea.europa.eu/en/datahub/datahubitem-view/98f04097-26de-4fca-86c4-63834818c0c0/folder_contents"
OUT = Path("bronze/eea_eu_ets")
OUT.mkdir(parents=True, exist_ok=True)

print("Open the official EEA datahub page and use its current July 2026 Direct download link:")
print(DATAHUB)
print("Preserve the downloaded CSV/TXT/SQL archive unchanged under", OUT)
print("MANUAL_INPUT_REQUIRED: no automated acquisition was performed.")
raise SystemExit(2)
