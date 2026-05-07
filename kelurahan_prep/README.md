# Kelurahan Data Preparation

Separate utility to fetch kelurahan-level data from BigQuery for scraping.

## Files

- `fetch_kelurahan.py` - Standalone Python script to fetch kelurahan data from BigQuery

## Usage

```bash
python3 fetch_kelurahan.py [output_file]
```

### Examples

Fetch and save to default location:
```bash
python3 fetch_kelurahan.py
```

Fetch and save to custom location:
```bash
python3 fetch_kelurahan.py ../data/input/kelurahan_prioritized.csv
```

## Output

CSV file with columns:
- `kelurahan_id` - Concatenated province/kabupaten/kecamatan/kelurahan code
- `provinsi_name` - Province name
- `kabupaten_name` - District (kabupaten) name
- `kecamatan_name` - Sub-district (kecamatan) name
- `kelurahan_name` - Village (kelurahan) name
- `numVisit` - Number of visits (visit count from retail_visit_ssot)

Data is ordered by `numVisit` descending (most visited first).

## Data Source

Query from:
- `merchant_success_analytics.retail_visit_ssot` - Visit events
- `trb_pymnts_derived.geojson_indo_lookup` - Kelurahan ID lookup

Total: 4,349 kelurahan with 262,990 visits
