"""
Fetch district GeoJSON data from BigQuery and save to data/input/districts.csv.

Auth:
    gcloud auth application-default login

Usage:
    python export_data/fetch_districts.py
    python export_data/fetch_districts.py --sql export_data/extract_geojson.sql --out data/input/districts.csv
"""
from pathlib import Path
import argparse
import pandas as pd
from google.cloud import bigquery

PROJECT_ID = "ledger-fcc1e"
SQL_FILE   = Path(__file__).parent / "extract_geojson.sql"
OUTPUT_CSV = Path(__file__).parent.parent / "data" / "input" / "districts.csv"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sql", default=str(SQL_FILE))
    parser.add_argument("--out", default=str(OUTPUT_CSV))
    parser.add_argument("--project", default=PROJECT_ID)
    args = parser.parse_args()

    sql_path = Path(args.sql)
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")

    query = sql_path.read_text()
    print(f"Loading SQL from: {sql_path}")

    client = bigquery.Client(project=args.project)
    print("Running BigQuery query...")
    df = client.query(query).to_dataframe()
    print(f"  → {len(df):,} rows fetched")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"  → Saved to: {out_path}")

    print("\nSample:")
    print(df[["district_id", "kelurahan_name", "kecamatan_name", "kabupaten_name", "provinsi_name"]].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
