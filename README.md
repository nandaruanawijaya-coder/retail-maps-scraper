# Google Maps Merchant Scraper — Indonesia Retail TAM

A high-performance web scraper for extracting merchant data (name, address, ratings, reviews, coordinates) from Google Maps across Indonesia's 7,268 kecamatan (sub-districts) and 21 retail product categories. Built for market analysis and regional TAM (Total Addressable Market) estimation.

## 🎯 Objectives

- **Comprehensive Coverage**: Capture 2,000–3,000 merchants per kecamatan across 21 FMCG and F&B categories
- **High Data Quality**: Extract 99%+ lat/lng accuracy, 83%+ review count coverage using search results without clicking
- **Regional Prioritization**: Focus on high-activity districts based on historical visit data (1,009 priority districts identified)
- **Automated Pipeline**: Scrape → deduplicate → CSV/JSON → BigQuery (real-time streaming)
- **Production Scale**: 2-worker parallel architecture targeting 12–15 days for 1,009 top districts

## 📊 Project Scope

### Geography
- **Total Kecamatan**: 7,268 across all Indonesian provinces
- **Priority Districts**: 1,009 with historical visit data, ranked by activity
  - Top 10: 35,509 visits (16.1% of total activity)
  - Top 50: 110,436 visits (50% of total activity)
  - Top 100: 155,656 visits (70.9% of total activity)
  - All 1,010: 220,038 visits (100% captured activity)

### Product Categories (21 Total)

**FMCG (10 categories)**
1. Supermarket
2. Convenience Store
3. Drugstore / Pharmacy
4. Hardware Store
5. Beauty Supply
6. Pet Store
7. Liquor Store
8. Toko Kelontong (traditional convenience)
9. Minimarket
10. Toko Sembako (dry goods shop)

**F&B (11 categories)**
11. Restaurant
12. Cafe
13. Bakery
14. Fast Food Restaurant
15. Meal Takeaway
16. Bar / Pub
17. Ice Cream Shop
18. Warung Makan (casual eatery)
19. Kedai Kopi (coffee shop)
20. Food Court
21. (Reserved for expansion)

## 🛠️ Technical Architecture

### Stack
- **Browser Automation**: Playwright (async/headless) — 2 parallel instances
- **Data Extraction**: Regex-based parsing from DOM and URL attributes
- **Deduplication**: In-memory hash by `name + address`
- **Storage**: CSV/JSON (local) + BigQuery (cloud streaming)
- **Language**: Python 3.9+

### Scraping Strategy

#### Lat/Lng Extraction (99.7% coverage)
Extract coordinates directly from merchant link `href` attributes using regex patterns — **no clicking required**:

```
Pattern 1: !8m2!3d[latitude]!4d[longitude]
Pattern 2: @[latitude],[longitude]
```

#### Review Count Extraction (83.3% coverage)
Hybrid approach using search results only:
1. **Fast pattern**: Simple regex `r"\((\d+)\)"` for `(123)` format
2. **Robust fallback**: Parse variants like "1.2K reviews", "1,234", "1 234" for remaining nulls

**Why search-results-only?** Clicking detail panels adds 6.5× overhead with zero coverage improvement.

### Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ Load Priority Districts (1,009 sorted by visit volume)      │
└──────────────────────┬──────────────────────────────────────┘
                       │
      ┌────────────────┴────────────────┐
      │                                 │
   Browser 1                        Browser 2
(Parallel Searches)             (Parallel Searches)
      │                                 │
      ├─→ [Kecamatan 1, Category 1]   │
      │   ├─→ Google Maps Search      │
      │   ├─→ Extract 120 merchants   │
      │   ├─→ Regex: coords + review  │
      │   └─→ Dedup merge             │
      │                               ├─→ [Kecamatan 1, Category 2]
      │                               │   └─→ (parallel)
      │
      └─ Repeat for all 21 categories per kecamatan
            ↓
      ┌─────────────────────────────────────┐
      │ Save CSV/JSON + Upload to BigQuery  │
      │ (After each kecamatan completes)    │
      └─────────────────────────────────────┘
```

## 📈 Performance Metrics

### Speed
- **Per-search baseline**: 6.2 seconds (21 categories × 50 districts ÷ 2 workers = ~25 hours)
- **Merchants per search**: 80–120 results (Google Maps default limit per query)
- **Deduplication overhead**: <2% (fast hash-based merge)

### Quality (Wagir, Malang test — 1,995 merchants)
- Lat/Lng: 1,990/1,995 (99.7% coverage)
- Review count: 1,662/1,995 (83.3% coverage)
- Valid entries: 100% (all records retain location + name)

## 📂 Project Structure

```
/Users/nanda.ruanawijaya/Documents/Buku/5. Retail/Scraper/
├── README.md                           # This file
├── run_parallel.py                     # Production CLI entry point
├── scraper/
│   ├── __init__.py
│   ├── boundary.py                     # District dataclass
│   ├── config.py                       # Categories, output schema, constants
│   ├── gmaps_scraper.py               # Playwright + DOM extraction
│   ├── gmaps_parser.py                # Raw data → standardized merchant dict
│   ├── deduplicator.py                # Merge by google_id, category union
│   ├── storage.py                      # CSV/JSON/progress checkpointing
│   ├── bigquery_uploader.py           # Streaming to BigQuery
│   └── requirements.txt                # Dependencies
├── data/
│   ├── input/
│   │   ├── districts.csv               # All 7,268 kecamatan (ID, name, hierarchy)
│   │   ├── districts_prioritized.csv   # 1,009 top districts (ranked by visits)
│   │   └── district_priority.sql       # SQL to fetch visit counts from source DB
│   ├── output/                         # Final CSV/JSON per kecamatan
│   │   └── {kecamatan_id}.csv
│   └── raw/                            # Raw Overpass/Google results (audit trail)
│       └── {kecamatan_id}_{category}.json
├── logs/
│   ├── scraper_parallel.log            # Main log file
│   └── run_sample_50.log               # Latest run
├── progress_parallel.json              # Resumable checkpoint: {kecamatan_id: [categories]}
└── export_data/
    └── district_priority.sql           # Query for BigQuery visit aggregation
```

## 🚀 Quick Start

### Prerequisites
```bash
python3 --version  # 3.9+
pip3 install -r scraper/requirements.txt
# Requires: Google Cloud SDK authenticated (gcloud auth application-default login)
```

### Run Scraper

**Test (5 districts):**
```bash
python3 run_parallel.py --sample 5
```

**Small Scale (50 priority districts, ~25 hours):**
```bash
python3 run_parallel.py --sample 50
```

**Large Scale (100 priority districts, ~35 hours):**
```bash
python3 run_parallel.py --sample 100
```

**Full Production (1,009 priority districts, ~200 hours / 8–9 days):**
```bash
python3 run_parallel.py --all
```

**Resume from Checkpoint:**
```bash
python3 run_parallel.py --resume
```

The scraper automatically detects and uses `districts_prioritized.csv` if present. To scrape all districts regardless of visit volume, rename/remove the prioritized file.

### Monitor Progress
```bash
# Real-time tail
tail -f logs/scraper_parallel.log

# Check BigQuery table
bq query --use_legacy_sql=false 'SELECT COUNT(*) as merchants, COUNT(DISTINCT kecamatan_name) as kecamatan FROM ledger-fcc1e.retail_payment_base.merchants_gmaps WHERE DATE(scraped_at) = CURRENT_DATE()'
```

## 📤 Output Schema

Each merchant record contains:

| Field | Type | Coverage | Notes |
|-------|------|----------|-------|
| google_id | string | 100% | Hash of (name, address) |
| name | string | 100% | Merchant name |
| address | string | 98% | Street address (from search results) |
| lat | float | 99.7% | Latitude (from href) |
| lng | float | 99.7% | Longitude (from href) |
| rating | float | 83% | Google rating 1–5 |
| review_count | integer | 83.3% | Total reviews |
| phone | string | 45% | Phone number (regex extracted) |
| website | string | 8% | Website URL |
| hours | string | 2% | Operating hours |
| price_range | string | 25% | $ to $$$$ |
| verified_badge | boolean | 5% | Google verified |
| our_category | string | 100% | e.g., "restaurant" |
| vertical | string | 100% | "FMCG" or "F&B" |
| kecamatan_name | string | 100% | Sub-district |
| kabupaten_name | string | 100% | District |
| provinsi_name | string | 100% | Province |
| district_id | integer | 100% | Unique kecamatan ID |
| scraped_at | timestamp | 100% | Query timestamp |

**BigQuery Table**: `ledger-fcc1e.retail_payment_base.merchants_gmaps`
- **Partitioning**: By `scraped_at` (date)
- **Clustering**: `kecamatan_name`, `our_category`

## 📊 Prioritization Rationale

The 1,009 priority districts are derived from `merchant_success_analytics.retail_visit_ssot` (internal visit analytics):

```sql
SELECT
    provinsi_name, kabupaten_name, kecamatan_name,
    COUNT(DISTINCT id) as numVisit
FROM merchant_success_analytics.retail_visit_ssot
GROUP BY ALL
ORDER BY numVisit DESC
```

**Distribution**:
- **Top 10 districts**: 16.1% of all visits → 6–8 hours of scraping
- **Top 50 districts**: 50% of all visits → 25 hours (current run)
- **Top 100 districts**: 70.9% of all visits → 35 hours
- **Top 1,009 districts**: 100% of visits in database → 200+ hours

Running against priority districts ensures **maximum ROI**: capture 70% of market activity in ~40% of full-run time.

## 🔄 Resumable Checkpointing

The scraper maintains `progress_parallel.json`:

```json
{
  "3507021": ["laundry", "toko_kelontong", "restaurant"],
  "1207026": ["laundry", "toko_kelontong"]
}
```

If interrupted, re-run with `--resume` to pick up where it left off. Already-scraped (kecamatan, category) pairs are skipped.

## 🛑 Known Limitations

1. **Review Count Gaps (17%)**: ~17% of merchants lack review counts in Google Maps search results (data availability, not extraction failure)
2. **Phone Coverage (45%)**: Phone numbers require manual inspection or detailed page access — search results have limited phone data
3. **Rate Limiting**: Google Maps may throttle after ~200–300 consecutive searches — backoff strategy (2–4s delay) mitigates but doesn't eliminate
4. **Headless Detection**: `--disable-blink-features=AutomationControlled` reduces but doesn't eliminate browser detection risk

## 🔐 Authentication

Requires **Google Cloud SDK** authentication for BigQuery uploads:

```bash
gcloud auth application-default login
```

Stores credentials in `~/.config/gcloud/` (not in repo).

## 📝 Example Output (CSV)

```csv
google_id,name,address,lat,lng,rating,review_count,phone,our_category,vertical,kecamatan_name,kabupaten_name,provinsi_name,district_id,scraped_at
gmaps_1234567890,Warung Makan Jaya,"Jl. Sudirman No. 42, Makassar",-8.6705,120.4216,4.5,127,0812345678,warung_makan,F&B,Rappocini,Kota Makassar,Sulawesi Selatan,7371013,2026-05-05T12:45:33Z
```

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'scraper.gmaps_scraper'"
```bash
pip3 install -r scraper/requirements.txt
```

### "BigQuery table not found"
```bash
bq mk --table ledger-fcc1e:retail_payment_base.merchants_gmaps scraper/schema.json
```

### Scraper hangs or slow progress
```bash
# Check system resources
top -o %MEM
# If memory high, reduce parallel workers (modify run_parallel.py: num_parallel=1)
```

### No output in `data/output/`
- Check `logs/scraper_parallel.log` for errors
- Verify BigQuery upload succeeded (check `scraped_at` timestamp)
- Confirm `progress_parallel.json` exists (marks completed kecamatan)

## 📚 References

- [Playwright Python Docs](https://playwright.dev/python/)
- [Google BigQuery Python Client](https://cloud.google.com/python/docs/reference/bigquery/latest)
- [Google Maps Search URL Structure](https://developers.google.com/maps)

## 📅 Current Status (2026-05-05)

- ✅ **Scraper Engine**: Production-ready, tested on Wagir (1,995 merchants)
- ✅ **Prioritization**: 1,009 districts ranked, top 50 (~110K visits) queued
- ✅ **BigQuery Pipeline**: Live streaming enabled
- 🔄 **Current Run**: `python3 run_parallel.py --sample 50` (started 12:45:30 UTC)
- 📈 **Expected ETA**: ~25 hours (all 50 districts + 21 categories)

---

**Built by**: Nanda Ruanawijaya  
**Last Updated**: 2026-05-05  
**License**: Internal Use Only
