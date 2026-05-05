# Project Status & Prioritization Summary

**Project**: Google Maps Merchant Scraper — Indonesia Retail TAM  
**Status**: 🟢 Production Ready  
**Last Updated**: 2026-05-05  
**Current Run**: Top 50 Priority Districts (110,436 visits)

---

## 📊 Prioritization Strategy

### The Problem
Indonesia has 7,268 kecamatan (sub-districts). Scraping all of them would take 12–15 days. However, not all districts are equally important for market analysis — some have 10× the retail activity of others.

### The Solution
Prioritize based on **historical visit data** from `merchant_success_analytics.retail_visit_ssot` (internal analytics).

**Query** (in `export_data/district_priority.sql`):
```sql
SELECT
    provinsi_name, kabupaten_name, kecamatan_name,
    COUNT(DISTINCT id) as numVisit
FROM merchant_success_analytics.retail_visit_ssot
GROUP BY ALL
ORDER BY numVisit DESC
```

### Priority Distribution (1,009 Districts with Visits)

```
┌─────────────────────────────────────────────────────────────┐
│ Cumulative Visit Distribution                               │
├─────────────────────────────────────────────────────────────┤
│ Top 10 districts:    35,509 visits   (16.1% of total)      │
│ Top 50 districts:   110,436 visits   (50.0% of total) ← [*] │
│ Top 100 districts:  155,656 visits   (70.9% of total)      │
│ Top 500 districts:  197,000 visits   (89.5% of total)      │
│ All 1,009 districts: 220,038 visits (100.0% of total)      │
└─────────────────────────────────────────────────────────────┘
[*] = Current production run
```

### Time-ROI Trade-off

| Scope | Districts | Searches | Est. Time | Visit Coverage | Notes |
|-------|-----------|----------|-----------|----------------|-------|
| Test | 5 | 105 | 5 min | 0.05% | Validation only |
| Pilot | 10 | 210 | 10 min | 0.2% | Quick test |
| Small | 50 | 1,050 | 25 hours | **50.0%** | ← **CURRENT RUN** |
| Medium | 100 | 2,100 | 35 hours | **70.9%** | Good coverage |
| Large | 500 | 10,500 | 175 hours | **89.5%** | Full regional reach |
| Full | 1,009 | 21,189 | 200+ hours | **100%** | Complete enumeration |

### Top 20 Priority Districts (by Visits)

| Rank | District | Kabupaten | Provinsi | Visits | % of Total |
|------|----------|-----------|----------|--------|-----------|
| 1 | Rappocini | Kota Makassar | Sulawesi Selatan | 6,558 | 2.98% |
| 2 | Percut Sei Tuan | Deli Serdang | Sumatera Utara | 4,425 | 2.01% |
| 3 | Kebayoran Baru | Kota Admin. Jakarta Selatan | DKI Jakarta | 4,322 | 1.96% |
| 4 | Tamalate | Kota Makassar | Sulawesi Selatan | 4,111 | 1.87% |
| 5 | Cipayung | Kota Admin. Jakarta Timur | DKI Jakarta | 3,999 | 1.82% |
| 6 | Ciracas | Kota Admin. Jakarta Timur | DKI Jakarta | 3,876 | 1.76% |
| 7 | Setiabudi | Kota Admin. Jakarta Selatan | DKI Jakarta | 3,754 | 1.71% |
| 8 | Mampang Prapatan | Kota Admin. Jakarta Selatan | DKI Jakarta | 3,744 | 1.70% |
| 9 | Panakkukang | Kota Makassar | Sulawesi Selatan | 3,592 | 1.63% |
| 10 | Somba Opu | Gowa | Sulawesi Selatan | 3,462 | 1.57% |
| 11 | Jagakarsa | Kota Admin. Jakarta Selatan | DKI Jakarta | 3,367 | 1.53% |
| 12 | Biringkanaya | Kota Makassar | Sulawesi Selatan | 3,343 | 1.52% |
| 13 | Manggala | Kota Makassar | Sulawesi Selatan | 3,214 | 1.46% |
| 14 | Tamalanrea | Kota Makassar | Sulawesi Selatan | 3,194 | 1.45% |
| 15 | Pasar Minggu | Kota Admin. Jakarta Selatan | DKI Jakarta | 3,179 | 1.45% |
| 16 | Sunggal | Deli Serdang | Sumatera Utara | 3,116 | 1.42% |
| 17 | Pancoran | Kota Admin. Jakarta Selatan | DKI Jakarta | 2,952 | 1.34% |
| 18 | Duren Sawit | Kota Admin. Jakarta Timur | DKI Jakarta | 2,913 | 1.32% |
| 19 | Denpasar Selatan | Kota Denpasar | Bali | 2,762 | 1.26% |
| 20 | Cimanggis | Kota Depok | Jawa Barat | 2,729 | 1.24% |

**Key Insight**: Top 3 cities = 30% of visits
- Makassar (Sulawesi Selatan): 7 districts in top 20
- Jakarta (DKI): 8 districts in top 20
- Medan (Sumatera Utara): 3 districts in top 20

---

## 🎯 Current Run (2026-05-05)

### Run Configuration
```bash
python3 run_parallel.py --sample 50
```

### Parameters
| Parameter | Value |
|-----------|-------|
| Scope | Top 50 priority districts |
| Total Searches | 50 districts × 21 categories = **1,050** |
| Parallel Workers | 2 (Playwright browsers) |
| Search Speed | 6.2 seconds/search (avg) |
| Est. Duration | **~25 hours** |
| Start Time | 2026-05-05 12:45:30 UTC |
| Visit Coverage | **50% of total activity** (110,436 visits) |
| Expected Merchants | ~2,000–2,500 per district = **100,000–125,000 total** |

### Monitoring Commands
```bash
# Real-time progress
tail -f logs/scraper_parallel.log

# Count completed kecamatan
cat progress_parallel.json | python3 -m json.tool | wc -l

# BigQuery count (live)
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) FROM `ledger-fcc1e.retail_payment_base.merchants_gmaps` WHERE DATE(scraped_at) = CURRENT_DATE()'

# Check which district is currently processing
tail -20 logs/scraper_parallel.log | grep "Scraping"
```

---

## 📈 Expected Deliverables

### Post-Run (25 hours from start)

**BigQuery Table**: `ledger-fcc1e.retail_payment_base.merchants_gmaps`
- **Rows**: ~100,000–125,000 merchants
- **Kecamatan**: 50 unique
- **Categories**: 21 per kecamatan
- **Key Metrics**:
  - Lat/Lng coverage: ~99.7% (estimated)
  - Review count coverage: ~83.3% (estimated)
  - Address coverage: ~98% (estimated)

**Local Output**: `data/output/`
- **CSV files**: 50 (one per district, e.g., `7371013.csv`)
- **JSON files**: 50 (same, JSON format)
- **Raw files**: 1,050 (audit trail, e.g., `7371013_restaurant.json`)

**Progress Checkpoint**: `progress_parallel.json`
- Maps 50 kecamatan to completed categories
- Enables resumption if interrupted

### Query Examples (Post-Run)

**Total merchants by category:**
```sql
SELECT our_category, COUNT(*) as count
FROM `ledger-fcc1e.retail_payment_base.merchants_gmaps`
WHERE DATE(scraped_at) = '2026-05-05'
GROUP BY our_category
ORDER BY count DESC
```

**Merchants by top districts:**
```sql
SELECT kecamatan_name, COUNT(*) as count, ROUND(AVG(rating), 2) as avg_rating
FROM `ledger-fcc1e.retail_payment_base.merchants_gmaps`
WHERE DATE(scraped_at) = '2026-05-05'
GROUP BY kecamatan_name
ORDER BY count DESC
LIMIT 20
```

**Regional summary (city-level):**
```sql
SELECT kabupaten_name, COUNT(*) as merchants, COUNT(DISTINCT kecamatan_name) as kecamatan
FROM `ledger-fcc1e.retail_payment_base.merchants_gmaps`
WHERE DATE(scraped_at) = '2026-05-05'
GROUP BY kabupaten_name
ORDER BY merchants DESC
```

---

## 🔄 After This Run

### Option 1: Expand Coverage
Run next batch of 50 districts (51–100) or all remaining (100–1,009):
```bash
# Remove progress file to start fresh set
rm progress_parallel.json

# Run next 50
python3 run_parallel.py --sample 50

# Or jump to medium (100 total)
python3 run_parallel.py --sample 100
```

### Option 2: Deep Dive into Top 50
Analyze patterns, export insights:
```sql
-- Export to CSV for analysis
bq extract \
  --destination_format=CSV \
  ledger-fcc1e:retail_payment_base.merchants_gmaps \
  gs://your-bucket/merchants_top50_$(date +%Y%m%d).csv
```

### Option 3: Iterate on Quality
If coverage metrics need improvement, adjust:
1. **Phone coverage**: Add Selenium + OCR (trades speed for detail)
2. **Review count**: Click detail pages (trades speed for 100% coverage)
3. **Address completeness**: Add reverse geocoding

---

## 🚀 Quick Reference: Next Steps

### If Run Completes Successfully ✅
1. Export results: `bq extract ... gs://bucket/merchants.csv`
2. Validate counts & coverage in BigQuery
3. Decide: Expand to 100? Or analyze current 50?
4. Document findings & insights

### If Run Interrupts ⚠️
1. Kill scraper: `pkill -f run_parallel.py`
2. Check progress: `cat progress_parallel.json | python3 -m json.tool`
3. Resume: `python3 run_parallel.py --resume`
4. No data loss — checkpoint system saves state

### If Run Fails 🔴
1. Check logs: `tail -200 logs/scraper_parallel.log | grep -i error`
2. Common issues:
   - Google blocking: Wait 30–60 min, retry
   - BigQuery auth: Run `gcloud auth application-default login`
   - Network: Check `ping google.com`, restart if needed
3. Re-run after fixing root cause (resumable)

---

## 📚 Documentation Structure

```
README.md              ← Start here (objectives, setup, quick start)
ARCHITECTURE.md        ← Technical deep-dive (system design, components)
OPERATIONS.md          ← Runbook (monitoring, troubleshooting, emergency procedures)
DATA_DICTIONARY.md     ← Schema reference (all 24 fields, coverage, examples)
PROJECT_STATUS.md      ← This file (prioritization, current run, next steps)
```

---

## 🔗 Key Files

### Input Data
- **`data/input/districts.csv`**: All 7,268 kecamatan (305 KB)
- **`data/input/districts_prioritized.csv`**: 1,009 priority districts (38 KB) ← **USED BY DEFAULT**
- **`export_data/district_priority.sql`**: Query to fetch priority data

### Configuration
- **`scraper/config.py`**: 21 categories, output schema, constants
- **`requirements.txt`**: Dependencies (playwright, google-cloud-bigquery, pandas, psycopg2)

### Scraper Code
- **`run_parallel.py`**: Main orchestrator (entry point)
- **`scraper/gmaps_scraper.py`**: Playwright browser automation
- **`scraper/gmaps_parser.py`**: DOM extraction & parsing
- **`scraper/deduplicator.py`**: Merge duplicates by google_id
- **`scraper/storage.py`**: CSV/JSON/checkpoint saving
- **`scraper/bigquery_uploader.py`**: Cloud upload

### Runtime Files
- **`progress_parallel.json`**: Checkpoint (resumable state)
- **`logs/scraper_parallel.log`**: Main log file
- **`data/output/{district_id}.csv`**: Final output per district
- **`data/raw/{district_id}_{category}.json`**: Audit trail

---

## 👥 Team Checklist

- [ ] Read README.md for high-level overview
- [ ] Verify district data loaded (`ls data/input/districts_prioritized.csv`)
- [ ] Test with `python3 run_parallel.py --sample 5` (5 min)
- [ ] Check BigQuery table exists (`bq show ledger-fcc1e:retail_payment_base.merchants_gmaps`)
- [ ] Start production run: `python3 run_parallel.py --sample 50`
- [ ] Monitor logs: `tail -f logs/scraper_parallel.log`
- [ ] Set reminder for ETA (25 hours from start)
- [ ] Post-run: Query results and validate coverage

---

## 📞 Support

**Issue**: Scraper not starting?
→ Check: Python 3.9+, dependencies installed, Google Cloud auth

**Issue**: Slow progress?
→ Check: Network connection, Google Maps throttling (wait 5–30 min)

**Issue**: BigQuery insert failures?
→ Check: Table schema, auth, quota

**Issue**: Lost progress?
→ Solution: Resume with `--resume` (checkpoint-safe)

See **OPERATIONS.md** for detailed troubleshooting.

---

## 📊 Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Lat/Lng Coverage | >99% | ✅ Achieved (99.7% in test) |
| Review Count Coverage | >80% | ✅ Achieved (83.3% in test) |
| Deduplication Rate | >95% | ✅ Achieved (0 dupes in test) |
| BigQuery Upload | 100% success | ✅ 1,995/1,995 rows in test |
| Production Speed | <7 sec/search avg | ✅ 6.2 sec/search in test |
| Run Completion | 25 hours for 50 dists | 🔄 In progress |

---

**Version**: 1.0  
**Last Updated**: 2026-05-05  
**Author**: Nanda Ruanawijaya  
**Status**: 🟢 Production Ready, 🔄 Active Run
