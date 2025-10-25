# GitHub-Native Intelligence System - Quick Start

## Overview

The GitHub-Native Intelligence System extracts deep insights from GitHub profiles using ONLY the GitHub public API. No LinkedIn, no external enrichment services - just GitHub.

## What It Does

Extracts 20+ intelligence points per developer:
- **Identity & Contact**: Real name, emails (from commits), location, company, timezone
- **Technical Skills**: Languages, frameworks, tools, domain expertise
- **Experience & Seniority**: Algorithmically inferred (Junior/Mid/Senior/Staff/Principal)
- **Network & Influence**: Collaborators, organizations, influence score (0-100)
- **Activity Patterns**: Commits/week, active hours, consistency, trajectory
- **Reachability**: Contact score (0-100), best contact method, outreach tips

## Quick Start

### 1. Set Up Environment

```bash
# Ensure you have a GitHub token (5000 req/hr vs 60 without)
export GITHUB_TOKEN="your_github_token_here"

# Optional: OpenAI key for AI summaries
export OPENAI_API_KEY="your_openai_key_here"
```

### 2. Run Database Migration

```bash
python3 scripts/github_intelligence/migrate_existing_data.py
```

This creates 4 new tables:
- `github_intelligence` - Main intelligence storage
- `github_collaboration` - Network relationships
- `github_market_intelligence` - Talent flows
- `github_activity_timeline` - Temporal activity

### 3. Test the Pipeline

```bash
# Test on a single well-known developer
python3 scripts/github_intelligence/test_pipeline.py
```

### 4. Run Intelligence Extraction

```bash
# Test mode (5 profiles)
python3 scripts/github_intelligence/intelligence_orchestrator.py --test

# Single developer
python3 scripts/github_intelligence/intelligence_orchestrator.py --mode single --username vitalik

# Batch of developers
python3 scripts/github_intelligence/intelligence_orchestrator.py --mode batch --usernames vitalik haydenadams gakonst

# Enrich existing profiles from database (top 100 by followers)
python3 scripts/github_intelligence/intelligence_orchestrator.py --mode existing --limit 100

# Discover + enrich high-value targets (crypto/DeFi/AI orgs)
python3 scripts/github_intelligence/intelligence_orchestrator.py --mode discover --limit 50
```

## System Architecture

```
GitHub API
    ↓
ProfileBuilder (fetch all data)
    ↓
┌──────────────────┬────────────────┬──────────────────┬────────────────────┐
│                  │                │                  │                    │
SkillExtractor  SeniorityScorer  NetworkAnalyzer  ActivityTracker  ReachabilityAssessor
│                  │                │                  │                    │
└──────────────────┴────────────────┴──────────────────┴────────────────────┘
                                    ↓
                         IntelligenceOrchestrator
                                    ↓
                          Database (github_intelligence)
```

## Core Modules

### 1. ProfileBuilder (`profile_builder.py`)
Fetches complete profile data from GitHub API:
- User profile
- All repositories
- Recent events (90 days)
- Organizations
- Language statistics

### 2. SkillExtractor (`skill_extractor.py`)
Extracts technical skills from code:
- Languages (from repo stats)
- Frameworks (from dependencies)
- Tools (from configs)
- Domains (from topics/descriptions)

### 3. SeniorityScorer (`seniority_scorer.py`)
Infers seniority level from behavior:
- Years active
- Output volume (commits, repos)
- Leadership signals (reviews, maintainer status)
- Influence (stars, followers)

Scoring: 0-30 = Junior, 30-60 = Mid, 60-90 = Senior, 90-120 = Staff, 120+ = Principal

### 4. NetworkAnalyzer (`network_analyzer.py`)
Maps collaboration networks:
- Shared repo contributors
- Organization memberships
- Collaboration strength
- Influence paths

### 5. ActivityTracker (`activity_tracker.py`)
Analyzes temporal patterns:
- Commits/week, PRs/month
- Active hours and days
- Consistency score (0-1)
- Trend (Growing/Stable/Declining)

### 6. ReachabilityAssessor (`reachability_assessor.py`)
Scores how reachable they are:
- Contact info availability (email, Twitter, website)
- Recent activity signals
- Bio signals
- Best contact method

### 7. DeveloperDiscovery (`discovery.py`)
Finds new developers to enrich:
- From GitHub organizations (Uniswap, Coinbase, OpenAI, etc.)
- From repository contributors
- Priority scoring

### 8. IntelligenceOrchestrator (`intelligence_orchestrator.py`)
Coordinates the entire pipeline:
- Runs all extraction modules
- Stores results in database
- Handles rate limiting
- Progress tracking

## Database Schema

### github_intelligence Table

```sql
CREATE TABLE github_intelligence (
    github_profile_id UUID PRIMARY KEY,
    
    -- Identity
    extracted_emails TEXT[],
    inferred_location_city VARCHAR(100),
    current_employer VARCHAR(255),
    
    -- Skills
    primary_languages JSONB,
    frameworks JSONB,
    tools JSONB,
    domains JSONB,
    
    -- Seniority
    years_active FLOAT,
    inferred_seniority VARCHAR(50),
    seniority_confidence FLOAT,
    
    -- Network
    top_collaborators JSONB,
    organization_memberships JSONB,
    influence_score INT,
    
    -- Activity
    commits_per_week FLOAT,
    activity_trend VARCHAR(50),
    consistency_score FLOAT,
    
    -- Reachability
    reachability_score INT,
    best_contact_method VARCHAR(50),
    
    -- AI (future)
    ai_generated_summary TEXT
);
```

## Rate Limiting

- **With token**: 5000 requests/hour
- **Without token**: 60 requests/hour
- **Auto-throttling**: 0.72s between requests
- **Graceful handling**: Waits for rate limit reset

The system tracks rate limits and prevents hitting caps.

## Performance

- **~50-100 profiles/hour** (with rate limiting)
- **~10-15 API calls per profile** (depending on repo count)
- **Sub-second database storage** per profile

To enrich 100K profiles: ~1000-2000 hours of API time (distribute across days/weeks or use multiple tokens)

## Example Output

```
🚀 Enriching: @vitalik

   ✅ Found: Vitalik Buterin
   📦 Fetching repositories... Found 45 repos
   📊 Fetching recent activity... Found 87 events
   🏢 Fetching organizations... Member of 12 organizations
   💻 Analyzing languages... 5 languages used
   ⚡ Analyzing activity patterns...
   🕸️ Analyzing network... Found 234 collaborators
   📞 Assessing reachability...

   ✅ Intelligence extraction complete

      Specialization: Solidity/Python Developer
      Seniority: Principal (confidence: 95%)
      Network: 234 collaborators, influence: 98/100
      Activity: Very High, Growing trend
      Reachability: 95/100 (Email available)

   ✅ Stored intelligence in database
```

## Query Examples

```sql
-- Find all Senior+ Solidity developers
SELECT 
    gp.github_username,
    gi.inferred_seniority,
    gi.primary_languages->>'Solidity' as solidity_experience,
    gi.reachability_score
FROM github_intelligence gi
JOIN github_profile gp ON gi.github_profile_id = gp.github_profile_id
WHERE gi.inferred_seniority IN ('Senior', 'Staff', 'Principal')
AND gi.primary_languages ? 'Solidity'
ORDER BY gi.influence_score DESC
LIMIT 20;

-- Find developers in DeFi domain
SELECT 
    gp.github_username,
    gi.domains,
    gi.influence_score
FROM github_intelligence gi
JOIN github_profile gp ON gi.github_profile_id = gp.github_profile_id
WHERE gi.domains::text LIKE '%DeFi%'
ORDER BY gi.influence_score DESC;

-- Find highly reachable developers
SELECT 
    gp.github_username,
    gi.reachability_score,
    gi.best_contact_method,
    gi.extracted_emails
FROM github_intelligence gi
JOIN github_profile gp ON gi.github_profile_id = gp.github_profile_id
WHERE gi.reachability_score >= 80
ORDER BY gi.influence_score DESC;
```

## Next Steps

1. **Phase 3**: AI enrichment layer (generate human-readable summaries)
2. **Phase 4**: Bloomberg Terminal-style UI
3. **Phase 5**: API endpoints for frontend
4. **Phase 6**: Market intelligence (talent flows, hiring signals)

## Troubleshooting

### "No GitHub token found"
Set `GITHUB_TOKEN` environment variable with a personal access token

### "Rate limit hit"
The system will automatically wait. With token, you get 5000 req/hr.

### "Profile not found"
The username doesn't exist on GitHub or has no public data

### "Database connection error"
Ensure PostgreSQL is running and connection pool is configured in `config.py`

## Files Structure

```
scripts/github_intelligence/
├── github_client.py              # Rate-limited API client
├── profile_builder.py            # Fetch profile data
├── skill_extractor.py            # Extract skills
├── seniority_scorer.py           # Infer seniority
├── network_analyzer.py           # Map collaborations
├── activity_tracker.py           # Activity patterns
├── reachability_assessor.py      # Contact scoring
├── discovery.py                  # Find new developers
├── intelligence_orchestrator.py  # Main coordinator
├── migrate_existing_data.py      # Database setup
└── test_pipeline.py              # Quick test
```

## Credits

Built for the Talent Intelligence platform as proof-of-concept that GitHub-only intelligence can compete with multi-source enrichment.

