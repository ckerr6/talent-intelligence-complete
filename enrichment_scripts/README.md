# PhantomBuster LinkedIn Enrichment Scripts

## Overview

This directory contains a complete PhantomBuster MCP integration for enriching LinkedIn profiles with full employment and education history.

## File Structure

```
enrichment_scripts/
├── README.md                              ← You are here
├── QUICK_START.md                         ← Start here for setup
├── PHANTOMBUSTER_SETUP.md                 ← Detailed setup instructions
│
├── phantombuster_linkedin_enrichment.py   ← Main enrichment script (630 lines)
├── monitor_enrichment_progress.py         ← Monitoring dashboard (290 lines)
├── validate_test_batch.py                 ← Pre-flight validation (110 lines)
├── test_workflow_dry_run.py               ← System test (270 lines)
│
├── run_test_enrichment.sh                 ← Automated test workflow
├── watch_enrichment.sh                    ← Real-time monitoring
│
└── requirements-phantombuster.txt         ← Python dependencies
```

## Quick Start

### 1. Install Dependencies (already done)
```bash
pip3 install -r requirements-phantombuster.txt
```

### 2. Add API Key
Edit `.env` file in project root:
```bash
PHANTOMBUSTER_API_KEY=your_key_here
```

### 3. Run Test (15 profiles)
```bash
./run_test_enrichment.sh 15
```

### 4. Monitor Progress
```bash
python3 monitor_enrichment_progress.py
```

## Main Scripts

### phantombuster_linkedin_enrichment.py

**Purpose**: Main enrichment engine

**Usage**:
```bash
# Test mode (random 15 profiles)
python3 phantombuster_linkedin_enrichment.py --test --batch-size 15

# Production mode (priority order, 50 profiles)
python3 phantombuster_linkedin_enrichment.py --batch-size 50

# Custom rate limiting (3 seconds between calls)
python3 phantombuster_linkedin_enrichment.py --rate-limit 3.0
```

**Features**:
- PhantomBuster MCP API client
- Queue management (pending → in_progress → completed/failed)
- Employment & education enrichment
- Company matching & creation
- Date parsing (PhantomBuster format)
- Comprehensive error handling
- Rate limiting
- Detailed logging

### monitor_enrichment_progress.py

**Purpose**: Real-time progress monitoring

**Usage**:
```bash
# One-time status check
python3 monitor_enrichment_progress.py

# Continuous monitoring (use watch script)
./watch_enrichment.sh 10  # Update every 10 seconds
```

**Shows**:
- Overall queue status (completed/pending/failed/in progress)
- Success rate percentage
- Priority breakdown
- Processing rate (profiles/hour) and ETA
- Recent activity (last hour)
- Top error types
- Retry candidates

### validate_test_batch.py

**Purpose**: Pre-flight validation

**Usage**:
```bash
python3 validate_test_batch.py
```

**Checks**:
- LinkedIn URLs exist
- Profiles are ready for enrichment
- Provides next steps

### test_workflow_dry_run.py

**Purpose**: System validation without API calls

**Usage**:
```bash
python3 test_workflow_dry_run.py
```

**Tests**:
- Database connectivity
- Queue operations
- Date parsing
- Company/employment/education tables
- Dependencies
- Logging

## Shell Scripts

### run_test_enrichment.sh

Automated workflow:
1. Validates test batch
2. Asks for confirmation
3. Runs enrichment
4. Shows results

```bash
./run_test_enrichment.sh [batch_size]
```

### watch_enrichment.sh

Real-time monitoring with auto-refresh:
```bash
./watch_enrichment.sh [interval_seconds]
```

## Current Queue Status

```
Total profiles:     3,869
  Priority 5:       2,698 (highest value)
  Priority 3:       1,090 (medium)
  Priority 1:          81 (lowest)

Status:             100% pending (ready to process)
```

## Expected Results

**Per Profile (Average)**:
- Employment records: 2-4
- Education records: 1-2
- Processing time: ~2 seconds (with rate limit)

**Test Batch (15 profiles)**:
- Employment added: 30-60 records
- Education added: 15-30 records
- New companies: 5-10
- Duration: ~45 seconds
- Success rate: 90-95%

## Monitoring

### Dashboard
```bash
python3 monitor_enrichment_progress.py
```

### SQL Queries
```bash
psql postgresql://localhost/talent -f ../sql/queries/enrichment_monitor.sql
```

### Logs
```bash
tail -f ../logs/phantombuster_enrichment.log
```

## Error Handling

### Automatic Retries

Failed profiles with < 3 attempts can be retried:

```sql
UPDATE enrichment_queue
SET status = 'pending', error_message = NULL
WHERE status = 'failed' AND attempts < 3;
```

### View Errors

```sql
SELECT 
    p.full_name,
    eq.error_message,
    eq.attempts
FROM enrichment_queue eq
JOIN person p ON eq.person_id = p.person_id
WHERE eq.status = 'failed'
ORDER BY eq.last_attempt DESC
LIMIT 20;
```

## Troubleshooting

### "API key not found"
- Check `.env` file has `PHANTOMBUSTER_API_KEY=...`
- Restart terminal or source `.env`

### "No profiles found"
- Check queue: `psql postgresql://localhost/talent -c "SELECT COUNT(*) FROM enrichment_queue WHERE status='pending';"`

### Rate limit errors
- Increase delay: `--rate-limit 5.0`
- Check PhantomBuster quota

### Database errors
- Verify PostgreSQL running
- Test: `psql postgresql://localhost/talent -c "SELECT 1;"`

## Documentation

- **Quick Start**: `QUICK_START.md`
- **Setup Guide**: `PHANTOMBUSTER_SETUP.md`
- **Full Implementation**: `../PHANTOMBUSTER_MCP_IMPLEMENTATION.md`
- **Completion Summary**: `../PHANTOMBUSTER_IMPLEMENTATION_COMPLETE.md`

## Next Steps

1. Add PhantomBuster API key to `.env`
2. Run test: `./run_test_enrichment.sh 15`
3. Verify results
4. Process full queue: `python3 phantombuster_linkedin_enrichment.py --batch-size 3869`

---

**Status**: ✅ Ready for testing (pending API key)  
**Last Updated**: October 24, 2025
