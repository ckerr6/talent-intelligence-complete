-- Migration: Performance Optimization Indexes
-- Date: 2025-10-23
-- Purpose: Add indexes for commonly queried fields to improve performance

-- ===== PERSON TABLE =====

-- Index for full name searches (case insensitive)
CREATE INDEX IF NOT EXISTS idx_person_full_name_lower ON person(LOWER(full_name));

-- Index for location filtering
CREATE INDEX IF NOT EXISTS idx_person_location ON person(location) WHERE location IS NOT NULL;

-- Index for headline searches
CREATE INDEX IF NOT EXISTS idx_person_headline ON person(headline) WHERE headline IS NOT NULL;

-- Composite index for search queries
CREATE INDEX IF NOT EXISTS idx_person_search ON person(full_name, location, headline);


-- ===== EMPLOYMENT TABLE =====

-- Index for company queries
CREATE INDEX IF NOT EXISTS idx_employment_company_id ON employment(company_id);

-- Index for person's employment history
CREATE INDEX IF NOT EXISTS idx_employment_person_id ON employment(person_id);

-- Index for current employment queries
CREATE INDEX IF NOT EXISTS idx_employment_current ON employment(person_id, is_current) WHERE is_current = TRUE;

-- Index for date range queries
CREATE INDEX IF NOT EXISTS idx_employment_dates ON employment(start_date, end_date);

-- Composite index for employment lookups
CREATE INDEX IF NOT EXISTS idx_employment_person_company ON employment(person_id, company_id, start_date DESC);


-- ===== COMPANY TABLE =====

-- Index for company name searches (case insensitive)
CREATE INDEX IF NOT EXISTS idx_company_name_lower ON company(LOWER(company_name));

-- Index for GitHub org lookups
CREATE INDEX IF NOT EXISTS idx_company_github_org ON company(github_org_name) WHERE github_org_name IS NOT NULL;


-- ===== GITHUB PROFILE TABLE =====

-- Index for GitHub username lookups
CREATE INDEX IF NOT EXISTS idx_github_username ON github_profile(username);

-- Index for GitHub email lookups
CREATE INDEX IF NOT EXISTS idx_github_email ON github_profile(github_email) WHERE github_email IS NOT NULL;

-- Index for person linkage
CREATE INDEX IF NOT EXISTS idx_github_person_id ON github_profile(person_id) WHERE person_id IS NOT NULL;

-- Index for location-based matching
CREATE INDEX IF NOT EXISTS idx_github_location ON github_profile(location) WHERE location IS NOT NULL;


-- ===== GITHUB REPOSITORY TABLE =====

-- Index for repository full name lookups
CREATE INDEX IF NOT EXISTS idx_github_repo_full_name ON github_repository(full_name);

-- Index for company repository queries
CREATE INDEX IF NOT EXISTS idx_github_repo_company ON github_repository(company_id) WHERE company_id IS NOT NULL;

-- Index for language filtering
CREATE INDEX IF NOT EXISTS idx_github_repo_language ON github_repository(language) WHERE language IS NOT NULL;

-- Index for popular repositories (stars)
CREATE INDEX IF NOT EXISTS idx_github_repo_stars ON github_repository(stars DESC) WHERE stars > 10;


-- ===== GITHUB CONTRIBUTION TABLE =====

-- Index for contributor queries
CREATE INDEX IF NOT EXISTS idx_github_contrib_profile ON github_contribution(github_profile_id);

-- Index for repository contributors
CREATE INDEX IF NOT EXISTS idx_github_contrib_repo ON github_contribution(repo_id);

-- Composite index for contribution lookups
CREATE INDEX IF NOT EXISTS idx_github_contrib_profile_repo ON github_contribution(github_profile_id, repo_id, contribution_count DESC);


-- ===== PERSON EMAIL TABLE =====

-- Index for email lookups (case insensitive)
CREATE INDEX IF NOT EXISTS idx_person_email_lower ON person_email(LOWER(email));

-- Index for person's emails
CREATE INDEX IF NOT EXISTS idx_person_email_person ON person_email(person_id);

-- Index for primary emails
CREATE INDEX IF NOT EXISTS idx_person_email_primary ON person_email(person_id, is_primary) WHERE is_primary = TRUE;


-- ===== NETWORK EDGES =====

-- Index for source person queries (already exists as PK, but good to be explicit)
CREATE INDEX IF NOT EXISTS idx_edge_coemployment_src ON edge_coemployment(src_person_id);

-- Index for destination person queries
CREATE INDEX IF NOT EXISTS idx_edge_coemployment_dst ON edge_coemployment(dst_person_id);

-- Bidirectional index for pathfinding
CREATE INDEX IF NOT EXISTS idx_edge_coemployment_both ON edge_coemployment(src_person_id, dst_person_id);


-- ===== RECRUITER WORKFLOW =====

-- Index for list membership queries
CREATE INDEX IF NOT EXISTS idx_list_members_list ON candidate_list_members(list_id);
CREATE INDEX IF NOT EXISTS idx_list_members_person ON candidate_list_members(person_id);

-- Index for notes queries
CREATE INDEX IF NOT EXISTS idx_person_notes_person ON person_notes(person_id);
CREATE INDEX IF NOT EXISTS idx_person_notes_created ON person_notes(person_id, created_at DESC);

-- Index for tags queries
CREATE INDEX IF NOT EXISTS idx_person_tags_person ON person_tags(person_id);
CREATE INDEX IF NOT EXISTS idx_person_tags_tag ON person_tags(tag);


-- ===== ANALYZE TABLES =====
-- Update table statistics for query optimizer

ANALYZE person;
ANALYZE employment;
ANALYZE company;
ANALYZE github_profile;
ANALYZE github_repository;
ANALYZE github_contribution;
ANALYZE person_email;
ANALYZE edge_coemployment;
ANALYZE candidate_list_members;
ANALYZE person_notes;
ANALYZE person_tags;

-- Print summary
SELECT 'Performance indexes created successfully!' as status;
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

