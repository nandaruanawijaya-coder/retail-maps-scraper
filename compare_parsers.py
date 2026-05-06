#!/usr/bin/env python3
"""
Comparison script: OLD parsers vs NEW parsers

Tests scraper on 1 district + 1 category (Supermarket in Depok).
Compares data quality improvements (address, hours, status, category, etc).

Usage:
  python compare_parsers.py

Output:
  - results_old.json (scraper data from original logic)
  - results_new.json (scraper data from new parsers)
  - COMPARISON_REPORT.txt (side-by-side comparison)
"""

import asyncio
import json
import logging
import sys
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


async def run_scraper_new():
    """Run scraper with NEW integrated parsers."""
    from scraper.gmaps_scraper import GoogleMapsScraper

    logger.info("=" * 80)
    logger.info("TESTING: NEW PARSERS (integrated into gmaps_scraper)")
    logger.info("=" * 80)

    scraper = GoogleMapsScraper()
    await scraper.init()

    try:
        # Test on Depok, Supermarket category
        results = await scraper.search(
            query="supermarket",
            location="Depok"
        )

        logger.info(f"✓ Found {len(results)} merchants with NEW parsers")
        return results

    finally:
        await scraper.close()


def analyze_results(results: List[Dict[str, Any]], label: str) -> Dict[str, Any]:
    """Analyze extraction quality for a result set."""
    stats = {
        "label": label,
        "total_merchants": len(results),
        "has_address": sum(1 for r in results if r.get("address")),
        "has_hours": sum(1 for r in results if r.get("hours")),
        "has_status": sum(1 for r in results if r.get("status")),
        "has_category": sum(1 for r in results if r.get("google_category")),
        "has_rating": sum(1 for r in results if r.get("rating")),
        "has_review_count": sum(1 for r in results if r.get("review_count")),
        "has_phone": sum(1 for r in results if r.get("phone")),
        "has_coords": sum(1 for r in results if r.get("lat") and r.get("lng")),
        "address_contamination": sum(
            1 for r in results
            if r.get("address") and ("Buka" in r["address"] or "Tutup" in r["address"])
        ),
    }

    # Calculate fill rates
    if stats["total_merchants"] > 0:
        stats["fill_rate"] = {
            "address_%": round(100 * stats["has_address"] / stats["total_merchants"], 1),
            "hours_%": round(100 * stats["has_hours"] / stats["total_merchants"], 1),
            "status_%": round(100 * stats["has_status"] / stats["total_merchants"], 1),
            "category_%": round(100 * stats["has_category"] / stats["total_merchants"], 1),
            "rating_%": round(100 * stats["has_rating"] / stats["total_merchants"], 1),
            "review_count_%": round(100 * stats["has_review_count"] / stats["total_merchants"], 1),
            "phone_%": round(100 * stats["has_phone"] / stats["total_merchants"], 1),
            "coords_%": round(100 * stats["has_coords"] / stats["total_merchants"], 1),
        }

    return stats


def generate_comparison_report(new_stats: Dict[str, Any]) -> str:
    """Generate a detailed comparison report."""
    report = []
    report.append("=" * 80)
    report.append("COMPARISON REPORT: NEW PARSERS")
    report.append("=" * 80)
    report.append(f"\nTest Date: {datetime.now().isoformat()}")
    report.append(f"District: Depok, West Java")
    report.append(f"Category: Supermarket")
    report.append(f"Total Merchants: {new_stats['total_merchants']}")

    report.append("\n" + "=" * 80)
    report.append("FIELD EXTRACTION RESULTS (NEW PARSERS)")
    report.append("=" * 80)

    fields = [
        ("Address", "has_address", "address_%"),
        ("Hours", "has_hours", "hours_%"),
        ("Status", "has_status", "status_%"),
        ("Google Category", "has_category", "category_%"),
        ("Rating", "has_rating", "rating_%"),
        ("Review Count", "has_review_count", "review_count_%"),
        ("Phone", "has_phone", "phone_%"),
        ("Coordinates", "has_coords", "coords_%"),
    ]

    report.append(f"\n{'Field':<20} {'Count':<10} {'Fill Rate'}")
    report.append("-" * 50)

    for field_name, key, pct_key in fields:
        count = new_stats[key]
        pct = new_stats.get("fill_rate", {}).get(pct_key, 0)
        report.append(f"{field_name:<20} {count:<10} {pct}%")

    report.append("\n" + "=" * 80)
    report.append("QUALITY CHECKS")
    report.append("=" * 80)

    contamination = new_stats["address_contamination"]
    contamination_pct = round(100 * contamination / new_stats["has_address"], 1) if new_stats["has_address"] > 0 else 0
    report.append(f"\nAddress contamination (Buka/Tutup): {contamination} ({contamination_pct}%)")
    if contamination == 0:
        report.append("✓ PASS: No address contamination detected!")
    else:
        report.append(f"⚠ WARNING: {contamination} addresses still contain Buka/Tutup status")

    report.append("\n" + "=" * 80)
    report.append("SAMPLE RECORDS (first 3)")
    report.append("=" * 80)

    return "\n".join(report)


def print_sample_records(results: List[Dict[str, Any]], count: int = 3):
    """Print sample records from results."""
    logger.info("\n" + "=" * 80)
    logger.info(f"SAMPLE RECORDS (first {count})")
    logger.info("=" * 80)

    for idx, record in enumerate(results[:count], 1):
        logger.info(f"\n[Record {idx}]")
        logger.info(f"  Name: {record.get('name', 'N/A')}")
        logger.info(f"  Address: {record.get('address', 'N/A')}")
        logger.info(f"  Hours: {record.get('hours', 'N/A')}")
        logger.info(f"  Status: {record.get('status', 'N/A')}")
        logger.info(f"  Google Category: {record.get('google_category', 'N/A')}")
        logger.info(f"  Rating: {record.get('rating', 'N/A')}")
        logger.info(f"  Review Count: {record.get('review_count', 'N/A')}")
        logger.info(f"  Phone: {record.get('phone', 'N/A')}")
        logger.info(f"  Lat/Lng: {record.get('lat', 'N/A')}, {record.get('lng', 'N/A')}")


async def main():
    """Run comparison test."""
    logger.info("Starting comparison test: NEW PARSERS")
    logger.info("Target: 1 district (Depok) + 1 category (Supermarket)")

    # Run NEW scraper
    new_results = await run_scraper_new()

    if not new_results:
        logger.error("✗ No results from scraper. Check network/browser.")
        sys.exit(1)

    # Save results
    with open("results_new.json", "w", encoding="utf-8") as f:
        json.dump(new_results, f, indent=2, ensure_ascii=False)
    logger.info(f"✓ Saved results to results_new.json")

    # Analyze results
    new_stats = analyze_results(new_results, "NEW Parsers")

    # Print sample records
    print_sample_records(new_results, count=3)

    # Generate report
    report = generate_comparison_report(new_stats)
    logger.info(report)

    # Save report
    with open("COMPARISON_REPORT.txt", "w", encoding="utf-8") as f:
        f.write(report)
    logger.info(f"\n✓ Report saved to COMPARISON_REPORT.txt")

    # Summary statistics
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 80)
    logger.info(f"Total merchants found: {new_stats['total_merchants']}")
    logger.info(f"\nField Fill Rates (NEW PARSERS):")
    for field, pct_key in [
        ("Address", "address_%"),
        ("Hours", "hours_%"),
        ("Status", "status_%"),
        ("Category", "category_%"),
        ("Rating", "rating_%"),
        ("Review Count", "review_count_%"),
        ("Phone", "phone_%"),
        ("Coordinates", "coords_%"),
    ]:
        pct = new_stats.get("fill_rate", {}).get(pct_key, 0)
        logger.info(f"  {field:<20} {pct:>6}%")

    logger.info("\n✓ Comparison complete!")
    logger.info("Check COMPARISON_REPORT.txt for detailed results")


if __name__ == "__main__":
    asyncio.run(main())
