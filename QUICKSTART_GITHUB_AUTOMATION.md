# 🚀 GitHub Automation - Quick Start

## Get Started in 5 Minutes!

### Step 1: Get GitHub Token (2 minutes)
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name: "Talent Intelligence"
4. Select scopes:
   - ✅ `public_repo`
   - ✅ `read:user`
   - ✅ `read:org`
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)

### Step 2: Set Token (30 seconds)
```bash
# Set for current session
export GITHUB_TOKEN='your_token_here'

# Or add to ~/.bashrc or ~/.zshrc for persistence
echo 'export GITHUB_TOKEN="your_token_here"' >> ~/.zshrc
source ~/.zshrc
```

### Step 3: Check Status (30 seconds)
```bash
cd /path/to/talent-intelligence-complete
python3 enrich_github_continuous.py --status-only
```

**You should see:**
```
📊 GITHUB ENRICHMENT STATUS
Total GitHub profiles: 17,534
Enriched profiles: 519 (3.0%)
Matched to people: 207 (1.2%)
Pending enrichment: 17,015
```

### Step 4: Test with 10 Profiles (2 minutes)
```bash
python3 enrich_github_continuous.py --batch-size 10 --with-matching
```

**Watch for:**
- ✅ "Enriched {username}" messages
- ✅ "Matched via {strategy}" messages
- ✅ No errors in output

### Step 5: Run Full Enrichment!
```bash
# Option A: One large batch
python3 enrich_github_continuous.py --batch-size 1000 --with-matching

# Option B: Continuous mode (recommended)
python3 enrich_github_continuous.py --continuous --with-matching

# Option C: Add to cron (hourly)
crontab -e
# Add this line:
0 * * * * cd /path/to/project && python3 enrich_github_continuous.py --batch-size 200 --with-matching >> logs/cron.log 2>&1
```

---

## Expected Timeline

### Hour 1
- 1,000 profiles enriched
- 300 newly matched
- **Coverage**: 3% → 9%

### Day 1 (8 hours)
- 8,000 profiles enriched  
- 3,000 matched to people
- **Coverage**: 3% → 46%

### Week 1
- 15,000+ profiles enriched
- 8,000+ matched to people
- **Coverage**: 3% → 85%+ ✅

---

## Monitoring

### Watch Logs
```bash
# Real-time log
tail -f logs/github_automation/enrichment_*.log

# Error logs only
grep ERROR logs/github_automation/enrichment_*.log
```

### Check Progress
```bash
# Quick status check
python3 enrich_github_continuous.py --status-only

# Database query
psql -U $USER -d talent -c "
SELECT 
    COUNT(*) as total,
    COUNT(CASE WHEN last_enriched IS NOT NULL THEN 1 END) as enriched,
    COUNT(person_id) as matched
FROM github_profile;
"
```

---

## Troubleshooting

### Problem: "No token - rate limit will be 60/hour"
**Solution**: Set GITHUB_TOKEN environment variable
```bash
export GITHUB_TOKEN='your_token'
```

### Problem: "Rate limit exceeded"
**Solution**: System automatically waits. Be patient!

### Problem: "No profiles need enrichment"
**Solution**: Great! Everything is enriched. Check matching:
```bash
python3 -c "
from github_automation import ProfileMatcher
matcher = ProfileMatcher()
matcher.match_unmatched_profiles(limit=1000)
"
```

### Problem: Low match rate
**Solution**: Normal! Only ~30-40% of profiles can be confidently matched. The rest become new people or need manual review.

---

## Key Commands

```bash
# Status check (no API calls)
python3 enrich_github_continuous.py --status-only

# Test with 10 profiles
python3 enrich_github_continuous.py --batch-size 10 --with-matching

# One batch (100 profiles)
python3 enrich_github_continuous.py --with-matching

# Large batch (1000 profiles)
python3 enrich_github_continuous.py --batch-size 1000 --with-matching

# Continuous until stopped (Ctrl+C)
python3 enrich_github_continuous.py --continuous --with-matching

# Check logs
tail -f logs/github_automation/enrichment_$(date +%Y%m%d).log
```

---

## What Happens During Enrichment?

1. **Queue Manager** finds profiles needing enrichment
2. **GitHub Client** fetches profile data from API
3. **Enrichment Engine** updates database with:
   - Name, email, bio, location
   - Company, Twitter, blog
   - Followers, repos, languages
   - LinkedIn URL (if in bio)
4. **Profile Matcher** links profiles to people:
   - Email matching (highest confidence)
   - LinkedIn URL matching
   - Name + company matching
   - Name + location matching
5. **Statistics** updated and logged

---

## Success Indicators

✅ **It's Working If:**
- Profiles incrementally being enriched
- Match count increasing
- No major errors in logs
- API rate limit respected (automatic)
- Statistics look reasonable

❌ **Check Issues If:**
- Error rate > 10%
- Match rate < 20%
- Frequent rate limit warnings
- Database connection errors
- Unexpected crashes

---

## After Completion

Once enrichment is done, you'll have:
- ✅ **15,000+ enriched profiles** (85%+ coverage)
- ✅ **8,000+ matched profiles** (45%+ match rate)
- ✅ **Comprehensive GitHub data** for talent intelligence
- ✅ **Automated daily updates** (if cron scheduled)

Use this data for:
- 🔍 **Better search** - Find developers by skills, location, company
- 📊 **Analytics** - Understand talent distribution, skills gaps
- 🎯 **Sourcing** - Target specific profiles for outreach
- 🤝 **Matching** - Link profiles across data sources
- 📈 **Trends** - Track technology adoption, hiring patterns

---

## Next Steps

After GitHub automation is running:
1. **Streamlit UI** - Build search interface
2. **Company Discovery** - Auto-discover GitHub orgs
3. **Skills Extraction** - Infer skills from repos
4. **Documentation** - User guides and API docs

See **`GITHUB_AUTOMATION_COMPLETE.md`** for full details!

---

**Ready? Let's go!** 🚀

```bash
export GITHUB_TOKEN='your_token_here'
python3 enrich_github_continuous.py --continuous --with-matching
```

