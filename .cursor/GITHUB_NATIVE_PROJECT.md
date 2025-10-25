# GitHub-Native Intelligence Platform

## Project Context
This branch (github-native-intelligence) is building a **GitHub-only** version 
of the talent intelligence platform focused on crypto/open source developers.

## Key Differences from Main Branch

### Main Branch (talent-intelligence-complete)
- Multi-source: LinkedIn + GitHub + emails
- 155K profiles from various sources
- Broad recruiting focus

### This Branch (github-native-intelligence)  
- **GitHub-only**: No LinkedIn scraping, no external enrichment other than GitHub API
- Deep technical intelligence from GitHub API alone
- "Bloomberg Terminal for open source developers"
- Focus: Crypto, DeFi, Web3, open source projects, big name companies, fast moving AI startups, top silicon valley companies, top silicon valley schools and hackathon winners, dev puzzle solvers

## What We're Building

A specialized platform that uses ONLY GitHub's public API to:
1. Discover developers via company orgs and repo contributors
2. Build comprehensive profiles from GitHub data alone
3. Extract skills, seniority, network, and specialization
4. Provide market intelligence (talent flows, hiring signals)
5. Bloomberg Terminal-style dashboards

## What We're Keeping from Main

### Database Schema ✅
- Keep core tables: person, employment, github_profile, github_contribution, etc
- These tables already exist and have good data
- We'll USE this existing data as a foundation

### GitHub Enrichment Infrastructure ✅
- Keep: scripts/github/enrich_github_continuous.py
- Keep: github_automation/ package
- Keep: All GitHub-related code

### API Infrastructure ✅
- Keep: FastAPI backend structure
- Keep: api/routers/, api/services/, api/crud/
- Keep: PostgreSQL database

### Frontend ✅
- Keep: React + TypeScript setup
- We'll BUILD NEW dashboards but use same tech stack

## What We're NOT Using

### LinkedIn/External Enrichment ❌
- Ignore: Any LinkedIn scraping code
- Ignore: Apollo.io integration suggestions
- Ignore: Clay enrichment workflows

### Multi-Source Complexity ❌
- Focus ONLY on GitHub as data source
- Simplify the pipeline

## Development Guidelines

### When Adding Features
1. Check if similar functionality exists in main codebase
2. Reuse database tables and API patterns
3. Only use GitHub API - no other data sources
4. Build Bloomberg Terminal-style UIs

### When Asked About Data Sources
- "We only use GitHub API"
- "No LinkedIn, no Apollo, no scraping"
- "We extract maximum intelligence from GitHub alone"

### When Refactoring
- Keep changes isolated to this branch
- Don't break main branch functionality
- Document GitHub-specific logic clearly

## File Organization for This Branch
```
talent-intelligence-complete/
├── api/                          # KEEP - reuse API structure
│   ├── routers/
│   │   ├── github_intelligence.py  # NEW - GitHub-only endpoints
│   │   └── ...existing...
│   └── services/
│       ├── github_intelligence/    # NEW - Deep GitHub analysis
│       │   ├── ai_profile_analyzer.py
│       │   ├── ai_specialization_detector.py
│       │   ├── ai_trajectory_analyzer.py
│       │   └── ai_outreach_generator.py
│       └── ...existing...
│
├── scripts/
│   └── github_intelligence/      # NEW - GitHub-native discovery
│       ├── discovery.py
│       ├── profile_builder.py
│       ├── skill_extractor.py
│       ├── seniority_scorer.py
│       ├── network_analyzer.py
│       ├── activity_tracker.py
│       ├── reachability_assessor.py
│       └── intelligence_orchestrator.py
│
├── frontend/
│   └── src/
│       ├── pages/
│       │   └── github_native/           # NEW - GitHub-native pages
│       │       ├── GitHubDeveloperProfile.tsx
│       │       ├── GitHubCompanyIntel.tsx
│       │       ├── GitHubMarketDashboard.tsx
│       │       ├── GitHubNetworkGraph.tsx
│       │       └── GitHubSearch.tsx
│       └── components/
│           └── github_native/           # NEW - Reusable components
│               ├── ProfileCard.tsx
│               ├── SkillsVisualization.tsx
│               ├── ActivityHeatmap.tsx
│               ├── NetworkGraph.tsx
│               ├── ReachabilityBadge.tsx
│               ├── SeniorityBadge.tsx
│               └── TrendChart.tsx
│
└── docs/
    └── github_native/            # NEW - GitHub-specific docs
        ├── VISION.md
        ├── ARCHITECTURE.md
        └── API.md
```

## Success Metrics

- Extract 20+ data points per developer from GitHub alone
- Build profiles as rich as main branch (without LinkedIn)
- Prove GitHub-only can compete with multi-source platforms
- "Bloomberg Terminal" quality dashboards

## Questions to Ask

When uncertain:
- "Does this feature require data beyond GitHub?" (If yes, skip it)
- "Can this be extracted from GitHub API?" (Check docs first)
- "Does similar logic exist in main branch we can adapt?"

## Data We Can Extract from GitHub API Alone

### Identity & Contact
- Real name (from profile)
- Location (city/country from profile field)
- Timezone (inferred from commit timestamps)
- Email addresses (from profile + commit metadata)
- Twitter handle (from profile)
- Personal website (from profile)
- Current employer (from company field)

### Technical Skills
- Programming languages (from repo language statistics)
- Frameworks (detected from dependency files)
- Tools (Docker, CI/CD from repo configs)
- Domains (DeFi, NFTs, etc. from repo topics)

### Experience & Seniority
- Years active (first commit to present)
- Total commits across all repos
- Repos maintained (owner status)
- Major project contributions
- PR review behavior (leadership signal)
- Inferred seniority level

### Network & Collaboration
- Organizations (member of)
- Collaborators (shared repo contributors)
- Code reviewers (who reviews their PRs)
- Influence score (followers, stars, etc.)

### Activity & Trajectory
- Commits per week/month
- PR frequency
- Active hours and days
- Activity trend (growing/stable/declining)
- Consistency score

### Reachability
- Contact information availability
- Recent activity (responsive signal)
- Bio signals (open to opportunities)
- Best contact method

All of this from GitHub's free public API!

