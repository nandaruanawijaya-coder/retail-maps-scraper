#!/usr/bin/env python3
"""
Fetch kelurahan-level data from BigQuery with visit counts.
Exports to CSV for use in kelurahan-level scraping.
"""
import os
from google.cloud import bigquery
import pandas as pd

PROJECT_ID = "ledger-fcc1e"

def fetch_kelurahan_data(output_file="kelurahan_prioritized.csv"):
    """Fetch kelurahan data from BigQuery and export to CSV."""
    client = bigquery.Client(project=PROJECT_ID)

    query = """
    SELECT
        CONCAT(lu.kd_provinsi, lu.kd_kabupaten, lu.kd_kecamatan, lu.kd_kelurahan) as kelurahan_id,
        visit.provinsi_name,
        visit.kabupaten_name,
        visit.kecamatan_name,
        visit.kelurahan_name,
        COUNT(DISTINCT id) as numVisit
    FROM `merchant_success_analytics.retail_visit_ssot` visit
    LEFT JOIN `trb_pymnts_derived.geojson_indo_lookup` lu
    ON
        visit.kelurahan_name = lu.kelurahan_name
        AND visit.kecamatan_name = lu.kecamatan_name
        AND visit.kabupaten_name = lu.kabupaten_name
        AND visit.provinsi_name = lu.provinsi_name
    GROUP BY ALL
    ORDER BY 6 DESC
    """

    print("Fetching kelurahan data from BigQuery...")
    try:
        df = client.query(query).to_dataframe()
        print(f"✓ Fetched {len(df)} kelurahan")

        # Save to CSV
        df.to_csv(output_file, index=False)
        print(f"✓ Saved to {output_file}")

        # Show stats
        print(f"\nTop 10 by visit count:")
        print(df.head(10)[['kelurahan_name', 'kecamatan_name', 'kabupaten_name', 'numVisit']])

        print(f"\nFile stats:")
        print(f"  Total kelurahan: {len(df)}")
        print(f"  Total visits: {df['numVisit'].sum():,}")
        print(f"  Avg visits per kelurahan: {df['numVisit'].mean():.0f}")

        return df
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

if __name__ == "__main__":
    import sys
    output = sys.argv[1] if len(sys.argv) > 1 else "kelurahan_prioritized.csv"
    fetch_kelurahan_data(output)
