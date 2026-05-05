# Operations Guide

Quick reference for running, monitoring, and troubleshooting the scraper in production.

## 📋 Pre-Launch Checklist

Before starting a production run, verify:

```bash
# 1. Python environment
python3 --version  # Should be 3.9+
pip3 list | grep playwright google-cloud-bigquery pandas

# 2. Google Cloud authentication
gcloud auth application-default login
gcloud config get-value project  # Should be 'ledger-fcc1e'

# 3. BigQuery table exists
bq ls ledger-fcc1e:retail_payment_base
bq show ledger-fcc1e:retail_payment_base.merchants_gmaps

# 4. District data available
ls -lh data/input/districts*.csv

# 5. Logs directory writable
mkdir -p logs && touch logs/test.log && rm logs/test.log

# 6. Output directory writable
mkdir -p data/output && touch data/output/test.txt && rm data/output/test.txt
```

If any check fails, fix before proceeding.

## 🚀 Running the Scraper

### Basic Commands

```bash
# Test run (5 districts, ~5 minutes)
python3 run_parallel.py --sample 5

# Small run (50 districts, ~25 hours)
python3 run_parallel.py --sample 50

# Medium run (100 districts, ~35 hours)
python3 run_parallel.py --sample 100

# Full production (1,009 districts, ~200 hours)
python3 run_parallel.py --all

# Resume interrupted run
python3 run_parallel.py --resume
```

### Background Execution (Recommended)

To run without tying up your terminal:

```bash
# Option 1: nohup (survives terminal close)
nohup python3 run_parallel.py --all > logs/nohup.log 2>&1 &
echo $! > pids/scraper.pid

# Option 2: tmux (detachable session)
tmux new-session -d -s scraper 'python3 run_parallel.py --all'
tmux attach -t scraper  # Reattach later
tmux kill-session -t scraper  # Cleanup

# Option 3: screen (legacy but reliable)
screen -S scraper -m python3 run_parallel.py --all
screen -r scraper  # Reattach
```

**Recommended**: tmux — allows reattachment and better control.

## 📊 Monitoring

### Real-Time Log Tail

```bash
# Last 50 lines
tail -50 logs/scraper_parallel.log

# Follow live (Ctrl+C to stop)
tail -f logs/scraper_parallel.log

# Filter for errors
tail -f logs/scraper_parallel.log | grep -i error

# Filter for BigQuery uploads
tail -f logs/scraper_parallel.log | grep -i bigquery

# Count merchants by category (cumulative)
grep "merchants" logs/scraper_parallel.log | tail -20
```

### Progress Metrics

**Check how many kecamatan completed:**
```bash
cat progress_parallel.json | python3 -m json.tool | wc -l
```

**See which categories are done for each:**
```bash
python3 << 'EOF'
import json
with open('progress_parallel.json') as f:
    progress = json.load(f)
    for kec_id, cats in sorted(progress.items())[:10]:
        print(f"{kec_id}: {len(cats)}/21 categories done")
EOF
```

**Estimate time remaining:**
```bash
python3 << 'EOF'
import json
import time
from datetime import datetime, timedelta

# Load progress
with open('progress_parallel.json') as f:
    progress = json.load(f)

# Count completed kecamatan
completed_count = len(progress)
target_count = 50  # or 100, 1009 depending on run

# Estimate: 1 min per kecamatan with 2 workers
elapsed_minutes = completed_count  # rough estimate
remaining_minutes = (target_count - completed_count) * 1
remaining_hours = remaining_minutes / 60

print(f"Completed: {completed_count}/{target_count} kecamatan")
print(f"Estimated remaining: {remaining_hours:.1f} hours")
if remaining_hours > 0:
    eta = datetime.now() + timedelta(hours=remaining_hours)
    print(f"ETA: {eta.strftime('%Y-%m-%d %H:%M:%S')}")
EOF
```

### BigQuery Validation

**Total merchants scraped today:**
```bash
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) as merchants FROM `ledger-fcc1e.retail_payment_base.merchants_gmaps` WHERE DATE(scraped_at) = CURRENT_DATE()'
```

**Merchants per kecamatan (top 10):**
```bash
bq query --use_legacy_sql=false \
  'SELECT kecamatan_name, COUNT(*) as count FROM `ledger-fcc1e.retail_payment_base.merchants_gmaps` WHERE DATE(scraped_at) = CURRENT_DATE() GROUP BY kecamatan_name ORDER BY count DESC LIMIT 10'
```

**Coverage by category:**
```bash
bq query --use_legacy_sql=false \
  'SELECT our_category, COUNT(*) as total, COUNTIF(lat IS NOT NULL) as with_coords, COUNTIF(review_count IS NOT NULL) as with_reviews FROM `ledger-fcc1e.retail_payment_base.merchants_gmaps` WHERE DATE(scraped_at) = CURRENT_DATE() GROUP BY our_category ORDER BY total DESC'
```

**Distinct kecamatan processed:**
```bash
bq query --use_legacy_sql=false \
  'SELECT COUNT(DISTINCT kecamatan_name) as kecamatan_count FROM `ledger-fcc1e.retail_payment_base.merchants_gmaps` WHERE DATE(scraped_at) = CURRENT_DATE()'
```

## 🛑 Stopping & Resuming

### Graceful Shutdown

```bash
# Find process
ps aux | grep run_parallel.py
# or
cat pids/scraper.pid  # If you saved it

# Terminate gracefully (allows current search to finish)
kill -TERM <PID>

# Force kill if unresponsive
kill -9 <PID>

# Clean up Python processes
pkill -f "python3 run_parallel.py"
```

**Progress is saved** in `progress_parallel.json` after each kecamatan, so:

```bash
# Resume exactly where it left off
python3 run_parallel.py --resume
```

### Restart After System Reboot

```bash
# Check if progress file exists
test -f progress_parallel.json && echo "Progress found" || echo "No progress file"

# Resume
python3 run_parallel.py --resume

# OR if you want to start fresh
rm progress_parallel.json
python3 run_parallel.py --sample 50
```

## 🔧 Troubleshooting

### Scraper Hangs (No Output for 5+ Minutes)

```bash
# Check if process is alive
ps aux | grep run_parallel.py

# Check system resources
top -o %CPU  # Check CPU usage
top -o %MEM  # Check memory usage (Playwright can leak)

# Check network
ping google.com
curl -I https://www.google.com/maps

# Check logs for errors
tail -100 logs/scraper_parallel.log | grep -i "error\|timeout\|warning"
```

**Common causes:**
- Google Maps throttling/blocking → wait 5–15 min and resume
- Network timeout → check internet connection
- Browser memory leak → kill and resume (should only lose current batch of 2 categories)
- Deadlock in async code → rare, requires process restart

### "No merchants found" for specific category

```bash
# Check raw output
cat data/raw/{kecamatan_id}_{category}.json | python3 -m json.tool | head

# If empty JSON array [], Google Maps returned nothing
# Possible causes:
# 1. Category doesn't apply to that location
# 2. Google blocked the search (check for "unusual traffic")
# 3. Network error (check logs)

# Manually check Google Maps
# Open: https://www.google.com/maps/search/{category}+in+{kecamatan},{kabupaten}
```

### BigQuery Insert Failures

```bash
# Check logs for error details
grep -i "bigquery\|error" logs/scraper_parallel.log | tail -20

# Common issues:
# 1. Schema mismatch → check output fields
# 2. Quota exceeded → wait, then resume
# 3. Auth expired → re-run: gcloud auth application-default login

# Manually verify table schema
bq show --schema ledger-fcc1e:retail_payment_base.merchants_gmaps
```

### CSV/JSON Files Not Created

```bash
# Check output directory permissions
ls -la data/output/

# Check if scraper marked categories as done
python3 << 'EOF'
import json
with open('progress_parallel.json') as f:
    progress = json.load(f)
    for kec_id in list(progress.keys())[:1]:
        print(f"{kec_id}: {progress[kec_id]}")
EOF

# If categories are marked done but files missing:
# The scraper may have crashed during save
# Options:
# 1. Remove the kecamatan from progress_parallel.json and re-run
# 2. Manually query BigQuery and export to CSV
```

### Memory Usage Growing (Playwright Leak)

Playwright (headless Chromium) can leak memory over long runs.

```bash
# Monitor
watch -n 5 'ps aux | grep run_parallel | grep -v grep | awk "{print \$6}"'

# If memory > 4GB:
# Kill scraper and resume (browsers will reset)
pkill -f run_parallel.py
python3 run_parallel.py --resume
```

**Prevention**: Monitor memory and manually restart daily if running 24/7.

## 📤 Exporting Data

### Export All Today's Scraped Data

```bash
# BigQuery to CSV
bq extract \
  --destination_format=CSV \
  ledger-fcc1e:retail_payment_base.merchants_gmaps \
  gs://your-bucket/merchants_$(date +%Y%m%d).csv

# Or local CSV (for <1M rows)
bq query --format=csv \
  'SELECT * FROM `ledger-fcc1e.retail_payment_base.merchants_gmaps` WHERE DATE(scraped_at) = CURRENT_DATE()' \
  > merchants_$(date +%Y%m%d).csv
```

### Aggregate by District

```bash
bq query --format=csv \
  'SELECT
     kecamatan_name,
     kabupaten_name,
     provinsi_name,
     COUNT(*) as merchant_count,
     COUNT(DISTINCT our_category) as categories,
     ROUND(AVG(rating), 2) as avg_rating,
     COUNTIF(review_count > 0) as with_reviews
   FROM `ledger-fcc1e.retail_payment_base.merchants_gmaps`
   WHERE DATE(scraped_at) = CURRENT_DATE()
   GROUP BY kecamatan_name, kabupaten_name, provinsi_name
   ORDER BY merchant_count DESC' \
  > district_summary_$(date +%Y%m%d).csv
```

## 🚨 Emergency Procedures

### Lost Progress File (start over)

```bash
# If progress_parallel.json is corrupted
rm progress_parallel.json

# Restart from sample 50 (will re-scrape, but OK)
python3 run_parallel.py --sample 50

# Check for duplicates in BigQuery (won't be an issue due to dedup)
bq query --use_legacy_sql=false \
  'SELECT google_id, COUNT(*) as count FROM `ledger-fcc1e.retail_payment_base.merchants_gmaps` WHERE DATE(scraped_at) = CURRENT_DATE() GROUP BY google_id HAVING count > 1'
```

### Corrupted Output Files

```bash
# If data/output/*.csv is corrupted, re-export from BigQuery
bq query --format=csv \
  'SELECT * FROM `ledger-fcc1e.retail_payment_base.merchants_gmaps` WHERE district_id = "7371013"' \
  > data/output/7371013.csv
```

### Complete Data Loss (restart from BigQuery backup)

```bash
# Check last scrape date
bq query --use_legacy_sql=false \
  'SELECT DISTINCT DATE(scraped_at) as date, COUNT(*) as merchants FROM `ledger-fcc1e.retail_payment_base.merchants_gmaps` GROUP BY date ORDER BY date DESC LIMIT 5'

# Export entire table
bq extract \
  ledger-fcc1e:retail_payment_base.merchants_gmaps \
  gs://your-bucket/merchants_full_backup.json

# Or query to CSV
bq query --use_legacy_sql=false --format=csv \
  'SELECT * FROM `ledger-fcc1e.retail_payment_base.merchants_gmaps`' \
  > merchants_backup_$(date +%Y%m%d).csv
```

## 📋 Checklist for Production Run

- [ ] Pre-launch checks passed
- [ ] District data loaded (`districts_prioritized.csv` exists)
- [ ] BigQuery table ready
- [ ] Sample run tested (--sample 5)
- [ ] Logs directory monitored (tmux/nohup session started)
- [ ] Team notified of start time & expected ETA
- [ ] Backup process documented (just in case)

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Start (50 districts) | `python3 run_parallel.py --sample 50` |
| Monitor live | `tail -f logs/scraper_parallel.log` |
| Check progress | `cat progress_parallel.json \| python3 -m json.tool \| wc -l` |
| Resume after interrupt | `python3 run_parallel.py --resume` |
| BigQuery count | `bq query 'SELECT COUNT(*) FROM ledger-fcc1e.retail_payment_base.merchants_gmaps'` |
| Export to CSV | `bq extract ledger-fcc1e:retail_payment_base.merchants_gmaps gs://bucket/out.csv` |
| Kill process | `pkill -f run_parallel.py` |

---

**Version**: 1.0  
**Last Updated**: 2026-05-05  
**Questions?** Check logs first: `tail -100 logs/scraper_parallel.log`
