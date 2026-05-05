# Kelurahan Feasibility Test Plan

## Test Objective
Determine whether scraping at **kelurahan level** (81,000 divisions) or **kecamatan level** (7,000 divisions) is feasible for Indonesia.

## Test Parameters
- **Location**: Jatinegara, Jakarta (1 kelurahan)
- **Categories**: All 28 categories
- **Rate Limiting**: Random delays 0.5-3 seconds between searches
- **Metrics Collected**:
  - Time per category
  - Merchants found per category
  - Blocking events detected
  - Errors encountered

## Expected Output
The test will calculate:

### Kelurahan Level (81,000 kelurahan)
```
Time per kelurahan = T seconds
Total time = T × 81,000 ÷ 3600 hours

Examples:
- If T = 60 seconds → 1,350 hours (56 days) ✓ FEASIBLE
- If T = 180 seconds → 4,050 hours (169 days) ✗ TOO LONG
- If T = 120 seconds → 2,700 hours (112 days) ~ BORDERLINE
```

### Kecamatan Level (7,000 kecamatan)
```
Time per kecamatan = T seconds  
Total time = T × 7,000 ÷ 3600 hours

Examples:
- If T = 60 seconds → ~117 hours (5 days) ✓ VERY FEASIBLE
- If T = 180 seconds → ~350 hours (15 days) ✓ FEASIBLE
```

## Feasibility Thresholds
- **< 30 days (720 hours)**: FEASIBLE - proceed
- **30-90 days**: BORDERLINE - consider smaller batches
- **> 90 days (2,160 hours)**: NOT FEASIBLE - need alternative approach

## Next Steps
1. Run test and get actual timings
2. Compare against thresholds
3. Make decision: kelurahan vs kecamatan vs hybrid
4. Plan full scrape accordingly

---
Test status: PENDING (waiting for browser install)
