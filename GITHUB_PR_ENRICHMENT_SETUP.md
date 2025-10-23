# GitHub PR Enrichment Setup Guide 🚀

**Phase 2 Implementation Complete!**

This guide explains how to run the GitHub PR enrichment script to collect merged PR data, lines of code, and quality metrics.

---

## 🎯 What This Does

Enriches GitHub profiles with **CRITICAL** data for expert sourcers:
- ✅ **Merged PR count** (confirms real contributions)
- ✅ **Lines of code added/deleted** (code volume)
- ✅ **Quality scores** (automated 0-100 rating)
- ✅ **Pro account detection** (private repos indicator)
- ✅ **PR merge dates** (recency signal)

---

## 📋 Prerequisites

### 1. Get a GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: "Talent Intelligence Enrichment"
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `read:user` (Read user profile data)
5. Click "Generate token"
6. **COPY THE TOKEN** - you won't see it again!

### 2. Set Environment Variable

**Option A: Add to `.env` file (recommended)**
```bash
cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete
echo "GITHUB_TOKEN=ghp_your_token_here" >> .env
```

**Option B: Export in terminal session**
```bash
export GITHUB_TOKEN=ghp_your_token_here
```

**Option C: Add to your shell profile (persistent)**
```bash
# For zsh (macOS default)
echo 'export GITHUB_TOKEN=ghp_your_token_here' >> ~/.zshrc
source ~/.zshrc

# For bash
echo 'export GITHUB_TOKEN=ghp_your_token_here' >> ~/.bashrc
source ~/.bashrc
```

### 3. Verify Token is Set

```bash
cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete
python3 -c "import os; print('✅ Token set!' if os.getenv('GITHUB_TOKEN') else '❌ Token NOT set')"
```

---

## 🚀 Running the Enrichment Script

### Test Mode (5 profiles)

**Always test first!**

```bash
cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete
python3 enrichment_scripts/07_github_pr_enrichment.py --test
```

Expected output:
```
============================================================
🚀 GitHub PR Enrichment Script
============================================================
🧪 TEST MODE: Processing 5 profiles only
============================================================
📊 Processing 5 GitHub profiles...
⏱️  Rate limit delay: 0.8s between requests
⏰ Estimated time: 0.1 minutes

[1/5] Processing: John Doe (@johndoe)
  ✓ Profile: 12 merged PRs, 5,432 lines
    • Uniswap/v3-core: 3 merged, score=78.5
    • ethereum/solidity: 1 merged, score=85.0
  ✅ Successfully enriched johndoe

[2/5] Processing: Jane Smith (@janesmith)
...

============================================================
✅ Enrichment complete!
   Success: 5/5
   Errors: 0/5
============================================================
```

### Production Mode (50 profiles)

```bash
python3 enrichment_scripts/07_github_pr_enrichment.py --batch-size 50
```

### Large Batch (500 profiles - ~7 hours)

```bash
nohup python3 enrichment_scripts/07_github_pr_enrichment.py --batch-size 500 > logs/pr_enrichment.log 2>&1 &
```

Monitor progress:
```bash
tail -f logs/pr_enrichment.log
```

---

## 📊 Script Options

| Option | Default | Description |
|--------|---------|-------------|
| `--test` | False | Test mode: only 5 profiles |
| `--batch-size` | 50 | Number of profiles to process |
| `--rate-limit-delay` | 0.8 | Seconds between requests (stays under 5000/hour) |

### Examples:

```bash
# Process 100 profiles
python3 enrichment_scripts/07_github_pr_enrichment.py --batch-size 100

# Process faster (but risk hitting rate limit)
python3 enrichment_scripts/07_github_pr_enrichment.py --batch-size 50 --rate-limit-delay 0.5

# Process slower (more conservative)
python3 enrichment_scripts/07_github_pr_enrichment.py --batch-size 50 --rate-limit-delay 1.0
```

---

## ⏱️ Rate Limits & Timing

**GitHub API Limits:**
- **GraphQL API**: 5,000 requests/hour
- **Resets**: Every hour
- **Our default**: 0.8s delay = 4,500 requests/hour (safe margin)

**Estimated Times:**

| Profiles | Time | Rate |
|----------|------|------|
| 5 (test) | ~4 seconds | Test only |
| 50 | ~40 seconds | Good for testing |
| 100 | ~1.5 minutes | Quick batch |
| 500 | ~7 minutes | Medium batch |
| 5,000 | ~70 minutes | Large batch |
| 50,000 | ~11 hours | Full enrichment |

**Tip**: Run large batches overnight!

```bash
# Start at night, check in morning
nohup python3 enrichment_scripts/07_github_pr_enrichment.py --batch-size 5000 > logs/pr_enrichment_$(date +%Y%m%d).log 2>&1 &

# Check progress
tail -f logs/pr_enrichment_*.log
```

---

## 📈 What Gets Updated

### `github_profile` table:
```sql
- total_merged_prs       -- Career total (CRITICAL!)
- is_pro_account         -- GitHub Pro indicator
- total_lines_contributed -- Career total lines
- total_stars_earned     -- Stars on personal repos
- enriched_at            -- Timestamp of enrichment
```

### `github_contribution` table (per repository):
```sql
- pr_count                    -- Total PRs
- merged_pr_count             -- Merged PRs (CRITICAL!)
- open_pr_count               -- Open PRs
- closed_unmerged_pr_count    -- Closed without merge
- lines_added                 -- Code added
- lines_deleted               -- Code removed
- files_changed               -- Files modified
- last_merged_pr_date         -- Most recent merge
- contribution_quality_score  -- 0-100 score
```

---

## 🔍 Verifying Results

### Check enrichment status:

```sql
-- See how many profiles are enriched
SELECT 
  COUNT(*) FILTER (WHERE enriched_at IS NOT NULL) as enriched,
  COUNT(*) FILTER (WHERE enriched_at IS NULL) as not_enriched,
  COUNT(*) as total
FROM github_profile;

-- Top contributors by merged PRs
SELECT 
  p.full_name,
  gp.github_username,
  gp.total_merged_prs,
  gp.total_lines_contributed,
  gp.is_pro_account
FROM github_profile gp
JOIN person p ON gp.person_id = p.person_id
WHERE gp.total_merged_prs > 0
ORDER BY gp.total_merged_prs DESC
LIMIT 10;

-- Quality score distribution
SELECT 
  CASE 
    WHEN contribution_quality_score >= 80 THEN 'Excellent (80-100)'
    WHEN contribution_quality_score >= 60 THEN 'Good (60-79)'
    WHEN contribution_quality_score >= 40 THEN 'Fair (40-59)'
    ELSE 'Low (<40)'
  END as quality_tier,
  COUNT(*) as count
FROM github_contribution
WHERE contribution_quality_score IS NOT NULL
GROUP BY quality_tier
ORDER BY MIN(contribution_quality_score) DESC;
```

---

## 🎨 Frontend Display

Once enriched, profiles will automatically show:

### Profile-Level Stats (top of GitHub section):
- 🟢 **"✓ X Merged Pull Requests"** - Confirmed contributions
- 🔵 **"X Lines of Code"** - Career total
- 🟣 **"✓ GitHub Pro"** - Has private repos

### Per-Repository Badges:
- ✅ **"✓ 3 Merged PRs"** - Confirmed merged
- 📊 **"Score: 85/100"** - Quality rating
- 📈 **"+5,432 lines"** - Code volume

### Visual Hierarchy:
- High scores (70-100): Green badge
- Medium scores (40-69): Blue badge
- Low scores (<40): Gray badge

---

## 🐛 Troubleshooting

### Error: "GITHUB_TOKEN not set"

**Solution**: Follow "Prerequisites" section above to set token

### Error: "API rate limit exceeded"

**Solutions**:
1. Wait 1 hour for rate limit reset
2. Check rate limit status:
   ```bash
   curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/rate_limit
   ```
3. Increase `--rate-limit-delay`

### Error: "User not found on GitHub"

**Normal**: Some usernames changed or accounts deleted. Script logs warning and continues.

### Script hangs/no output

**Solutions**:
1. Check internet connection
2. Verify token is valid: https://github.com/settings/tokens
3. Check GitHub API status: https://www.githubstatus.com/

### Database connection errors

**Solutions**:
1. Verify PostgreSQL is running:
   ```bash
   psql -d talent -c "SELECT 1;"
   ```
2. Check config.py settings
3. Verify database migrations ran:
   ```bash
   psql -d talent -c "\d github_contribution" | grep "merged_pr_count"
   ```

---

## 📊 Quality Score Algorithm

The script calculates a 0-100 quality score based on:

### Positive Signals (+points):
- **Official repo** (not fork): +20
- **Merged PRs**: +5 per PR (max +30)
- **Code volume**:
  - 1000+ lines: +15
  - 100-999 lines: +10
  - 10-99 lines: +5
- **Repository popularity**:
  - 1000+ stars: +15
  - 100-999 stars: +10
  - 50-99 stars: +5
- **Recent activity**:
  - Last 3 months: +10
  - Last 6 months: +5

### Negative Signals (-points):
- **Fork with no upstream merge**: -10

### Score Interpretation:

| Score | Meaning | Recommendation |
|-------|---------|----------------|
| 80-100 | Excellent | Strong hire signal |
| 60-79 | Good | Solid contributor |
| 40-59 | Fair | Verify manually |
| 0-39 | Low | Needs investigation |

---

## 🎯 Best Practices

### 1. **Test First**
Always run `--test` mode before large batches

### 2. **Monitor Progress**
Use `tail -f logs/pr_enrichment.log` for long-running jobs

### 3. **Incremental Enrichment**
Run daily/weekly for new profiles:
```bash
# Cron job example (daily at 2 AM)
0 2 * * * cd /path/to/project && python3 enrichment_scripts/07_github_pr_enrichment.py --batch-size 100
```

### 4. **Check Data Quality**
After enrichment, spot-check a few profiles:
```sql
SELECT * FROM github_profile WHERE enriched_at IS NOT NULL LIMIT 5;
```

### 5. **Re-enrichment**
To update stale data, clear `enriched_at`:
```sql
UPDATE github_profile 
SET enriched_at = NULL 
WHERE enriched_at < NOW() - INTERVAL '30 days';
```

---

## 🚀 Next Steps After Enrichment

1. ✅ **View enriched profiles** in the UI
2. ✅ **Sort by quality scores** to find top talent
3. ✅ **Filter by merged PRs** for confirmed contributors
4. ✅ **Export data** for analysis
5. ✅ **Share with team** - show off the rich data!

---

## 📝 Example Session

```bash
# 1. Set token
export GITHUB_TOKEN=ghp_your_token_here

# 2. Test with 5 profiles
python3 enrichment_scripts/07_github_pr_enrichment.py --test

# Output:
# ============================================================
# 🚀 GitHub PR Enrichment Script
# ============================================================
# 🧪 TEST MODE: Processing 5 profiles only
# ...
# ✅ Enrichment complete!
#    Success: 5/5

# 3. Check results in database
psql -d talent -c "
SELECT p.full_name, gp.total_merged_prs, gp.total_lines_contributed
FROM github_profile gp
JOIN person p ON gp.person_id = p.person_id
WHERE gp.enriched_at IS NOT NULL
LIMIT 5;
"

# 4. View in UI
# Open http://localhost:3000 and view any GitHub profile

# 5. Run larger batch (overnight)
nohup python3 enrichment_scripts/07_github_pr_enrichment.py --batch-size 1000 > logs/pr_enrichment.log 2>&1 &
```

---

## ✅ Success Checklist

- [ ] GitHub token created and set
- [ ] Token verified with test command
- [ ] Database migration run (08_github_pr_enrichment.sql)
- [ ] Test mode run successfully (5 profiles)
- [ ] Results verified in database
- [ ] Results visible in UI
- [ ] Production batch running/complete

---

**Phase 2 is ready to roll! Get your GitHub token and let the enrichment begin!** 🎉


