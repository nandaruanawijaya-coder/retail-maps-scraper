#!/usr/bin/env python3
"""
Kelurahan-level Google Maps merchant scraper.
Scrapes merchants at kelurahan level with full location hierarchy.
Uploads to separate BigQuery table to preserve previous kecamatan-level data.
Supports resume from interruptions.
"""
import asyncio
import logging
import os
import sys
import json
import pandas as pd
from datetime import datetime

# Add parent directory to path to import scraper modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scraper.config import CATEGORIES, OUTPUT_FIELDS
from scraper.gmaps_parser import GoogleMapsParser
from gmaps_scraper_kelurahan import GoogleMapsScraperKelurahan
from bigquery_uploader_kelurahan import upload_merchants_to_bigquery, create_table_if_not_exists


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROGRESS_FILE = os.path.join(BASE_DIR, "progress_kelurahan.json")
LOG_DIR = os.path.join(BASE_DIR, "logs")


def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, f"kelurahan_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logging.info(f"Logging to {log_file}")
    return log_file


def load_progress():
    """Load progress from previous run."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"completed": []}


def save_progress(progress):
    """Save progress to file."""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def is_completed(kel_id, cat_name, progress):
    """Check if kelurahan-category combo is already completed."""
    return f"{kel_id}_{cat_name}" in progress["completed"]


def mark_completed(kel_id, cat_name, progress):
    """Mark kelurahan-category combo as completed."""
    progress["completed"].append(f"{kel_id}_{cat_name}")


async def scrape_kelurahan_batch(kelurahan_list, num_scrapers=2):
    """Scrape top kelurahan with multiple parallel scrapers and resume capability."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("KELURAHAN-LEVEL SCRAPER")
    logger.info("=" * 80)
    logger.info(f"Kelurahan to process: {len(kelurahan_list)}")
    logger.info(f"Categories per kelurahan: {len(CATEGORIES)}")
    logger.info(f"Parallel scrapers: {num_scrapers}")
    logger.info(f"Total searches: {len(kelurahan_list) * len(CATEGORIES):,}")
    logger.info(f"Start time: {datetime.now().isoformat()}")
    logger.info("=" * 80)

    # Load progress
    progress = load_progress()
    completed_count = len(progress["completed"])
    logger.info(f"Resuming from progress: {completed_count} kelurahan-category combos already completed")
    logger.info("=" * 80)

    # Create BigQuery table
    logger.info("Preparing BigQuery table...")
    create_table_if_not_exists()

    # Initialize scrapers
    scrapers = []
    for i in range(num_scrapers):
        scraper = GoogleMapsScraperKelurahan()
        await scraper.init()
        scrapers.append(scraper)

    total_merchants = 0

    try:
        for kel_idx, kelurahan_data in enumerate(kelurahan_list, 1):
            kel_id = kelurahan_data['kelurahan_id']
            kelurahan_merchants = []
            logger.info(f"\n[{kel_idx}/{len(kelurahan_list)}] {kelurahan_data['kelurahan_name']}, {kelurahan_data['kecamatan_name']}")

            # Process categories in parallel batches
            for batch_idx in range(0, len(CATEGORIES), num_scrapers):
                batch = CATEGORIES[batch_idx:batch_idx + num_scrapers]

                # Create async tasks for parallel execution
                tasks = []
                for cat_idx, category in enumerate(batch):
                    cat_name = category['name']

                    # Check if already completed
                    if is_completed(kel_id, cat_name, progress):
                        logger.info(f"  {cat_name:30s}: SKIPPED (already completed)")
                        continue

                    scraper = scrapers[cat_idx % num_scrapers]

                    async def search_and_parse(scraper, category, kelurahan_data, kel_id):
                        try:
                            merchants_raw = await scraper.search(
                                query=category['gmaps_query'],
                                kelurahan=kelurahan_data['kelurahan_name'],
                                kecamatan=kelurahan_data['kecamatan_name'],
                                kabupaten=kelurahan_data['kabupaten_name'],
                                provinsi=kelurahan_data['provinsi_name']
                            )

                            # Merchants are already extracted, just add location data and category
                            merchants = []
                            for raw in merchants_raw:
                                if raw and raw.get('name'):
                                    raw['kelurahan_name'] = kelurahan_data['kelurahan_name']
                                    raw['kecamatan_name'] = kelurahan_data['kecamatan_name']
                                    raw['kabupaten_name'] = kelurahan_data['kabupaten_name']
                                    raw['provinsi_name'] = kelurahan_data['provinsi_name']
                                    raw['kelurahan_id'] = str(kelurahan_data['kelurahan_id'])
                                    raw['our_category'] = category['name']
                                    raw['vertical'] = category['vertical']
                                    merchants.append(raw)

                            mark_completed(kel_id, category['name'], progress)
                            save_progress(progress)

                            logger.info(f"  {category['name']:30s}: {len(merchants_raw):3d} merchants ({len(merchants)} parsed)")
                            return merchants
                        except Exception as e:
                            logger.error(f"Error for {category['name']}: {e}")
                            return []

                    tasks.append(search_and_parse(scraper, category, kelurahan_data, kel_id))

                # Run all tasks in parallel
                if tasks:
                    batch_results = await asyncio.gather(*tasks)
                    for merchants in batch_results:
                        kelurahan_merchants.extend(merchants)

                    # Brief pause between batches
                    if batch_idx + num_scrapers < len(CATEGORIES):
                        await asyncio.sleep(1)

            # Upload merchants for this kelurahan immediately
            if kelurahan_merchants:
                logger.info(f"\n  Uploading {len(kelurahan_merchants)} merchants from {kelurahan_data['kelurahan_name']}...")
                upload_success = upload_merchants_to_bigquery(kelurahan_merchants)
                if upload_success:
                    total_merchants += len(kelurahan_merchants)
                    logger.info(f"  ✓ Uploaded {len(kelurahan_merchants)} merchants")
                else:
                    logger.warning(f"  ✗ Upload failed for {len(kelurahan_merchants)} merchants")

        # Summary
        logger.info("=" * 80)
        logger.info(f"✓ BATCH COMPLETE")
        logger.info(f"✓ Total merchants uploaded: {total_merchants:,}")
        logger.info(f"✓ End time: {datetime.now().isoformat()}")
        logger.info("=" * 80)

    finally:
        # Close all scrapers
        for scraper in scrapers:
            await scraper.close()


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Kelurahan-level Google Maps Scraper")
    parser.add_argument("--top", type=int, default=50, help="Top N kelurahan to scrape (default: 50)")
    args = parser.parse_args()

    # Load kelurahan data
    kelurahan_file = os.path.join(
        os.path.dirname(__file__), '..', 'data', 'input', 'kelurahan_prioritized.csv'
    )

    if not os.path.exists(kelurahan_file):
        print(f"Error: {kelurahan_file} not found")
        print("Run: python3 kelurahan_prep/fetch_kelurahan.py")
        sys.exit(1)

    df = pd.read_csv(kelurahan_file)
    kelurahan_list = df.head(args.top).to_dict('records')

    print(f"Scraping top {len(kelurahan_list)} kelurahan...")
    await scrape_kelurahan_batch(kelurahan_list, num_scrapers=2)


if __name__ == "__main__":
    asyncio.run(main())
