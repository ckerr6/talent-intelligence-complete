# Tier 1: Validation Test Suite

**Purpose:** Validate all newly implemented capabilities  
**Date:** October 24, 2025  
**Status:** Ready to execute

---

## Test Categories

1. **Skills System** - Core recruiting capability
2. **Ecosystem Organization** - Industry-specific searches
3. **Email Management** - Contact capability
4. **GitHub Integration** - Technical depth
5. **Data Quality** - Overall health

---

## 1. Skills System Validation ✅

### Test 1.1: Find Solidity Developers
```sql
-- Should return developers with Solidity skill
SELECT 
    p.full_name,
    p.location,
    p.headline,
    ps.proficiency_score,
    ps.evidence_sources,
    ps.repos_using_skill,
    ps.merged_prs_count
FROM person p
JOIN person_skills ps ON p.person_id = ps.person_id
JOIN skills s ON ps.skill_id = s.skill_id
WHERE s.skill_name = 'Solidity'
ORDER BY ps.proficiency_score DESC
LIMIT 20;
```

**Expected:** 20 profiles with Solidity skills, proficiency 40-90
**Key Checks:**
- ✅ Proficiency scores are reasonable (not all 0 or 100)
- ✅ Evidence sources show 'title', 'headline', or 'repos'
- ✅ Names and locations are real people
- ✅ Results ranked by proficiency

### Test 1.2: Multi-Skill Search (Rust + Go)
```sql
-- Find polyglot developers
SELECT 
    p.full_name,
    p.location,
    array_agg(DISTINCT s.skill_name ORDER BY s.skill_name) as skills,
    AVG(ps.proficiency_score)::INT as avg_proficiency
FROM person p
JOIN person_skills ps ON p.person_id = ps.person_id
JOIN skills s ON ps.skill_id = s.skill_id
WHERE p.person_id IN (
    -- People with Rust
    SELECT person_id FROM person_skills ps1
    JOIN skills s1 ON ps1.skill_id = s1.skill_id
    WHERE s1.skill_name = 'Rust'
    INTERSECT
    -- People with Go
    SELECT person_id FROM person_skills ps2
    JOIN skills s2 ON ps2.skill_id = s2.skill_id
    WHERE s2.skill_name = 'Go'
)
GROUP BY p.person_id, p.full_name, p.location
ORDER BY avg_proficiency DESC
LIMIT 20;
```

**Expected:** 10-20 profiles with both Rust AND Go
**Key Checks:**
- ✅ All results have both skills
- ✅ Skills array shows additional languages
- ✅ Average proficiency is reasonable

### Test 1.3: Senior-Level Filter
```sql
-- Find senior/lead engineers only
SELECT 
    p.full_name,
    p.headline,
    s.skill_name,
    ps.proficiency_score,
    ps.evidence_sources
FROM person p
JOIN person_skills ps ON p.person_id = ps.person_id
JOIN skills s ON ps.skill_id = s.skill_id
WHERE ps.proficiency_score >= 75  -- Senior+ level
AND s.category = 'language'
ORDER BY ps.proficiency_score DESC
LIMIT 20;
```

**Expected:** 20 profiles with senior-level proficiency (75+)
**Key Checks:**
- ✅ Headlines show senior/lead/principal titles
- ✅ Evidence sources include 'title' or 'headline'
- ✅ Proficiency scores 75-90

### Test 1.4: Skills Distribution
```sql
-- How many people have each skill?
SELECT 
    s.skill_name,
    s.category,
    COUNT(DISTINCT ps.person_id) as people_count,
    AVG(ps.proficiency_score)::INT as avg_proficiency,
    SUM(ps.repos_using_skill) as total_repos
FROM skills s
LEFT JOIN person_skills ps ON s.skill_id = ps.skill_id
GROUP BY s.skill_id, s.skill_name, s.category
HAVING COUNT(DISTINCT ps.person_id) > 0
ORDER BY people_count DESC
LIMIT 30;
```

**Expected:** Top skills have 1,000+ people
**Key Checks:**
- ✅ JavaScript/TypeScript/Python at top
- ✅ Blockchain skills present (Solidity, Ethereum)
- ✅ Reasonable distribution across categories
- ✅ Average proficiency 40-70

### Test 1.5: Coverage Stats
```sql
-- Overall skills coverage
SELECT 
    COUNT(DISTINCT p.person_id) as total_people,
    COUNT(DISTINCT ps.person_id) as people_with_skills,
    ROUND(100.0 * COUNT(DISTINCT ps.person_id) / COUNT(DISTINCT p.person_id), 2) as coverage_pct,
    COUNT(ps.person_skills_id) as total_skill_records,
    ROUND(COUNT(ps.person_skills_id)::FLOAT / COUNT(DISTINCT ps.person_id), 2) as avg_skills_per_person
FROM person p
LEFT JOIN person_skills ps ON p.person_id = ps.person_id;
```

**Expected:** 
- Coverage: 60-65%
- Avg skills per person: 1.5-2.0
**Key Checks:**
- ✅ Coverage > 50%
- ✅ Not everyone has skills (realistic)

---

## 2. Ecosystem Organization Validation ✅

### Test 2.1: Find Ethereum Developers
```sql
-- Search by ecosystem
SELECT 
    p.full_name,
    p.location,
    pea.contribution_count,
    pea.repo_count,
    pea.last_contribution_date
FROM person p
JOIN person_ecosystem_activity pea ON p.person_id = pea.person_id
JOIN crypto_ecosystem ce ON pea.ecosystem_id = ce.ecosystem_id
WHERE ce.ecosystem_name = 'Ethereum'
ORDER BY pea.contribution_count DESC
LIMIT 20;
```

**Expected:** 20 Ethereum contributors
**Key Checks:**
- ✅ Contribution counts > 0
- ✅ Repo counts > 0
- ✅ Recent contribution dates
- ✅ Real people names

### Test 2.2: Top Ecosystems
```sql
-- Which ecosystems have the most developers?
SELECT 
    ce.ecosystem_name,
    COUNT(DISTINCT pea.person_id) as developer_count,
    SUM(pea.contribution_count) as total_contributions,
    SUM(pea.repo_count) as total_repos
FROM crypto_ecosystem ce
LEFT JOIN person_ecosystem_activity pea ON ce.ecosystem_id = pea.ecosystem_id
GROUP BY ce.ecosystem_id, ce.ecosystem_name
HAVING COUNT(DISTINCT pea.person_id) > 0
ORDER BY developer_count DESC
LIMIT 20;
```

**Expected:** Ethereum, Avalanche, Base at top
**Key Checks:**
- ✅ Major ecosystems present
- ✅ Reasonable developer counts (100s-1000s)
- ✅ Contribution counts correlate with size

### Test 2.3: Repository Ecosystem Tags
```sql
-- How many repos are tagged?
SELECT 
    COUNT(*) as total_repos,
    COUNT(CASE WHEN ecosystem_ids IS NOT NULL AND array_length(ecosystem_ids, 1) > 0 
          THEN 1 END) as repos_with_ecosystems,
    ROUND(100.0 * COUNT(CASE WHEN ecosystem_ids IS NOT NULL AND array_length(ecosystem_ids, 1) > 0 
          THEN 1 END) / COUNT(*), 2) as coverage_pct
FROM github_repository;
```

**Expected:** 90%+ repos tagged
**Key Checks:**
- ✅ Coverage > 90%

### Test 2.4: Multi-Ecosystem Contributors
```sql
-- People contributing to multiple ecosystems
SELECT 
    p.full_name,
    COUNT(DISTINCT pea.ecosystem_id) as ecosystem_count,
    array_agg(DISTINCT ce.ecosystem_name ORDER BY ce.ecosystem_name) as ecosystems
FROM person p
JOIN person_ecosystem_activity pea ON p.person_id = pea.person_id
JOIN crypto_ecosystem ce ON pea.ecosystem_id = ce.ecosystem_id
GROUP BY p.person_id, p.full_name
HAVING COUNT(DISTINCT pea.ecosystem_id) >= 3
ORDER BY ecosystem_count DESC
LIMIT 20;
```

**Expected:** Some polyglot blockchain developers
**Key Checks:**
- ✅ 3+ ecosystems per person
- ✅ Diverse ecosystem combinations

---

## 3. Email Management Validation ✅

### Test 3.1: Email Coverage
```sql
-- How many people have emails?
SELECT 
    COUNT(DISTINCT p.person_id) as total_people,
    COUNT(DISTINCT pe.person_id) as people_with_emails,
    ROUND(100.0 * COUNT(DISTINCT pe.person_id) / COUNT(DISTINCT p.person_id), 2) as coverage_pct,
    COUNT(pe.email_id) as total_email_records
FROM person p
LEFT JOIN person_email pe ON p.person_id = pe.person_id;
```

**Expected:** 18-20% coverage, 60K+ email records
**Key Checks:**
- ✅ Coverage > 15%
- ✅ Total emails > 60K

### Test 3.2: Email Types Distribution
```sql
-- Email type breakdown
SELECT 
    email_type,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as pct
FROM person_email
GROUP BY email_type
ORDER BY count DESC;
```

**Expected:** Work emails dominate
**Key Checks:**
- ✅ 'work' > 'personal'
- ✅ Some 'unknown'

### Test 3.3: People with Multiple Emails
```sql
-- People with 2+ emails
SELECT 
    p.full_name,
    COUNT(pe.email_id) as email_count,
    array_agg(pe.email_type ORDER BY pe.is_primary DESC) as types
FROM person p
JOIN person_email pe ON p.person_id = pe.person_id
GROUP BY p.person_id, p.full_name
HAVING COUNT(pe.email_id) > 1
ORDER BY email_count DESC
LIMIT 20;
```

**Expected:** Some people with 2-3 emails
**Key Checks:**
- ✅ Multiple email types per person
- ✅ Primary email designated

---

## 4. GitHub Integration Validation ✅

### Test 4.1: GitHub Profile Linkage
```sql
-- Linkage stats
SELECT 
    COUNT(*) as total_profiles,
    COUNT(person_id) as linked_profiles,
    COUNT(*) - COUNT(person_id) as unlinked_profiles,
    ROUND(100.0 * COUNT(person_id) / COUNT(*), 2) as linkage_pct
FROM github_profile;
```

**Expected:** 100% linkage
**Key Checks:**
- ✅ Linkage = 100%

### Test 4.2: People with GitHub
```sql
-- How many people have GitHub profiles?
SELECT 
    COUNT(DISTINCT p.person_id) as total_people,
    COUNT(DISTINCT gp.person_id) as people_with_github,
    ROUND(100.0 * COUNT(DISTINCT gp.person_id) / COUNT(DISTINCT p.person_id), 2) as coverage_pct
FROM person p
LEFT JOIN github_profile gp ON p.person_id = gp.person_id;
```

**Expected:** 60-65% coverage
**Key Checks:**
- ✅ Coverage > 60%

### Test 4.3: Contribution Stats
```sql
-- Contribution distribution
SELECT 
    COUNT(DISTINCT gc.github_profile_id) as contributors,
    SUM(gc.contribution_count) as total_contributions,
    AVG(gc.contribution_count)::INT as avg_contributions,
    MAX(gc.contribution_count) as max_contributions
FROM github_contribution gc;
```

**Expected:** High contribution counts
**Key Checks:**
- ✅ Contributors > 50K
- ✅ Average reasonable (100-1000)

---

## 5. Cross-Functional Queries ✅

### Test 5.1: Full Recruiter Search
```sql
-- "Find senior Solidity developers in San Francisco with GitHub"
SELECT 
    p.full_name,
    p.location,
    p.headline,
    ps.proficiency_score as solidity_proficiency,
    gp.github_username,
    gp.followers,
    gp.public_repos,
    array_agg(DISTINCT pe.email) FILTER (WHERE pe.email IS NOT NULL) as emails
FROM person p
JOIN person_skills ps ON p.person_id = ps.person_id
JOIN skills s ON ps.skill_id = s.skill_id
LEFT JOIN github_profile gp ON p.person_id = gp.person_id
LEFT JOIN person_email pe ON p.person_id = pe.person_id
WHERE s.skill_name = 'Solidity'
AND ps.proficiency_score >= 70  -- Senior level
AND p.location ILIKE '%San Francisco%'
GROUP BY p.person_id, p.full_name, p.location, p.headline, 
         ps.proficiency_score, gp.github_username, gp.followers, gp.public_repos
ORDER BY ps.proficiency_score DESC;
```

**Expected:** Filtered list of senior SF Solidity devs
**Key Checks:**
- ✅ All have Solidity skill
- ✅ All are senior level (proficiency 70+)
- ✅ All in SF area
- ✅ Some have GitHub
- ✅ Some have emails

### Test 5.2: Ecosystem + Skills
```sql
-- "Find Rust developers who contributed to Ethereum"
SELECT 
    p.full_name,
    ps.proficiency_score as rust_proficiency,
    pea.contribution_count as ethereum_contributions,
    pea.repo_count as ethereum_repos
FROM person p
JOIN person_skills ps ON p.person_id = ps.person_id
JOIN skills s ON ps.skill_id = s.skill_id
JOIN person_ecosystem_activity pea ON p.person_id = pea.person_id
JOIN crypto_ecosystem ce ON pea.ecosystem_id = ce.ecosystem_id
WHERE s.skill_name = 'Rust'
AND ce.ecosystem_name = 'Ethereum'
ORDER BY rust_proficiency DESC, ethereum_contributions DESC
LIMIT 20;
```

**Expected:** Rust devs with Ethereum contributions
**Key Checks:**
- ✅ All have Rust skill
- ✅ All have Ethereum activity
- ✅ Reasonable numbers

### Test 5.3: Complete Profile
```sql
-- Full profile for one person
WITH person_details AS (
    SELECT person_id FROM person LIMIT 1
)
SELECT 
    'Skills' as data_type,
    COUNT(DISTINCT ps.skill_id) as count
FROM person_skills ps
WHERE ps.person_id = (SELECT person_id FROM person_details)
UNION ALL
SELECT 'Emails', COUNT(DISTINCT pe.email_id)
FROM person_email pe
WHERE pe.person_id = (SELECT person_id FROM person_details)
UNION ALL
SELECT 'Employment', COUNT(DISTINCT e.employment_id)
FROM employment e
WHERE e.person_id = (SELECT person_id FROM person_details)
UNION ALL
SELECT 'Ecosystems', COUNT(DISTINCT pea.ecosystem_id)
FROM person_ecosystem_activity pea
WHERE pea.person_id = (SELECT person_id FROM person_details)
UNION ALL
SELECT 'GitHub', COUNT(DISTINCT gp.github_profile_id)
FROM github_profile gp
WHERE gp.person_id = (SELECT person_id FROM person_details);
```

**Expected:** Multiple data points per person
**Key Checks:**
- ✅ Skills present
- ✅ Some have emails
- ✅ Employment history exists
- ✅ Some have ecosystem activity

---

## 6. Data Quality Checks ✅

### Test 6.1: Null/Empty Checks
```sql
-- Check for data quality issues
SELECT 
    'person' as table_name,
    COUNT(*) as total,
    COUNT(CASE WHEN full_name IS NULL OR full_name = '' THEN 1 END) as missing_names,
    COUNT(CASE WHEN linkedin_url IS NULL THEN 1 END) as missing_linkedin
FROM person
UNION ALL
SELECT 
    'person_skills',
    COUNT(*),
    COUNT(CASE WHEN proficiency_score IS NULL THEN 1 END),
    COUNT(CASE WHEN confidence_score IS NULL THEN 1 END)
FROM person_skills
UNION ALL
SELECT 
    'person_email',
    COUNT(*),
    COUNT(CASE WHEN email IS NULL OR email = '' THEN 1 END),
    COUNT(CASE WHEN email_type IS NULL THEN 1 END)
FROM person_email;
```

**Expected:** Minimal nulls in critical fields
**Key Checks:**
- ✅ No null names
- ✅ Skills have proficiency scores
- ✅ Emails have values

### Test 6.2: Duplicate Checks
```sql
-- Check for duplicates
SELECT 
    person_id,
    skill_id,
    COUNT(*) as duplicate_count
FROM person_skills
GROUP BY person_id, skill_id
HAVING COUNT(*) > 1;
```

**Expected:** No duplicates (0 rows)
**Key Checks:**
- ✅ Unique constraint working

### Test 6.3: Index Performance
```sql
-- Test index usage (should be fast)
EXPLAIN ANALYZE
SELECT p.full_name, ps.proficiency_score
FROM person p
JOIN person_skills ps ON p.person_id = ps.person_id
JOIN skills s ON ps.skill_id = s.skill_id
WHERE s.skill_name = 'Solidity'
ORDER BY ps.proficiency_score DESC
LIMIT 20;
```

**Expected:** < 100ms execution
**Key Checks:**
- ✅ Index scans (not sequential)
- ✅ Fast execution

---

## Running the Test Suite

### Quick Test (5 minutes)
```bash
cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete

# Run key queries
psql -d talent -f validation_tests/quick_tests.sql > validation_results.txt
```

### Full Test Suite (15 minutes)
```bash
# Run all tests
psql -d talent < validation_tests/full_test_suite.sql > validation_full_results.txt

# Review results
cat validation_full_results.txt
```

### Manual Spot Checks
1. Pick 10 random Solidity developers
2. Verify their skills match their titles/repos
3. Check proficiency scores are reasonable
4. Verify email data is real
5. Check ecosystem tags make sense

---

## Success Criteria

### Must Pass ✅
- [ ] Skills coverage > 60%
- [ ] Email coverage > 15%
- [ ] GitHub linkage = 100%
- [ ] Ecosystem repos tagged > 90%
- [ ] No duplicate person_skills records
- [ ] Proficiency scores reasonable (not all 0 or 100)
- [ ] Top skills match expectations (JS, Python, TypeScript)

### Should Pass ✅
- [ ] Multi-skill queries work
- [ ] Ecosystem searches work
- [ ] Cross-functional queries work
- [ ] Performance < 100ms for indexed queries
- [ ] Data quality: minimal nulls

### Nice to Have ✅
- [ ] 2+ skills per person average
- [ ] Some multi-ecosystem contributors
- [ ] Email type distribution reasonable

---

## Issue Tracking

Found an issue? Document it:

| Issue | Severity | Query | Expected | Actual | Fix |
|-------|----------|-------|----------|--------|-----|
| Example: Low Solidity count | Medium | Test 1.1 | 1000+ | 200 | Need more extraction patterns |

---

## Next Steps After Validation

1. ✅ Review test results
2. ✅ Fix any critical issues found
3. ✅ Document known limitations
4. ✅ Move to Tier 2 planning
5. ⏸️ Schedule PR enrichment & importance scoring for later

---

**Created:** October 24, 2025  
**Purpose:** Validate Tier 1 implementations before Tier 2

