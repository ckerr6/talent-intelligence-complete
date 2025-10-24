# PhantomBuster MCP Quick Start

## Prerequisites
✅ Dependencies installed (`pip3 install -r requirements-phantombuster.txt`)  
✅ Database connected (PostgreSQL `talent` database)  
✅ Enrichment queue populated (3,869 profiles ready)

## 🚀 5-Minute Test Run

### Step 1: Add API Key
Edit your `.env` file in project root:
```bash
PHANTOMBUSTER_API_KEY=your_actual_key_here
```

### Step 2: Validate Test Batch
```bash
cd enrichment_scripts
python3 validate_test_batch.py
```

### Step 3: Run Test Enrichment
```bash
./run_test_enrichment.sh 15
```

This will:
- ✅ Validate 15 random profiles
- ✅ Ask for confirmation
- ✅ Scrape LinkedIn profiles via PhantomBuster MCP
- ✅ Update database with employment & education
- ✅ Show results dashboard

### Step 4: Check Results

**View enriched profiles:**
```bash
psql postgresql://localhost/talent -c "
SELECT 
    p.full_name,
    COUNT(e.employment_id) as jobs,
    COUNT(ed.education_id) as schools
FROM person p
LEFT JOIN employment e ON p.person_id = e.person_id
LEFT JOIN education ed ON p.person_id = ed.person_id
WHERE p.refreshed_at > NOW() - INTERVAL '1 hour'
GROUP BY p.person_id, p.full_name;
"
```

**Monitor queue:**
```bash
python3 monitor_enrichment_progress.py
```

## 📊 Common Commands

### Check queue status
```bash
python3 monitor_enrichment_progress.py
```

### Run batch enrichment
```bash
# Small batch
python3 phantombuster_linkedin_enrichment.py --batch-size 50

# Large batch  
python3 phantombuster_linkedin_enrichment.py --batch-size 500

# Test mode (random selection)
python3 phantombuster_linkedin_enrichment.py --test --batch-size 15
```

### Watch live progress
```bash
./watch_enrichment.sh 10  # Update every 10 seconds
```

### View logs
```bash
tail -f ../logs/phantombuster_enrichment.log
```

### Reset failed profiles for retry
```bash
psql postgresql://localhost/talent -c "
UPDATE enrichment_queue 
SET status = 'pending', error_message = NULL 
WHERE status = 'failed' AND attempts < 3;
"
```

## 🆘 Troubleshooting

### "PHANTOMBUSTER_API_KEY not found"
- Make sure API key is in `.env` file
- Check the key starts with `PHANTOMBUSTER_API_KEY=`
- Restart terminal or source `.env`

### "No profiles found in queue"
- Check queue: `psql postgresql://localhost/talent -c "SELECT COUNT(*) FROM enrichment_queue WHERE status='pending';"`
- Re-populate queue if needed

### Rate limit errors
- Increase delay: `python3 phantombuster_linkedin_enrichment.py --rate-limit 5.0`
- Check PhantomBuster quota/limits

### Database connection errors
- Verify PostgreSQL is running
- Check connection string in `config.py`
- Test: `psql postgresql://localhost/talent -c "SELECT 1;"`

## 📖 Full Documentation
See `PHANTOMBUSTER_MCP_IMPLEMENTATION.md` for complete details.

