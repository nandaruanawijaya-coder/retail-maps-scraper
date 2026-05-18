#!/usr/bin/env python3
"""Run Bandung kelurahan 61-100 (Lembang onwards)."""
import asyncio
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'kelurahan_scraper'))

from kelurahan_scraper.run_kelurahan import scrape_kelurahan_batch

async def main():
    bandung_file = os.path.join(os.path.dirname(__file__), 'data', 'input', 'bandung_kelurahan.csv')
    df = pd.read_csv(bandung_file)

    # Kelurahan 61-100 from Bandung (0-indexed rows 60-99)
    kelurahan_list = df.iloc[60:100].to_dict('records')

    print(f"Processing Bandung kelurahan 61-100: {len(kelurahan_list)} kelurahan")
    await scrape_kelurahan_batch(kelurahan_list, num_scrapers=2)

if __name__ == "__main__":
    asyncio.run(main())
