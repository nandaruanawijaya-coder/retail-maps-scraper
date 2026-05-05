# Documentation Index

Complete documentation for the Google Maps Merchant Scraper project. Start here, then navigate to specific guides based on your role.

## 📖 Getting Started

**New to the project?** Read in this order:

1. **[README.md](README.md)** (5 min read)
   - Project objectives and scope
   - Quick start commands
   - Technology stack overview
   - Current status

2. **[PROJECT_STATUS.md](PROJECT_STATUS.md)** (10 min read)
   - Prioritization strategy (50% visit coverage with just 50 districts)
   - Current run details (started 2026-05-05, ETA 25 hours)
   - Top 20 priority districts
   - Next steps

3. **[OPERATIONS.md](OPERATIONS.md)** (reference)
   - How to run the scraper
   - Real-time monitoring commands
   - Troubleshooting guide
   - Emergency procedures

## 🔬 Technical Documentation

**For engineers building or extending the scraper:**

1. **[ARCHITECTURE.md](ARCHITECTURE.md)** (30 min read)
   - System design & data flow
   - Component breakdown (8 modules)
   - Implementation details for each component
   - Performance analysis & bottlenecks
   - Data quality decisions & rationale
   - Failure modes & mitigations
   - Future optimization ideas

2. **[DATA_DICTIONARY.md](DATA_DICTIONARY.md)** (reference)
   - Complete schema (24 fields)
   - Field coverage by category
   - NULL handling rules
   - Data quality metrics
   - Example records (high/medium/low quality)
   - SQL & Python query examples

## 📚 Role-Based Navigation

### 👨‍💼 Project Manager
Start with → **PROJECT_STATUS.md**
- **Why**: Prioritization rationale, time-ROI trade-offs, coverage estimates
- **Then**: README.md → OPERATIONS.md (monitoring, success metrics)
- **Check**: `tail -f logs/scraper_parallel.log` for daily status

### 👨‍💻 Data Engineer / DevOps
Start with → **ARCHITECTURE.md**
- **Why**: System design, scaling considerations, failure handling
- **Then**: OPERATIONS.md → DATA_DICTIONARY.md
- **Deploy**: Follow OPERATIONS.md pre-launch checklist

### 📊 Data Analyst
Start with → **DATA_DICTIONARY.md**
- **Why**: Field definitions, coverage metrics, example queries
- **Then**: PROJECT_STATUS.md (distribution insights)
- **Query**: Use SQL examples to extract insights

### 🔧 QA / Validation
Start with → **OPERATIONS.md**
- **Why**: Monitoring, validation queries, quality checks
- **Then**: DATA_DICTIONARY.md (expected coverage targets)
- **Monitor**: Sample queries post-run to verify data quality

### 👤 Stakeholder / Business
Start with → **README.md**
- **Why**: Clear overview without technical jargon
- **Then**: PROJECT_STATUS.md (prioritization strategy, ROI)
- **Access**: Query results via BigQuery dashboard

## 🗂️ File Structure

```
/Scraper/
├── Documentation/
│   ├── README.md                    ← Start here
│   ├── ARCHITECTURE.md              ← Technical deep-dive
│   ├── OPERATIONS.md                ← Runbook & troubleshooting
│   ├── DATA_DICTIONARY.md           ← Schema reference
│   ├── PROJECT_STATUS.md            ← Prioritization & current status
│   └── DOCUMENTATION_INDEX.md       ← This file
│
├── Scraper Code/
│   ├── run_parallel.py              ← Main entry point
│   └── scraper/
│       ├── config.py                ← Categories & constants
│       ├── gmaps_scraper.py         ← Playwright automation
│       ├── gmaps_parser.py          ← DOM extraction
│       ├── deduplicator.py          ← Dedup logic
│       ├── storage.py               ← CSV/JSON/checkpointing
│       ├── bigquery_uploader.py     ← Cloud integration
│       ├── boundary.py              ← Location hierarchy
│       └── requirements.txt         ← Dependencies
│
├── Configuration/
│   ├── data/input/
│   │   ├── districts.csv            ← All 7,268 kecamatan
│   │   └── districts_prioritized.csv ← 1,009 priority (ranked by visits)
│   └── export_data/
│       └── district_priority.sql    ← Query to fetch priority ranking
│
├── Runtime/
│   ├── logs/
│   │   ├── scraper_parallel.log     ← Main log
│   │   └── run_sample_50.log        ← Latest run
│   ├── data/
│   │   ├── output/                  ← CSV/JSON results
│   │   └── raw/                     ← Audit trail JSON
│   └── progress_parallel.json       ← Resumable checkpoint
│
└── External/
    └── BigQuery Table: ledger-fcc1e.retail_payment_base.merchants_gmaps
```

## 🎯 Common Tasks

### "I want to run the scraper"
→ **OPERATIONS.md** → "Running the Scraper" section

### "I want to understand the prioritization"
→ **PROJECT_STATUS.md** → "Prioritization Strategy" section

### "I need to troubleshoot an error"
→ **OPERATIONS.md** → "Troubleshooting" section

### "I want to analyze the results"
→ **DATA_DICTIONARY.md** → "Using the Data" section

### "I need to deploy this to production"
→ **OPERATIONS.md** → "Pre-Launch Checklist"

### "I want to modify/extend the scraper"
→ **ARCHITECTURE.md** → "Component Breakdown" section

### "I need to know what data we have"
→ **DATA_DICTIONARY.md** → "Output Fields" section

### "I want to see what's running"
→ **OPERATIONS.md** → "Monitoring" section

## 📊 Quick Stats (From Last Run)

**Test Run** (Wagir, Malang - 1 district, 21 categories):
- **Merchants Found**: 1,995
- **Lat/Lng Coverage**: 99.7% (1,990/1,995)
- **Review Count Coverage**: 83.3% (1,662/1,995)
- **BigQuery Upload**: 100% success (1,995 rows)
- **Duration**: 5 hours 40 minutes

**Current Production Run** (Top 50 districts by visit volume):
- **Districts**: 50 (110,436 visits = 50% of total activity)
- **Categories**: 21 per district = 1,050 total searches
- **Expected Merchants**: 100,000–125,000
- **Expected Duration**: ~25 hours
- **Start Time**: 2026-05-05 12:45:30 UTC
- **Priority Focus**: Makassar (7 districts), Jakarta (8 districts), Medan (3 districts)

## 🔄 Update Frequency

| Document | Update Frequency | Last Updated |
|----------|------------------|--------------|
| README.md | As needed (quarterly) | 2026-05-05 |
| ARCHITECTURE.md | Annual | 2026-05-05 |
| OPERATIONS.md | Quarterly (with new features) | 2026-05-05 |
| DATA_DICTIONARY.md | As schema changes | 2026-05-05 |
| PROJECT_STATUS.md | Weekly (during active runs) | 2026-05-05 |
| DOCUMENTATION_INDEX.md | Monthly | 2026-05-05 |

## 🚀 Next Steps

### This Week
- Monitor current run (top 50 districts)
- Validate data quality in BigQuery
- Export results for stakeholder review

### Next Week
- Decide on expansion: Continue to 100 districts? Or analyze current 50 first?
- If expanding: Run `python3 run_parallel.py --sample 100`
- If analyzing: Query insights, identify patterns, report findings

### Next Month
- Plan Phase 2: Decision point on full enumeration (all 1,009 districts)
- Cost-benefit analysis: 50% coverage in 25 hours vs. 100% coverage in 200+ hours

## 📞 Support & Questions

**Technical Questions?**
→ Check ARCHITECTURE.md or DATA_DICTIONARY.md

**How do I...?**
→ Check OPERATIONS.md or README.md

**What data do we have?**
→ Check DATA_DICTIONARY.md or PROJECT_STATUS.md (statistics)

**How do I monitor the run?**
→ OPERATIONS.md → "Monitoring" section

**What do I do if something breaks?**
→ OPERATIONS.md → "Troubleshooting" section

## 📋 Checklist Before Using Scraper

- [ ] Read README.md (understand objectives)
- [ ] Check PROJECT_STATUS.md (understand current run)
- [ ] Review DATA_DICTIONARY.md (understand data schema)
- [ ] Run test: `python3 run_parallel.py --sample 5`
- [ ] Check logs for errors
- [ ] Verify BigQuery table has new rows
- [ ] Review OPERATIONS.md monitoring section
- [ ] Set up log monitoring for long runs

## Version & Maintenance

- **Version**: 1.0
- **Last Updated**: 2026-05-05
- **Maintained By**: Nanda Ruanawijaya (nanda.ruanawijaya@bukuwarung.com)
- **Status**: 🟢 Production Ready
- **Current Activity**: 🔄 Active Run (Top 50 Districts)

---

## 🎓 Learning Path

**Complete Onboarding** (first time):
1. README.md (5 min)
2. PROJECT_STATUS.md (10 min)
3. Watch current run: `tail -f logs/scraper_parallel.log` (1 min)
4. Query results: See DATA_DICTIONARY.md examples (5 min)
5. Review ARCHITECTURE.md for deep understanding (30 min)
6. Save OPERATIONS.md as reference for future runs

**Total Time**: ~1 hour for complete understanding

---

**Questions?** Every document has usage notes. Start with README.md, then navigate based on your role.
