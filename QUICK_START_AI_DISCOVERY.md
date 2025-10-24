# Quick Start: AI-Powered GitHub Discovery System

**Get started discovering and enriching crypto developers in 5 minutes.**

---

## ✅ Prerequisites

### 1. GitHub Token (Required)

Get a GitHub Personal Access Token:
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `public_repo`, `read:user`, `read:org`
4. Copy the token

Set it as an environment variable:
```bash
export GITHUB_TOKEN="ghp_your_token_here"

# Make it permanent (add to ~/.zshrc):
echo 'export GITHUB_TOKEN="ghp_your_token_here"' >> ~/.zshrc
source ~/.zshrc
```

### 2. Database Setup (Already Done)

The schema has been created! Verify:
```bash
psql -d talent -c "SELECT COUNT(*) FROM discovery_source;"
```

Should return 7 discovery sources.

---

## 🚀 Quick Start Workflow

### Step 1: Import Priority Repositories (3-5 minutes)

Import the high-priority repos you specified (paradigmxyz, ethereum/EIPs, etc.):

```bash
cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete

# Import specific repos
python3 scripts/github/import_priority_repositories.py --repos \
    ethereum/EIPs \
    ethereum/execution-specs \
    paradigmxyz/reth \
    paradigmxyz/foundry

# Or import ALL priority repos and orgs (15-20 minutes)
python3 scripts/github/import_priority_repositories.py
```

**What this does**:
- Fetches repo metadata from GitHub
- Stores in `github_repository` table
- Links to ecosystems
- Tracks discovery source

**Expected output**:
- 50+ repositories imported
- Full metadata (stars, forks, languages, etc.)

### Step 2: Discover Contributors (10-30 minutes)

Discover all developers contributing to these repos:

```bash
# Discover from specific repos (faster, ~5 minutes)
python3 scripts/github/discover_contributors.py --repos ethereum/EIPs

# Discover from ALL Tier 1 repos (slower, ~30 minutes)
python3 scripts/github/discover_contributors.py --priority-tier 1 --limit 10

# Full discovery (can run overnight)
python3 scripts/github/discover_contributors.py --priority-tier 1
```

**What this does**:
- Fetches contributors for each repo
- Enriches GitHub profiles (bio, location, company, etc.)
- Tags with ecosystem tags (ethereum, eip-author, etc.)
- Creates contribution records
- Tracks discovery lineage

**Expected output**:
- 1,000+ developers discovered and enriched
- Ecosystem tags applied
- Full contribution history

### Step 3: Verify Results

Check what you've discovered:

```bash
psql -d talent << 'EOF'
-- Discovery statistics
SELECT * FROM v_discovery_stats;

-- Top Ethereum developers
SELECT 
    github_username,
    github_name,
    importance_score,
    ecosystem_tags,
    followers,
    total_merged_prs
FROM v_top_developers
WHERE 'ethereum' = ANY(ecosystem_tags)
LIMIT 20;

-- Repos by ecosystem
SELECT 
    ecosystem_name,
    repo_count,
    developer_count,
    total_stars
FROM v_top_ecosystems
WHERE priority_score <= 2
ORDER BY total_stars DESC;
EOF
```

---

## 📊 What You Get

After running the quick start, you'll have:

### In Database

✅ **Priority Repositories**:
- ethereum/EIPs
- All paradigmxyz/* repos (reth, foundry, artemis, etc.)
- All foundry-rs/* repos
- All alloy-rs/* repos
- gakonst personal repos
- Full metadata for each

✅ **Developers**:
- All contributors to above repos
- Enriched profiles (bio, location, company, followers, etc.)
- Ecosystem tags (ethereum, paradigm-ecosystem, eip-author, etc.)
- Contribution counts per repo
- Importance scores

✅ **Discovery Lineage**:
- Every entity knows where it came from
- Full audit trail in `entity_discovery` table
- Relationship tracking

✅ **Ecosystems**:
- Ethereum, Paradigm, Uniswap, Base, Optimism, Arbitrum, etc.
- Repos and developers organized by ecosystem
- Hierarchical relationships

### Query Examples

**Find all EIP authors**:
```sql
SELECT github_username, github_name, total_merged_prs
FROM v_top_developers
WHERE 'eip-author' = ANY(ecosystem_tags)
ORDER BY importance_score DESC
LIMIT 50;
```

**Find Paradigm ecosystem developers**:
```sql
SELECT github_username, github_name, github_company, location
FROM v_top_developers
WHERE 'paradigm-ecosystem' = ANY(ecosystem_tags)
ORDER BY importance_score DESC;
```

**Find developers contributing to multiple ecosystems**:
```sql
SELECT 
    github_username,
    github_name,
    ecosystem_tags,
    array_length(ecosystem_tags, 1) as ecosystem_count
FROM github_profile
WHERE array_length(ecosystem_tags, 1) >= 3
ORDER BY ecosystem_count DESC, importance_score DESC
LIMIT 30;
```

---

## 🎯 Next Steps

### Option A: Continue Discovery

Expand to more ecosystems:

```bash
# Discover Uniswap contributors
python3 scripts/github/discover_contributors.py --repos \
    Uniswap/v3-core \
    Uniswap/v3-periphery \
    Uniswap/v4-core

# Discover all Tier 2 ecosystems
python3 scripts/github/discover_contributors.py --priority-tier 2 --limit 20
```

### Option B: Parse Electric Capital Taxonomy

Import 50,000+ repos from Electric Capital:

```bash
# Download and parse (takes ~30 minutes)
python3 scripts/github/parse_electric_capital_taxonomy.py --full --priority-only

# Or full taxonomy (takes ~2 hours)
python3 scripts/github/parse_electric_capital_taxonomy.py --full
```

This will:
- Import 1,000+ crypto ecosystems
- Link 50,000+ repositories to ecosystems
- Organize everything taxonomically

### Option C: Set Up Continuous Discovery

Monitor repos for new contributors (coming in Phase 7):

```bash
# Set up daily cron job
echo "0 2 * * * cd $(pwd) && python3 scripts/github/discover_contributors.py --priority-tier 1 --limit 50" | crontab -
```

---

## 🔍 Understanding the Data

### Discovery Sources

Every entity has a `discovery_source_id` that tells you where it came from:

| Source Type | Description | Example |
|-------------|-------------|---------|
| `manual_import` | You specified it | ethereum/EIPs |
| `electric_capital_taxonomy` | From EC taxonomy | Any repo in taxonomy |
| `ethereum_eip` | From EIP repo | EIP authors |
| `paradigm_ecosystem` | From Paradigm | paradigmxyz/* contributors |
| `contributor_expansion` | Discovered via contribution | Contributors to known repos |
| `orbit_discovery` | In orbit of notable devs | Coming in Phase 5 |

### Ecosystem Tags

Developers automatically get tagged:

| Tag | Meaning |
|-----|---------|
| `ethereum` | Contributed to Ethereum ecosystem |
| `eip-author` | Contributed to ethereum/EIPs |
| `paradigm-ecosystem` | Contributed to paradigmxyz repos |
| `defi` | Contributed to DeFi protocols |
| `uniswap` | Contributed to Uniswap |

### Importance Scores

Both repos and developers get scores (0-100):

**Repositories**: Based on stars, forks, contributors, ecosystem membership, activity
**Developers**: Based on followers, merged PRs, lines of code, repos contributed to, ecosystems

Higher scores = more important/influential

---

## 🐛 Troubleshooting

### Issue: "GITHUB_TOKEN not set"

**Solution**:
```bash
export GITHUB_TOKEN="ghp_your_token_here"
echo $GITHUB_TOKEN  # Verify it's set
```

### Issue: "Rate limit exceeded"

**Solution**: Wait 1 hour or use multiple tokens. Check status:
```bash
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit
```

### Issue: "Repository not found"

**Solution**: The repo may not exist or may be private. Check on GitHub first.

### Issue: Slow discovery

**Explanation**: This is normal. GitHub API is rate-limited to 5,000 requests/hour.
- Each repo = ~1 API call
- Each contributor = 1 API call
- Script includes 0.75s delay to stay under limit

**Tip**: Run overnight for large discovery jobs.

---

## 📚 Documentation

- **Full System Docs**: [docs/AI_DISCOVERY_SYSTEM.md](docs/AI_DISCOVERY_SYSTEM.md)
- **Ecosystem Guide**: [docs/ECOSYSTEM_TAXONOMY.md](docs/ECOSYSTEM_TAXONOMY.md)
- **Database Schema**: See migration `migration_scripts/09_ai_discovery_schema.sql`

---

## 💡 Pro Tips

### 1. Start Small, Scale Up

Don't try to discover everything at once:
```bash
# Start with 1 repo
python3 scripts/github/discover_contributors.py --repos ethereum/EIPs

# Then 10 repos
python3 scripts/github/discover_contributors.py --priority-tier 1 --limit 10

# Then go big
python3 scripts/github/discover_contributors.py --priority-tier 1
```

### 2. Monitor Progress

Watch logs in real-time:
```bash
# In one terminal, run discovery
python3 scripts/github/discover_contributors.py --priority-tier 1 --limit 20

# In another terminal, watch database
watch -n 5 'psql -d talent -c "SELECT * FROM v_discovery_stats;"'
```

### 3. Focus on Quality

Tier 1 repos have the highest quality developers:
- ethereum/EIPs → Core Ethereum developers
- paradigmxyz/* → Cutting-edge Rust developers
- Uniswap → Top DeFi developers

### 4. Export for Analysis

Export discovered developers:
```bash
psql -d talent -c "COPY (
    SELECT 
        github_username,
        github_name,
        github_email,
        location,
        github_company,
        ecosystem_tags,
        importance_score,
        total_merged_prs
    FROM v_top_developers
    WHERE 'ethereum' = ANY(ecosystem_tags)
    ORDER BY importance_score DESC
    LIMIT 1000
) TO STDOUT WITH CSV HEADER" > ethereum_developers.csv
```

### 5. Update Regularly

Re-run discovery weekly to catch new contributors:
```bash
# Weekly cron job (Sundays at 2 AM)
0 2 * * 0 cd /path/to/project && python3 scripts/github/discover_contributors.py --priority-tier 1 --limit 100
```

---

## ✅ Success Checklist

After quick start, you should have:

- [ ] GitHub token set and working
- [ ] 50+ priority repositories imported
- [ ] 1,000+ developers discovered and enriched
- [ ] Ecosystem tags applied (ethereum, paradigm-ecosystem, etc.)
- [ ] Discovery statistics show progress
- [ ] Can query developers by ecosystem
- [ ] Importance scores calculated
- [ ] Discovery lineage tracked

---

## 🎉 You're Ready!

You now have an AI-powered discovery system that:

✅ Tracks **where every developer came from**  
✅ Organizes by **crypto ecosystems**  
✅ Prioritizes by **importance and relevance**  
✅ Continuously **discovers new talent**  
✅ Maintains **full lineage and audit trail**  

**Next**: Use the frontend to visualize this data, or build custom queries for your recruiting needs!

---

**Questions?** Check the full docs: [docs/AI_DISCOVERY_SYSTEM.md](docs/AI_DISCOVERY_SYSTEM.md)

