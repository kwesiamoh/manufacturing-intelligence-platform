from pathlib import Path
import re
import pandas as pd

BASE = Path(__file__).resolve().parents[1]

SRC = BASE / "bronze" / "production_downtime" / "production_raw.xlsx"
OUT = BASE / "silver" / "production_downtime"

OUT.mkdir(parents=True, exist_ok=True)


def clean_name(name):
    name = str(name).strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return re.sub(r"_+", "_", name).strip("_")


if not SRC.exists():
    raise FileNotFoundError(f"Missing Bronze file: {SRC}")

workbook = pd.ExcelFile(SRC)

for sheet_name in workbook.sheet_names:
    df = pd.read_excel(SRC, sheet_name=sheet_name)

    # Preserve source data; only normalize column names.
    df.columns = [clean_name(c) for c in df.columns]

    # Remove rows that are completely empty.
    df = df.dropna(how="all")

    output_file = OUT / f"{clean_name(sheet_name)}.parquet"

    df.to_parquet(
        output_file,
        index=False,
        engine="pyarrow",
        compression="zstd"
    )

    print(
        f"{sheet_name}: "
        f"{len(df):,} rows x {len(df.columns)} columns -> "
        f"{output_file.name}"
    )

print(f"\nSilver dataset written to: {OUT}")
print("No synthetic production or downtime records were created.")
