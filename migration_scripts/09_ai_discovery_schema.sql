-- AI Discovery System Schema Migration
-- Created: 2025-10-24
-- Purpose: Add tables and columns for AI-powered GitHub discovery and ecosystem tracking

-- ============================================================================
-- PART 1: CREATE NEW TABLES
-- ============================================================================

-- Discovery Source Table
-- Tracks where entities (repos, people, companies) were discovered
CREATE TABLE IF NOT EXISTS discovery_source (
    source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT NOT NULL CHECK (source_type IN (
        'electric_capital_taxonomy',
        'ethereum_eip',
        'paradigm_ecosystem',
        'contributor_expansion',
        'ai_discovery',
        'manual_import',
        'orbit_discovery'
    )),
    source_name TEXT NOT NULL,
    source_url TEXT,
    priority_tier INTEGER NOT NULL DEFAULT 5 CHECK (priority_tier BETWEEN 1 AND 5),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_source_name_type UNIQUE(source_name, source_type)
);

CREATE INDEX idx_discovery_source_type ON discovery_source(source_type);
CREATE INDEX idx_discovery_source_priority ON discovery_source(priority_tier);
CREATE INDEX idx_discovery_source_metadata ON discovery_source USING GIN(metadata);

COMMENT ON TABLE discovery_source IS 'Tracks where entities were discovered (Electric Capital, EIPs, orbit expansion, etc.)';
COMMENT ON COLUMN discovery_source.priority_tier IS '1=highest priority (Ethereum, Paradigm), 5=lowest';

-- ============================================================================

-- Entity Discovery Table
-- Tracks individual discovery events with lineage
CREATE TABLE IF NOT EXISTS entity_discovery (
    discovery_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL CHECK (entity_type IN ('person', 'repository', 'company')),
    entity_id UUID NOT NULL,
    source_id UUID NOT NULL REFERENCES discovery_source(source_id) ON DELETE CASCADE,
    discovered_via_id UUID,
    discovery_method TEXT NOT NULL,
    discovery_metadata JSONB DEFAULT '{}',
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_entity_discovery UNIQUE(entity_type, entity_id, source_id)
);

CREATE INDEX idx_entity_discovery_entity ON entity_discovery(entity_type, entity_id);
CREATE INDEX idx_entity_discovery_source ON entity_discovery(source_id);
CREATE INDEX idx_entity_discovery_via ON entity_discovery(discovered_via_id);
CREATE INDEX idx_entity_discovery_method ON entity_discovery(discovery_method);
CREATE INDEX idx_entity_discovery_metadata ON entity_discovery USING GIN(discovery_metadata);

COMMENT ON TABLE entity_discovery IS 'Individual discovery events with full lineage tracking';
COMMENT ON COLUMN entity_discovery.discovered_via_id IS 'Parent entity that led to this discovery (e.g., repo that led to person)';
COMMENT ON COLUMN entity_discovery.discovery_method IS 'How discovered: taxonomy_import, contributor_scrape, orbit_expansion, etc.';

-- ============================================================================

-- Repository Relationship Table
-- Tracks connections between repositories
CREATE TABLE IF NOT EXISTS repository_relationship (
    relationship_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id_from UUID NOT NULL REFERENCES github_repository(repo_id) ON DELETE CASCADE,
    repo_id_to UUID NOT NULL REFERENCES github_repository(repo_id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL CHECK (relationship_type IN (
        'fork',
        'dependency',
        'same_ecosystem',
        'contributor_overlap',
        'org_sibling',
        'mentioned_in_docs'
    )),
    strength_score FLOAT CHECK (strength_score BETWEEN 0 AND 1),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_repo_relationship UNIQUE(repo_id_from, repo_id_to, relationship_type),
    CONSTRAINT no_self_relationship CHECK (repo_id_from != repo_id_to)
);

CREATE INDEX idx_repo_relationship_from ON repository_relationship(repo_id_from);
CREATE INDEX idx_repo_relationship_to ON repository_relationship(repo_id_to);
CREATE INDEX idx_repo_relationship_type ON repository_relationship(relationship_type);
CREATE INDEX idx_repo_relationship_strength ON repository_relationship(strength_score DESC);

COMMENT ON TABLE repository_relationship IS 'Tracks relationships between repositories for network analysis';
COMMENT ON COLUMN repository_relationship.strength_score IS 'Relationship strength 0-1 based on contributor overlap, activity, etc.';

-- ============================================================================

-- Crypto Ecosystem Table
-- Organizes repos and people into crypto ecosystems
CREATE TABLE IF NOT EXISTS crypto_ecosystem (
    ecosystem_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ecosystem_name TEXT NOT NULL UNIQUE,
    normalized_name TEXT NOT NULL,
    parent_ecosystem_id UUID REFERENCES crypto_ecosystem(ecosystem_id) ON DELETE SET NULL,
    description TEXT,
    official_repos TEXT[] DEFAULT '{}',
    taxonomy_source TEXT,
    priority_score INTEGER NOT NULL DEFAULT 5 CHECK (priority_score BETWEEN 1 AND 5),
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    repo_count INTEGER DEFAULT 0,
    developer_count INTEGER DEFAULT 0,
    total_stars INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_crypto_ecosystem_name ON crypto_ecosystem(ecosystem_name);
CREATE INDEX idx_crypto_ecosystem_normalized ON crypto_ecosystem(normalized_name);
CREATE INDEX idx_crypto_ecosystem_parent ON crypto_ecosystem(parent_ecosystem_id);
CREATE INDEX idx_crypto_ecosystem_priority ON crypto_ecosystem(priority_score);
CREATE INDEX idx_crypto_ecosystem_tags ON crypto_ecosystem USING GIN(tags);
CREATE INDEX idx_crypto_ecosystem_repos ON crypto_ecosystem USING GIN(official_repos);

COMMENT ON TABLE crypto_ecosystem IS 'Crypto/blockchain ecosystems from Electric Capital taxonomy and manual curation';
COMMENT ON COLUMN crypto_ecosystem.normalized_name IS 'Lowercase name for matching (e.g., "ethereum", "uniswap")';
COMMENT ON COLUMN crypto_ecosystem.priority_score IS '1=highest priority (Ethereum, major L2s), 5=lowest';

-- ============================================================================
-- PART 2: ENHANCE EXISTING TABLES
-- ============================================================================

-- Enhance github_repository table
ALTER TABLE github_repository 
    ADD COLUMN IF NOT EXISTS ecosystem_ids UUID[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS importance_score FLOAT DEFAULT 0 CHECK (importance_score >= 0),
    ADD COLUMN IF NOT EXISTS last_contributor_sync TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS contributor_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS discovery_source_id UUID REFERENCES discovery_source(source_id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_github_repository_ecosystems ON github_repository USING GIN(ecosystem_ids);
CREATE INDEX IF NOT EXISTS idx_github_repository_importance ON github_repository(importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_github_repository_contributor_sync ON github_repository(last_contributor_sync);
CREATE INDEX IF NOT EXISTS idx_github_repository_discovery_source ON github_repository(discovery_source_id);

COMMENT ON COLUMN github_repository.ecosystem_ids IS 'Array of ecosystem UUIDs this repo belongs to';
COMMENT ON COLUMN github_repository.importance_score IS 'Computed importance based on stars, activity, ecosystem relevance';
COMMENT ON COLUMN github_repository.last_contributor_sync IS 'When contributors were last discovered for this repo';
COMMENT ON COLUMN github_repository.contributor_count IS 'Cached count of contributors';

-- ============================================================================

-- Enhance github_profile table
ALTER TABLE github_profile
    ADD COLUMN IF NOT EXISTS ecosystem_tags TEXT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS importance_score FLOAT DEFAULT 0 CHECK (importance_score >= 0),
    ADD COLUMN IF NOT EXISTS discovery_source_id UUID REFERENCES discovery_source(source_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS orbit_of UUID[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS specialties TEXT[] DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_github_profile_ecosystem_tags ON github_profile USING GIN(ecosystem_tags);
CREATE INDEX IF NOT EXISTS idx_github_profile_importance ON github_profile(importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_github_profile_discovery_source ON github_profile(discovery_source_id);
CREATE INDEX IF NOT EXISTS idx_github_profile_orbit ON github_profile USING GIN(orbit_of);
CREATE INDEX IF NOT EXISTS idx_github_profile_specialties ON github_profile USING GIN(specialties);

COMMENT ON COLUMN github_profile.ecosystem_tags IS 'Tags like ["ethereum", "defi", "eip-author", "paradigm-ecosystem"]';
COMMENT ON COLUMN github_profile.importance_score IS 'Computed importance based on contributions, PRs, ecosystem involvement';
COMMENT ON COLUMN github_profile.orbit_of IS 'Array of github_profile_ids this person is in the orbit of';
COMMENT ON COLUMN github_profile.specialties IS 'AI-detected specialties like ["smart-contracts", "protocol-development"]';

-- ============================================================================

-- Enhance company table
ALTER TABLE company
    ADD COLUMN IF NOT EXISTS ecosystem_tags TEXT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS discovery_source_id UUID REFERENCES discovery_source(source_id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_company_ecosystem_tags ON company USING GIN(ecosystem_tags);
CREATE INDEX IF NOT EXISTS idx_company_discovery_source ON company(discovery_source_id);

COMMENT ON COLUMN company.ecosystem_tags IS 'Ecosystems company is part of like ["ethereum", "defi"]';

-- ============================================================================

-- Enhance github_contribution table
ALTER TABLE github_contribution
    ADD COLUMN IF NOT EXISTS contribution_type TEXT DEFAULT 'contributor' 
        CHECK (contribution_type IN ('owner', 'contributor', 'core_team', 'occasional'));

CREATE INDEX IF NOT EXISTS idx_github_contribution_type ON github_contribution(contribution_type);

COMMENT ON COLUMN github_contribution.contribution_type IS 'Type of contribution: owner, contributor, core_team, occasional';

-- ============================================================================
-- PART 3: CREATE HELPER FUNCTIONS
-- ============================================================================

-- Function to update ecosystem counts
CREATE OR REPLACE FUNCTION update_ecosystem_counts()
RETURNS TRIGGER AS $$
BEGIN
    -- Update repo count
    UPDATE crypto_ecosystem e
    SET repo_count = (
        SELECT COUNT(DISTINCT r.repo_id)
        FROM github_repository r
        WHERE e.ecosystem_id = ANY(r.ecosystem_ids)
    ),
    developer_count = (
        SELECT COUNT(DISTINCT gp.github_profile_id)
        FROM github_profile gp
        WHERE e.normalized_name = ANY(gp.ecosystem_tags)
    ),
    total_stars = (
        SELECT COALESCE(SUM(r.stars), 0)
        FROM github_repository r
        WHERE e.ecosystem_id = ANY(r.ecosystem_ids)
    )
    WHERE e.ecosystem_id = NEW.ecosystem_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update ecosystem counts
CREATE TRIGGER trigger_update_ecosystem_counts
    AFTER INSERT OR UPDATE ON crypto_ecosystem
    FOR EACH ROW
    EXECUTE FUNCTION update_ecosystem_counts();

-- ============================================================================

-- Function to compute repository importance score
CREATE OR REPLACE FUNCTION compute_repository_importance(repo_id_param UUID)
RETURNS FLOAT AS $$
DECLARE
    score FLOAT := 0;
    repo_record RECORD;
BEGIN
    SELECT r.stars, r.forks, r.contributor_count, r.ecosystem_ids,
           EXTRACT(EPOCH FROM (NOW() - r.last_pushed_at)) / 86400 AS days_since_push
    INTO repo_record
    FROM github_repository r
    WHERE r.repo_id = repo_id_param;
    
    IF repo_record IS NULL THEN
        RETURN 0;
    END IF;
    
    -- Stars (max 50 points)
    score := score + LEAST(repo_record.stars / 100.0, 50);
    
    -- Forks (max 20 points)
    score := score + LEAST(repo_record.forks / 50.0, 20);
    
    -- Contributors (max 20 points)
    score := score + LEAST(repo_record.contributor_count / 10.0, 20);
    
    -- Ecosystem membership (10 points if in any ecosystem)
    IF array_length(repo_record.ecosystem_ids, 1) > 0 THEN
        score := score + 10;
    END IF;
    
    -- Recent activity bonus (max 10 points, decays over 365 days)
    IF repo_record.days_since_push IS NOT NULL THEN
        score := score + GREATEST(10 - (repo_record.days_since_push / 36.5), 0);
    END IF;
    
    RETURN LEAST(score, 100);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================

-- Function to compute developer importance score
CREATE OR REPLACE FUNCTION compute_developer_importance(profile_id_param UUID)
RETURNS FLOAT AS $$
DECLARE
    score FLOAT := 0;
    profile_record RECORD;
BEGIN
    SELECT 
        gp.followers,
        gp.total_merged_prs,
        gp.total_lines_contributed,
        gp.ecosystem_tags,
        array_length(gp.orbit_of, 1) AS orbit_count,
        (SELECT COUNT(*) FROM github_contribution gc WHERE gc.github_profile_id = gp.github_profile_id) AS repo_count
    INTO profile_record
    FROM github_profile gp
    WHERE gp.github_profile_id = profile_id_param;
    
    IF profile_record IS NULL THEN
        RETURN 0;
    END IF;
    
    -- Followers (max 20 points)
    score := score + LEAST(profile_record.followers / 50.0, 20);
    
    -- Merged PRs (max 30 points)
    score := score + LEAST(profile_record.total_merged_prs / 10.0, 30);
    
    -- Lines of code (max 20 points)
    score := score + LEAST(profile_record.total_lines_contributed / 5000.0, 20);
    
    -- Repo contributions (max 15 points)
    score := score + LEAST(profile_record.repo_count / 5.0, 15);
    
    -- Ecosystem tags (5 points per ecosystem, max 15)
    IF array_length(profile_record.ecosystem_tags, 1) > 0 THEN
        score := score + LEAST(array_length(profile_record.ecosystem_tags, 1) * 5, 15);
    END IF;
    
    -- Orbit connections (5 points if in orbit of notable devs)
    IF profile_record.orbit_count > 0 THEN
        score := score + 5;
    END IF;
    
    RETURN LEAST(score, 100);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PART 4: CREATE VIEWS FOR EASY QUERYING
-- ============================================================================

-- View: Top Ecosystems by Activity
CREATE OR REPLACE VIEW v_top_ecosystems AS
SELECT 
    e.ecosystem_id,
    e.ecosystem_name,
    e.priority_score,
    e.repo_count,
    e.developer_count,
    e.total_stars,
    e.tags,
    ds.source_name AS discovered_via,
    ds.priority_tier
FROM crypto_ecosystem e
LEFT JOIN discovery_source ds ON e.taxonomy_source = ds.source_name
ORDER BY e.priority_score ASC, e.total_stars DESC;

-- View: Top Repositories by Importance
CREATE OR REPLACE VIEW v_top_repositories AS
SELECT 
    r.repo_id,
    r.full_name,
    r.description,
    r.stars,
    r.forks,
    r.contributor_count,
    r.importance_score,
    r.ecosystem_ids,
    (SELECT array_agg(e.ecosystem_name) 
     FROM crypto_ecosystem e 
     WHERE e.ecosystem_id = ANY(r.ecosystem_ids)) AS ecosystem_names,
    ds.source_name AS discovered_via,
    ds.priority_tier
FROM github_repository r
LEFT JOIN discovery_source ds ON r.discovery_source_id = ds.source_id
WHERE r.importance_score > 0
ORDER BY r.importance_score DESC;

-- View: Top Developers by Importance
CREATE OR REPLACE VIEW v_top_developers AS
SELECT 
    gp.github_profile_id,
    gp.github_username,
    gp.github_name,
    gp.followers,
    gp.total_merged_prs,
    gp.importance_score,
    gp.ecosystem_tags,
    gp.specialties,
    (SELECT COUNT(*) FROM github_contribution gc WHERE gc.github_profile_id = gp.github_profile_id) AS repo_count,
    ds.source_name AS discovered_via,
    p.full_name,
    p.person_id
FROM github_profile gp
LEFT JOIN discovery_source ds ON gp.discovery_source_id = ds.source_id
LEFT JOIN person p ON gp.person_id = p.person_id
WHERE gp.importance_score > 0
ORDER BY gp.importance_score DESC;

-- View: Discovery Statistics
CREATE OR REPLACE VIEW v_discovery_stats AS
SELECT 
    ds.source_id,
    ds.source_type,
    ds.source_name,
    ds.priority_tier,
    COUNT(DISTINCT ed.discovery_id) AS total_discoveries,
    COUNT(DISTINCT CASE WHEN ed.entity_type = 'repository' THEN ed.entity_id END) AS repos_discovered,
    COUNT(DISTINCT CASE WHEN ed.entity_type = 'person' THEN ed.entity_id END) AS people_discovered,
    COUNT(DISTINCT CASE WHEN ed.entity_type = 'company' THEN ed.entity_id END) AS companies_discovered,
    MIN(ed.discovered_at) AS first_discovery,
    MAX(ed.discovered_at) AS last_discovery
FROM discovery_source ds
LEFT JOIN entity_discovery ed ON ds.source_id = ed.source_id
GROUP BY ds.source_id, ds.source_type, ds.source_name, ds.priority_tier
ORDER BY ds.priority_tier, total_discoveries DESC;

-- ============================================================================
-- PART 5: INSERT SEED DATA
-- ============================================================================

-- Insert primary discovery sources
INSERT INTO discovery_source (source_type, source_name, source_url, priority_tier, metadata) VALUES
    ('electric_capital_taxonomy', 'Electric Capital Crypto Ecosystems', 'https://github.com/electric-capital/crypto-ecosystems', 1, '{"description": "Comprehensive crypto ecosystem taxonomy"}'),
    ('ethereum_eip', 'Ethereum EIPs', 'https://github.com/ethereum/EIPs', 1, '{"description": "Ethereum Improvement Proposals repository"}'),
    ('paradigm_ecosystem', 'Paradigm Ecosystem', 'https://github.com/paradigmxyz', 1, '{"description": "Paradigm research and tooling repositories"}'),
    ('manual_import', 'Manual Import', NULL, 1, '{"description": "Manually curated high-priority repositories"}'),
    ('contributor_expansion', 'Contributor Expansion', NULL, 2, '{"description": "Discovered via contributor analysis"}'),
    ('orbit_discovery', 'Orbit Discovery', NULL, 2, '{"description": "Found in orbit of notable developers"}'),
    ('ai_discovery', 'AI Discovery', NULL, 3, '{"description": "Discovered and scored by AI analysis"}'::jsonb)
ON CONFLICT (source_name, source_type) DO NOTHING;

-- Insert seed ecosystems
INSERT INTO crypto_ecosystem (ecosystem_name, normalized_name, priority_score, taxonomy_source, tags) VALUES
    ('Ethereum', 'ethereum', 1, 'electric_capital_taxonomy', ARRAY['layer1', 'smart-contracts', 'evm']),
    ('Base', 'base', 1, 'electric_capital_taxonomy', ARRAY['layer2', 'ethereum', 'optimism']),
    ('Optimism', 'optimism', 1, 'electric_capital_taxonomy', ARRAY['layer2', 'ethereum']),
    ('Arbitrum', 'arbitrum', 1, 'electric_capital_taxonomy', ARRAY['layer2', 'ethereum']),
    ('Paradigm', 'paradigm', 1, 'manual', ARRAY['research', 'infrastructure', 'tooling']),
    ('Uniswap', 'uniswap', 2, 'electric_capital_taxonomy', ARRAY['defi', 'dex', 'ethereum']),
    ('DeFi', 'defi', 2, 'electric_capital_taxonomy', ARRAY['finance', 'protocols'])
ON CONFLICT (ecosystem_name) DO NOTHING;

-- ============================================================================

-- Update statistics
ANALYZE discovery_source;
ANALYZE entity_discovery;
ANALYZE repository_relationship;
ANALYZE crypto_ecosystem;
ANALYZE github_repository;
ANALYZE github_profile;
ANALYZE company;

-- ============================================================================

-- Print summary
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'AI Discovery Schema Migration Complete!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Created tables:';
    RAISE NOTICE '  - discovery_source';
    RAISE NOTICE '  - entity_discovery';
    RAISE NOTICE '  - repository_relationship';
    RAISE NOTICE '  - crypto_ecosystem';
    RAISE NOTICE '';
    RAISE NOTICE 'Enhanced tables:';
    RAISE NOTICE '  - github_repository (+ ecosystem_ids, importance_score, etc.)';
    RAISE NOTICE '  - github_profile (+ ecosystem_tags, orbit_of, etc.)';
    RAISE NOTICE '  - company (+ ecosystem_tags)';
    RAISE NOTICE '';
    RAISE NOTICE 'Created functions:';
    RAISE NOTICE '  - compute_repository_importance()';
    RAISE NOTICE '  - compute_developer_importance()';
    RAISE NOTICE '';
    RAISE NOTICE 'Created views:';
    RAISE NOTICE '  - v_top_ecosystems';
    RAISE NOTICE '  - v_top_repositories';
    RAISE NOTICE '  - v_top_developers';
    RAISE NOTICE '  - v_discovery_stats';
    RAISE NOTICE '';
    RAISE NOTICE 'Ready for AI-powered discovery! 🚀';
    RAISE NOTICE '========================================';
END $$;

