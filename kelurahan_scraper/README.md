# Kelurahan-Level Google Maps Scraper

Separate scraper for kelurahan-level merchant data extraction.
Uploads to different BigQuery table to preserve kecamatan-level data.

## Search Format

```
[Category] in Kelurahan [kelurahan_name], Kecamatan [kecamatan_name], [kabupaten_name], [provinsi_name]
```

Example: `supermarket in Kelurahan Tidung, Kecamatan Rappocini, Kota Makassar, Sulawesi Selatan`

## Files

- `gmaps_scraper_kelurahan.py` - Kelurahan-specific Playwright scraper
- `bigquery_uploader_kelurahan.py` - BigQuery uploader (new table: `merchants_gmaps_kelurahan`)
- `run_kelurahan.py` - Main execution script

## BigQuery Table

**Table ID:** `ledger-fcc1e.retail_payment_base.merchants_gmaps_kelurahan`

Columns:
- google_id, name, address, lat, lng
- rating, review_count, phone, hours
- google_category, status
- our_category, vertical
- kelurahan_name, kecamatan_name, kabupaten_name, provinsi_name
- kelurahan_id
- scraped_at (partitioned by day, clustered by kelurahan_name + our_category)

## Usage

Scrape top 50 kelurahan:
```bash
python3 run_kelurahan.py --top 50
```

Scrape top 100 kelurahan:
```bash
python3 run_kelurahan.py --top 100
```

Scrape all 4,348 kelurahan:
```bash
python3 run_kelurahan.py --top 4348
```

## Prerequisites

1. Kelurahan data prepared:
   ```bash
   cd ../kelurahan_prep
   python3 fetch_kelurahan.py
   ```

2. BigQuery authentication (already configured for main scraper)

## Data Isolation

- **Kecamatan-level data:** `merchants_gmaps` table (unchanged)
- **Kelurahan-level data:** `merchants_gmaps_kelurahan` table (new)

Both tables coexist in the same dataset. No data loss.

## Performance

- Top 50 kelurahan × 30 categories = 1,500 searches
- With 2 parallel scrapers: ~2-3 hours
- Run with caffeinate to keep system awake:
  ```bash
  caffeinate -i python3 run_kelurahan.py --top 50
  ```
