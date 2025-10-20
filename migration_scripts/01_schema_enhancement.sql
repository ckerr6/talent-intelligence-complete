-- ============================================================================
-- Schema Enhancement for PostgreSQL talent Database
-- Adds email and GitHub tracking capabilities
-- ============================================================================

-- Create person_email table for multiple emails per person
CREATE TABLE IF NOT EXISTS person_email (
    email_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES person(person_id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    email_type TEXT, -- 'work', 'personal', 'unknown'
    is_primary BOOLEAN DEFAULT FALSE,
    source TEXT, -- Where this email came from (e.g., 'sqlite_migration', 'manual', 'scrape')
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT email_not_empty CHECK (length(trim(email)) > 0)
);

-- Indexes for person_email
CREATE INDEX IF NOT EXISTS idx_person_email_person_id ON person_email(person_id);
CREATE INDEX IF NOT EXISTS idx_person_email_email ON person_email(lower(email));
CREATE UNIQUE INDEX IF NOT EXISTS idx_person_email_unique ON person_email(person_id, lower(email));

-- Create github_profile table
CREATE TABLE IF NOT EXISTS github_profile (
    github_profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID REFERENCES person(person_id) ON DELETE CASCADE,
    github_username TEXT UNIQUE NOT NULL,
    github_name TEXT,
    github_email TEXT,
    github_company TEXT,
    followers INTEGER DEFAULT 0,
    following INTEGER DEFAULT 0,
    public_repos INTEGER DEFAULT 0,
    bio TEXT,
    blog TEXT,
    twitter_username TEXT,
    location TEXT,
    hireable BOOLEAN,
    avatar_url TEXT,
    created_at_github TIMESTAMP WITH TIME ZONE,
    updated_at_github TIMESTAMP WITH TIME ZONE,
    last_enriched TIMESTAMP WITH TIME ZONE,
    source TEXT DEFAULT 'sqlite_migration',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT github_username_not_empty CHECK (length(trim(github_username)) > 0)
);

-- Indexes for github_profile
CREATE INDEX IF NOT EXISTS idx_github_profile_person_id ON github_profile(person_id);
CREATE INDEX IF NOT EXISTS idx_github_profile_username ON github_profile(lower(github_username));
CREATE INDEX IF NOT EXISTS idx_github_profile_email ON github_profile(lower(github_email)) WHERE github_email IS NOT NULL;

-- Create github_repository table (if doesn't exist)
CREATE TABLE IF NOT EXISTS github_repository (
    repo_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES company(company_id) ON DELETE SET NULL,
    repo_name TEXT NOT NULL,
    full_name TEXT UNIQUE NOT NULL,
    owner_username TEXT,
    language TEXT,
    stars INTEGER DEFAULT 0,
    forks INTEGER DEFAULT 0,
    description TEXT,
    homepage_url TEXT,
    is_fork BOOLEAN DEFAULT FALSE,
    created_at_github TIMESTAMP WITH TIME ZONE,
    updated_at_github TIMESTAMP WITH TIME ZONE,
    last_pushed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT repo_full_name_not_empty CHECK (length(trim(full_name)) > 0)
);

-- Indexes for github_repository
CREATE INDEX IF NOT EXISTS idx_github_repository_company_id ON github_repository(company_id);
CREATE INDEX IF NOT EXISTS idx_github_repository_owner ON github_repository(lower(owner_username));
CREATE INDEX IF NOT EXISTS idx_github_repository_language ON github_repository(language);

-- Create github_contribution table (links profiles to repos)
CREATE TABLE IF NOT EXISTS github_contribution (
    contribution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    github_profile_id UUID NOT NULL REFERENCES github_profile(github_profile_id) ON DELETE CASCADE,
    repo_id UUID NOT NULL REFERENCES github_repository(repo_id) ON DELETE CASCADE,
    contribution_count INTEGER DEFAULT 0,
    first_contribution_date DATE,
    last_contribution_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(github_profile_id, repo_id)
);

-- Indexes for github_contribution
CREATE INDEX IF NOT EXISTS idx_github_contribution_profile_id ON github_contribution(github_profile_id);
CREATE INDEX IF NOT EXISTS idx_github_contribution_repo_id ON github_contribution(repo_id);

-- Add normalized_linkedin_url column to person table for better matching
ALTER TABLE person ADD COLUMN IF NOT EXISTS normalized_linkedin_url TEXT;
CREATE INDEX IF NOT EXISTS idx_person_normalized_linkedin ON person(normalized_linkedin_url) WHERE normalized_linkedin_url IS NOT NULL;

-- Create function to update normalized LinkedIn URLs
CREATE OR REPLACE FUNCTION normalize_linkedin_url(url TEXT) 
RETURNS TEXT AS $$
BEGIN
    IF url IS NULL OR trim(url) = '' THEN
        RETURN NULL;
    END IF;
    
    -- Convert to lowercase
    url := lower(trim(url));
    
    -- URL decode (basic - for common cases)
    url := replace(url, '%2f', '/');
    url := replace(url, '%3a', ':');
    
    -- Remove protocol
    url := regexp_replace(url, '^https?://', '');
    
    -- Remove www.
    url := regexp_replace(url, '^www\.', '');
    
    -- Remove trailing slash
    url := regexp_replace(url, '/$', '');
    
    -- Extract just the linkedin.com/in/slug part
    IF url ~ 'linkedin\.com/in/' THEN
        url := regexp_replace(url, '.*linkedin\.com/in/([^/?]+).*', 'linkedin.com/in/\1');
    END IF;
    
    RETURN url;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Populate normalized_linkedin_url for existing records
UPDATE person 
SET normalized_linkedin_url = normalize_linkedin_url(linkedin_url)
WHERE linkedin_url IS NOT NULL 
AND (normalized_linkedin_url IS NULL OR normalized_linkedin_url = '');

-- Create migration tracking table
CREATE TABLE IF NOT EXISTS migration_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    migration_name TEXT NOT NULL,
    migration_phase TEXT, -- 'schema', 'email', 'github', 'deduplication', 'validation'
    status TEXT NOT NULL, -- 'started', 'completed', 'failed'
    records_processed INTEGER DEFAULT 0,
    records_created INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB
);

-- Create index on migration_log
CREATE INDEX IF NOT EXISTS idx_migration_log_name ON migration_log(migration_name);
CREATE INDEX IF NOT EXISTS idx_migration_log_phase ON migration_log(migration_phase);

-- Insert log entry for schema enhancement
INSERT INTO migration_log (migration_name, migration_phase, status)
VALUES ('schema_enhancement', 'schema', 'completed');

-- Grant permissions (adjust as needed for your user)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_user;

COMMENT ON TABLE person_email IS 'Stores multiple email addresses per person with type and verification status';
COMMENT ON TABLE github_profile IS 'GitHub profile data for people, migrated from SQLite and enriched via API';
COMMENT ON TABLE github_repository IS 'Repository information for companies and individuals';
COMMENT ON TABLE github_contribution IS 'Junction table linking GitHub profiles to repositories they contributed to';
COMMENT ON TABLE migration_log IS 'Tracks all migration operations for audit and debugging purposes';

-- Display schema enhancement summary
SELECT 
    'Schema Enhancement Complete' as status,
    COUNT(*) FILTER (WHERE table_name = 'person_email') as person_email_table,
    COUNT(*) FILTER (WHERE table_name = 'github_profile') as github_profile_table,
    COUNT(*) FILTER (WHERE table_name = 'github_repository') as github_repository_table,
    COUNT(*) FILTER (WHERE table_name = 'github_contribution') as github_contribution_table,
    COUNT(*) FILTER (WHERE table_name = 'migration_log') as migration_log_table
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('person_email', 'github_profile', 'github_repository', 'github_contribution', 'migration_log');

