-- Migration: Advanced Search Indexes
-- Purpose: Add indexes for efficient multi-criteria candidate search
-- Date: 2025-10-23
-- Dependencies: person, employment, github_profile, github_contributions tables

\timing on

BEGIN;

-- =============================================================================
-- ENABLE EXTENSIONS
-- =============================================================================

-- Enable pg_trgm for fuzzy text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

\echo '✓ pg_trgm extension enabled'

-- =============================================================================
-- TEXT SEARCH INDEXES (using trigram for fuzzy matching)
-- =============================================================================

-- Index for job title fuzzy search
-- This allows searches like "engineer", "developer" to match variations
DROP INDEX IF EXISTS idx_employment_title_trgm;
CREATE INDEX idx_employment_title_trgm 
ON employment USING gin(title gin_trgm_ops)
WHERE title IS NOT NULL AND title != '';

\echo '✓ Created trigram index on employment.title'

-- Index for person headline fuzzy search  
-- Allows keyword search across headlines
DROP INDEX IF EXISTS idx_person_headline_trgm;
CREATE INDEX idx_person_headline_trgm 
ON person USING gin(headline gin_trgm_ops)
WHERE headline IS NOT NULL AND headline != '';

\echo '✓ Created trigram index on person.headline'

-- Index for person description (if we add it later)
DROP INDEX IF EXISTS idx_person_description_trgm;
CREATE INDEX IF NOT EXISTS idx_person_description_trgm 
ON person USING gin(description gin_trgm_ops)
WHERE description IS NOT NULL AND description != '';

\echo '✓ Created trigram index on person.description'

-- =============================================================================
-- TECHNOLOGY/LANGUAGE INDEXES
-- =============================================================================

-- Index for GitHub contribution language filtering
-- Critical for technology-based search
DROP INDEX IF EXISTS idx_github_contribution_language;
CREATE INDEX idx_github_contribution_language 
ON github_contribution (LOWER(language))
WHERE language IS NOT NULL AND language != '';

\echo '✓ Created index on github_contribution.language'

-- Index for repository primary language
DROP INDEX IF EXISTS idx_github_repo_language;
CREATE INDEX IF NOT EXISTS idx_github_repo_language 
ON github_repository (LOWER(primary_language))
WHERE primary_language IS NOT NULL;

\echo '✓ Created index on github_repository.primary_language'

-- Composite index for technology search with person lookup
DROP INDEX IF EXISTS idx_github_contrib_person_language;
CREATE INDEX idx_github_contrib_person_language
ON github_contribution (github_profile_id, language)
WHERE language IS NOT NULL;

\echo '✓ Created composite index on github_contribution (profile_id, language)'

-- =============================================================================
-- COMPANY SEARCH INDEXES
-- =============================================================================

-- Index for company name search (case-insensitive)
DROP INDEX IF EXISTS idx_company_name_lower;
CREATE INDEX idx_company_name_lower 
ON company (LOWER(company_name));

\echo '✓ Created index on company.company_name (lowercase)'

-- Index for company name fuzzy search
DROP INDEX IF EXISTS idx_company_name_trgm;
CREATE INDEX idx_company_name_trgm 
ON company USING gin(company_name gin_trgm_ops);

\echo '✓ Created trigram index on company.company_name'

-- Composite index for employment by person and company
DROP INDEX IF EXISTS idx_employment_person_company;
CREATE INDEX IF NOT EXISTS idx_employment_person_company
ON employment (person_id, company_id);

\echo '✓ Created composite index on employment (person_id, company_id)'

-- =============================================================================
-- GITHUB REPOSITORY OWNERSHIP INDEXES
-- =============================================================================

-- Index for finding contributions by company ownership
DROP INDEX IF EXISTS idx_github_contrib_owner_company;
CREATE INDEX idx_github_contrib_owner_company
ON github_contribution (LOWER(owner_company_name))
WHERE owner_company_name IS NOT NULL;

\echo '✓ Created index on github_contribution.owner_company_name'

-- =============================================================================
-- FILTER INDEXES (email, GitHub presence, etc.)
-- =============================================================================

-- Index for email presence check (if not already exists)
DROP INDEX IF EXISTS idx_person_email_person_id;
CREATE INDEX IF NOT EXISTS idx_person_email_person_id 
ON person_email (person_id);

\echo '✓ Created index on person_email.person_id'

-- Index for GitHub profile presence check
DROP INDEX IF EXISTS idx_github_profile_person_id;
CREATE INDEX IF NOT EXISTS idx_github_profile_person_id 
ON github_profile (person_id);

\echo '✓ Created index on github_profile.person_id'

-- =============================================================================
-- LOCATION SEARCH INDEX
-- =============================================================================

-- Index for location filtering
DROP INDEX IF EXISTS idx_person_location;
CREATE INDEX idx_person_location 
ON person (LOWER(location))
WHERE location IS NOT NULL AND location != '';

\echo '✓ Created index on person.location'

-- =============================================================================
-- EXPERIENCE CALCULATION INDEXES
-- =============================================================================

-- Index for finding first job date (experience calculation)
DROP INDEX IF EXISTS idx_employment_person_start_date;
CREATE INDEX IF NOT EXISTS idx_employment_person_start_date
ON employment (person_id, start_date)
WHERE start_date IS NOT NULL;

\echo '✓ Created index on employment (person_id, start_date)'

-- Index for current employment lookup
DROP INDEX IF EXISTS idx_employment_current;
CREATE INDEX IF NOT EXISTS idx_employment_current
ON employment (person_id, end_date)
WHERE end_date IS NULL;

\echo '✓ Created index on employment for current jobs'

-- =============================================================================
-- STATISTICS INDEXES
-- =============================================================================

-- Index for technology statistics
DROP INDEX IF EXISTS idx_github_contrib_stats;
CREATE INDEX idx_github_contrib_stats
ON github_contribution (language, stars)
WHERE language IS NOT NULL;

\echo '✓ Created index for technology statistics'

COMMIT;

-- =============================================================================
-- ANALYZE TABLES
-- =============================================================================

-- Update statistics for query planner
ANALYZE person;
ANALYZE employment;
ANALYZE company;
ANALYZE github_profile;
ANALYZE github_contribution;
ANALYZE github_repository;
ANALYZE person_email;

\echo ''
\echo '========================================='
\echo 'Advanced Search Indexes Created Successfully'
\echo '========================================='
\echo ''
\echo 'Indexes created:'
\echo '  - Text search: title, headline, description, company name'
\echo '  - Technology: GitHub languages and contributions'
\echo '  - Company: employment history and repo ownership'
\echo '  - Filters: email, GitHub, location'
\echo '  - Performance: composite indexes for common queries'
\echo ''
\echo 'These indexes enable:'
\echo '  ✓ Fast technology/language filtering'
\echo '  ✓ Fuzzy text search on titles and keywords'  
\echo '  ✓ Company-based filtering (employment + repos)'
\echo '  ✓ Combined multi-criteria searches'
\echo '  ✓ Efficient autocomplete queries'
\echo ''

