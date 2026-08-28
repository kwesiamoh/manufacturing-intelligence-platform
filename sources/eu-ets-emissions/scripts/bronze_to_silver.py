from pathlib import Path
import re
import pandas as pd

BRONZE = Path("bronze/eea_eu_ets")
SILVER = Path("silver/eea_eu_ets")

SILVER.mkdir(parents=True, exist_ok=True)

SRC = BRONZE / "ETS_Database_July_2026.xlsx"


def snake(x):
    x = re.sub(r"[^0-9A-Za-z]+", "_", str(x).strip())
    return re.sub(r"_+", "_", x).strip("_").lower()


if not SRC.exists():
    raise FileNotFoundError(f"Missing source workbook: {SRC}")

workbook = pd.ExcelFile(SRC)

for sheet in workbook.sheet_names:

    # Preserve mixed values/footnotes safely.
    df = pd.read_excel(
        SRC,
        sheet_name=sheet,
        dtype=str
    )

    df = df.dropna(how="all")
    df.columns = [snake(c) for c in df.columns]

    out = SILVER / f"{snake(sheet)}.parquet"

    df.to_parquet(
        out,
        index=False,
        engine="pyarrow",
        compression="zstd"
    )

    print(
        f"{sheet}: {len(df):,} rows x {len(df.columns)} columns "
        f"-> {out}"
    )

print("Silver EU ETS conversion complete.")
print("No synthetic emissions records were created.")
