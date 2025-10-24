# Crypto Ecosystem Taxonomy

**Purpose**: Organize repositories, developers, and companies into meaningful crypto/blockchain ecosystems for better discovery and analysis.

**Source**: Primarily based on Electric Capital's crypto-ecosystems taxonomy with manual curation for priority entities.

---

## 🌳 Ecosystem Structure

### Hierarchical Organization

Ecosystems can have parent-child relationships:

```
Ethereum (parent)
├── Base (child)
├── Optimism (child)
├── Arbitrum (child)
└── Ethereum Name Service (child)

DeFi (parent)
├── Uniswap (child)
├── Aave (child)
├── Compound (child)
└── Curve (child)
```

### Multiple Ecosystem Membership

Entities can belong to multiple ecosystems:

```
uniswap/v3-core
├── Uniswap ecosystem
├── DeFi ecosystem
└── Ethereum ecosystem

paradigmxyz/reth
├── Paradigm ecosystem
└── Ethereum ecosystem
```

---

## 🎯 Priority Tiers

### Tier 1 - Highest Priority (Immediate Focus)

**Layer 1 Blockchains**:
- Ethereum
- Bitcoin (if relevant)

**Layer 2 Solutions**:
- Base
- Optimism
- Arbitrum

**Major Protocols**:
- Uniswap
- Paradigm ecosystem

**Key Infrastructure**:
- Ethereum EIPs

**Why Tier 1**:
- Highest developer activity
- Most influential in crypto space
- Strong network effects
- High-quality talent pool

### Tier 2 - High Priority

**Alt Layer 1s**:
- Solana
- Polygon
- Avalanche
- NEAR
- Sui
- Aptos
- Cosmos
- Polkadot

**DeFi Protocols**:
- Aave
- Compound
- Maker/MakerDAO
- Curve
- Balancer
- Yearn Finance
- Synthetix
- Lido
- Rocket Pool

**Infrastructure**:
- Chainlink
- The Graph

**NFT/Marketplace**:
- OpenSea
- Blur
- Rarible

**Identity/Social**:
- ENS (Ethereum Name Service)
- Lens Protocol

**Exchanges/Financial**:
- Coinbase
- Circle
- Binance
- Kraken
- Gemini

**Why Tier 2**:
- Significant developer ecosystems
- Established protocols
- High TVL or user base
- Important to crypto landscape

### Tier 3-5 - Standard to Low Priority

**Tier 3**: Emerging ecosystems with growing developer activity
**Tier 4**: Smaller established projects
**Tier 5**: Niche or experimental projects

---

## 🏷️ Ecosystem Tags

### Tag Categories

#### 1. Network Type
- `layer1` - Base blockchain
- `layer2` - Scaling solution
- `sidechain` - Independent chain with bridge
- `rollup` - Optimistic or ZK rollup
- `evm` - EVM-compatible

#### 2. Sector
- `defi` - Decentralized finance
- `nft` - Non-fungible tokens
- `gaming` - Blockchain gaming
- `social` - Social protocols
- `identity` - Identity systems
- `infrastructure` - Core infrastructure
- `tooling` - Developer tools
- `oracle` - Price feeds/data
- `bridge` - Cross-chain bridges

#### 3. Technology
- `smart-contracts` - Smart contract platform
- `zero-knowledge` - ZK technology
- `consensus` - Consensus research
- `cryptography` - Cryptographic research
- `virtual-machine` - VM implementation

#### 4. Organization Type
- `research` - Research organization
- `investment-firm` - VC/investment
- `exchange` - Cryptocurrency exchange
- `protocol` - Protocol development

### Example Tagging

```json
{
  "ecosystem_name": "Ethereum",
  "tags": [
    "layer1",
    "smart-contracts",
    "evm",
    "defi"
  ]
}

{
  "ecosystem_name": "Base",
  "tags": [
    "layer2",
    "rollup",
    "ethereum",
    "optimism",
    "coinbase"
  ]
}

{
  "ecosystem_name": "Paradigm",
  "tags": [
    "research",
    "infrastructure",
    "tooling",
    "investment-firm"
  ]
}
```

---

## 👥 Developer Ecosystem Tags

When a developer contributes to repos in an ecosystem, they get tagged:

```json
{
  "github_username": "developer_alice",
  "ecosystem_tags": [
    "ethereum",           // Contributed to Ethereum repos
    "eip-author",         // Authored EIPs
    "defi",              // Worked on DeFi protocols
    "uniswap"            // Contributed to Uniswap
  ]
}
```

### Special Developer Tags

- **`eip-author`**: Contributed to ethereum/EIPs
- **`erc-author`**: Contributed to ethereum/ERCs  
- **`paradigm-ecosystem`**: Contributed to Paradigm repos (paradigmxyz/*)
- **`core-developer`**: Core team member (owner/frequent contributor)
- **`protocol-developer`**: Works on protocol-level code
- **`tooling-developer`**: Builds developer tools

---

## 🔍 Discovery Through Ecosystems

### 1. Find Developers in Ecosystem

```sql
-- All Ethereum developers
SELECT 
    gp.github_username,
    gp.github_name,
    gp.importance_score,
    gp.ecosystem_tags
FROM github_profile gp
WHERE 'ethereum' = ANY(gp.ecosystem_tags)
ORDER BY gp.importance_score DESC
LIMIT 100;
```

### 2. Find Repos in Ecosystem

```sql
-- All Uniswap repos
SELECT 
    r.full_name,
    r.stars,
    r.description,
    r.importance_score
FROM github_repository r
JOIN crypto_ecosystem e ON e.ecosystem_id = ANY(r.ecosystem_ids)
WHERE e.normalized_name = 'uniswap'
ORDER BY r.stars DESC;
```

### 3. Find Companies in Ecosystem

```sql
-- All DeFi companies
SELECT 
    c.company_name,
    c.website,
    c.ecosystem_tags
FROM company c
WHERE 'defi' = ANY(c.ecosystem_tags)
ORDER BY c.company_name;
```

### 4. Cross-Ecosystem Analysis

```sql
-- Developers who work across multiple ecosystems
SELECT 
    gp.github_username,
    gp.github_name,
    gp.ecosystem_tags,
    array_length(gp.ecosystem_tags, 1) as ecosystem_count
FROM github_profile gp
WHERE array_length(gp.ecosystem_tags, 1) >= 3
ORDER BY ecosystem_count DESC, gp.importance_score DESC
LIMIT 50;
```

---

## 📊 Ecosystem Statistics

### View Ecosystem Stats

```sql
SELECT * FROM v_top_ecosystems;
```

**Output**:
```
ecosystem_name  | priority_score | repo_count | developer_count | total_stars
----------------+----------------+------------+-----------------+------------
Ethereum        |              1 |      15234 |           42516 |    1234567
Uniswap         |              1 |        234 |            5621 |     234567
Base            |              1 |        421 |            2134 |     156789
Paradigm        |              1 |         45 |            1234 |      89012
...
```

### Compute Stats

The `update_ecosystem_counts()` trigger automatically updates:
- `repo_count`: Number of repos in ecosystem
- `developer_count`: Number of developers tagged with ecosystem
- `total_stars`: Sum of stars across all repos

Manual refresh:
```sql
-- Refresh for specific ecosystem
SELECT update_ecosystem_counts();
```

---

## 🎯 Priority Scoring Logic

### Repository Priority

1. **Ecosystem Membership** (+10 points if in Tier 1 ecosystem)
2. **Stars** (weighted by ecosystem popularity)
3. **Recent Activity** (pushed within 90 days)
4. **Contributor Count** (more contributors = higher priority)

### Developer Priority

1. **Ecosystem Tags** (Tier 1 ecosystem = higher priority)
2. **Multiple Ecosystems** (cross-ecosystem experts)
3. **Special Roles** (EIP author, core developer)
4. **Contribution Quality** (merged PRs, lines of code)

---

## 🔄 Ecosystem Updates

### Adding New Ecosystems

**From Electric Capital Taxonomy**:
```bash
python3 scripts/github/parse_electric_capital_taxonomy.py --full
```

**Manually**:
```sql
INSERT INTO crypto_ecosystem (
    ecosystem_name,
    normalized_name,
    priority_score,
    tags,
    description
) VALUES (
    'New Protocol',
    'newprotocol',
    2,
    ARRAY['defi', 'lending'],
    'A new DeFi lending protocol'
);
```

### Linking Repos to Ecosystems

**Automatically** (via taxonomy parser):
- Repos are linked when imported from taxonomy

**Manually**:
```sql
-- Add ecosystem to existing repo
UPDATE github_repository
SET ecosystem_ids = ecosystem_ids || (
    SELECT ARRAY[ecosystem_id] 
    FROM crypto_ecosystem 
    WHERE normalized_name = 'ethereum'
)
WHERE full_name = 'paradigmxyz/reth';
```

### Tagging Developers

**Automatically** (via contributor discovery):
- Developers are tagged when discovered from repos

**Manually**:
```sql
-- Add ecosystem tag to developer
UPDATE github_profile
SET ecosystem_tags = ecosystem_tags || ARRAY['ethereum']
WHERE github_username = 'vitalik';
```

---

## 📈 Growth Tracking

### Track Ecosystem Growth Over Time

```sql
-- New developers per ecosystem (last 30 days)
SELECT 
    e.ecosystem_name,
    COUNT(DISTINCT ed.entity_id) as new_developers
FROM entity_discovery ed
JOIN crypto_ecosystem e ON e.normalized_name = ANY(
    SELECT unnest(ecosystem_tags) 
    FROM github_profile 
    WHERE github_profile_id = ed.entity_id
)
WHERE ed.entity_type = 'person'
  AND ed.discovered_at >= NOW() - INTERVAL '30 days'
GROUP BY e.ecosystem_name
ORDER BY new_developers DESC;
```

### Track Repository Growth

```sql
-- New repos per ecosystem (last 30 days)
SELECT 
    e.ecosystem_name,
    COUNT(DISTINCT r.repo_id) as new_repos
FROM github_repository r
JOIN crypto_ecosystem e ON e.ecosystem_id = ANY(r.ecosystem_ids)
WHERE r.created_at >= NOW() - INTERVAL '30 days'
GROUP BY e.ecosystem_name
ORDER BY new_repos DESC;
```

---

## 🎨 Frontend Display Guidelines

### Ecosystem Badge Colors

**Tier 1** (Highest Priority):
- Background: Gradient purple/blue
- Border: Gold
- Icon: ⭐

**Tier 2** (High Priority):
- Background: Gradient blue/green
- Border: Silver
- Icon: 💎

**Tier 3-5** (Standard):
- Background: Light gray
- Border: Gray
- Icon: 📦

### Display Format

**On Profile Pages**:
```
👤 Developer Name
   Ecosystems: [Ethereum] [DeFi] [EIP Author]
```

**On Repository Pages**:
```
📦 repo-name
   Part of: [Ethereum Ecosystem] [Paradigm]
   Priority: Tier 1 ⭐
```

**On Company Pages**:
```
🏢 Company Name
   Active in: [Ethereum] [DeFi] [Layer 2]
```

---

## 🔗 Related Documentation

- [AI Discovery System](./AI_DISCOVERY_SYSTEM.md) - Overall system architecture
- [GitHub Documentation](../GITHUB_SOURCING_ENHANCEMENTS.md) - GitHub enrichment
- [API Endpoints](./API_ENDPOINTS_DISCOVERY.md) - API for accessing ecosystem data

---

**Remember**: Ecosystems are living, evolving classifications. They should be updated regularly as the crypto landscape changes.

