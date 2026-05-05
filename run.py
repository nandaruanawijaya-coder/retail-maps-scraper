#!/usr/bin/env python3
"""
Google Maps Merchant Scraper — Kecamatan Level
Scrapes ~7,300 kecamatan × 28 categories = 204K searches over ~16 days
Usage:
  python run.py --sample 10     (Trial: 10 kecamatan)
  python run.py --all           (Full: all 7,268 kecamatan)
  python run.py --resume        (Resume from progress.json)
"""
import argparse
import asyncio
import logging
import os
import sys
import pandas as pd
from datetime import datetime

from scraper.boundary import District
from scraper.config import CATEGORIES, OUTPUT_FIELDS
from scraper.deduplicator import Deduplicator
from scraper.gmaps_scraper import GoogleMapsScraper
from scraper.gmaps_parser import GoogleMapsParser
from scraper.storage import StorageManager
from scraper.bigquery_uploader import upload_merchants_to_bigquery, create_table_if_not_exists

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def setup_logging():
    log_dir = os.path.join(BASE_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(os.path.join(log_dir, "scraper.log"), encoding="utf-8"),
        ],
    )


async def scrape_kecamatan(scraper, parser_obj, storage, kecamatan_row, idx, total):
    """Scrape all categories for one kecamatan."""
    kecamatan_id = str(kecamatan_row["district_id"])
    kecamatan_name = kecamatan_row["kecamatan_name"]
    kabupaten_name = kecamatan_row["kabupaten_name"]
    provinsi_name = kecamatan_row["provinsi_name"]

    logger = logging.getLogger(__name__)
    dedup = Deduplicator()

    for cat_idx, cat in enumerate(CATEGORIES, 1):
        cat_name = cat["name"]
        gmaps_query = cat["gmaps_query"]

        if storage.is_done(kecamatan_id, cat_name):
            continue

        try:
            raw_results = await scraper.search(gmaps_query, kecamatan_name)
            storage.save_raw(raw_results, kecamatan_id, cat_name)

            merchants = []
            for raw in raw_results:
                district = District(
                    district_id=kecamatan_id,
                    kelurahan=kecamatan_name,
                    kecamatan=kecamatan_name,
                    kabupaten=kabupaten_name,
                    provinsi=provinsi_name,
                )
                merchant = parser_obj.parse_merchant(raw, cat, district)
                if merchant:
                    merchants.append(merchant)
                    dedup.add(merchant)

            storage.mark_done(kecamatan_id, cat_name)

            if cat_idx == 1 or cat_idx % 10 == 0:
                logger.info(f"  [{cat_idx:2d}/28] {cat_name:25s}: {len(raw_results):2d}")

            if cat_idx < len(CATEGORIES):
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error for {cat_name}: {e}")

    # Save results for this kecamatan
    unique = dedup.get_unique()
    if unique:
        csv_records = []
        for merchant in unique:
            record = merchant.copy()
            for field in OUTPUT_FIELDS:
                if field not in record:
                    record[field] = None
            csv_records.append(record)

        storage.save_csv(csv_records, kecamatan_id)
        storage.save_json(csv_records, kecamatan_id)

        # Upload to BigQuery
        upload_merchants_to_bigquery(csv_records)

    if idx % 100 == 0:
        logger.info(f"Progress: {idx}/{total} kecamatan completed")


async def main():
    parser = argparse.ArgumentParser(description="Google Maps Merchant Scraper - Kecamatan Level")
    parser.add_argument("--sample", type=int, default=0,
                        help="Sample N kecamatan for testing")
    parser.add_argument("--all", action="store_true",
                        help="Scrape all ~7,300 kecamatan (will take ~16 days)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from progress.json")
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    # Load kecamatan data
    districts_file = os.path.join(BASE_DIR, "data", "input", "districts.csv")
    if not os.path.exists(districts_file):
        logger.error(f"Districts file not found: {districts_file}")
        sys.exit(1)

    df = pd.read_csv(districts_file)
    kecamatan_list = df.to_dict("records")

    if args.sample > 0:
        step = max(1, len(kecamatan_list) // args.sample)
        kecamatan_list = kecamatan_list[::step][:args.sample]

    logger.info("=" * 80)
    logger.info("KECAMATAN-LEVEL MERCHANT SCRAPER")
    logger.info("=" * 80)
    logger.info(f"Total kecamatan: {len(kecamatan_list):,}")
    logger.info(f"Categories per kecamatan: {len(CATEGORIES)}")
    logger.info(f"Total searches: {len(kecamatan_list) * len(CATEGORIES):,}")
    logger.info(f"Estimated time: {(len(kecamatan_list) * len(CATEGORIES) * 6.2 / 86400):.1f} days (at 6.2s/search)")
    logger.info(f"Start time: {datetime.now().isoformat()}")
    logger.info("=" * 80)

    storage = StorageManager(
        output_dir=os.path.join(BASE_DIR, "data", "output"),
        raw_dir=os.path.join(BASE_DIR, "data", "raw"),
        progress_file=os.path.join(BASE_DIR, "progress.json"),
    )

    # Create BigQuery table if needed
    try:
        create_table_if_not_exists()
    except Exception as e:
        logger.warning(f"Could not create BigQuery table: {e}")

    scraper = GoogleMapsScraper()
    parser_obj = GoogleMapsParser()

    await scraper.init()

    try:
        for idx, kecamatan_row in enumerate(kecamatan_list, 1):
            await scrape_kecamatan(scraper, parser_obj, storage, kecamatan_row, idx, len(kecamatan_list))

    except KeyboardInterrupt:
        logger.warning("Scraper interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await scraper.close()

    # Final stats
    stats = scraper.get_stats()
    logger.info("\n" + "=" * 80)
    logger.info("FINAL STATISTICS")
    logger.info("=" * 80)
    logger.info(f"Total searches: {stats['searches']}")
    logger.info(f"Total merchants found: {stats['merchants_found']}")
    logger.info(f"Blocking events: {stats['blocks']}")
    logger.info(f"Errors: {stats['errors']}")
    logger.info(f"Total time: {stats['total_time']/3600:.1f} hours ({stats['total_time']/86400:.2f} days)")
    logger.info(f"Avg time per search: {stats['avg_time_per_search']:.2f}s")
    logger.info(f"End time: {datetime.now().isoformat()}")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
