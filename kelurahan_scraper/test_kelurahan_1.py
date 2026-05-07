#!/usr/bin/env python3
"""Test 1 kelurahan + 1 category end-to-end."""
import asyncio
import logging
import os
import sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scraper.config import CATEGORIES
from gmaps_scraper_kelurahan import GoogleMapsScraperKelurahan
from bigquery_uploader_kelurahan import upload_merchants_to_bigquery, create_table_if_not_exists

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


async def test_1kelurahan_1category():
    """Test with 1 kelurahan and 1 category."""
    logger.info("=" * 80)
    logger.info("TEST: 1 Kelurahan + 1 Category")
    logger.info("=" * 80)

    # Load kelurahan data
    kelurahan_file = os.path.join(
        os.path.dirname(__file__), '..', 'data', 'input', 'kelurahan_prioritized.csv'
    )
    df = pd.read_csv(kelurahan_file)
    kelurahan_list = df.head(1).to_dict('records')  # Just first kelurahan
    kelurahan = kelurahan_list[0]

    logger.info(f"Kelurahan: {kelurahan['kelurahan_name']}, {kelurahan['kecamatan_name']}")
    logger.info(f"Category: {CATEGORIES[0]['name']} (gmaps_query: {CATEGORIES[0]['gmaps_query']})")

    # Create BigQuery table
    logger.info("Creating BigQuery table...")
    create_table_if_not_exists()

    # Initialize scraper
    logger.info("Initializing browser...")
    scraper = GoogleMapsScraperKelurahan()
    await scraper.init()

    try:
        # Search
        logger.info(f"\nSearching...")
        merchants_raw = await scraper.search(
            query=CATEGORIES[0]['gmaps_query'],
            kelurahan=kelurahan['kelurahan_name'],
            kecamatan=kelurahan['kecamatan_name'],
            kabupaten=kelurahan['kabupaten_name'],
            provinsi=kelurahan['provinsi_name']
        )

        logger.info(f"Found {len(merchants_raw)} merchants")

        # Add location and category data
        merchants = []
        for raw in merchants_raw:
            if raw and raw.get('name'):
                raw['kelurahan_name'] = kelurahan['kelurahan_name']
                raw['kecamatan_name'] = kelurahan['kecamatan_name']
                raw['kabupaten_name'] = kelurahan['kabupaten_name']
                raw['provinsi_name'] = kelurahan['provinsi_name']
                raw['kelurahan_id'] = str(kelurahan['kelurahan_id'])
                raw['our_category'] = CATEGORIES[0]['name']
                raw['vertical'] = CATEGORIES[0]['vertical']
                merchants.append(raw)

        logger.info(f"Parsed {len(merchants)} merchants")

        # Show sample
        if merchants:
            logger.info("\n" + "=" * 80)
            logger.info("SAMPLE MERCHANT:")
            logger.info("=" * 80)
            sample = merchants[0]
            for key in sorted(sample.keys()):
                logger.info(f"  {key:20s}: {sample[key]}")

        # Upload
        logger.info(f"\nUploading {len(merchants)} merchants to BigQuery...")
        upload_success = upload_merchants_to_bigquery(merchants)

        if upload_success:
            logger.info(f"✓ SUCCESS: Uploaded to merchants_gmaps_kelurahan")
        else:
            logger.error("✗ FAILED: BigQuery upload failed")

    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(test_1kelurahan_1category())
