#!/usr/bin/env python3
"""
Parallel scraper: 2 browser instances (kecamatan-level parallelization)
Processes multiple kecamatan in parallel with BigQuery uploads
Usage:
  python run_parallel.py --sample 5    (Trial: 5 kecamatan)
  python run_parallel.py --all         (Full: all 7,300 kecamatan, ~6-7 days)
  python run_parallel.py --resume      (Resume from progress_parallel.json)
"""
import asyncio
import argparse
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
            logging.FileHandler(os.path.join(log_dir, "scraper_parallel.log"), encoding="utf-8"),
        ],
    )


async def scrape_kecamatan_parallel(scrapers, parser_obj, storage, kecamatan_data, num_parallel=2):
    """Scrape all categories for one kecamatan using parallel searches."""
    kecamatan_id = str(kecamatan_data["district_id"])
    kecamatan_name = kecamatan_data["kecamatan_name"]
    kabupaten_name = kecamatan_data["kabupaten_name"]
    provinsi_name = kecamatan_data["provinsi_name"]

    logger = logging.getLogger(__name__)
    dedup = Deduplicator()

    logger.info(f"Scraping {kecamatan_name}, {kabupaten_name} with {num_parallel} parallel searches")

    # Process categories in batches
    for batch_idx in range(0, len(CATEGORIES), num_parallel):
        batch = CATEGORIES[batch_idx:batch_idx + num_parallel]

        # Create tasks for parallel execution
        tasks = []
        for cat_idx, cat in enumerate(batch):
            cat_name = cat["name"]
            gmaps_query = cat["gmaps_query"]
            scraper = scrapers[cat_idx % len(scrapers)]

            if storage.is_done(kecamatan_id, cat_name):
                logger.debug(f"  ✓ {cat_name} (already done)")
                continue

            async def search_and_parse(scraper, cat, kecamatan_id):
                try:
                    raw_results = await scraper.search(
                        query=cat["gmaps_query"],
                        location=kecamatan_name,
                        kecamatan=kecamatan_name,
                        kabupaten=kabupaten_name,
                        provinsi=provinsi_name
                    )
                    storage.save_raw(raw_results, kecamatan_id, cat["name"])

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

                    storage.mark_done(kecamatan_id, cat["name"])
                    logger.info(f"  {cat['name']:30s}: {len(raw_results):3d} merchants")
                    return len(raw_results)
                except Exception as e:
                    logger.error(f"Error for {cat['name']}: {e}")
                    return 0

            tasks.append(search_and_parse(scraper, cat, kecamatan_id))

        # Run tasks in parallel
        if tasks:
            await asyncio.gather(*tasks)

            # Brief pause between batches
            if batch_idx + num_parallel < len(CATEGORIES):
                await asyncio.sleep(2)

    # Save results
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
        
        # Merge with existing JSON if resuming (deduplication)
        import json
        import os
        json_path = os.path.join(storage.output_dir, f"{kecamatan_id}.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    existing_merchants = json.load(f)
                existing_ids = {m.get('google_id') for m in existing_merchants}
                new_merchants = [m for m in csv_records if m.get('google_id') not in existing_ids]
                merged = existing_merchants + new_merchants
                logger.info(f"Merged: {len(existing_merchants)} existing + {len(new_merchants)} new = {len(merged)} total")
                csv_records = merged
            except Exception as e:
                logger.warning(f"Could not merge existing JSON: {e}. Overwriting.")
        
        storage.save_json(csv_records, kecamatan_id)

        # Upload to BigQuery
        logger.info(f"Uploading {len(csv_records)} merchants to BigQuery...")
        upload_success = upload_merchants_to_bigquery(csv_records)
        if upload_success:
            logger.info(f"✓ Saved {len(unique)} unique merchants to {kecamatan_id} (BigQuery + CSV/JSON)")
        else:
            logger.warning(f"✓ Saved {len(unique)} unique merchants to {kecamatan_id} (CSV/JSON only, BigQuery failed)")
    else:
        logger.info(f"✓ No merchants found for {kecamatan_id}")


async def main():
    parser = argparse.ArgumentParser(description="Google Maps Merchant Scraper - Parallel 2-Worker")
    parser.add_argument("--sample", type=int, default=0,
                        help="Sample N kecamatan for testing")
    parser.add_argument("--all", action="store_true",
                        help="Scrape all ~7,300 kecamatan (will take ~6-7 days with 2 parallel workers)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from progress_parallel.json")
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    # Load kecamatan data - prefer prioritized list if available
    prioritized_file = os.path.join(BASE_DIR, "data", "input", "districts_prioritized.csv")
    districts_file = prioritized_file if os.path.exists(prioritized_file) else os.path.join(BASE_DIR, "data", "input", "districts.csv")

    if not os.path.exists(districts_file):
        logger.error(f"Districts file not found: {districts_file}")
        sys.exit(1)

    df = pd.read_csv(districts_file)
    using_prioritized = os.path.exists(prioritized_file)
    logger.info(f"Using {'PRIORITIZED' if using_prioritized else 'ALL'} districts file: {os.path.basename(districts_file)}")
    kecamatan_list = df.to_dict("records")

    if args.sample > 0:
        step = max(1, len(kecamatan_list) // args.sample)
        kecamatan_list = kecamatan_list[::step][:args.sample]

    logger.info("=" * 80)
    logger.info("PARALLEL SCRAPER - 2 BROWSER INSTANCES")
    logger.info("=" * 80)
    logger.info(f"Total kecamatan: {len(kecamatan_list):,}")
    logger.info(f"Total categories per kecamatan: {len(CATEGORIES)}")
    logger.info(f"Parallel browser instances: 2")
    logger.info(f"Total searches: {len(kecamatan_list) * len(CATEGORIES):,}")
    logger.info(f"Estimated time: {(len(kecamatan_list) * len(CATEGORIES) * 6.2 / 86400 / 2):.1f} days (at 6.2s/search, 2 parallel workers)")
    logger.info(f"BigQuery uploads: ENABLED")
    logger.info(f"Start time: {datetime.now().isoformat()}")
    logger.info("=" * 80)

    # Create BigQuery table if needed
    logger.info("Preparing BigQuery table...")
    try:
        create_table_if_not_exists()
    except Exception as e:
        logger.warning(f"Could not create BigQuery table: {e}")
        logger.warning("Continuing without BigQuery uploads")

    storage = StorageManager(
        output_dir=os.path.join(BASE_DIR, "data", "output"),
        raw_dir=os.path.join(BASE_DIR, "data", "raw"),
        progress_file=os.path.join(BASE_DIR, "progress_parallel.json"),
    )

    # Create 2 scraper instances
    scrapers = []
    for i in range(2):
        scraper = GoogleMapsScraper()
        await scraper.init()
        scrapers.append(scraper)

    parser_obj = GoogleMapsParser()

    try:
        for kecamatan_data in kecamatan_list:
            await scrape_kecamatan_parallel(scrapers, parser_obj, storage, kecamatan_data, num_parallel=2)

    except KeyboardInterrupt:
        logger.warning("Scraper interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        for scraper in scrapers:
            await scraper.close()

    # Final stats
    logger.info("\n" + "=" * 80)
    logger.info("PARALLEL TEST RESULTS")
    logger.info("=" * 80)
    logger.info(f"Test completed: {datetime.now().isoformat()}")
    logger.info("Check logs above for blocking/errors")
    logger.info("If no blocking detected, ready to scale to production")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
