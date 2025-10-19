# 🏗️ GitHub Enrichment Architecture

## Database Schema

The system uses these interconnected tables:

```
┌─────────────────────┐
│     companies       │
│─────────────────────│
│ company_id (PK)     │
│ name                │
│ github_org          │◄───────┐
│ website             │        │
│ ...                 │        │
└─────────────────────┘        │
         │                     │
         │ 1:N                 │
         ▼                     │
┌─────────────────────────┐   │
│ company_repositories    │   │
│─────────────────────────│   │
│ repo_id (PK)            │   │
│ company_id (FK) ────────┘   │
│ repo_name               │   │
│ full_name               │   │
│ language                │   │
│ stars                   │   │
│ forks                   │   │
│ ...                     │   │
└─────────────────────────┘   │
         │                    │
         │ 1:N                │
         ▼                    │
┌──────────────────────────┐  │
│github_repo_contributions │  │
│──────────────────────────│  │
│ contribution_id (PK)     │  │
│ github_profile_id (FK)───┼──┼─┐
│ company_id (FK) ─────────┘  │ │
│ repo_id (FK) ───────────────┘ │
│ repo_full_name           │    │
│ contribution_count       │    │
└──────────────────────────┘    │
                                │
         ┌──────────────────────┘
         │
         ▼
┌─────────────────────┐
│  github_profiles    │
│─────────────────────│
│ github_profile_id   │
│ person_id (FK) ─────┼───────┐
│ github_username     │       │
│ github_name         │       │
│ github_email        │       │
│ github_company      │       │
│ followers           │       │
│ following           │       │
│ public_repos        │       │
│ ...                 │       │
└─────────────────────┘       │
                              │
                              │
         ┌────────────────────┘
         │
         ▼
┌─────────────────────┐
│       people        │
│─────────────────────│
│ person_id (PK)      │
│ first_name          │
│ last_name           │
│ primary_email       │
│ ...                 │
└─────────────────────┘
```

## Workflow

### 1. Enrich Existing Profiles

**What it does:**
- Takes the 12,815 GitHub usernames we already have
- Calls GitHub API for each user
- Updates with latest data (followers, repos, company, etc.)

**Command:**
```bash
python3 github_api_enrichment.py enrich-existing talent_intelligence.db
```

**Time:** ~3-4 hours with token (12,815 users × 0.72s each)

**Output:**
- All `github_profiles` updated with current API data
- Rate: ~5000 profiles/hour
- No new profiles created, only enrichment

---

### 2. Company Discovery

**What it does:**
1. Starts with company GitHub org (e.g., "uniswap-labs")
2. Fetches ALL public repositories for that org
3. For EACH repo, gets ALL contributors
4. For EACH contributor, creates/updates profile
5. Links everything: Company → Repos → Contributors → People

**Command:**
```bash
python3 github_api_enrichment.py discover-company talent_intelligence.db uniswap-labs "Uniswap"
```

**Time:** Depends on company size
- Small company (10 repos, 50 contributors): ~10 minutes
- Medium company (50 repos, 500 contributors): ~30 minutes  
- Large company (100+ repos, 2000+ contributors): ~2 hours

**Output:**
- New records in `company_repositories` (all repos)
- New records in `github_profiles` (all contributors)
- New records in `github_repo_contributions` (who contributed where)
- Links created: Company ← Repos ← Contributors ← People

**Example Discovery for Uniswap:**
```
Company: Uniswap (uniswap-labs)
  ├─ Repo: v3-core (1,234 stars)
  │   ├─ Contributor: haydenadams (523 commits)
  │   ├─ Contributor: moodysalem (412 commits)
  │   └─ ... (50 more contributors)
  │
  ├─ Repo: v3-periphery (987 stars)
  │   ├─ Contributor: haydenadams (234 commits)
  │   └─ ... (40 more contributors)
  │
  └─ ... (20 more repos)

Total:
- Repositories discovered: 22
- Contributors found: 456
- New profiles created: 312
- Existing profiles enriched: 144
```

---

### 3. User Enrichment

**What it does:**
- Fetches complete profile for ONE specific user
- Useful for spot checks or VIP profiles

**Command:**
```bash
python3 github_api_enrichment.py enrich-user talent_intelligence.db haydenadams
```

**Time:** ~1 second per user

**Output:**
- One `github_profiles` record created/updated
- Full data from GitHub API

---

## Data Flow

### Discovery Workflow

```
1. Input: GitHub org name (e.g., "uniswap-labs")
         │
         ▼
2. API Call: GET /orgs/uniswap-labs/repos
         │
         ├─ Repo 1: v3-core
         ├─ Repo 2: v3-periphery
         └─ Repo 3: interface
         │
         ▼
3. For each repo:
   API Call: GET /repos/uniswap-labs/v3-core/contributors
         │
         ├─ Contributor 1: haydenadams (523 commits)
         ├─ Contributor 2: moodysalem (412 commits)
         └─ ...
         │
         ▼
4. For each contributor:
   API Call: GET /users/haydenadams
         │
         ├─ Name: Hayden Adams
         ├─ Email: hayden@uniswap.org
         ├─ Company: Uniswap Labs
         ├─ Followers: 5,234
         └─ ...
         │
         ▼
5. Save to database:
   company_repositories:
   - repo_id, company_id, name, stars, language, ...
   
   github_profiles:
   - github_profile_id, username, name, email, followers, ...
   
   github_repo_contributions:
   - links profile → repo → company
   - stores contribution_count
```

## Rate Limiting

GitHub API limits:
- **Without token:** 60 requests/hour
- **With token:** 5,000 requests/hour

Our strategy:
- Keep 100 request buffer (never go below 100 remaining)
- Wait ~0.72 seconds between requests (5000/hour)
- Auto-pause when hitting limit
- Resume when limit resets

**Math:**
- Enrich 12,815 existing profiles: 12,815 requests = 2.6 hours
- Discover medium company (50 repos, 500 contributors):
  - 1 request (org repos)
  - 50 requests (contributors per repo)
  - 500 requests (user profiles)
  - Total: ~551 requests = ~7 minutes

## Example Use Cases

### Use Case 1: "I want current data for all GitHub profiles I have"

```bash
cd "/Users/charlie.kerr/Documents/CK Docs/FINAL_DATABASE"
export GITHUB_TOKEN="your_token_here"
python3 github_api_enrichment.py enrich-existing talent_intelligence.db
```

**Result:** 12,815 profiles updated with latest followers, repos, company data

---

### Use Case 2: "I want to find all engineers at Uniswap"

```bash
# Step 1: Discover Uniswap's GitHub
python3 github_api_enrichment.py discover-company talent_intelligence.db uniswap-labs "Uniswap"

# Step 2: Query database
sqlite3 talent_intelligence.db
```

```sql
-- Get all Uniswap contributors
SELECT 
    gp.github_username,
    gp.github_name,
    gp.github_email,
    gp.followers,
    COUNT(DISTINCT grc.repo_id) as repos_contributed,
    SUM(grc.contribution_count) as total_contributions
FROM github_profiles gp
JOIN github_repo_contributions grc ON gp.github_profile_id = grc.github_profile_id
JOIN companies c ON grc.company_id = c.company_id
WHERE c.name = 'Uniswap'
GROUP BY gp.github_profile_id
ORDER BY total_contributions DESC
LIMIT 50;
```

**Result:** Top 50 Uniswap contributors with contribution stats

---

### Use Case 3: "I want to find all Solidity developers"

```bash
# First, discover several companies
python3 github_api_enrichment.py discover-company talent_intelligence.db uniswap-labs "Uniswap"
python3 github_api_enrichment.py discover-company talent_intelligence.db aave "Aave"
python3 github_api_enrichment.py discover-company talent_intelligence.db compoundfinance "Compound"
```

```sql
-- Find developers who contributed to Solidity repos
SELECT DISTINCT
    gp.github_username,
    gp.github_name,
    gp.github_email,
    gp.followers,
    COUNT(DISTINCT grc.repo_id) as solidity_repos
FROM github_profiles gp
JOIN github_repo_contributions grc ON gp.github_profile_id = grc.github_profile_id
JOIN company_repositories cr ON grc.repo_id = cr.repo_id
WHERE cr.language = 'Solidity'
GROUP BY gp.github_profile_id
HAVING solidity_repos >= 2
ORDER BY gp.followers DESC
LIMIT 100;
```

**Result:** Top 100 Solidity developers by influence (followers)

---

### Use Case 4: "I want to track a specific person's contributions"

```bash
# Enrich specific user
python3 github_api_enrichment.py enrich-user talent_intelligence.db haydenadams
```

```sql
-- See everywhere they've contributed
SELECT 
    c.name as company,
    cr.repo_name,
    grc.contribution_count,
    cr.language
FROM github_repo_contributions grc
JOIN github_profiles gp ON grc.github_profile_id = gp.github_profile_id
JOIN company_repositories cr ON grc.repo_id = cr.repo_id
JOIN companies c ON cr.company_id = c.company_id
WHERE gp.github_username = 'haydenadams'
ORDER BY grc.contribution_count DESC;
```

**Result:** All repos Hayden Adams has contributed to, sorted by commit count

---

## Architecture Benefits

### ✅ Scalability
- Can handle millions of contributors
- Batch processing with checkpoints
- Resume capability if interrupted

### ✅ Completeness
- Gets ALL repos for a company
- Gets ALL contributors to each repo
- Gets FULL profile data for each person
- Links everything properly

### ✅ Freshness
- Re-run enrichment anytime to update data
- API gives real-time follower counts
- Tracks when data was last updated

### ✅ Queryability
- Find people by company
- Find people by tech stack (language)
- Find people by influence (followers)
- Track contribution patterns
- Identify top contributors

### ✅ Extensibility
- Easy to add new companies
- Easy to re-enrich existing data
- Can filter by date, language, contribution count, etc.

---

## Next Steps After Setup

1. **Enrich existing profiles** (3-4 hours)
   ```bash
   python3 github_api_enrichment.py enrich-existing talent_intelligence.db
   ```

2. **Discover key companies** (30 min each)
   ```bash
   python3 github_api_enrichment.py discover-company talent_intelligence.db uniswap-labs "Uniswap"
   python3 github_api_enrichment.py discover-company talent_intelligence.db coinbase "Coinbase"
   python3 github_api_enrichment.py discover-company talent_intelligence.db ensdomains "ENS"
   ```

3. **Query and analyze**
   - Find top contributors
   - Identify tech stacks
   - Build sourcing lists
   - Track hiring activity

4. **Keep fresh**
   - Re-run enrichment monthly to update follower counts
   - Re-discover companies quarterly to find new contributors
   - Monitor repository activity for hiring signals

---

## Troubleshooting

### "Rate limit exceeded"
- Wait for reset (check `X-RateLimit-Reset` header)
- Script will auto-pause and resume
- Use GITHUB_TOKEN for 5000/hour instead of 60/hour

### "User not found (404)"
- User deleted account or changed username
- Script skips these automatically
- Logged in enrichment_log.txt

### "Database locked"
- Close any other database connections
- SQLite only allows one writer at a time
- Use `./query_database.sh` in read-only mode

### "Out of disk space"
- Database will grow significantly with company discovery
- Estimate: ~100MB per major company (with all contributors)
- Check: `df -h /Users/charlie.kerr/Documents`

---

## Architecture Recap

**The system is designed to:**

1. **Start broad** (enrich existing 12K profiles)
2. **Go deep** (discover companies, repos, contributors)
3. **Link everything** (company → repos → people)
4. **Stay fresh** (re-run enrichment anytime)
5. **Enable queries** (find people by tech, company, influence)

**It works with our existing architecture because:**
- Uses existing `companies`, `people`, `github_profiles` tables
- Adds `company_repositories` for repo data
- Adds `github_repo_contributions` for contribution tracking
- All foreign keys properly linked
- Queryable via SQL for any analysis

🎯 **Ready to start enriching!**
