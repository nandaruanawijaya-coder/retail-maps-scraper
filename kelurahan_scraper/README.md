# Kelurahan-Level Google Maps Scraper

Scrapes merchant data at kelurahan level (sub-sub-district granularity).
Uploads to separate BigQuery table to preserve kecamatan-level data.

## Search Format

```
[Category] in Kelurahan [kelurahan_name], Kecamatan [kecamatan_name], [kabupaten_name], [provinsi_name]
```

**Example**: `restaurant in Kelurahan Lembang, Kecamatan Lembang, Bandung Barat, Jawa Barat`

## Files

- `gmaps_scraper_kelurahan.py` - Kelurahan-specific Playwright scraper with full extraction
- `bigquery_uploader_kelurahan.py` - BigQuery uploader (table: `merchants_gmaps_kelurahan`)
- `run_kelurahan.py` - Main execution script with resume capability
- `logs/` - Timestamped log files per run
- `progress_kelurahan.json` - Resumable state (added to .gitignore)

## BigQuery Table

**Table ID:** `ledger-fcc1e.retail_payment_base.merchants_gmaps_kelurahan`

**Schema (19 fields)**:
- `google_id` (string) - Hash of name + address
- `name`, `address` (string)
- `lat`, `lng` (float) - 99.1% coverage
- `rating` (float) - 83% coverage
- `review_count` (int) - 83% coverage
- `phone` (string) - 45% coverage
- `hours` (string) - Operating hours
- `google_category` (string) - Google Maps category
- `status` (string) - Open/closed status
- `our_category`, `vertical` (string)
- `kelurahan_name`, `kecamatan_name`, `kabupaten_name`, `provinsi_name` (string)
- `kelurahan_id` (string) - Kelurahan identifier
- `scraped_at` (timestamp) - Partitioning key, clustered with kelurahan_name + our_category

## Usage

### Basic: Run top N from general kelurahan list
```bash
python3 run_kelurahan.py --top 50
python3 run_kelurahan.py --top 100
```

### Bandung Region: 505 kelurahan
```bash
# Run kelurahan 1-60
python3 run_bandung_100.py --top 60

# Run kelurahan 61-100 (recommended with caffeinate)
caffeinate -i python3 run_bandung_61_100.py
```

### Create Bandung region CSV (if needed)
```bash
python3 filter_bandung_kelurahan.py
# Outputs: data/input/bandung_kelurahan.csv (505 kelurahan)
```

### Resume from interruption
```bash
# Automatically detects progress_kelurahan.json
# Skips completed combinations, continues from last incomplete kelurahan
caffeinate -i python3 run_bandung_61_100.py
```

## Prerequisites

1. Kelurahan data must exist:
   ```bash
   ls data/input/kelurahan_prioritized.csv
   # or: data/input/bandung_kelurahan.csv
   ```

2. BigQuery authentication:
   ```bash
   gcloud auth application-default login
   ```

## Data Isolation

- **Kecamatan-level**: Table `merchants_gmaps` (unchanged)
- **Kelurahan-level**: Table `merchants_gmaps_kelurahan` (NEW)

Both tables coexist. No data loss.

## Performance

- **Per kelurahan**: 30 categories
- **Throughput**: ~1,200 searches per 40 kelurahan
- **With 2 parallel scrapers**: ~2-3 hours per 40 kelurahan
- **With caffeinate**: Prevents Mac from sleeping during long runs

**Example**: Top 100 Bandung kelurahan
- Total: 3,000 searches (100 × 30)
- Time: ~4-5 hours
- Resumable with progress tracking

## Progress Tracking

The scraper maintains `progress_kelurahan.json` with completed kelurahan-category pairs:

```json
{
  "completed": [
    "3173008004.0_laundry",
    "3173008004.0_toko_kelontong",
    ...
  ]
}
```

**Resumable behavior**:
- If interrupted mid-run, restart same command
- Scraper loads progress, skips completed combinations
- Continues from next incomplete kelurahan
- Progress saved after each kelurahan completes

## Data Quality

- **Lat/Lng**: 99.1% coverage (extracted from href, no clicking needed)
- **Review Count**: 83% coverage (search results only)
- **Address**: 98% clean (contamination removed)
- **Merchants per kelurahan**: 100-500+ depending on category

## Workflow

```
Load kelurahan list (e.g., Bandung CSV with 505 entries)
                │
    ┌───────────┴───────────┐
    │                       │
  Browser 1              Browser 2
  (30 categories        (30 categories
   per kelurahan)        per kelurahan)
    │                       │
    ├─→ [Kelurahan 1]       │
    │   ├─→ Search Category 1
    │   ├─→ Extract 100-500 merchants
    │   ├─→ Parse lat/lng from href
    │   └─→ Deduplicate by google_id
    │                       ├─→ [Kelurahan 2]
    │                       │   (parallel)
    └─ Repeat for all 30 categories per kelurahan
              ↓
      Upload to BigQuery
      (after each kelurahan completes)
```
