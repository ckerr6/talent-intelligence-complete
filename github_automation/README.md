# GitHub Automation System

**Automated discovery, enrichment, and matching of GitHub profiles to people.**

## 🎯 Overview

This system automatically:
1. **Discovers** unenriched GitHub profiles in your database
2. **Enriches** them with data from GitHub API (bio, location, followers, repos, etc.)
3. **Matches** enriched profiles to existing people using multiple strategies
4. **Creates** new person records for high-quality unmatched profiles
5. **Monitors** progress and data quality continuously

### Current Stats
- **17,534 GitHub profiles** in database
- **207 matched** to people (1.2%)
- **519 enriched** (3.0%)

### Goals
- Increase enrichment to **85%+ (15,000+ profiles)**
- Increase matches to **50%+ (8,500+ profiles)**
- Discover **5,000+ new people** from GitHub orgs/repos

---

## 🚀 Quick Start

### 1. Set GitHub Token
```bash
export GITHUB_TOKEN='your_github_personal_access_token'
```

Get a token from: https://github.com/settings/tokens
- Requires: `public_repo`, `read:user`, `read:org` scopes

### 2. Run Status Check
```bash
python3 enrich_github_continuous.py --status-only
```

This shows:
- Current enrichment coverage
- Match rates
- Pending profiles
- Estimated time to complete

### 3. Run Enrichment
```bash
# Enrich 100 profiles (one batch)
python3 enrich_github_continuous.py

# Enrich with matching
python3 enrich_github_continuous.py --with-matching

# Continuous mode (runs until stopped)
python3 enrich_github_continuous.py --continuous --with-matching
```

### 4. Monitor Progress
```bash
# Watch logs in real-time
tail -f logs/github_automation/enrichment_*.log
```

---

## 📋 Architecture

```
GitHub Automation System
├── GitHubClient          # Rate-limited API wrapper
├── QueueManager          # Priority queue of profiles
├── EnrichmentEngine      # Profile enrichment logic
├── ProfileMatcher        # Matching to existing people
└── Scheduler            # (Future) Cron/daemon mode
```

### Components

#### 1. **GitHubClient** (`github_client.py`)
- Rate-limited GitHub API wrapper
- Automatic retry with exponential backoff
- Request caching (optional)
- Comprehensive error handling
- Statistics tracking

**Features:**
- ✅ Respects GitHub rate limits (5000/hour with token)
- ✅ Automatic waiting when rate limit reached
- ✅ Retries on server errors
- ✅ Detailed logging and statistics

#### 2. **QueueManager** (`queue_manager.py`)
- Manages priority queue of profiles to enrich
- Prioritizes by:
  - Never enriched (highest priority)
  - Has email/location (easier to match)
  - High followers (more visible/important)
  - Stale data (>30 days old)

**Features:**
- ✅ Smart prioritization
- ✅ Batch processing
- ✅ Status tracking
- ✅ Statistics and monitoring

#### 3. **EnrichmentEngine** (`enrichment_engine.py`)
- Enriches profiles via GitHub API
- Extracts comprehensive data
- Updates database efficiently
- Tracks success/failure rates

**Data Collected:**
- Name, email, bio, location
- Company, blog, Twitter
- Followers, following, public repos
- Programming languages
- Top repositories
- LinkedIn URL (if in bio)
- Hire-ability status

#### 4. **ProfileMatcher** (`matcher.py`)
- Matches GitHub profiles to people
- Multiple strategies with confidence scoring
- Auto-match above threshold
- Creates new person records when appropriate

**Matching Strategies:**
1. **Email match** (95% confidence) - matches person_email table
2. **LinkedIn URL** (99% confidence) - extracted from bio
3. **Name + Company** (85% confidence) - current employment
4. **Name + Location** (70% confidence) - less specific

---

## 🔧 Configuration

Edit `github_automation/config.py` to customize:

```python
# Rate Limiting
RATE_LIMIT_BUFFER = 100      # Keep N requests in reserve
REQUEST_DELAY = 0.72          # Seconds between requests

# Enrichment
BATCH_SIZE = 100              # Profiles per batch
STALE_DAYS = 30               # Re-enrich after N days

# Matching
AUTO_MATCH_THRESHOLD = 0.85   # Auto-match if confidence >= this
EMAIL_MATCH_CONFIDENCE = 0.95
NAME_COMPANY_MATCH_CONFIDENCE = 0.85

# Priority Weights
PRIORITY_HAS_EMAIL = 10
PRIORITY_HAS_LOCATION = 5
PRIORITY_HIGH_FOLLOWERS = 8
```

---

## 📊 Usage Examples

### Status Dashboard
```bash
python3 enrich_github_continuous.py --status-only
```

**Output:**
```
====================================================================
📊 GITHUB ENRICHMENT STATUS
====================================================================

📈 Current State:
  Total GitHub profiles: 17,534
  Enriched profiles: 519 (3.0%)
  Matched to people: 207 (1.2%)
  Pending enrichment: 17,015

🎯 Goals:
  Target enrichment: 85% (14,904 profiles)
  Target matches: 50% (8,767 profiles)

📋 Remaining:
  Need to enrich: 14,385 more profiles
  Need to match: 8,560 more profiles

⏱️  Estimated time to complete: 4.7 hours
   (At ~1 profile/second with GitHub API rate limits)
```

### One-Time Enrichment
```bash
# Enrich 100 profiles
python3 enrich_github_continuous.py

# Enrich 500 profiles
python3 enrich_github_continuous.py --batch-size 500

# Enrich and match
python3 enrich_github_continuous.py --batch-size 100 --with-matching
```

### Continuous Mode
```bash
# Run continuously (Ctrl+C to stop)
python3 enrich_github_continuous.py --continuous --with-matching
```

**Runs continuously:**
1. Enriches batch of profiles
2. Matches to existing people
3. Shows progress
4. Waits 10 seconds
5. Repeats

### Scheduled Runs (Cron)
```bash
# Add to crontab for hourly enrichment
0 * * * * cd /path/to/project && /usr/bin/python3 enrich_github_continuous.py --batch-size 200 --with-matching >> logs/cron.log 2>&1

# Daily full enrichment at 2 AM
0 2 * * * cd /path/to/project && /usr/bin/python3 enrich_github_continuous.py --batch-size 1000 --with-matching >> logs/cron.log 2>&1
```

---

## 📈 Expected Results

### After 1 Hour
- ✅ 1,000+ profiles enriched
- ✅ 300+ new matches
- ✅ System validated and stable

### After 1 Day (8 hours of running)
- ✅ 8,000+ profiles enriched (45% coverage)
- ✅ 3,000+ matched to people (17% match rate)
- ✅ Continuous automation working

### After 1 Week
- ✅ 15,000+ profiles enriched (85% coverage)
- ✅ 8,000+ matched to people (45% match rate)
- ✅ 2,000+ new people discovered
- ✅ Automated daily updates

---

## 🔍 Monitoring

### Log Files
```bash
# Main enrichment log
logs/github_automation/enrichment_YYYYMMDD.log

# Error log (if errors occur)
logs/github_automation/errors_YYYYMMDD.log
```

### Key Metrics
- **Enrichment rate**: profiles/hour
- **Match rate**: % of enriched profiles matched
- **API quota usage**: requests remaining
- **Error rate**: failures/total attempts
- **Data quality**: % complete profiles

### Database Queries
```sql
-- Current stats
SELECT 
    COUNT(*) as total,
    COUNT(person_id) as matched,
    COUNT(CASE WHEN bio IS NOT NULL THEN 1 END) as enriched
FROM github_profile;

-- Match rate by strategy
SELECT 
    source,
    COUNT(*) as count
FROM github_profile
WHERE person_id IS NOT NULL
GROUP BY source;

-- Recent enrichments
SELECT 
    github_username,
    github_name,
    location,
    followers,
    last_enriched
FROM github_profile
WHERE last_enriched >= NOW() - INTERVAL '1 hour'
ORDER BY last_enriched DESC
LIMIT 20;
```

---

## 🚨 Troubleshooting

### Issue: Rate Limit Exceeded
**Symptoms:** "⚠️ Rate limit exceeded" messages
**Solution:** 
- System automatically waits for rate limit reset
- Ensure GITHUB_TOKEN is set
- Reduce BATCH_SIZE if needed

### Issue: No Profiles Being Enriched
**Check:**
1. Are there pending profiles? `--status-only`
2. Is GITHUB_TOKEN set? `echo $GITHUB_TOKEN`
3. Check logs for errors

### Issue: Low Match Rate
**Solutions:**
- Ensure profiles are enriched first (need email/name/location)
- Check matching thresholds in config.py
- Review low-confidence matches in logs
- May need to adjust matching strategies

### Issue: Database Connection Errors
**Check:**
1. PostgreSQL is running
2. Environment variables set (PGHOST, PGDATABASE, etc.)
3. Connection pool settings in config.py

---

## 🔐 Security

### GitHub Token
- Store in environment variable, not code
- Use token with minimal necessary scopes
- Rotate tokens regularly
- Never commit tokens to git

### Database
- Use connection pooling
- Parameterized queries (SQL injection safe)
- Read-only tokens for monitoring
- Backup before major changes

---

## 🎯 Next Steps

### Phase 1: Basic Enrichment (Days 1-2) ✅
- [x] Core infrastructure
- [x] GitHub API client
- [x] Enrichment engine
- [x] Queue management
- [x] Basic CLI

### Phase 2: Matching (Days 3-4)
- [x] Multiple matching strategies
- [x] Confidence scoring
- [x] Auto-matching
- [ ] Manual review interface

### Phase 3: Discovery (Days 5-7)
- [ ] Company GitHub org discovery
- [ ] Repository contributor extraction
- [ ] Automatic profile discovery
- [ ] Organization member sync

### Phase 4: Automation (Days 8-10)
- [ ] Daemon mode (systemd/launchd)
- [ ] Health monitoring
- [ ] Alerting on failures
- [ ] Metrics dashboard

### Phase 5: Advanced Features (Future)
- [ ] ML-based matching
- [ ] Skills extraction from repos
- [ ] Contribution analysis
- [ ] Developer ranking/scoring
- [ ] Network analysis

---

## 📚 API Reference

### GitHubClient
```python
from github_automation import GitHubClient

client = GitHubClient(token='your_token')

# Get user profile
user = client.get_user('username')

# Get user repos
repos = client.get_user_repos('username')

# Get org members
members = client.get_org_members('company')

# Check rate limit
client.check_rate_limit()

# Get statistics
stats = client.get_stats()
```

### QueueManager
```python
from github_automation import QueueManager

queue = QueueManager()

# Get profiles needing enrichment
profiles = queue.get_unenriched_profiles(limit=100)

# Mark as enriched
queue.mark_enriched(profile_id, success=True)

# Get statistics
stats = queue.get_statistics()
```

### EnrichmentEngine
```python
from github_automation import EnrichmentEngine

engine = EnrichmentEngine()

# Enrich single profile
success = engine.enrich_profile(profile)

# Enrich batch
stats = engine.enrich_batch(profiles)
```

### ProfileMatcher
```python
from github_automation import ProfileMatcher

matcher = ProfileMatcher()

# Match single profile
person_id, confidence, strategy = matcher.match_profile(profile)

# Match all unmatched
stats = matcher.match_unmatched_profiles(limit=100)
```

---

## 💡 Tips & Best Practices

1. **Start Small**: Run with `--batch-size 10` first to validate
2. **Monitor Logs**: Watch logs in real-time to catch issues early
3. **Check Status Often**: Use `--status-only` to track progress
4. **Match After Enriching**: Always use `--with-matching` for best results
5. **Run During Off-Hours**: Less database contention
6. **Backup First**: Backup database before large enrichment runs
7. **Use Continuous Mode**: For unattended operation
8. **Set Alerts**: Monitor error rates and rate limit usage

---

## 📞 Support

For issues, questions, or improvements:
1. Check logs in `logs/github_automation/`
2. Review configuration in `github_automation/config.py`
3. Check database with provided SQL queries
4. Review GitHub API rate limits

---

**Status**: ✅ Production Ready
**Version**: 1.0.0
**Last Updated**: October 20, 2025

