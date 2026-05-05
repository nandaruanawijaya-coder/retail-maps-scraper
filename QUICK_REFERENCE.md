# Quick Reference Card

## 🚀 Start the Scraper

```bash
# Test run (5 min)
python3 run_parallel.py --sample 5

# Small run (25 hours) ← CURRENTLY RUNNING
python3 run_parallel.py --sample 50

# Medium run (35 hours)
python3 run_parallel.py --sample 100

# Full production (200+ hours)
python3 run_parallel.py --all

# Resume interrupted run
python3 run_parallel.py --resume
```

## 📊 Monitor Progress

```bash
# Real-time logs
tail -f logs/scraper_parallel.log

# Last 50 lines
tail -50 logs/scraper_parallel.log

# Filter for errors
tail -f logs/scraper_parallel.log | grep -i error

# How many districts completed
python3 -c "import json; print(f'Completed: {len(json.load(open(\"progress_parallel.json\")))} kecamatan')"

# Total merchants in BigQuery (today)
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) FROM `ledger-fcc1e.retail_payment_base.merchants_gmaps` WHERE DATE(scraped_at) = CURRENT_DATE()'
```

## ⏸️ Stop the Scraper

```bash
# Graceful stop (allows current batch to finish)
pkill -SIGTERM -f run_parallel.py

# Force kill (immediate)
pkill -9 -f run_parallel.py

# Check if running
ps aux | grep run_parallel.py | grep -v grep
```

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| "ModuleNotFoundError" | `pip3 install -r scraper/requirements.txt` |
| "BigQuery auth error" | `gcloud auth application-default login` |
| "Scraper hangs" | Check `tail -100 logs/scraper_parallel.log` for Google block |
| "No output files" | Check if categories marked done in `progress_parallel.json` |
| "Memory leak (slow)" | Kill and resume: `pkill -f run_parallel.py && python3 run_parallel.py --resume` |
| "Lost progress file" | Run again: `python3 run_parallel.py --sample 50` (will re-scrape but BigQuery dedupes) |

## 📈 Key Statistics

**Current Run** (Top 50 Priority Districts):
- **Districts**: 50
- **Total Searches**: 1,050 (50 × 21 categories)
- **Est. Merchants**: 100,000–125,000
- **Est. Duration**: 25 hours
- **Visit Coverage**: 50% of total activity

**Expected Coverage**:
- Lat/Lng: ~99.7%
- Review count: ~83.3%
- Address: ~98%

## 🔗 Quick Links

| Need | File |
|------|------|
| How to start | README.md |
| Tech details | ARCHITECTURE.md |
| Monitoring/troubleshooting | OPERATIONS.md |
| Data schema | DATA_DICTIONARY.md |
| Prioritization strategy | PROJECT_STATUS.md |
| All guides | DOCUMENTATION_INDEX.md |

## ✅ Pre-Run Checklist

- [ ] `python3 --version` → 3.9+
- [ ] `pip3 list | grep playwright` → installed
- [ ] `gcloud auth list` → authenticated
- [ ] `ls data/input/districts_prioritized.csv` → exists
- [ ] `bq show ledger-fcc1e:retail_payment_base.merchants_gmaps` → table exists
- [ ] `mkdir -p logs data/output` → directories exist
- [ ] Test run: `python3 run_parallel.py --sample 5` → passes

## 🎯 Current Status

✅ Documentation complete (6 guides)
✅ Prioritization implemented (1,009 districts ranked)
🔄 Production run active (top 50 districts, ~25 hours)
⏳ ETA: 25 hours from 2026-05-05 12:45:30 UTC

---

**Last Updated**: 2026-05-05
**Status**: 🟢 Production Ready
**Current Activity**: 🔄 Running (Serpong, Kota Tangerang Selatan)
