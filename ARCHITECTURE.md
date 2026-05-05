# Architecture & Implementation Details

## System Design

### High-Level Flow

```
┌──────────────────┐
│ Priority Districts│  (1,009 kecamatan sorted by visit volume)
│   districts_     │
│  prioritized.csv │
└────────┬─────────┘
         │
         ├──────────────┬──────────────┐
         │              │              │
      Loop over    ╔════════════════╗   (Parallel)
      50 districts ║  Browser 1     ║  ╔════════════════╗
                   ║  (Playwright)  ║  ║  Browser 2     ║
                   ║                ║  ║  (Playwright)  ║
                   ╚════════════════╝  ╚════════════════╝
         │              │              │
    [Kecamatan A]       │              │  [Kecamatan A]
    21 categories       │              │  21 categories
    (batched)           │              │
         │              │              │
    [Cat 1, Cat 2]  [Cat 3, Cat 4]  [Cat 5, Cat 6]
    (parallel)         (parallel)      (parallel)
         │              │              │
    Google Maps API search queries
    (per category, per kecamatan)
         │              │              │
    Raw results (120–200 merchants per search)
         │              │              │
    ┌────┴──────────────┴──────────────┴────┐
    │  Parse & Extract Data                 │
    │  ├─ Lat/Lng from href (regex)        │
    │  ├─ Review count (hybrid parsing)    │
    │  ├─ Name, address (DOM text)         │
    │  └─ Rating (DOM text)                │
    └────┬─────────────────────────────────┘
         │
    ┌────┴──────────────────────────┐
    │  Deduplicator                 │
    │  (merge by google_id per      │
    │   kecamatan, union categories)│
    └────┬──────────────────────────┘
         │
    [Unique merchants for Kecamatan A]
         │
    ┌────┴──────────────────────────┐
    │  Storage Manager              │
    │  ├─ CSV: data/output/         │
    │  ├─ JSON: data/output/        │
    │  └─ Progress: progress_      │
    │     parallel.json            │
    └────┬──────────────────────────┘
         │
    ┌────┴──────────────────────────┐
    │  BigQuery Uploader            │
    │  (batch insert after each     │
    │   kecamatan completes)        │
    └────┬──────────────────────────┘
         │
    ┌────┴──────────────────────────┐
    │  ledger-fcc1e:               │
    │  retail_payment_base.        │
    │  merchants_gmaps             │
    │  (partitioned by scraped_at, │
    │   clustered by kecamatan)    │
    └────────────────────────────────┘

    [Repeat for next kecamatan]
```

## Component Breakdown

### 1. **config.py** — Category Registry & Constants

Defines all 21 product categories with mappings:

```python
CATEGORIES = [
    {
        "name": "supermarket",
        "gmaps_query": "supermarket",  # Google Maps search term
        "vertical": "FMCG",
    },
    # ... 20 more
]

OUTPUT_FIELDS = [
    "google_id", "name", "address", "lat", "lng",
    "rating", "review_count", "phone", "website",
    # ... more fields
]

# Scraping parameters
REQUEST_DELAY_MIN = 0.5  # seconds between searches
REQUEST_DELAY_MAX = 2.5
HEADLESS = True
BROWSER_TIMEOUT = 15000  # ms
```

### 2. **gmaps_scraper.py** — Browser Automation & Extraction

**Class: GoogleMapsScraper**

#### `async def search(query, location, kecamatan, kabupaten, provinsi)`

Searches Google Maps for a single category in a specific location:

```python
# Input
query = "restaurant"
location = "Rappocini"
kecamatan = "Rappocini"
kabupaten = "Kota Makassar"
provinsi = "Sulawesi Selatan"

# Build search URL
url = f"https://www.google.com/maps/search/restaurant+in+Rappocini%2C+Kota+Makassar%2C+Sulawesi+Selatan"

# Navigate with Playwright
await self.page.goto(url, wait_until="domcontentloaded")

# Scroll to load all results (max 200 scrolls, 0.3s delay)
# Detect blocks (403, captcha) early
# Return list of merchant dicts
```

**Key optimizations:**
- Random delay before search: `get_random_delay()` (0.5–2.5s) to avoid detection
- Headless mode with anti-detection flags: `--disable-blink-features=AutomationControlled`
- Async/await for 2-worker parallelism
- Graceful timeout handling (page load, selector wait)

#### `async def _extract_results(search_term) -> List[Dict]`

Scrolls through Google Maps result panel to load all merchants:

```
DOM Structure:
<div class="Nv2PK">  ← merchant result card
  <a href="...maps/place/...!8m2!3d-8.67!4d120.42...">
    <div>Warung Jaya</div>  ← name
    <div>4.5</div>          ← rating
    <div>(127)</div>        ← review count
    <div>Jl. Sudirman...</div> ← address
</a>
</div>
```

**Scroll strategy:**
1. Wait for first result: `await page.wait_for_selector('div.Nv2PK', timeout=5000)`
2. Loop: scroll last element into view, wait 0.3s, check count increase
3. Stop when no new results for 15 consecutive scrolls (or max 200 scrolls)
4. Extract all `div.Nv2PK` elements at once

#### `async def _extract_from_element(element, idx) -> Dict`

Extracts data from a single merchant card element:

**Lat/Lng Extraction (99.7% coverage)**
```python
# Pattern 1: !8m2!3d[lat]!4d[lng]
coords_match = re.search(r'!8m2!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', href)
if coords_match:
    lat, lng = float(coords_match.group(1)), float(coords_match.group(2))

# Fallback Pattern 2: @[lat],[lng]
coords_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', href)
if coords_match:
    lat, lng = float(coords_match.group(1)), float(coords_match.group(2))
```

**Review Count Extraction (83.3% coverage)**
```python
# Step 1: Fast pattern (parentheses)
review_match = re.search(r"\((\d+)\)", text)
if review_match:
    review_count = int(review_match.group(1))

# Step 2: Robust parsing (K abbreviations, separators)
if review_count is None:
    review_count = parse_reviews_count_robust(text)
```

**Rating Extraction**
```python
rating_match = re.search(r"([\d],[\d]|[\d]\.[\d])", text)
if rating_match:
    rating_str = rating_match.group(1).replace(",", ".")
    rating = float(rating_str)
```

**Address Extraction**
```python
# Split by · separator (Google Maps format)
parts = text.split("·")
if len(parts) >= 2:
    addr_part = parts[1].strip()
    # Clean merged text like "noBuka" → "Buka"
    addr_part = re.sub(r'no([A-Z])', r' \1', addr_part)
```

### 3. **gmaps_parser.py** — Data Standardization

**Class: GoogleMapsParser**

```python
def parse_merchant(raw_data: dict, category: dict, district) -> Optional[dict]:
    """
    Convert raw Google Maps data to standard merchant record.
    Input: raw_data from scraper, category dict, District object
    Output: standardized merchant dict with all fields
    """
    return {
        "google_id": hash((name, address)) % 10**10,
        "name": raw_data["name"],
        "address": raw_data.get("address", ""),
        "lat": raw_data.get("lat"),
        "lng": raw_data.get("lng"),
        "rating": raw_data.get("rating"),
        "review_count": raw_data.get("review_count"),
        # ... location hierarchy from district object
        "our_category": category["name"],
        "vertical": category["vertical"],
        "kecamatan_name": district.kecamatan,
        # ... (12 fields total)
    }
```

### 4. **deduplicator.py** — Merge by ID

**Class: Deduplicator**

Merges duplicate merchants (same `google_id`) within a kecamatan:

```python
def add(merchant: dict):
    """Add merchant or merge if google_id exists."""
    gid = merchant["google_id"]
    if gid not in self.data:
        self.data[gid] = merchant
    else:
        # Merge categories if duplicate
        existing = self.data[gid]
        existing["categories"].append(merchant["our_category"])

def get_unique() -> List[dict]:
    """Return deduplicated merchants."""
    return list(self.data.values())
```

**Why deduplicate?** Same merchant can appear in multiple searches (e.g., "restaurant", "cafe" if it serves both). Merge by `google_id` to avoid double-counting.

### 5. **storage.py** — Local Storage & Checkpointing

**Class: StorageManager**

Manages CSV/JSON output and resumable progress:

```python
def save_csv(records: List[dict], kecamatan_id: str):
    """Save to data/output/{kecamatan_id}.csv"""

def save_json(records: List[dict], kecamatan_id: str):
    """Save to data/output/{kecamatan_id}.json"""

def save_raw(raw_results: List[dict], kecamatan_id: str, category: str):
    """Save to data/raw/{kecamatan_id}_{category}.json for audit"""

def is_done(kecamatan_id: str, category: str) -> bool:
    """Check progress_parallel.json — skip if already completed"""

def mark_done(kecamatan_id: str, category: str):
    """Update progress_parallel.json after successful scrape"""
```

**Progress Format** (`progress_parallel.json`):
```json
{
  "7371013": ["laundry", "toko_kelontong", "restaurant"],
  "1207026": ["laundry", "toko_kelontong"],
  ...
}
```

Resume logic: When restarted, read this file and skip any (kecamatan, category) pair already in the list.

### 6. **bigquery_uploader.py** — Cloud Storage

**Function: `upload_merchants_to_bigquery(records: List[dict]) -> bool`**

Streams merchant records to BigQuery using the client library:

```python
from google.cloud import bigquery

client = bigquery.Client(project="ledger-fcc1e")
table_id = "ledger-fcc1e.retail_payment_base.merchants_gmaps"

# Batch insert (default 10K rows, auto-paged)
errors = client.insert_rows_json(table_id, records)
if errors:
    logger.error(f"BigQuery insert errors: {errors}")
    return False
return True
```

**BigQuery Table Schema**:
- 24 fields (string, float, integer, timestamp)
- Partitioned by `scraped_at` (DATE)
- Clustered by `kecamatan_name`, `our_category`
- Auto-appends `scraped_at = CURRENT_TIMESTAMP()` on insert

### 7. **boundary.py** — Location Hierarchy

**Dataclass: District**

Simple container for kecamatan location info:

```python
@dataclass
class District:
    district_id: str
    kelurahan: str         # village
    kecamatan: str         # sub-district
    kabupaten: str         # district
    provinsi: str          # province
    district_name: str = None  # defaults to kecamatan

    def __post_init__(self):
        if self.district_name is None:
            self.district_name = self.kecamatan
```

Used to populate location fields in final merchant record.

### 8. **run_parallel.py** — Production Orchestrator

**Main Workflow:**

```python
async def main():
    # 1. Load priority districts (auto-detect districts_prioritized.csv)
    df = pd.read_csv("data/input/districts_prioritized.csv")
    kecamatan_list = df.to_dict("records")

    # 2. Filter by sample size (--sample 50 → top 50 districts)
    if args.sample > 0:
        kecamatan_list = kecamatan_list[:args.sample]

    # 3. Create BigQuery table if needed
    create_table_if_not_exists()

    # 4. Initialize 2 scrapers and parser
    scrapers = [GoogleMapsScraper() for _ in range(2)]
    for scraper in scrapers:
        await scraper.init()
    parser = GoogleMapsParser()

    # 5. Loop over kecamatan
    for kecamatan_data in kecamatan_list:
        await scrape_kecamatan_parallel(
            scrapers, parser, storage, kecamatan_data, num_parallel=2
        )

    # 6. Close browsers
    for scraper in scrapers:
        await scraper.close()
```

**Parallel Batch Logic**:

```python
async def scrape_kecamatan_parallel(scrapers, parser_obj, storage, kecamatan_data):
    """Scrape 21 categories for one kecamatan using 2 parallel browsers."""
    
    # Batch categories in groups of 2 (one per browser)
    for batch_idx in range(0, len(CATEGORIES), 2):
        batch = CATEGORIES[batch_idx:batch_idx + 2]
        tasks = []
        
        for cat_idx, cat in enumerate(batch):
            scraper = scrapers[cat_idx % 2]  # Alternate between browsers
            
            # Skip if already done (resumable)
            if storage.is_done(kecamatan_id, cat["name"]):
                continue
            
            # Async search + parse
            async def search_and_parse(scraper, cat):
                raw_results = await scraper.search(cat["gmaps_query"], kecamatan_name)
                storage.save_raw(raw_results, kecamatan_id, cat["name"])
                
                merchants = []
                for raw in raw_results:
                    merchant = parser_obj.parse_merchant(raw, cat, district)
                    if merchant:
                        merchants.append(merchant)
                        dedup.add(merchant)
                
                storage.mark_done(kecamatan_id, cat["name"])
                return len(raw_results)
            
            tasks.append(search_and_parse(scraper, cat))
        
        # Run both tasks concurrently
        if tasks:
            await asyncio.gather(*tasks)
    
    # Save final output after all categories done
    unique = dedup.get_unique()
    storage.save_csv(unique, kecamatan_id)
    storage.save_json(unique, kecamatan_id)
    
    # Upload to BigQuery
    upload_merchants_to_bigquery(unique)
```

## Performance Analysis

### Bottleneck Timeline (per search)

```
Random delay:           0.5–2.5s  ██████
Page load (wait_for):   1–3s      ███████
Scroll loop (200 max):  4–12s     ████████████████
DOM extraction:         0.2–0.5s  ██
Text parsing:           0.01s     █
─────────────────────────────────
Total:                  6–18s     (average 6.2s)
```

**Why scroll is slow**: 0.3s delay × ~20 scrolls = 6s just waiting for results to load. Google Maps intentionally throttles dynamic loading.

### Scaling Math

```
1 kecamatan × 21 categories × 6.2s/search = 130s ≈ 2 minutes
2 parallel workers (batching) → 1 minute per kecamatan
50 districts × 1 min = 50 minutes
```

**In practice**: ~25 hours for 50 districts because:
- Not all categories load 200 scrolls (some have <30 results)
- BigQuery uploads add 1–2 minutes per 2K merchants
- Network variance (DNS, page load fluctuation)

### Database Performance

**BigQuery clustering benefits**:
- Scans are filtered by `kecamatan_name` → reduces scanned data by ~99%
- Scans filtered by `our_category` → further 95% reduction
- Example query on 500M rows scans <1M rows

```sql
SELECT COUNT(*) FROM merchants_gmaps
WHERE kecamatan_name = 'Rappocini'
  AND our_category = 'restaurant'
  AND DATE(scraped_at) = '2026-05-05'
-- Scans ~2.5K rows (not 500M)
```

## Data Quality Decisions

### Why No Clicking for Reviews?

**Decision**: Accept 83% review_count coverage rather than click detail pages.

**Rationale**:
- Detail page click adds **6.5× overhead** (121s vs 18.5s for 116 merchants)
- Zero coverage improvement (same merchants, same review counts)
- Review count is secondary data (name, address, lat/lng are primary)
- User priority: "scrape all on search results + scroll, without clicking"

### Why Hybrid Review Parsing?

**Decision**: Use fast regex first, robust fallback for edge cases.

**Implementation**:
```python
# Fast (matches 70% of cases)
m = re.search(r"\((\d+)\)", text)
if m: return int(m.group(1))

# Robust (catches K notation, separators)
return parse_reviews_count_robust(text)
```

**Why?** Balances speed (avoid slow parsing) with coverage (catch variants).

### Why Deduplicate?

**Decision**: Merge merchants with same (name, address) within a kecamatan.

**Scenario**: Restaurant that serves food + has a bar listing under two categories.
- Without dedup: appears in "restaurant" AND "bar" → double-counted
- With dedup: one record with `categories = ["restaurant", "bar"]`

## Failure Modes & Mitigations

| Failure | Symptom | Mitigation |
|---------|---------|-----------|
| Google block (403/captcha) | Zero merchants returned | Detect in `page.content()`, backoff 5min, retry |
| Page load timeout | Stuck on navigate | `asyncio.wait_for(..., timeout=20)` + catch |
| Selector timeout | Results won't load | Return empty list, log, continue |
| BigQuery auth fail | No upload | Log warning, continue (save CSV anyway) |
| Duplicate google_id | Data inconsistency | Deduplicator merges, keeps first entry |
| Memory leak (Playwright) | Gradual slowdown | Close browsers between batches |

## Testing & Validation

### Sanity Checks

**End-to-End Test** (Wagir, Malang):
- ✅ 1,995 merchants scraped
- ✅ 1,990 lat/lng extracted (99.7%)
- ✅ 1,662 review counts (83.3%)
- ✅ 0 duplicates after dedup
- ✅ 1,995 rows inserted to BigQuery

**Query Validation**:
```sql
SELECT
    our_category,
    COUNT(*) as count,
    COUNTIF(lat IS NOT NULL) as with_coords,
    COUNTIF(review_count IS NOT NULL) as with_reviews
FROM merchants_gmaps
WHERE DATE(scraped_at) = '2026-05-05'
GROUP BY our_category
ORDER BY count DESC
```

Expected: review_count ~83% coverage across all categories.

## Future Optimization Ideas

1. **Multi-locale Search**: Prepend province name to query (e.g., "restaurant in Rappocini, Makassar, South Sulawesi") for disambiguation
2. **Detail Panel Optional**: Add `--with-reviews` flag to toggle clicking for 100% review coverage (at cost of 6.5× time)
3. **Caching Merchants**: Store seen google_id across all scrapes to avoid re-scraping same merchant in nearby kecamatan
4. **Map Screenshots**: Save map view with merchant annotations for manual validation
5. **Phone Number Extraction**: Send search URL to Selenium + OCR to extract visible phone numbers (currently 45% coverage)

---

**Version**: 1.0  
**Last Updated**: 2026-05-05
