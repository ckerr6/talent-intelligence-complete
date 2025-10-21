# 🚀 QUICK START GUIDE

## ONE COMMAND TO BUILD YOUR DATABASE

```bash
cd "/Users/charlie.kerr/Documents/CK Docs/FINAL_DATABASE"
chmod +x RUN_ME.sh
./RUN_ME.sh
```

That's it! The script will:
1. ✅ Check dependencies (auto-install if needed)
2. ✅ Process all candidate CSV files
3. ✅ Deduplicate intelligently
4. ✅ Build SQLite database
5. ✅ Generate quality reports

**Expected time**: 2-5 minutes

---

## What You'll Get

```
FINAL_DATABASE/
├── talent_intelligence.db          ← Your database! (~50MB)
├── data_quality_report.txt         ← Stats & metrics
├── deduplication_report.txt        ← What was merged
├── sample_queries.sql              ← Example queries
└── import_log.txt                  ← Detailed log
```

---

## Verify Your Database

### Check the data
```bash
sqlite3 talent_intelligence.db
```

```sql
-- Count total people
SELECT COUNT(*) FROM people;
-- Should be ~15,000-16,000

-- Check data quality
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN primary_email IS NOT NULL THEN 1 ELSE 0 END) as with_email,
    SUM(CASE WHEN data_quality_score > 0.7 THEN 1 ELSE 0 END) as high_quality
FROM people;

-- Find someone
SELECT * FROM people WHERE primary_email LIKE '%@uniswap%';
```

### View reports
```bash
cat data_quality_report.txt
cat deduplication_report.txt
```

---

## Common Queries

### Find candidates at a company
```sql
SELECT p.first_name, p.last_name, p.primary_email, e.title
FROM people p
JOIN employment e ON p.person_id = e.person_id
WHERE LOWER(e.company_name) LIKE '%coinbase%'
AND e.is_current = 1;
```

### Get complete profile
```sql
SELECT 
    p.first_name, p.last_name, p.primary_email,
    sp_linkedin.profile_url as linkedin,
    sp_github.profile_url as github,
    e.company_name, e.title
FROM people p
LEFT JOIN social_profiles sp_linkedin ON p.person_id = sp_linkedin.person_id AND sp_linkedin.platform = 'linkedin'
LEFT JOIN social_profiles sp_github ON p.person_id = sp_github.person_id AND sp_github.platform = 'github'
LEFT JOIN employment e ON p.person_id = e.person_id AND e.is_current = 1
WHERE p.primary_email = 'example@email.com';
```

### High-quality candidates
```sql
SELECT first_name, last_name, primary_email, data_quality_score
FROM people
WHERE data_quality_score > 0.7
ORDER BY data_quality_score DESC
LIMIT 50;
```

---

## Troubleshooting

### Script fails with "pandas not found"
```bash
pip3 install pandas numpy
```

### Very few candidates found
- Check `import_log.txt` to see which files were processed
- Verify CSVs exist in `/Users/charlie.kerr/Documents/CK Docs/merged_output`

### Too many/few duplicates merged
- Check `deduplication_report.txt` for merge statistics
- Adjust matching rules in `build_candidate_database.py` if needed

### Database locked error
- Close any other programs accessing the database
- The script handles this automatically

---

## What's Next?

### Phase 2: Add Company Data
After validating Phase 1, we'll add:
- Company profiles with funding data
- Investor relationships
- Company GitHub/LinkedIn/Twitter

### Phase 3: GitHub Enrichment
- Match 400k GitHub contributors to existing candidates
- Create developer sourcing pool
- Extract skills from repos

### Phase 4: Query Interface
- Build web UI for searching
- REST API for programmatic access
- Automated updates

---

## File Descriptions

| File | Purpose |
|------|---------|
| `RUN_ME.sh` | One-command executor |
| `build_candidate_database.py` | Main processing script |
| `COMPLETE_PLAN.md` | Full documentation |
| `ABOUTME.txt` | Directory overview |

---

## Need Help?

Check these files in order:
1. `import_log.txt` - Detailed processing log
2. `data_quality_report.txt` - Statistics & metrics
3. `deduplication_report.txt` - Merge details
4. `COMPLETE_PLAN.md` - Full documentation

---

**Ready? Run `./RUN_ME.sh` and watch your database build in real-time!** ✨
