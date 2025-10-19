# Talent Intelligence Database - Complete Solution

## 🎯 Goal
Create a single, clean, queryable database containing all your candidate and company data.

---

## 📁 What's In This Directory

### 🚀 Phase 1: Candidate Database (START HERE)

| File | Purpose |
|------|---------|
| **`RUN_ME.sh`** | ⭐ **RUN THIS FIRST** - One command to build everything |
| `build_candidate_database.py` | Main processing script (auto-run by RUN_ME.sh) |
| `query_database.sh` | Interactive menu to explore your data |

### 📚 Documentation

| File | Purpose |
|------|---------|
| **`QUICK_START.md`** | ⭐ Fast start guide - read this first |
| `EXECUTIVE_SUMMARY.md` | High-level overview and results |
| `COMPLETE_PLAN.md` | Full technical documentation |
| `ABOUTME.txt` | This directory overview |

### 🔄 Phase 2: Companies (Coming Next)

| File | Purpose |
|------|---------|
| `build_company_database.py` | Company data processor (stub for now) |

### 📊 Generated Files (After Running)

| File | Purpose |
|------|---------|
| `talent_intelligence.db` | **Your database!** |
| `data_quality_report.txt` | Statistics & metrics |
| `deduplication_report.txt` | Merge details |
| `sample_queries.sql` | Example SQL queries |
| `import_log.txt` | Detailed processing log |

---

## ⚡ Quick Start (3 Steps)

### Step 1: Build the Database
```bash
cd "/Users/charlie.kerr/Documents/CK Docs/FINAL_DATABASE"
chmod +x RUN_ME.sh
./RUN_ME.sh
```

**Wait 2-5 minutes while it processes...**

### Step 2: Verify Success
```bash
chmod +x query_database.sh
./query_database.sh
# Choose option 1 to see statistics
```

### Step 3: Start Querying!
```bash
# Interactive menu
./query_database.sh

# Or direct SQL
sqlite3 talent_intelligence.db
SELECT COUNT(*) FROM people;
```

**That's it!** You now have a working database.

---

## 📊 What You'll Get

### Expected Results
- ✅ **~15,000 unique candidates** (deduplicated)
- ✅ **90%+ with email or LinkedIn**
- ✅ **80%+ with company/title info**
- ✅ **Quality score: 0.6-0.8 average**
- ✅ **~1,000 duplicates merged**

### Database Tables
- `people` - Core candidate profiles
- `social_profiles` - LinkedIn, GitHub, Twitter
- `emails` - All email addresses
- `employment` - Current and historical jobs
- `data_sources` - Track data provenance

---

## 🎓 Learn More

### First Time User?
1. Read `QUICK_START.md` - 5 minute overview
2. Run `./RUN_ME.sh` - build your database
3. Run `./query_database.sh` - explore your data

### Want Technical Details?
- Read `COMPLETE_PLAN.md` - Full documentation
- Read `EXECUTIVE_SUMMARY.md` - High-level overview

### Need Help?
- Check `import_log.txt` - detailed logs
- Check `data_quality_report.txt` - statistics
- Check `deduplication_report.txt` - merge details

---

## 🔍 Common Queries

### Find candidates at a company
```sql
SELECT p.first_name, p.last_name, p.primary_email, e.title
FROM people p
JOIN employment e ON p.person_id = e.person_id
WHERE LOWER(e.company_name) LIKE '%uniswap%'
AND e.is_current = 1;
```

### Get complete profile
```sql
SELECT 
    p.*,
    sp_linkedin.profile_url as linkedin,
    sp_github.profile_url as github,
    e.company_name, e.title
FROM people p
LEFT JOIN social_profiles sp_linkedin ON p.person_id = sp_linkedin.person_id AND sp_linkedin.platform = 'linkedin'
LEFT JOIN social_profiles sp_github ON p.person_id = sp_github.person_id AND sp_github.platform = 'github'  
LEFT JOIN employment e ON p.person_id = e.person_id AND e.is_current = 1
WHERE p.primary_email = 'example@email.com';
```

### Export to CSV
```bash
./query_database.sh
# Choose option 8
```

---

## 🚀 Roadmap

### ✅ Phase 1: Candidates (Ready NOW)
- High-quality candidate database
- Smart deduplication
- Quality scoring
- **Status**: Complete

### 🔄 Phase 2: Companies (Next)
- Company profiles
- Funding rounds
- Investor relationships
- Link candidates to companies
- **Status**: Planned

### 🎯 Phase 3: GitHub (Future)
- Process 400k GitHub contributors
- Match to existing candidates
- Skills extraction
- Developer sourcing pool
- **Status**: Planned

### 🌟 Phase 4: Interface (Future)
- Web UI for searching
- REST API
- Automated updates
- **Status**: Planned

---

## 🛠️ Technical Specs

### Requirements
- Python 3.7+
- pandas, numpy
- SQLite 3 (built into macOS)

### Performance
- **Processing time**: 2-5 minutes
- **Memory usage**: ~2GB peak
- **Database size**: ~50MB
- **Batch size**: 5,000 records

### Compatibility
- macOS (M1 Pro tested)
- Linux (should work)
- Windows (should work with minor path adjustments)

---

## ❓ FAQ

### Why SQLite instead of PostgreSQL?
SQLite is perfect for Phase 1:
- Zero setup
- Single file, easy to backup
- Fast for 15k-100k records
- Easy migration to PostgreSQL later

### How does deduplication work?
Three-tier matching:
1. Email match → merge (100% confidence)
2. LinkedIn match → merge (100% confidence)
3. Name + Company → merge (95% confidence)

### Can I customize the matching rules?
Yes! Edit `build_candidate_database.py`:
- Adjust quality thresholds
- Modify matching logic
- Change batch sizes

### How do I export data?
Three ways:
1. `./query_database.sh` → option 8 → CSV export
2. `sqlite3 -csv talent_intelligence.db "SELECT * FROM people;" > output.csv`
3. Use any SQLite GUI tool (DB Browser, DBeaver, etc.)

### How do I backup my database?
```bash
# Simple copy
cp talent_intelligence.db talent_intelligence_backup_$(date +%Y%m%d).db

# Or use SQLite backup
sqlite3 talent_intelligence.db ".backup backup.db"
```

### Can I migrate to PostgreSQL later?
Yes, easily:
```bash
# Install pgloader
brew install pgloader

# Migrate
pgloader talent_intelligence.db postgresql://user:pass@localhost/talent_db
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "pandas not found" | `pip3 install pandas numpy` |
| "Permission denied" | `chmod +x RUN_ME.sh` |
| Very few candidates found | Check `import_log.txt` |
| Database locked | Close other DB programs |
| Out of memory | Edit script, reduce BATCH_SIZE to 2500 |

---

## 📞 Support

**Check these files in order:**
1. `import_log.txt` - Detailed processing log
2. `data_quality_report.txt` - Statistics
3. `deduplication_report.txt` - Merge details
4. `COMPLETE_PLAN.md` - Full documentation

**Common issues are documented** in each guide's Troubleshooting section.

---

## ✨ Key Features

### ✅ Smart Deduplication
- Multi-factor matching (email, LinkedIn, name+company)
- Conservative approach - no over-merging
- Detailed merge logs

### ✅ Quality Scoring
- Each person rated 0.0-1.0
- Based on completeness
- Filter by quality easily

### ✅ Memory Efficient
- Batch processing (5k at a time)
- No memory overflow
- Perfect for M1 Pro 16GB

### ✅ Production Ready
- Proper database schema
- Foreign key relationships
- Indexed for fast queries

### ✅ Extensible
- Easy to add Phase 2 and 3
- Clean schema for growth
- Simple PostgreSQL migration

---

## 🎉 Success Metrics

After running Phase 1:

- ✅ ~15,000 unique candidates
- ✅ 90%+ contact coverage
- ✅ 80%+ employment data
- ✅ Average quality 0.6-0.8
- ✅ Processed in < 5 minutes

---

## 📖 Learn More

- `QUICK_START.md` - Fast introduction
- `EXECUTIVE_SUMMARY.md` - Overview & results
- `COMPLETE_PLAN.md` - Technical deep dive

---

**Ready to start? Run `./RUN_ME.sh` now!** 🚀
