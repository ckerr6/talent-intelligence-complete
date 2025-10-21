-- ============================================================================
-- Ecosystem Schema Enhancement for PostgreSQL talent Database
-- Adds crypto ecosystem tracking capabilities
-- ============================================================================

-- Create crypto_ecosystem table
CREATE TABLE IF NOT EXISTS crypto_ecosystem (
    ecosystem_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ecosystem_name TEXT UNIQUE NOT NULL,
    parent_ecosystem_id UUID REFERENCES crypto_ecosystem(ecosystem_id) ON DELETE SET NULL,
    ecosystem_type TEXT, -- 'protocol', 'vc_portfolio', 'exchange', 'layer1', 'layer2', 'defi', 'nft', etc.
    description TEXT,
    tags TEXT[], -- Additional tags for categorization
    website_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT ecosystem_name_not_empty CHECK (length(trim(ecosystem_name)) > 0)
);

-- Indexes for crypto_ecosystem
CREATE INDEX IF NOT EXISTS idx_crypto_ecosystem_name ON crypto_ecosystem(lower(ecosystem_name));
CREATE INDEX IF NOT EXISTS idx_crypto_ecosystem_parent ON crypto_ecosystem(parent_ecosystem_id) WHERE parent_ecosystem_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_crypto_ecosystem_type ON crypto_ecosystem(ecosystem_type) WHERE ecosystem_type IS NOT NULL;

-- Link repositories to ecosystems (many-to-many)
CREATE TABLE IF NOT EXISTS ecosystem_repository (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ecosystem_id UUID NOT NULL REFERENCES crypto_ecosystem(ecosystem_id) ON DELETE CASCADE,
    repo_id UUID NOT NULL REFERENCES github_repository(repo_id) ON DELETE CASCADE,
    tags TEXT[], -- from crypto-ecosystems export (e.g., '#protocol', '#developer-tool')
    source TEXT DEFAULT 'crypto-ecosystems', -- Where this mapping came from
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(ecosystem_id, repo_id)
);

-- Indexes for ecosystem_repository
CREATE INDEX IF NOT EXISTS idx_ecosystem_repository_ecosystem ON ecosystem_repository(ecosystem_id);
CREATE INDEX IF NOT EXISTS idx_ecosystem_repository_repo ON ecosystem_repository(repo_id);

-- Link companies to ecosystems (many-to-many)
CREATE TABLE IF NOT EXISTS company_ecosystem (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES company(company_id) ON DELETE CASCADE,
    ecosystem_id UUID NOT NULL REFERENCES crypto_ecosystem(ecosystem_id) ON DELETE CASCADE,
    relationship_type TEXT, -- 'owner', 'contributor', 'portfolio_company', 'investor', 'core_team'
    confidence_score NUMERIC(3, 2) DEFAULT 1.0, -- 0.0 to 1.0 confidence in this relationship
    source TEXT, -- Where this relationship was discovered
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(company_id, ecosystem_id, relationship_type)
);

-- Indexes for company_ecosystem
CREATE INDEX IF NOT EXISTS idx_company_ecosystem_company ON company_ecosystem(company_id);
CREATE INDEX IF NOT EXISTS idx_company_ecosystem_ecosystem ON company_ecosystem(ecosystem_id);
CREATE INDEX IF NOT EXISTS idx_company_ecosystem_type ON company_ecosystem(relationship_type) WHERE relationship_type IS NOT NULL;

-- Track person activity in ecosystems (derived from contributions)
CREATE TABLE IF NOT EXISTS person_ecosystem_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES person(person_id) ON DELETE CASCADE,
    ecosystem_id UUID NOT NULL REFERENCES crypto_ecosystem(ecosystem_id) ON DELETE CASCADE,
    contribution_count INTEGER DEFAULT 0,
    repo_count INTEGER DEFAULT 0, -- how many repos in this ecosystem they've contributed to
    first_contribution_date DATE,
    last_contribution_date DATE,
    top_languages TEXT[], -- Their most used languages in this ecosystem
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(person_id, ecosystem_id)
);

-- Indexes for person_ecosystem_activity
CREATE INDEX IF NOT EXISTS idx_person_ecosystem_activity_person ON person_ecosystem_activity(person_id);
CREATE INDEX IF NOT EXISTS idx_person_ecosystem_activity_ecosystem ON person_ecosystem_activity(ecosystem_id);
CREATE INDEX IF NOT EXISTS idx_person_ecosystem_activity_contrib ON person_ecosystem_activity(contribution_count DESC);

-- Add ecosystem metadata to github_repository table
ALTER TABLE github_repository ADD COLUMN IF NOT EXISTS primary_ecosystem_id UUID REFERENCES crypto_ecosystem(ecosystem_id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_github_repository_ecosystem ON github_repository(primary_ecosystem_id) WHERE primary_ecosystem_id IS NOT NULL;

-- Add last_ecosystem_sync timestamp for tracking when we last updated ecosystem data
ALTER TABLE github_repository ADD COLUMN IF NOT EXISTS last_ecosystem_sync TIMESTAMP WITH TIME ZONE;

-- Create function to update person_ecosystem_activity
CREATE OR REPLACE FUNCTION update_person_ecosystem_activity()
RETURNS void AS $$
BEGIN
    -- Truncate and rebuild from current contribution data
    TRUNCATE person_ecosystem_activity;
    
    INSERT INTO person_ecosystem_activity (
        person_id,
        ecosystem_id,
        contribution_count,
        repo_count,
        first_contribution_date,
        last_contribution_date
    )
    SELECT 
        gp.person_id,
        er.ecosystem_id,
        SUM(gc.contribution_count) as contribution_count,
        COUNT(DISTINCT gc.repo_id) as repo_count,
        MIN(gc.first_contribution_date) as first_contribution_date,
        MAX(gc.last_contribution_date) as last_contribution_date
    FROM github_contribution gc
    JOIN github_profile gp ON gc.github_profile_id = gp.github_profile_id
    JOIN ecosystem_repository er ON gc.repo_id = er.repo_id
    WHERE gp.person_id IS NOT NULL
    GROUP BY gp.person_id, er.ecosystem_id
    ON CONFLICT (person_id, ecosystem_id) DO UPDATE SET
        contribution_count = EXCLUDED.contribution_count,
        repo_count = EXCLUDED.repo_count,
        first_contribution_date = EXCLUDED.first_contribution_date,
        last_contribution_date = EXCLUDED.last_contribution_date,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Create function to normalize ecosystem names (for matching)
CREATE OR REPLACE FUNCTION normalize_ecosystem_name(name TEXT) 
RETURNS TEXT AS $$
BEGIN
    IF name IS NULL OR trim(name) = '' THEN
        RETURN NULL;
    END IF;
    
    -- Convert to lowercase
    name := lower(trim(name));
    
    -- Remove common suffixes/prefixes
    name := regexp_replace(name, '\s+(labs?|inc\.?|llc|ltd\.?|foundation|protocol|network)$', '', 'i');
    
    -- Remove special characters but keep spaces
    name := regexp_replace(name, '[^a-z0-9\s]', '', 'g');
    
    -- Collapse multiple spaces to single space
    name := regexp_replace(name, '\s+', ' ', 'g');
    
    RETURN trim(name);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Add normalized_name column to crypto_ecosystem
ALTER TABLE crypto_ecosystem ADD COLUMN IF NOT EXISTS normalized_name TEXT;
CREATE INDEX IF NOT EXISTS idx_crypto_ecosystem_normalized ON crypto_ecosystem(normalized_name) WHERE normalized_name IS NOT NULL;

-- Create view for ecosystem statistics
CREATE OR REPLACE VIEW ecosystem_statistics AS
SELECT 
    e.ecosystem_id,
    e.ecosystem_name,
    e.ecosystem_type,
    COUNT(DISTINCT er.repo_id) as repo_count,
    COUNT(DISTINCT ce.company_id) as company_count,
    COUNT(DISTINCT pea.person_id) as contributor_count,
    COALESCE(SUM(pea.contribution_count), 0) as total_contributions,
    MAX(pea.last_contribution_date) as last_activity_date
FROM crypto_ecosystem e
LEFT JOIN ecosystem_repository er ON e.ecosystem_id = er.ecosystem_id
LEFT JOIN company_ecosystem ce ON e.ecosystem_id = ce.ecosystem_id
LEFT JOIN person_ecosystem_activity pea ON e.ecosystem_id = pea.ecosystem_id
GROUP BY e.ecosystem_id, e.ecosystem_name, e.ecosystem_type;

-- Log migration completion
INSERT INTO migration_log (migration_name, migration_phase, status, records_created)
VALUES ('02_ecosystem_schema', 'schema', 'completed', 0)
ON CONFLICT DO NOTHING;

-- Comments for documentation
COMMENT ON TABLE crypto_ecosystem IS 'Crypto ecosystems (protocols, VC portfolios, etc.)';
COMMENT ON TABLE ecosystem_repository IS 'Many-to-many mapping of ecosystems to repositories';
COMMENT ON TABLE company_ecosystem IS 'Many-to-many mapping of companies to ecosystems';
COMMENT ON TABLE person_ecosystem_activity IS 'Tracks developer activity across ecosystems (derived from contributions)';
COMMENT ON FUNCTION update_person_ecosystem_activity() IS 'Rebuilds person_ecosystem_activity from contribution data';
COMMENT ON FUNCTION normalize_ecosystem_name(TEXT) IS 'Normalizes ecosystem names for matching (lowercase, no special chars)';
COMMENT ON VIEW ecosystem_statistics IS 'Aggregate statistics for each ecosystem';

