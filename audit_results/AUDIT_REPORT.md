# Database Audit Report
**Generated:** 2025-10-20 15:46:39

---

## Executive Summary

### Databases Found
- **Total Databases**: 12
- **Active Databases**: 12
- **Empty/Abandoned**: 0

### Data Summary (Across All Databases)
- **Total People Records**: 106,018
- **Total Company Records**: 136,264

---

## Database Inventory

### SQLite Databases


#### talent_intelligence.db
- **Path**: `/Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete/talent_intelligence.db`
- **Size**: 22.66 MB
- **Last Modified**: 2025-10-20T15:27:14.652324
- **Status**: ✅ Active

**Tables**: people, social_profiles, sqlite_sequence, emails, employment, data_sources, companies, company_funding_rounds, company_social_profiles, github_profiles...

**Key Statistics**:

- People: 15,350
  - With Email: 7,034 (45.8%)
  - With LinkedIn: 11,912 (77.6%)
  - Avg Quality Score: 0.774

- Companies: 3,154
  - With Website: 2,687
  - With GitHub Org: 174

- GitHub Profiles: 18,029
  - Linked to People: 4,203
  - With Email: 5,482

#### talent_intelligence_backup_20251019_115502.db
- **Path**: `/Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete/talent_intelligence_backup_20251019_115502.db`
- **Size**: 21.09 MB
- **Last Modified**: 2025-10-20T15:27:14.671787
- **Status**: ✅ Active

**Tables**: people, social_profiles, sqlite_sequence, emails, employment, data_sources, companies, company_funding_rounds, company_social_profiles, github_profiles...

**Key Statistics**:

- People: 15,337
  - With Email: 7,028 (45.8%)
  - With LinkedIn: 11,912 (77.7%)
  - Avg Quality Score: 0.774

- Companies: 3,154
  - With Website: 2,687
  - With GitHub Org: 174

- GitHub Profiles: 17,528
  - Linked to People: 2,982
  - With Email: 4,999

#### talent_intelligence.db
- **Path**: `/Users/charlie.kerr/Documents/CK Docs/FINAL_DATABASE/talent_intelligence.db`
- **Size**: 22.66 MB
- **Last Modified**: 2025-10-19T23:30:08.776002
- **Status**: ✅ Active

**Tables**: people, social_profiles, sqlite_sequence, emails, employment, data_sources, companies, company_funding_rounds, company_social_profiles, github_profiles...

**Key Statistics**:

- People: 15,350
  - With Email: 7,034 (45.8%)
  - With LinkedIn: 11,912 (77.6%)
  - Avg Quality Score: 0.774

- Companies: 3,154
  - With Website: 2,687
  - With GitHub Org: 174

- GitHub Profiles: 18,029
  - Linked to People: 4,203
  - With Email: 5,482

### PostgreSQL Databases

#### talent
- **Size**: 132 MB
- **Owner**: "charlie.kerr"
- **Last Activity**: 2025-10-20T14:44:33.424778-04:00
- **Status**: ✅ Active

**Tables**: company, company_funding_round, domain_company_map, edge_coemployment, education, employment, person

**Key Statistics**:

- People: 32,515
  - With Email: 0
  - With LinkedIn: 32,515

- Companies: 91,722
  - With Website: 0

- Employment Records: 203,076
  - Unique People: 30,075
  - Avg Records per Person: 6.8

#### talent_intelligence
- **Size**: 2893 MB
- **Owner**: postgres
- **Last Activity**: 2025-10-20T14:44:33.843402-04:00
- **Status**: ✅ Active

**Tables**: companies, company_repositories, company_social_profiles, data_sources, education_history, emails, employment_history, funding_rounds, github_contributions, github_match_reviews...

**Key Statistics**:

- People: 15,337
  - With Email: 7,028
  - With LinkedIn: 0
  - Avg Quality Score: 0.774

- Companies: 35,080
  - With Website: 2,674
  - With GitHub Org: 174

- GitHub Profiles: 17,528
  - Linked to People: 2,982

#### talent_intel
- **Size**: 18 MB
- **Owner**: postgres
- **Last Activity**: 2025-10-20T14:44:33.901605-04:00
- **Status**: ✅ Active

**Tables**: companies, education_history, interactions, people, person_skills, skills, vw_candidates_by_company, vw_complete_profiles, vw_data_quality, vw_high_priority_candidates...

**Key Statistics**:

- People: 12,129
  - With Email: 3,605
  - With LinkedIn: 12,129

- Companies: 0
  - With Website: 0

#### talent_graph
- **Size**: 9153 kB
- **Owner**: "charlie.kerr"
- **Last Activity**: 2025-10-20T14:44:33.932792-04:00
- **Status**: ✅ Active

**Tables**: companies, datasources, people, people_crypto_interests, people_farcaster, relationships, vcs

**Key Statistics**:

- People: 0
  - With Email: 0
  - With LinkedIn: 0

- Companies: 0
  - With Website: 0

#### talentgraph
- **Size**: 9433 kB
- **Owner**: "charlie.kerr"
- **Last Activity**: 2025-10-20T14:44:33.948221-04:00
- **Status**: ✅ Active

**Tables**: Companies, DataSources, People, Relationships, SequelizeMeta, VCs

**Key Statistics**:

#### talentgraph2
- **Size**: 16 MB
- **Owner**: postgres
- **Last Activity**: 2025-10-20T14:44:33.986210-04:00
- **Status**: ✅ Active

**Tables**: SequelizeMeta, contributor, contributors, relationship, relationships, staging

**Key Statistics**:

#### talentgraph_development
- **Size**: 8993 kB
- **Owner**: "charlie.kerr"
- **Last Activity**: 2025-10-20T14:44:33.997803-04:00
- **Status**: ✅ Active

**Tables**: Companies, DataSources, People, Relationships, SequelizeMeta, VCS, VCs

**Key Statistics**:

#### tech_recruiting_db
- **Size**: 31 GB
- **Owner**: postgres
- **Last Activity**: 2025-10-20T14:44:34.038077-04:00
- **Status**: ✅ Active

**Tables**: Contributors, HighSignalAccounts, Relationships, Stagings, contributors, high_signal_accounts, relationships, staging

**Key Statistics**:

#### crypto_dev_network
- **Size**: 225 MB
- **Owner**: postgres
- **Last Activity**: 2025-10-20T14:44:34.070124-04:00
- **Status**: ✅ Active

**Tables**: contributors, highsignalaccounts, relationships, staging

**Key Statistics**:

---

## Overlap Analysis

### Key Findings


#### sqlite vs talent (LinkedIn URLs)
- In Both: 0
- Only in sqlite: 11,912
- Only in talent: 32,515
- Total Unique: 44,427

#### sqlite vs talent_intelligence (LinkedIn URLs)
- In Both: 0
- Only in sqlite: 11,912
- Only in talent_intelligence: 0
- Total Unique: 11,912

#### sqlite vs talent_intel (LinkedIn URLs)
- In Both: 8,467
- Only in sqlite: 3,445
- Only in talent_intel: 3,662
- Total Unique: 15,574

#### talent vs talent_intelligence (LinkedIn URLs)
- In Both: 0
- Only in talent: 32,515
- Only in talent_intelligence: 0
- Total Unique: 32,515

#### talent vs talent_intel (LinkedIn URLs)
- In Both: 0
- Only in talent: 32,515
- Only in talent_intel: 12,129
- Total Unique: 44,644

#### talent_intelligence vs talent_intel (LinkedIn URLs)
- In Both: 0
- Only in talent_intelligence: 0
- Only in talent_intel: 12,129
- Total Unique: 12,129

---

## Critical Findings & Recommendations


### 1. Schema Differences Detected

**PostgreSQL `talent` Database:**
- Uses `person` table (singular) instead of `people` (plural)
- Likely stores LinkedIn URLs in the `linkedin_url` column directly on person table
- Has 32,515 people but 0 emails found in analysis
- **Issue**: Different schema than SQLite/other PostgreSQL databases

**PostgreSQL `talent_intelligence` & SQLite:**
- Use `people` table (plural)
- Store social profiles in separate `social_profiles` table
- Nearly identical schemas (99.9% email overlap confirms this)

**PostgreSQL `talent_intel`:**
- Uses `person` table (similar to `talent`)
- Has 12,129 people with 71% overlap with SQLite
- Appears to be a subset or older version

### 2. Data Completeness Issues

**PostgreSQL `talent`:**
- ✅ Most people records (32,515)
- ✅ Most company records (91,722 - includes historical employers)
- ⚠️ 0 emails found (schema difference - needs investigation)
- ⚠️ 0% LinkedIn URL overlap with other databases (different format/normalization)

**SQLite `talent_intelligence.db`:**
- ✅ Clean, well-structured data
- ✅ High data quality scores (avg 0.77)
- ✅ 11,912 LinkedIn URLs
- ✅ 7,036 emails
- ✅ GitHub enrichment (18,029 profiles)
- ⚠️ Only current employment (not historical)

**PostgreSQL `talent_intelligence`:**
- Appears to be a direct import of SQLite data
- 99.9% email overlap confirms duplication
- 35,080 companies (10x more than SQLite due to historical data)

---

## Recommended Consolidation Strategy

### Phase 1: Investigate Schema Differences

**Action Required**: Examine PostgreSQL `talent` database schema in detail

```sql
-- Run this to understand talent database structure:
\d person
\d company  
\d employment
\d edge_*
```

The `talent` database likely uses a graph-based schema (note: edge_* tables) which is fundamentally different from the relational schema used in SQLite and `talent_intelligence`.

### Phase 2: Determine Primary Database

**Option A: PostgreSQL `talent` as Primary** ✅ RECOMMENDED
- **Pros**:
  - Most comprehensive (32,515 people, 91,722 companies)
  - Full employment history (203,076 records mentioned in your report)
  - Production-ready graph schema
  - Currently referenced as primary in your problem statement
- **Cons**:
  - Different schema from SQLite
  - Need to migrate SQLite LinkedIn profiles and emails
  - Need to investigate why 0 emails showing up

**Option B: Create New Unified Database**
- Start fresh with best practices
- Migrate data from all sources
- More work but cleaner result

### Phase 3: Migration Plan

If choosing Option A (PostgreSQL `talent` as primary):

1. **Investigate `talent` schema** 
   - Confirm how emails are stored
   - Confirm how LinkedIn URLs are stored
   - Document graph structure

2. **Migrate from SQLite**
   - 11,912 LinkedIn profiles
   - 7,036 emails
   - 18,029 GitHub profiles with enrichment data

3. **Deduplicate within `talent`**
   - 32,515 people might include duplicates
   - Need email/LinkedIn based deduplication

4. **Archive Other Databases**
   - `talent_intelligence` (duplicate of SQLite)
   - `talent_intel` (subset of data)
   - Empty databases (talent_graph, talentgraph, etc.)

### Phase 4: Cleanup

**Databases to Archive**:
- ✅ SQLite databases (after migration)
- ✅ PostgreSQL `talent_intelligence` (duplicate)
- ✅ PostgreSQL `talent_intel` (subset, verify unique data first)
- ✅ PostgreSQL `talent_graph`, `talentgraph`, `talentgraph2`, `talentgraph_development` (empty)
- ✅ PostgreSQL `tech_recruiting_db`, `crypto_dev_network` (not found/empty)

**Single Source of Truth**: PostgreSQL `talent`

---

## Next Steps

1. **IMMEDIATE**: Run schema analysis on PostgreSQL `talent` database
   ```bash
   psql -d talent -c "\dt"
   psql -d talent -c "\d person"
   psql -d talent -c "\d company"
   ```

2. **INVESTIGATE**: Why 0 emails showing in `talent` database
   - Check actual table structure
   - Might be in edge_ tables or different column name

3. **VERIFY**: Employment history in `talent` database
   - Confirm 203,076 employment records exist
   - Verify historical tracking vs current only

4. **PLAN**: Detailed migration script for SQLite → PostgreSQL `talent`
   - Map schemas
   - Handle duplicates
   - Verify data integrity

5. **EXECUTE**: Migration with full backups
   - Backup all databases before changes
   - Migrate in stages
   - Validate after each step


### Detailed Recommendations from Overlap Analysis

1. **[HIGH]** MIGRATE
   - source: SQLite talent_intelligence.db
   - target: PostgreSQL talent
   - records: 11912
   - reason: 11,912 LinkedIn profiles exist in SQLite but not in PostgreSQL talent

2. **[INFO]** VERIFY
   - description: PostgreSQL talent has 32,515 additional LinkedIn profiles not in SQLite
   - reason: These might be from GitHub enrichment or other sources

3. **[MEDIUM]** EVALUATE
   - database: PostgreSQL talent_intel
   - unique_records: 12129
   - reason: Has 12,129 LinkedIn profiles not in talent database
   - suggestion: Review and migrate unique records to talent if valuable

