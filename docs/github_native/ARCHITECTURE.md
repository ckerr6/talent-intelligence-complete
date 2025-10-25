# GitHub-Native Intelligence Platform - Architecture

## System Overview

This platform extracts deep technical intelligence from GitHub's public API alone,
without any LinkedIn scraping, Apollo.io enrichment, or other external data sources.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  Bloomberg Terminal-style Dashboards & Visualizations   │
└────────────────────┬────────────────────────────────────┘
                     │ REST API
┌────────────────────┴────────────────────────────────────┐
│                  FastAPI Backend                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  GitHub Intelligence Router                       │  │
│  │  /api/github-intelligence/*                       │  │
│  └──────────────────┬───────────────────────────────┘  │
│                     │                                    │
│  ┌──────────────────┴───────────────────────────────┐  │
│  │  AI Services                                      │  │
│  │  - Profile Analyzer                               │  │
│  │  - Specialization Detector                        │  │
│  │  - Trajectory Analyzer                            │  │
│  │  - Outreach Generator                             │  │
│  └──────────────────┬───────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│              PostgreSQL Database                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Existing Tables (from main branch):             │  │
│  │  - person                                         │  │
│  │  - github_profile                                 │  │
│  │  - github_contribution                            │  │
│  │  - github_pull_request                            │  │
│  │  - repository                                     │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  New Tables (this branch):                       │  │
│  │  - github_intelligence                            │  │
│  │  - github_collaboration                           │  │
│  │  - github_market_intelligence                     │  │
│  │  - github_activity_timeline                       │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│        Intelligence Extraction Scripts                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  intelligence_orchestrator.py (main entry point) │  │
│  │  ├── discovery.py                                │  │
│  │  ├── profile_builder.py                          │  │
│  │  ├── skill_extractor.py                          │  │
│  │  ├── seniority_scorer.py                         │  │
│  │  ├── network_analyzer.py                         │  │
│  │  ├── activity_tracker.py                         │  │
│  │  └── reachability_assessor.py                    │  │
│  └──────────────────┬───────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Rate-limited API calls
                     │ (5000 req/hr with token)
                     │
┌────────────────────┴────────────────────────────────────┐
│                   GitHub API                             │
│  - User profiles                                         │
│  - Repositories & languages                              │
│  - Commits, PRs, reviews                                 │
│  - Events, organizations                                 │
│  - Followers, following                                  │
└──────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Discovery Phase
```
GitHub Orgs/Repos → discovery.py → New GitHub usernames
                                 ↓
                         Store in queue for enrichment
```

### 2. Enrichment Phase
```
GitHub Username → profile_builder.py → Fetch all data from GitHub API
                                    ↓
                  ┌─────────────────┴─────────────────┐
                  │                                   │
    skill_extractor.py                    network_analyzer.py
    seniority_scorer.py                   activity_tracker.py
    reachability_assessor.py
                  │                                   │
                  └─────────────────┬─────────────────┘
                                    ↓
                    Store in github_intelligence table
```

### 3. AI Enrichment Phase
```
Raw GitHub Intelligence → ai_profile_analyzer.py → Human-readable summary
                                                 ↓
                              Update github_intelligence.ai_generated_summary
```

### 4. Query Phase
```
Frontend Request → API Router → Database Query → Format & Return
                                               ↓
                                  Cache in Redis (optional)
```

## Database Schema (New Tables)

### `github_intelligence`
Primary table storing all extracted intelligence for each GitHub profile.

**Key Design Decisions:**
- One row per github_profile_id
- Heavy use of JSONB for flexible, denormalized data
- All data extracted from GitHub API alone
- AI-generated fields for human-readable summaries

**Columns:**
```sql
CREATE TABLE github_intelligence (
    github_profile_id UUID PRIMARY KEY REFERENCES github_profile(github_profile_id),
    
    -- Identity & Contact (extracted from GitHub)
    extracted_emails TEXT[],
    inferred_timezone VARCHAR(50),
    inferred_location_city VARCHAR(100),
    inferred_location_country VARCHAR(100),
    current_employer VARCHAR(255),
    
    -- Technical Skills (analyzed from repos/commits)
    primary_languages JSONB,  -- {language: lines_of_code}
    frameworks JSONB,          -- [framework1, framework2, ...]
    tools JSONB,
    domains JSONB,             -- [DeFi, NFT, L2, ...]
    
    -- Experience & Seniority
    years_active FLOAT,
    total_commits INT,
    repos_maintained INT,
    major_project_contributions INT,
    inferred_seniority VARCHAR(50),  -- Junior, Mid, Senior, Staff, Principal
    seniority_confidence FLOAT,      -- 0.0 to 1.0
    
    -- Collaboration & Network
    top_collaborators JSONB,  -- [{username, collaboration_strength, shared_repos}, ...]
    organization_memberships JSONB,  -- [org1, org2, ...]
    influence_score INT,      -- 0-100
    
    -- Specialization
    technical_specialization JSONB,  -- [Smart Contracts, Frontend, ...]
    domain_specialization JSONB,     -- [DeFi, Gaming, ...]
    focus_areas JSONB,               -- [Security, Performance, ...]
    
    -- Activity & Trajectory
    commits_per_week FLOAT,
    prs_per_month FLOAT,
    activity_trend VARCHAR(50),  -- Growing, Stable, Declining
    last_active_date TIMESTAMP,
    consistency_score FLOAT,     -- 0.0 to 1.0
    
    -- Reachability
    reachability_score INT,  -- 0-100
    reachability_signals JSONB,  -- [{signal, weight}, ...]
    best_contact_method VARCHAR(50),
    
    -- AI Analysis
    ai_generated_summary TEXT,
    ideal_role_fit TEXT,
    ai_analyzed_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_github_intelligence_seniority ON github_intelligence(inferred_seniority);
CREATE INDEX idx_github_intelligence_reachability ON github_intelligence(reachability_score);
CREATE INDEX idx_github_intelligence_active ON github_intelligence(last_active_date);
CREATE INDEX idx_github_intelligence_influence ON github_intelligence(influence_score);
```

### `github_collaboration`
Track collaboration relationships between developers.

```sql
CREATE TABLE github_collaboration (
    collaboration_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    github_profile_id UUID REFERENCES github_profile(github_profile_id),
    collaborator_profile_id UUID REFERENCES github_profile(github_profile_id),
    
    shared_repos TEXT[],
    collaboration_strength INT,  -- Number of interactions
    relationship_type VARCHAR(50),  -- coworker, reviewer, contributor
    
    reviews_given INT DEFAULT 0,
    reviews_received INT DEFAULT 0,
    shared_organizations TEXT[],
    
    first_interaction TIMESTAMP,
    last_interaction TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(github_profile_id, collaborator_profile_id)
);

CREATE INDEX idx_collaboration_profile ON github_collaboration(github_profile_id);
CREATE INDEX idx_collaboration_strength ON github_collaboration(collaboration_strength);
```

### `github_market_intelligence`
Track talent flows and hiring signals over time.

```sql
CREATE TABLE github_market_intelligence (
    market_intel_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    organization_name VARCHAR(255),
    snapshot_date DATE,
    
    -- Team metrics
    total_contributors INT,
    active_contributors_90d INT,
    core_team_size INT,
    
    -- Language distribution
    language_distribution JSONB,  -- {language: contributor_count}
    
    -- Skill distribution
    skill_distribution JSONB,  -- {skill: count}
    
    -- Talent flow
    new_contributors_30d INT,
    departed_contributors_30d INT,
    departed_to JSONB,  -- [{company, count}, ...]
    
    -- Hiring signals
    hiring_trend VARCHAR(50),  -- Growing, Stable, Declining
    growth_rate FLOAT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(organization_name, snapshot_date)
);

CREATE INDEX idx_market_intel_org ON github_market_intelligence(organization_name);
CREATE INDEX idx_market_intel_date ON github_market_intelligence(snapshot_date);
```

### `github_activity_timeline`
Time-series data for tracking activity trends.

```sql
CREATE TABLE github_activity_timeline (
    timeline_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    github_profile_id UUID REFERENCES github_profile(github_profile_id),
    
    week_start DATE,
    
    commits_count INT,
    prs_opened INT,
    prs_merged INT,
    issues_opened INT,
    reviews_given INT,
    
    active_days INT,  -- Days active this week
    active_hours JSONB,  -- [hour1, hour2, ...] when they were active
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(github_profile_id, week_start)
);

CREATE INDEX idx_activity_timeline_profile ON github_activity_timeline(github_profile_id);
CREATE INDEX idx_activity_timeline_date ON github_activity_timeline(week_start);
```

## Intelligence Extraction Pipeline

### Discovery (`discovery.py`)
**Purpose:** Find new GitHub developers to analyze

**Sources:**
1. GitHub organization members
2. Repository contributors (especially high-value repos)
3. Collaborators of known developers

**Output:** Queue of GitHub usernames to enrich

### Profile Building (`profile_builder.py`)
**Purpose:** Fetch all available data for a GitHub user

**GitHub API Calls:**
- `GET /users/{username}` - Basic profile
- `GET /users/{username}/repos` - All repositories
- `GET /users/{username}/events` - Recent activity
- `GET /users/{username}/orgs` - Organizations
- `GET /repos/{repo}/commits?author={username}` - Commits per repo
- `GET /repos/{repo}/pulls?creator={username}` - Pull requests
- `GET /repos/{repo}/languages` - Language statistics

**Output:** Comprehensive raw data object

### Skill Extraction (`skill_extractor.py`)
**Purpose:** Determine technical skills from code

**Process:**
1. Aggregate language statistics across all repos
2. Parse dependency files (package.json, requirements.txt, etc.)
3. Detect frameworks (React, Hardhat, OpenZeppelin, etc.)
4. Identify tools (Docker, CI/CD configs)
5. Infer domains from repo topics and descriptions

**Output:** Skills object with languages, frameworks, tools, domains

### Seniority Scoring (`seniority_scorer.py`)
**Purpose:** Infer seniority level from behavior patterns

**Signals:**
- Years active (account age + activity span)
- Output volume (commits, PRs, repos)
- Leadership (PR reviews, maintainer status)
- Influence (stars, followers, org memberships)

**Scoring Algorithm:**
```python
score = (
    min(years_active * 10, 50) +
    min(total_commits / 100, 20) +
    pr_review_count * 2 +
    repos_maintained * 3 +
    min(stars_earned / 100, 15) +
    organization_memberships * 5
)

# Classification
if score < 30: Junior
elif score < 60: Mid-Level
elif score < 90: Senior
elif score < 120: Staff
else: Principal
```

**Output:** Seniority level + confidence score

### Network Analysis (`network_analyzer.py`)
**Purpose:** Map collaboration relationships

**Process:**
1. Find all repos user contributed to
2. Identify other contributors to those repos
3. Count shared repos and interactions
4. Track PR review relationships
5. Calculate influence score

**Output:** Network object with collaborators and influence metrics

### Activity Tracking (`activity_tracker.py`)
**Purpose:** Analyze activity patterns and trajectory

**Metrics:**
- Commits per week/month
- Active hours and days
- Consistency score
- Trend analysis (growing/stable/declining)

**Output:** Activity metrics and trajectory classification

### Reachability Assessment (`reachability_assessor.py`)
**Purpose:** Score how easy it is to reach this person

**Signals:**
- Public email (profile or commits)
- Twitter handle
- Personal website
- Recent activity
- Bio signals ("open to opportunities")

**Scoring:**
- Public email: +30
- Twitter: +20
- Website: +15
- Active (90d): +20
- Bio signals: +15

**Output:** Reachability score (0-100) + best contact method

## API Endpoints

### `POST /api/github-intelligence/analyze/{username}`
Trigger deep analysis of a GitHub user (if not already analyzed).

### `GET /api/github-intelligence/profile/{username}`
Get enriched profile with all intelligence data.

### `GET /api/github-intelligence/company/{org}`
Get company intelligence (team composition, skills, trends).

### `GET /api/github-intelligence/market-trends`
Get market intelligence (talent flows, hiring signals, skill trends).

### `POST /api/github-intelligence/search`
Advanced search with filters (skills, seniority, location, etc.).

## AI Services

### Profile Analyzer
**Input:** All extracted GitHub intelligence
**Process:** Generate human-readable summary using GPT-4o-mini
**Output:** Executive summary, strengths, ideal role fit

### Specialization Detector
**Input:** Repos, commits, PRs
**Process:** Analyze patterns and identify specific focus
**Output:** Specialization description (e.g., "Security-focused DeFi engineer")

### Trajectory Analyzer
**Input:** Activity timeline, skill evolution
**Process:** Identify growth patterns and predict trajectory
**Output:** Career trajectory classification and predictions

### Outreach Generator
**Input:** Complete profile + job context
**Process:** Generate personalized outreach message
**Output:** Customized message referencing specific work

## Rate Limiting

GitHub API limits: 5000 requests/hour with token

**Strategy:**
- Track requests per hour
- Implement 0.72s delay between requests
- Priority queue (high-value profiles first)
- Batch processing with checkpoints
- Graceful degradation on rate limit hit

## Performance Considerations

### Database
- Heavy use of JSONB for flexibility
- Indexes on commonly queried fields
- Connection pooling (existing infrastructure)

### Caching
- Redis cache for expensive queries (existing infrastructure)
- Cache enriched profiles for 24 hours
- Cache company intelligence for 1 hour

### API
- Async/await for I/O operations
- Pagination for large result sets
- Background jobs for slow enrichment

## Testing Strategy

### Unit Tests
- Test each extraction module independently
- Mock GitHub API responses
- Validate scoring algorithms

### Integration Tests
- Test end-to-end pipeline on real data
- Validate database operations
- Test API endpoints

### Performance Tests
- Measure extraction rate (profiles/hour)
- Test API response times
- Validate rate limiting

## Deployment

This branch shares infrastructure with main:
- Same PostgreSQL database (new tables)
- Same FastAPI backend (new routers)
- Same React frontend (new pages)
- Same deployment process

Can be merged to main or kept as separate branch.

