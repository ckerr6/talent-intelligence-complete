# AI-Powered GitHub Discovery System

**Status**: Phase 1-4 Complete | In Active Development
**Created**: October 24, 2025
**Last Updated**: October 24, 2025

---

## 🎯 Overview

The AI-Powered GitHub Discovery System is an intelligent framework that automatically discovers, enriches, and organizes GitHub repositories, developers, and companies within the crypto/blockchain ecosystem. It starts from high-priority sources (like Electric Capital's taxonomy, Ethereum EIPs, Paradigm ecosystem) and expands outward through network analysis.

### Key Capabilities

- **Intelligent Discovery**: Automatically finds relevant repos, developers, and companies
- **Rich Metadata**: Stores comprehensive information with full lineage tracking
- **Ecosystem Organization**: Taxonomizes entities into crypto ecosystems
- **Priority Scoring**: Ranks entities by importance and relevance
- **Network Analysis**: Maps relationships and "orbits" between developers
- **AI-Powered Relevance**: Uses LLMs to score relevance and extract insights
- **Continuous Monitoring**: Automatically discovers new contributors and repos

---

## 📊 Database Schema

### New Tables

#### `discovery_source`
Tracks where entities came from.

| Column | Type | Description |
|--------|------|-------------|
| `source_id` | UUID (PK) | Unique identifier |
| `source_type` | ENUM | Type: electric_capital_taxonomy, ethereum_eip, paradigm_ecosystem, contributor_expansion, ai_discovery |
| `source_name` | TEXT | Human-readable name |
| `source_url` | TEXT | Source URL if applicable |
| `priority_tier` | INT | 1=highest priority, 5=lowest |
| `metadata` | JSONB | Additional context |
| `created_at`, `updated_at` | TIMESTAMP | Tracking |

**Usage**: Every entity (repo, person, company) references a discovery source to track provenance.

#### `entity_discovery`
Tracks individual discovery events with lineage.

| Column | Type | Description |
|--------|------|-------------|
| `discovery_id` | UUID (PK) | Unique identifier |
| `entity_type` | ENUM | person, repository, company |
| `entity_id` | UUID | FK to actual entity |
| `source_id` | UUID | FK to discovery_source |
| `discovered_via_id` | UUID | Parent entity that led to discovery |
| `discovery_method` | TEXT | taxonomy_import, contributor_scrape, orbit_expansion, etc. |
| `discovery_metadata` | JSONB | Context about discovery |
| `discovered_at` | TIMESTAMP | When discovered |

**Usage**: Full audit trail of how every entity was discovered. E.g., "Person X was discovered via Repository Y using method 'contributor_scrape'".

#### `repository_relationship`
Tracks connections between repositories.

| Column | Type | Description |
|--------|------|-------------|
| `relationship_id` | UUID (PK) | Unique identifier |
| `repo_id_from` | UUID | FK to github_repository |
| `repo_id_to` | UUID | FK to github_repository |
| `relationship_type` | ENUM | fork, dependency, same_ecosystem, contributor_overlap, org_sibling |
| `strength_score` | FLOAT (0-1) | Relationship strength |
| `metadata` | JSONB | Additional context |

**Usage**: Map repository networks for discovery and recommendations.

#### `crypto_ecosystem`
Organizes entities into crypto ecosystems.

| Column | Type | Description |
|--------|------|-------------|
| `ecosystem_id` | UUID (PK) | Unique identifier |
| `ecosystem_name` | TEXT | "Ethereum", "Uniswap", etc. |
| `normalized_name` | TEXT | Lowercase for matching |
| `parent_ecosystem_id` | UUID | For nested ecosystems |
| `description` | TEXT | What it is |
| `official_repos` | TEXT[] | Array of repo full_names |
| `taxonomy_source` | TEXT | Where it came from |
| `priority_score` | INT (1-5) | Importance ranking |
| `tags` | TEXT[] | Classification tags |
| `metadata` | JSONB | Extra data |
| `repo_count`, `developer_count`, `total_stars` | INT | Computed stats |

**Usage**: Organize everything by ecosystem. E.g., all Ethereum repos, developers, and companies.

### Enhanced Existing Tables

#### `github_repository` - New Columns
- `ecosystem_ids` (UUID[]): Multiple ecosystems this repo belongs to
- `importance_score` (FLOAT): Computed score (0-100)
- `last_contributor_sync` (TIMESTAMP): When contributors were last synced
- `contributor_count` (INT): Cached count
- `discovery_source_id` (UUID): Where we found this repo

#### `github_profile` - New Columns
- `ecosystem_tags` (TEXT[]): ["ethereum", "defi", "eip-author", "paradigm-ecosystem"]
- `importance_score` (FLOAT): Computed score (0-100)
- `discovery_source_id` (UUID): Where we found this person
- `orbit_of` (UUID[]): Notable devs this person is in orbit of
- `specialties` (TEXT[]): AI-detected specialties

#### `company` - New Columns
- `ecosystem_tags` (TEXT[]): Ecosystems company is part of
- `discovery_source_id` (UUID): Where we found this company

#### `github_contribution` - New Column
- `contribution_type` (ENUM): owner, contributor, core_team, occasional

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Data Sources                               │
├─────────────────────────────────────────────────────────────┤
│  • Electric Capital Taxonomy                                 │
│  • Ethereum EIPs Repository                                  │
│  • Paradigm Ecosystem (paradigmxyz/*)                        │
│  • Notable Developers (gakonst, etc.)                        │
│  • GitHub API                                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                Import & Discovery Layer                      │
├─────────────────────────────────────────────────────────────┤
│  1. Taxonomy Parser        → Ecosystems & Repos              │
│  2. Priority Importer      → Specific High-Value Repos       │
│  3. Contributor Discovery  → Developers from Repos           │
│  4. Orbit Discovery        → Developer Networks              │
│  5. Continuous Monitoring  → New Activity                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 Enrichment & AI Layer                        │
├─────────────────────────────────────────────────────────────┤
│  • Profile Enrichment      → Bio, location, company          │
│  • Contribution Analysis   → PRs, lines of code              │
│  • AI Relevance Scoring    → LLM-based relevance             │
│  • Importance Calculation  → Algorithmic scoring             │
│  • Network Analysis        → Relationship strength           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layer                             │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL Database with:                                   │
│  • Discovery lineage tracking                                │
│  • Ecosystem organization                                    │
│  • Importance scores                                         │
│  • Network relationships                                     │
│  • Full audit trail                                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   API & Frontend                             │
├─────────────────────────────────────────────────────────────┤
│  • Discovery API endpoints                                   │
│  • Ecosystem browsers                                        │
│  • Network visualizations                                    │
│  • Priority dashboards                                       │
│  • AI insights display                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Scripts & Tools

### Phase 1: Database Setup
**File**: `migration_scripts/09_ai_discovery_schema.sql`

Creates all new tables, adds columns to existing tables, creates indexes, and sets up helper functions.

**Run**:
```bash
psql -d talent -f migration_scripts/09_ai_discovery_schema.sql
```

### Phase 2: Electric Capital Taxonomy Parser
**File**: `scripts/github/parse_electric_capital_taxonomy.py`

Downloads and parses the Electric Capital crypto-ecosystems taxonomy to populate ecosystems and repositories.

**Usage**:
```bash
# Download taxonomy
python3 scripts/github/parse_electric_capital_taxonomy.py --download --output exports.jsonl

# Parse taxonomy
python3 scripts/github/parse_electric_capital_taxonomy.py --parse exports.jsonl

# Full workflow (download + parse)
python3 scripts/github/parse_electric_capital_taxonomy.py --full

# Only priority ecosystems (tier 1-2)
python3 scripts/github/parse_electric_capital_taxonomy.py --full --priority-only
```

**Output**: ~1000+ ecosystems, ~50k+ repositories with ecosystem tagging

### Phase 3: Priority Repository Importer
**File**: `scripts/github/import_priority_repositories.py`

Imports specific high-priority repositories:
- `electric-capital/crypto-ecosystems`
- `ethereum/EIPs`, `ethereum/ERCs`
- All `paradigmxyz/*` repos
- All `foundry-rs/*`, `alloy-rs/*` repos
- `gakonst` personal repos

**Usage**:
```bash
# Import all priority repos
python3 scripts/github/import_priority_repositories.py

# Import specific repos
python3 scripts/github/import_priority_repositories.py --repos ethereum/EIPs paradigmxyz/reth

# Dry run
python3 scripts/github/import_priority_repositories.py --dry-run
```

**Output**: Repositories with full metadata, linked to ecosystems, tracked discovery source

### Phase 4: Contributor Discovery Engine
**File**: `scripts/github/discover_contributors.py`

Discovers and enriches all contributors to priority repositories.

**Features**:
- Fetches contributors via GitHub API
- Enriches profiles with full metadata
- Tags with ecosystem tags (ethereum, eip-author, paradigm-ecosystem, etc.)
- Creates contribution records
- Tracks discovery lineage

**Usage**:
```bash
# Discover contributors for tier 1 repos
python3 scripts/github/discover_contributors.py --priority-tier 1

# Discover for specific repos
python3 scripts/github/discover_contributors.py --repos ethereum/EIPs paradigmxyz/reth

# Limit number of repos
python3 scripts/github/discover_contributors.py --priority-tier 1 --limit 10

# Dry run
python3 scripts/github/discover_contributors.py --repos ethereum/EIPs --dry-run
```

**Output**: Thousands of enriched GitHub profiles with ecosystem tags and contribution records

---

## 📈 Priority System

### Priority Tiers

**Tier 1 (Highest Priority)**:
- Ethereum ecosystem
- Base, Optimism, Arbitrum (major L2s)
- Uniswap
- Paradigm ecosystem
- ethereum/EIPs

**Tier 2 (High Priority)**:
- Polygon, Avalanche, Solana, NEAR, Sui, Aptos
- Cosmos, Polkadot
- Major DeFi protocols: Aave, Compound, Maker, Curve, Balancer, Yearn
- Infrastructure: Chainlink, The Graph
- Exchanges: Coinbase, Circle, Binance

**Tier 3-5 (Standard to Low Priority)**:
- Other ecosystems from Electric Capital taxonomy
- Smaller projects
- Emerging ecosystems

### Priority Logic

Repositories and developers are prioritized by:
1. **Ecosystem Priority**: Tier 1 ecosystems → process first
2. **Repository Stars**: More stars → higher priority
3. **Activity**: Recently active → higher priority
4. **Network Position**: Central to network → higher priority
5. **Contribution Quality**: More merged PRs, more code → higher priority

---

## 🎯 Ecosystem Tagging

Developers are automatically tagged with ecosystems based on:

1. **Repository Membership**: Contributed to repos in that ecosystem
2. **Organization Membership**: Part of GitHub orgs (e.g., paradigmxyz)
3. **Special Roles**: 
   - `eip-author`: Contributed to ethereum/EIPs
   - `paradigm-ecosystem`: Contributed to Paradigm repos
   - `defi`: Contributed to DeFi protocols
   - `ethereum`, `uniswap`, `solana`, etc.: Ecosystem-specific

### Example Tags

```json
{
  "github_username": "gakonst",
  "ecosystem_tags": [
    "ethereum",
    "paradigm-ecosystem",
    "eip-author",
    "defi"
  ]
}
```

---

## 🔍 Discovery Methods

### 1. Taxonomy Import
**Method**: `taxonomy_import`
**Source**: Electric Capital crypto-ecosystems repository
**Output**: Ecosystems, repositories, initial organization

### 2. Manual Import
**Method**: `manual_import`
**Source**: User-specified priority repos
**Output**: High-value repositories with full metadata

### 3. Contributor Scrape
**Method**: `contributor_scrape`
**Source**: GitHub API `/repos/{owner}/{repo}/contributors`
**Output**: Developers who contribute to repos
**Lineage**: Person discovered via Repository

### 4. Orbit Discovery
**Method**: `orbit_expansion`
**Source**: GitHub social graph, co-contributions
**Output**: Developers in the "orbit" of notable developers
**Lineage**: Person discovered via Person

### 5. AI Discovery
**Method**: `ai_discovery`
**Source**: LLM analysis of repos, bios, contributions
**Output**: Relevance-scored entities with reasoning

---

## 📊 Importance Scoring

### Repository Importance (0-100)

```python
score = 0

# Stars (max 50 points)
score += min(stars / 100, 50)

# Forks (max 20 points)
score += min(forks / 50, 20)

# Contributors (max 20 points)
score += min(contributor_count / 10, 20)

# Ecosystem membership (10 points)
if has_ecosystems:
    score += 10

# Recent activity (max 10 points)
if pushed_within_90_days:
    score += 10 * (1 - days_since_push / 90)

return min(score, 100)
```

### Developer Importance (0-100)

```python
score = 0

# Followers (max 20 points)
score += min(followers / 50, 20)

# Merged PRs (max 30 points)
score += min(merged_prs / 10, 30)

# Lines of code (max 20 points)
score += min(total_lines / 5000, 20)

# Repo contributions (max 15 points)
score += min(repo_count / 5, 15)

# Ecosystem tags (5 points per ecosystem, max 15)
score += min(len(ecosystem_tags) * 5, 15)

# Orbit connections (5 points)
if in_orbit_of_notable_devs:
    score += 5

return min(score, 100)
```

These scores are computed by database functions and can be called anytime:

```sql
-- Compute repository importance
SELECT compute_repository_importance('repo-uuid-here');

-- Compute developer importance
SELECT compute_developer_importance('profile-uuid-here');
```

---

## 🔗 Discovery Lineage Examples

### Example 1: Developer from Repository

```
Discovery Path:
1. ethereum/EIPs → Imported manually (priority tier 1)
2. Vitalik Buterin → Discovered as contributor to ethereum/EIPs
3. Discovery Record:
   - entity_type: 'person'
   - source: 'contributor_expansion'
   - discovered_via: ethereum/EIPs repo_id
   - method: 'contributor_scrape'
   - metadata: {contributions: 247, ecosystem: 'ethereum'}
```

### Example 2: Repository from Taxonomy

```
Discovery Path:
1. Electric Capital Taxonomy → Downloaded
2. "Ethereum" ecosystem → Created from taxonomy
3. ethereum/go-ethereum → Linked to Ethereum ecosystem
4. Discovery Record:
   - entity_type: 'repository'
   - source: 'electric_capital_taxonomy'
   - method: 'taxonomy_import'
   - metadata: {ecosystem: 'Ethereum', tags: ['layer1', 'client']}
```

### Example 3: Developer from Orbit

```
Discovery Path:
1. gakonst → Known notable developer
2. Analyzed gakonst's following/followers
3. Found developer X who:
   - Follows gakonst
   - Contributes to same repos
   - Works at Paradigm
4. Discovery Record:
   - entity_type: 'person'
   - source: 'orbit_discovery'
   - discovered_via: gakonst's profile_id
   - method: 'orbit_expansion'
   - metadata: {relationship_strength: 0.85, shared_repos: 5}
```

---

## 🔧 Helper Functions

### Update Importance Scores

```sql
-- Update all repository scores
UPDATE github_repository
SET importance_score = compute_repository_importance(repo_id);

-- Update all developer scores
UPDATE github_profile
SET importance_score = compute_developer_importance(github_profile_id);
```

### Query by Ecosystem

```sql
-- Get all Ethereum developers
SELECT gp.github_username, gp.importance_score
FROM github_profile gp
WHERE 'ethereum' = ANY(gp.ecosystem_tags)
ORDER BY gp.importance_score DESC
LIMIT 100;

-- Get all repos in Uniswap ecosystem
SELECT r.full_name, r.stars, r.importance_score
FROM github_repository r
JOIN crypto_ecosystem e ON e.ecosystem_id = ANY(r.ecosystem_ids)
WHERE e.normalized_name = 'uniswap'
ORDER BY r.importance_score DESC;
```

### Track Discovery Stats

```sql
-- View discovery statistics
SELECT * FROM v_discovery_stats;

-- Top ecosystems
SELECT * FROM v_top_ecosystems LIMIT 20;

-- Top repositories
SELECT * FROM v_top_repositories LIMIT 50;

-- Top developers
SELECT * FROM v_top_developers LIMIT 100;
```

---

## 📝 Next Phases (In Development)

### Phase 5: Orbit Discovery
- Map developer networks
- Find co-contributors
- Analyze social connections
- Compute relationship strength scores

### Phase 6: AI Relevance Scoring
- LLM analysis of repos and developers
- Semantic relevance scoring
- Automatic specialty detection
- Reasoning and insights

### Phase 7: Continuous Discovery
- Daily monitoring of priority repos
- Auto-discover new contributors
- Track activity changes
- Alert on significant discoveries

### Phase 8: API Endpoints
- `/api/discovery/ecosystems` - List ecosystems
- `/api/discovery/ecosystem/{name}/developers` - Developers in ecosystem
- `/api/discovery/orbit/{username}` - Developer network
- `/api/discovery/recent` - Recent discoveries

### Phase 9: Frontend Integration
- Ecosystem browser
- Network graph visualization
- Priority dashboard
- Discovery timeline
- Source attribution badges

---

## 💡 Key Insights

### Why This Matters

1. **Complete Picture**: Track not just what we have, but where it came from
2. **AI Training**: Rich metadata and relationships for ML models
3. **Quality Focus**: Prioritize high-value entities automatically
4. **Network Effects**: Discover through relationships, not just search
5. **Continuous Learning**: System gets smarter over time
6. **Full Transparency**: Every entity has a provenance story

### Success Metrics

- **50,000+ repositories** from Electric Capital taxonomy
- **100,000+ developers** discovered from priority repos
- **10,000+ developers** tagged as "ethereum ecosystem"
- **1,000+ orbit relationships** mapped
- **100% lineage tracking** - every entity knows its origin
- **Automated daily discovery** of 100+ new contributors

---

## 🚀 Quick Start

### 1. Setup Database
```bash
psql -d talent -f migration_scripts/09_ai_discovery_schema.sql
```

### 2. Import Priority Repos
```bash
python3 scripts/github/import_priority_repositories.py
```

### 3. Discover Contributors
```bash
python3 scripts/github/discover_contributors.py --priority-tier 1 --limit 20
```

### 4. Check Results
```sql
-- View top ecosystems
SELECT * FROM v_top_ecosystems LIMIT 10;

-- View recently discovered developers
SELECT * FROM v_top_developers WHERE 'ethereum' = ANY(ecosystem_tags) LIMIT 20;

-- Check discovery stats
SELECT * FROM v_discovery_stats;
```

---

## 🎯 Configuration

### Environment Variables

```bash
# Required
export GITHUB_TOKEN="ghp_your_token_here"

# Optional
export OPENAI_API_KEY="sk-your_key_here"  # For AI scoring
```

### GitHub Rate Limits

- **Without token**: 60 requests/hour
- **With token**: 5,000 requests/hour
- **Script defaults**: 0.75s delay between requests (~4,800/hour)

---

## 📞 Support

For questions or issues:
1. Check logs in `logs/github_automation/`
2. Review discovery stats: `SELECT * FROM v_discovery_stats;`
3. Verify GitHub token: `echo $GITHUB_TOKEN`

---

**Built for AI-forward recruiting with full transparency and lineage tracking.** 🚀

