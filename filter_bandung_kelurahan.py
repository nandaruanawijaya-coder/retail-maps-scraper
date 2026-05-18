#!/usr/bin/env python3
"""Filter kelurahan data for Bandung region from existing CSV."""
import pandas as pd

# Load existing kelurahan data
df = pd.read_csv('data/input/kelurahan_prioritized.csv')

print(f"Total kelurahan in CSV: {len(df)}")

# Filter for Bandung region
bandung_cities = ['Kota Bandung', 'Bandung', 'Bandung Barat']
df_bandung = df[df['kabupaten_name'].isin(bandung_cities)].copy()

print(f"\nKelurahan in Bandung region: {len(df_bandung)}")

# Show summary by city
print("\nSummary by Kabupaten:")
print(df_bandung.groupby('kabupaten_name')['kelurahan_name'].count())

# Save to CSV
output_file = 'data/input/bandung_kelurahan.csv'
df_bandung.to_csv(output_file, index=False)
print(f"\n✓ Saved to {output_file}")

print("\nFirst 10 rows:")
print(df_bandung.head(10))
