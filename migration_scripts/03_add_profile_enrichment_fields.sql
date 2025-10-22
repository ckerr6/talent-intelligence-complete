-- ============================================================================
-- Add Profile Enrichment Fields for Personal Repository Data
-- Stores top languages and top repositories for each GitHub user
-- ============================================================================

-- Add JSON fields to store enriched repository data
ALTER TABLE github_profile 
ADD COLUMN IF NOT EXISTS top_languages JSONB,
ADD COLUMN IF NOT EXISTS top_repos JSONB;

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_github_profile_top_languages ON github_profile USING GIN (top_languages);
CREATE INDEX IF NOT EXISTS idx_github_profile_top_repos ON github_profile USING GIN (top_repos);

-- Add comments for documentation
COMMENT ON COLUMN github_profile.top_languages IS 'Languages used across user repositories with counts, e.g. {"Python": 25, "JavaScript": 15}';
COMMENT ON COLUMN github_profile.top_repos IS 'Top 5 most-starred personal repositories with metadata';

-- Example queries for using this data:

-- Find users who code in Python:
-- SELECT github_username, github_name, top_languages->'Python' as python_repos
-- FROM github_profile
-- WHERE top_languages ? 'Python'
-- ORDER BY (top_languages->>'Python')::int DESC;

-- Find users with popular projects (>100 stars):
-- SELECT github_username, github_name, top_repos
-- FROM github_profile, jsonb_array_elements(top_repos) as repo
-- WHERE (repo->>'stars')::int > 100;

-- Log migration
INSERT INTO migration_log (migration_name, migration_phase, status, records_created)
VALUES ('03_add_profile_enrichment_fields', 'schema', 'completed', 0)
ON CONFLICT DO NOTHING;

-- Show summary
SELECT 
    COUNT(*) as total_profiles,
    COUNT(top_languages) as profiles_with_languages,
    COUNT(top_repos) as profiles_with_repos
FROM github_profile;

