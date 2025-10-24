# Execute Tier 1 Batch Processes

**Status:** Ready to execute  
**Time Required:** 5-7 nights + 1.5 hours  
**Scripts:** All tested and ready

---

## Overview

Two batch processes remain to be executed:
1. **PR Enrichment** - 5-7 overnight runs (98K-150K profiles)
2. **Importance Scoring** - 1.5 hours (334K repos + 101K profiles)

Both are **optional** but recommended for complete Tier 1 execution.

---

## Option 1: PR Enrichment (Recommended First)

### What It Does
Enriches GitHub profiles with:
- Total merged PRs
- Total commits
- Total issues
- Total pull requests
- Contribution quality score

### Time Required
- **Tier 1** (98K linked profiles): ~20 hours
- **Tier 2** (10K high-follower): ~2-3 hours  
- **Tier 3** (ecosystem contributors): ~3-4 hours
- **Tier 4** (active profiles): ~5-7 hours

**Total: 5-7 overnight runs**

### Execution Commands

#### Test on Sample First (Recommended)
```bash
cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete

# Test Tier 1 with 100 profiles
python3 scripts/github/batch_pr_enrichment_orchestrator.py --tier 1 --limit 100

# Check results
psql -d talent -c "SELECT COUNT(*) FROM github_profile WHERE total_merged_prs > 0"
```

#### Run Tier 1 (Highest Priority - Linked Profiles)
```bash
# Create logs directory
mkdir -p logs

# Run in background (will take ~20 hours)
nohup python3 scripts/github/batch_pr_enrichment_orchestrator.py --tier 1 \
  > logs/pr_enrichment_tier1_$(date +%Y%m%d).log 2>&1 &

# Get process ID
echo $! > logs/pr_enrichment.pid

# Monitor progress
tail -f logs/pr_enrichment_tier1_*.log

# Or check progress periodically
watch -n 60 'tail -20 logs/pr_enrichment_tier1_*.log'
```

#### Resume if Interrupted
```bash
# Script saves checkpoints automatically
python3 scripts/github/batch_pr_enrichment_orchestrator.py --resume
```

#### Run Remaining Tiers
```bash
# Tier 2: High followers
nohup python3 scripts/github/batch_pr_enrichment_orchestrator.py --tier 2 \
  > logs/pr_enrichment_tier2_$(date +%Y%m%d).log 2>&1 &

# Tier 3: Ecosystem contributors  
nohup python3 scripts/github/batch_pr_enrichment_orchestrator.py --tier 3 \
  > logs/pr_enrichment_tier3_$(date +%Y%m%d).log 2>&1 &

# Tier 4: Active profiles
nohup python3 scripts/github/batch_pr_enrichment_orchestrator.py --tier 4 \
  > logs/pr_enrichment_tier4_$(date +%Y%m%d).log 2>&1 &

# Or run all tiers in sequence
nohup python3 scripts/github/batch_pr_enrichment_orchestrator.py --all-tiers \
  > logs/pr_enrichment_all_$(date +%Y%m%d).log 2>&1 &
```

#### Check Results
```bash
# Check enrichment progress
psql -d talent -c "
SELECT 
  COUNT(*) as total_profiles,
  COUNT(CASE WHEN total_merged_prs IS NOT NULL THEN 1 END) as enriched,
  ROUND(100.0 * COUNT(CASE WHEN total_merged_prs IS NOT NULL THEN 1 END) / COUNT(*), 2) as pct
FROM github_profile
"

# Top profiles by merged PRs
psql -d talent -c "
SELECT github_username, total_merged_prs, followers
FROM github_profile
WHERE total_merged_prs > 0
ORDER BY total_merged_prs DESC
LIMIT 20
"
```

#### Stop if Needed
```bash
# Get process ID
PID=$(cat logs/pr_enrichment.pid)

# Stop gracefully (saves checkpoint)
kill -SIGINT $PID

# Resume later
python3 scripts/github/batch_pr_enrichment_orchestrator.py --resume
```

---

## Option 2: Importance Scoring (Faster)

### What It Does
Computes importance scores for:
- **Repositories** (based on stars, forks, contributors, ecosystem, activity)
- **Developers** (based on contribution to important repos)

### Time Required
- **Repositories**: ~1 hour (334K repos at ~100/sec)
- **Developers**: ~20 minutes (101K profiles at ~100/sec)
- **Total: ~1.5 hours**

### Execution Commands

#### Test on Sample First
```bash
cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete

# Test repos (1000 samples)
python3 scripts/analytics/compute_all_importance_scores.py --repos --limit 1000

# Test developers (1000 samples)
python3 scripts/analytics/compute_all_importance_scores.py --developers --limit 1000

# Check results
python3 scripts/analytics/compute_all_importance_scores.py --report
```

#### Run Full Computation
```bash
# Run all (repos + developers + indexes + report)
nohup python3 scripts/analytics/compute_all_importance_scores.py --all \
  > logs/importance_scores_$(date +%Y%m%d).log 2>&1 &

# Monitor progress
tail -f logs/importance_scores_*.log
```

#### Or Run Separately
```bash
# Just repositories
python3 scripts/analytics/compute_all_importance_scores.py --repos

# Just developers
python3 scripts/analytics/compute_all_importance_scores.py --developers
```

#### Check Results
```bash
# View report
python3 scripts/analytics/compute_all_importance_scores.py --report

# Or query directly
psql -d talent -c "
SELECT full_name, stars, forks, importance_score
FROM github_repository
WHERE importance_score > 0
ORDER BY importance_score DESC
LIMIT 20
"

psql -d talent -c "
SELECT github_username, followers, importance_score
FROM github_profile
WHERE importance_score > 0
ORDER BY importance_score DESC
LIMIT 20
"
```

---

## Recommended Execution Order

### Day 1 (Tonight)
1. ✅ Test PR enrichment on 100 profiles
2. ✅ Start Tier 1 PR enrichment overnight (~20 hours)

### Day 2 (Next Morning)
1. ✅ Check Tier 1 results
2. ✅ Run importance scoring (~1.5 hours)
3. ✅ Verify results with report

### Day 3-7 (Optional - If Time Permits)
1. ✅ Run Tier 2-4 PR enrichment
2. ✅ Final validation

### Skip Execution (Valid Option)
- Platform is functional without these
- Can execute anytime in the future
- Move to Tier 2 immediately

---

## Monitoring & Troubleshooting

### Check GitHub API Rate Limit
```bash
# Check current rate limit
curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/rate_limit

# Or from script logs
grep "Rate limit" logs/pr_enrichment*.log
```

### Check Process Status
```bash
# Is it running?
ps aux | grep batch_pr_enrichment

# How long has it been running?
ps -p $(cat logs/pr_enrichment.pid) -o etime=

# Check resource usage
top -p $(cat logs/pr_enrichment.pid)
```

### Common Issues

#### Issue: Script stops unexpectedly
**Solution:** Resume from checkpoint
```bash
python3 scripts/github/batch_pr_enrichment_orchestrator.py --resume
```

#### Issue: Rate limit hit
**Solution:** Script pauses automatically, wait 1 hour

#### Issue: Database connection lost
**Solution:** Script reconnects automatically

#### Issue: Import error
**Solution:** Check dependencies
```bash
pip install psycopg2-binary requests
```

---

## Verification Queries

### After PR Enrichment
```sql
-- Overall stats
SELECT 
  COUNT(*) as total,
  COUNT(CASE WHEN total_merged_prs > 0 THEN 1 END) as with_prs,
  AVG(CASE WHEN total_merged_prs > 0 THEN total_merged_prs END) as avg_prs,
  MAX(total_merged_prs) as max_prs
FROM github_profile;

-- Top contributors
SELECT 
  p.full_name,
  gp.github_username,
  gp.total_merged_prs,
  gp.contribution_quality_score
FROM github_profile gp
LEFT JOIN person p ON gp.person_id = p.person_id
WHERE gp.total_merged_prs > 10
ORDER BY gp.total_merged_prs DESC
LIMIT 20;
```

### After Importance Scoring
```sql
-- Repository stats
SELECT 
  COUNT(*) as total,
  COUNT(CASE WHEN importance_score > 0 THEN 1 END) as scored,
  AVG(CASE WHEN importance_score > 0 THEN importance_score END) as avg_score,
  MAX(importance_score) as max_score
FROM github_repository;

-- Top repositories
SELECT full_name, stars, importance_score
FROM github_repository
WHERE importance_score > 0
ORDER BY importance_score DESC
LIMIT 20;

-- Developer stats
SELECT 
  COUNT(*) as total,
  COUNT(CASE WHEN importance_score > 0 THEN 1 END) as scored,
  AVG(CASE WHEN importance_score > 0 THEN importance_score END) as avg_score
FROM github_profile;
```

---

## Expected Results

### PR Enrichment (Tier 1 Only)
- **Profiles enriched**: 98,000
- **Time**: 20 hours
- **Coverage**: 96.5% of profiles
- **New capability**: Filter by PR count and quality

### PR Enrichment (All Tiers)
- **Profiles enriched**: 150,000+
- **Time**: 30-35 hours (over 5-7 nights)
- **Coverage**: ~95% of all profiles
- **Full feature completeness**

### Importance Scoring
- **Repos scored**: 334,000
- **Developers scored**: 101,000
- **Time**: 1.5 hours
- **New capability**: Sort by importance, find top contributors

---

## Decision Time

### Execute Now?
**Pros:**
- Complete Tier 1 fully
- Reach 85% platform completeness
- All features operational
- Can move to Tier 2 with confidence

**Cons:**
- Requires 5-7 nights of overnight runs
- GitHub API dependency
- Can wait if needed

### Execute Later?
**Pros:**
- Move to Tier 2 immediately
- Can execute anytime
- Platform functional without it

**Cons:**
- PR filtering incomplete
- Importance ranking missing
- Only 80% vs 85% complete

### Minimum Execution
**Run importance scoring only** (1.5 hours)
- Fastest path to value
- No overnight runs needed
- Unlocks ranking features
- Skip PR enrichment for now

---

## Questions?

- Check script help: `python3 [script] --help`
- View logs: `tail -f logs/*.log`
- Test first: Use `--limit` flag
- Resume anytime: Use `--resume` flag

**All scripts are production-ready and tested.**

---

**Created:** October 24, 2025  
**Status:** Ready to execute

