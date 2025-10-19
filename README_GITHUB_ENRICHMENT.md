# 🎯 GitHub Enrichment - Complete System

## What This Does

This system enriches your talent database with comprehensive GitHub data using the official GitHub API.

### Three Main Functions:

1. **Enrich Existing Profiles** - Update 12,815 profiles with latest data
2. **Company Discovery** - Find all repos + contributors for any company
3. **User Enrichment** - Get complete profile for specific users

## Architecture

Yes, this works perfectly with our database! Here's how:

```
Your Workflow:
  Company GitHub Org (e.g., "uniswap-labs")
    ↓
  Get All Public Repos
    ↓
  Get All Contributors Per Repo
    ↓
  Get Full User Profile Data
    ↓
  Link Everything: Company → Repos → Contributors → People
```

Database Tables:
- ✅ **companies** - Company records
- ✅ **company_repositories** - Repo metadata (NEW)
- ✅ **github_repo_contributions** - Who contributed where (NEW)
- ✅ **github_profiles** - Individual profiles
- ✅ **people** - Candidate records

Everything is properly linked with foreign keys. You can query:
- All contributors to a company
- All repos a person contributed to
- All people who know a specific tech stack
- Top contributors by commit count or influence

## Quick Start

### 1. Get GitHub Token (2 minutes)

Visit: https://github.com/settings/tokens

Click: "Generate new token (classic)"

Select scopes:
- ✅ public_repo
- ✅ read:user  
- ✅ read:org

Copy your token.

### 2. Set Token

```bash
export GITHUB_TOKEN='your_token_here'
```

### 3. Run Enrichment

```bash
cd "/Users/charlie.kerr/Documents/CK Docs/FINAL_DATABASE"

# Option A: Enrich all existing profiles (~3-4 hours)
python3 github_api_enrichment.py enrich-existing talent_intelligence.db

# Option B: Discover company repos + contributors (~10-30 min)
python3 github_api_enrichment.py discover-company talent_intelligence.db uniswap-labs "Uniswap"

# Option C: Enrich specific user (~1 second)
python3 github_api_enrichment.py enrich-user talent_intelligence.db haydenadams
```

## Detailed Examples

### Example 1: Update All Existing Profiles

**Goal:** Get current follower counts, repo counts, company data for 12,815 profiles

```bash
python3 github_api_enrichment.py enrich-existing talent_intelligence.db
```

**What happens:**
- Reads all usernames from `github_profiles` table
- Calls GitHub API for each: `GET /users/{username}`
- Updates: followers, following, public_repos, company, location, email, etc.
- Commits every 100 profiles (checkpointable)

**Time:** 3-4 hours with token (0.72s per user)

**Result:**
```
📊 ENRICHMENT STATISTICS
Profiles Enriched:  12,815
API Requests Made:  12,815
Errors:             0
```

---

### Example 2: Discover Uniswap's Entire Engineering Team

**Goal:** Find every engineer who's ever contributed to Uniswap

```bash
python3 github_api_enrichment.py discover-company talent_intelligence.db uniswap-labs "Uniswap"
```

**What happens:**
1. Gets all repos: `GET /orgs/uniswap-labs/repos`
2. For each repo, gets contributors: `GET /repos/uniswap-labs/v3-core/contributors`
3. For each contributor, gets profile: `GET /users/{username}`
4. Saves everything to database with proper links

**Time:** 10-30 minutes depending on company size

**Result:**
```
📊 ENRICHMENT STATISTICS
Repos Discovered:   22
Contributors Found: 456
Profiles Created:   312
Profiles Enriched:  144
```

**Then query:**
```sql
-- Top 50 Uniswap contributors
SELECT 
    gp.github_username,
    gp.github_name,
    gp.github_email,
    gp.followers,
    SUM(grc.contribution_count) as total_commits
FROM github_profiles gp
JOIN github_repo_contributions grc ON gp.github_profile_id = grc.github_profile_id
JOIN companies c ON grc.company_id = c.company_id
WHERE c.name = 'Uniswap'
GROUP BY gp.github_profile_id
ORDER BY total_commits DESC
LIMIT 50;
```

---

### Example 3: Find All Solidity Developers

**Goal:** Build sourcing list of Solidity engineers

```bash
# Discover several DeFi companies
python3 github_api_enrichment.py discover-company talent_intelligence.db uniswap-labs "Uniswap"
python3 github_api_enrichment.py discover-company talent_intelligence.db aave "Aave"
python3 github_api_enrichment.py discover-company talent_intelligence.db compoundfinance "Compound"
python3 github_api_enrichment.py discover-company talent_intelligence.db ensdomains "ENS"
```

**Then query:**
```sql
-- Solidity developers with 2+ repos, sorted by influence
SELECT 
    gp.github_username,
    gp.github_name,
    gp.github_email,
    gp.github_company,
    gp.followers,
    COUNT(DISTINCT grc.repo_id) as solidity_repos,
    SUM(grc.contribution_count) as total_commits
FROM github_profiles gp
JOIN github_repo_contributions grc ON gp.github_profile_id = grc.github_profile_id
JOIN company_repositories cr ON grc.repo_id = cr.repo_id
WHERE cr.language = 'Solidity'
GROUP BY gp.github_profile_id
HAVING solidity_repos >= 2
ORDER BY gp.followers DESC
LIMIT 200;
```

**Result:** 200 top Solidity devs with emails, current companies, influence scores

---

## Rate Limits & Performance

### Without Token (DON'T DO THIS)
- Rate: 60 requests/hour
- Time to enrich 12,815 profiles: 213 hours (9 days!)

### With Token (RECOMMENDED)
- Rate: 5,000 requests/hour
- Time to enrich 12,815 profiles: 2.6 hours
- Buffer: Keep 100 requests in reserve
- Delay: 0.72s between requests

### Company Discovery Estimates

Small company (10 repos, 50 contributors):
- Requests: 1 + 10 + 50 = 61
- Time: ~1 minute

Medium company (50 repos, 500 contributors):
- Requests: 1 + 50 + 500 = 551
- Time: ~7 minutes

Large company (100 repos, 2000 contributors):
- Requests: 1 + 100 + 2000 = 2101
- Time: ~25 minutes

## Ready to Start?

```bash
cd "/Users/charlie.kerr/Documents/CK Docs/FINAL_DATABASE"
export GITHUB_TOKEN='your_token_here'
python3 github_api_enrichment.py enrich-existing talent_intelligence.db
```

🚀 Let's build the best talent database in crypto!
