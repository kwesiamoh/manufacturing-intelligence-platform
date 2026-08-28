from pathlib import Path
import argparse
import zipfile


ROOT = Path(__file__).resolve().parents[1]
base = ROOT / "bronze" / "eea_eu_ets"
DEFAULT_WORKBOOK = base / "ETS_Database_July_2026.xlsx"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate retained EEA EU ETS Bronze")
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    workbook = parser.parse_args().workbook

    if not workbook.is_file():
        print(
            "FAIL: required EEA EU ETS workbook is missing. Complete the manual "
            "official Datahub acquisition first."
        )
        return 1
    if workbook.stat().st_size == 0:
        print("FAIL: required EEA EU ETS workbook is empty")
        return 1
    if not zipfile.is_zipfile(workbook):
        print("FAIL: required EEA EU ETS workbook is not a valid XLSX container")
        return 1

    with zipfile.ZipFile(workbook) as archive:
        names = set(archive.namelist())
        if "xl/workbook.xml" not in names:
            print("FAIL: XLSX container lacks xl/workbook.xml")
            return 1

    print(f"PASS: required workbook is a valid XLSX container: {workbook}")
    print(
        "WARN: release-specific worksheet semantics remain a documented manual "
        "review; this validator enforces the retained package's mandatory "
        "container condition."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
