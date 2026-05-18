# Google Maps Merchant Scraper — Indonesia Retail TAM

A high-performance web scraper for extracting merchant data (name, address, ratings, reviews, coordinates) from Google Maps across Indonesia at **kelurahan level** (sub-sub-district granularity). Supports 30 FMCG and F&B retail product categories. Built for hyperlocal market analysis and regional TAM (Total Addressable Market) estimation.

## 🎯 Objectives

- **Hyperlocal Coverage**: Capture 100–500+ merchants per kelurahan (sub-sub-district) across 30 FMCG and F&B categories
- **High Data Quality**: Extract 99.1%+ lat/lng accuracy, 83%+ review count coverage using search results without clicking
- **Regional Prioritization**: Focus on high-activity areas based on historical visit data (Bandung region: 505 kelurahan identified)
- **Automated Pipeline**: Scrape → deduplicate → BigQuery (incremental uploads per kelurahan)
- **Production Scale**: 2-worker parallel architecture targeting 2–4 hours per 40 kelurahan with caffeinate (prevents sleep)

## 📊 Project Scope

### Geography
- **Total Kelurahan**: 4,348+ across all Indonesian provinces
- **Current Focus**: Bandung Region (Kota Bandung, Bandung, Bandung Barat)
  - Total kelurahan in region: 505
  - Prioritized by visit history
  - Completed: Top 60 kelurahan (1,800 searches)
  - In progress: 61-100 (1,200 searches)

### Product Categories (30 Total)

**FMCG (15 categories)**
1. Toko Kelontong (traditional convenience)
2. Laundry
3. Pasar (market)
4. Toko Bahan Makanan (food supplies)
5. Stationery
6. Home Goods
7. Vape Store
8. Toko Sepatu (shoe store)
9. Toko Pakaian (clothing store)
10. Toko HP (phone store)
11. Apotek (pharmacy)
12. Agen Pulsa (phone credit)
13. Toko Oleh-Oleh (souvenir shop)
14. Toko Optik (optical store)
15. Barbershop

**F&B (15 categories)**
16. Restaurant
17. Cafe
18. Bakery
19. Warung Makan (casual eatery)
20. Warteg (traditional canteen)
21. Warung Padang (Padang cuisine)
22. Makanan Ringan (snack shop)
23. Cake Shop
24. Light Meal
25. Warung Ayam Goreng (fried chicken)
26. Rumah Mie (noodle shop)
27. Warung Boba (bubble tea)
28. Juice Bar
29. Nasi Kuning (yellow rice)
30. Tahu Goreng (fried tofu)

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
├── README.md                           # This file (main documentation)
├── IMPLEMENTATION_COMPLETE.md          # TDD parser implementation status
├── scraper/                            # Core scraper modules (kecamatan-level)
│   ├── config.py                       # Categories, output schema, constants
│   ├── gmaps_scraper.py               # Playwright + DOM extraction
│   ├── gmaps_parser.py                # Raw data → standardized merchant dict
│   ├── parsers.py                      # Pure parsing functions (99 tests)
│   ├── bigquery_uploader.py           # BigQuery uploader for merchants_gmaps
│   └── requirements.txt                # Dependencies
├── kelurahan_scraper/                  # Kelurahan-level scraper (sub-sub-district)
│   ├── README.md                       # Kelurahan-specific documentation
│   ├── gmaps_scraper_kelurahan.py     # Kelurahan search format + full extraction
│   ├── bigquery_uploader_kelurahan.py # BigQuery uploader for merchants_gmaps_kelurahan
│   ├── run_kelurahan.py               # Main execution script with progress tracking
│   ├── logs/                           # Kelurahan scraper logs
│   └── progress_kelurahan.json        # Resumable progress state (in .gitignore)
├── data/
│   ├── input/
│   │   ├── kelurahan_prioritized.csv   # All 4,348+ kelurahan (ID, name, hierarchy)
│   │   ├── bandung_kelurahan.csv       # 505 kelurahan filtered for Bandung region
│   │   └── districts_prioritized.csv   # Legacy: 1,009 priority kecamatan
│   └── output/                         # Final outputs
├── filter_bandung_kelurahan.py         # Script to filter Bandung region CSV
├── run_bandung_61_100.py               # Script to run kelurahan 61-100 from Bandung
└── logs/                               # Main logs directory
```

## 🚀 Quick Start

### Prerequisites
```bash
python3 --version  # 3.9+
pip3 install -r scraper/requirements.txt
# Requires: Google Cloud SDK authenticated (gcloud auth application-default login)
gcloud auth application-default login
```

### Kelurahan-Level Scraper (Current Focus)

**Run Bandung region (top 100 kelurahan with caffeinate):**
```bash
caffeinate -i python3 run_bandung_61_100.py
# Prevents Mac from sleeping during multi-hour run
```

**Run any 50 kelurahan:**
```bash
python3 -c "
import asyncio, os, sys, pandas as pd
sys.path.insert(0, 'kelurahan_scraper')
from run_kelurahan import scrape_kelurahan_batch

async def main():
    df = pd.read_csv('data/input/kelurahan_prioritized.csv')
    await scrape_kelurahan_batch(df.head(50).to_dict('records'), num_scrapers=2)

asyncio.run(main())
"
```

**Or use custom run scripts:**
```bash
python3 run_bandung_61_100.py          # Bandung 61-100 (40 kelurahan)
# Automatically resumes from saved progress if interrupted
```

### Monitor Progress

**Check running process:**
```bash
tail -f /tmp/bandung_61_100.log
```

**Check BigQuery:**
```bash
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) merchants, COUNT(DISTINCT kelurahan_name) kelurahan 
   FROM ledger-fcc1e.retail_payment_base.merchants_gmaps_kelurahan 
   WHERE DATE(scraped_at) = CURRENT_DATE()'
```

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

**BigQuery Tables**:
- **Kecamatan-level**: `ledger-fcc1e.retail_payment_base.merchants_gmaps` (original)
  - Partitioned by `scraped_at` (date)
  - Clustered by `kecamatan_name`, `our_category`
- **Kelurahan-level**: `ledger-fcc1e.retail_payment_base.merchants_gmaps_kelurahan` (NEW)
  - Partitioned by `scraped_at` (date)
  - Clustered by `kelurahan_name`, `our_category`
  - Includes additional fields: `kelurahan_id`, `kelurahan_name`

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

## 📅 Current Status (2026-05-18)

### Kecamatan-Level (Original Scope)
- ✅ **Engine**: Production-ready with 99-test parser TDD implementation
- ✅ **BigQuery**: Table `merchants_gmaps` with full data pipeline

### Kelurahan-Level (New/Current)
- ✅ **Scraper**: Full implementation with 30 categories
- ✅ **Bandung Region**: 505 kelurahan filtered and prioritized
- ✅ **Top 60 Kelurahan**: Completed (1,800 searches)
- 🔄 **Top 61-100**: In progress with caffeinate
- ✅ **BigQuery**: New table `merchants_gmaps_kelurahan` with kelurahan-level granularity
- ✅ **Resume Capability**: Progress tracking with automatic resumable checkpoints

### Data Quality
- **Lat/Lng Accuracy**: 99.1% coverage (extracted from href, no clicking)
- **Review Count**: 83%+ coverage (search results only)
- **Address Quality**: 98%+ after contamination removal
- **Merchant Count**: 100-500+ per kelurahan depending on category

---

**Built by**: Nanda Ruanawijaya  
**Last Updated**: 2026-05-18  
**License**: Internal Use Only
