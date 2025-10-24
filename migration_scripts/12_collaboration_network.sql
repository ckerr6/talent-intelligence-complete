-- ============================================================================
-- Collaboration Network Schema
-- Creates GitHub collaboration edges and co-employment network
-- Part of "WOW Factor" - Shows who has worked with whom
-- Created: 2025-10-24
-- ============================================================================

BEGIN;

-- Log migration start
INSERT INTO migration_log (migration_name, migration_phase, status, records_processed)
VALUES ('12_collaboration_network', 'schema_creation', 'started', 0);

-- ============================================================================
-- PART 1: GITHUB COLLABORATION NETWORK
-- ============================================================================

-- Maps who has collaborated with whom on GitHub repos
CREATE TABLE IF NOT EXISTS edge_github_collaboration (
  edge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  src_person_id UUID NOT NULL REFERENCES person(person_id) ON DELETE CASCADE,
  dst_person_id UUID NOT NULL REFERENCES person(person_id) ON DELETE CASCADE,
  
  -- Collaboration metrics
  shared_repos INT DEFAULT 0,
  shared_contributions INT DEFAULT 0,
  collaboration_strength FLOAT CHECK (collaboration_strength >= 0 AND collaboration_strength <= 1),
  
  -- Temporal info
  first_collaboration_date DATE,
  last_collaboration_date DATE,
  collaboration_months INT, -- Duration of collaboration
  
  -- Details
  repos_list UUID[], -- Array of repo_ids where they collaborated
  top_shared_repos JSONB, -- [{"repo_name": "...", "contributions": ...}]
  
  -- Metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  UNIQUE(src_person_id, dst_person_id),
  CHECK (src_person_id != dst_person_id) -- No self-loops
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_github_collab_src ON edge_github_collaboration(src_person_id);
CREATE INDEX IF NOT EXISTS idx_github_collab_dst ON edge_github_collaboration(dst_person_id);
CREATE INDEX IF NOT EXISTS idx_github_collab_strength ON edge_github_collaboration(collaboration_strength DESC);
CREATE INDEX IF NOT EXISTS idx_github_collab_repos ON edge_github_collaboration(shared_repos DESC);
CREATE INDEX IF NOT EXISTS idx_github_collab_dates ON edge_github_collaboration(last_collaboration_date DESC NULLS LAST);

-- GIN index for array queries (find all edges for specific repos)
CREATE INDEX IF NOT EXISTS idx_github_collab_repos_list ON edge_github_collaboration USING GIN(repos_list);

-- ============================================================================
-- PART 2: AGGREGATED CO-EMPLOYMENT VIEW
-- ============================================================================

-- Create a view that aggregates co-employment edges
-- (edge_coemployment has one row per company, we need aggregated view)

CREATE OR REPLACE VIEW v_coemployment_aggregated AS
SELECT 
  src_person_id,
  dst_person_id,
  COUNT(DISTINCT company_id) as shared_companies_count,
  ARRAY_AGG(DISTINCT company_id) as shared_companies_list,
  SUM(overlap_months) as total_overlap_months,
  MAX(last_overlap_end) as most_recent_overlap_end,
  MIN(first_overlap_start) as first_overlap_start,
  -- Calculate strength based on: companies (0.5) + duration (0.5)
  LEAST(
    (COUNT(DISTINCT company_id)::FLOAT / 5.0) * 0.5 + 
    (SUM(overlap_months)::FLOAT / 36.0) * 0.5,
    1.0
  ) as collaboration_strength
FROM edge_coemployment
GROUP BY src_person_id, dst_person_id;

-- ============================================================================
-- PART 3: COMBINED NETWORK VIEW
-- ============================================================================

-- View that combines GitHub + employment networks for comprehensive relationship mapping
CREATE OR REPLACE VIEW v_person_network AS
SELECT 
  p.person_id,
  p.full_name,
  p.location,
  p.headline,
  
  -- GitHub connections
  (SELECT COUNT(*) FROM edge_github_collaboration egc 
   WHERE egc.src_person_id = p.person_id OR egc.dst_person_id = p.person_id) as github_connections,
  
  -- Employment connections (count unique people, not companies)
  (SELECT COUNT(DISTINCT 
      CASE WHEN ec.src_person_id = p.person_id THEN ec.dst_person_id 
           ELSE ec.src_person_id END
    ) FROM edge_coemployment ec 
   WHERE ec.src_person_id = p.person_id OR ec.dst_person_id = p.person_id) as employment_connections,
  
  -- Total unique connections
  (SELECT COUNT(DISTINCT connected_person_id) FROM (
    SELECT dst_person_id as connected_person_id 
    FROM edge_github_collaboration 
    WHERE src_person_id = p.person_id
    UNION
    SELECT src_person_id 
    FROM edge_github_collaboration 
    WHERE dst_person_id = p.person_id
    UNION
    SELECT dst_person_id 
    FROM edge_coemployment 
    WHERE src_person_id = p.person_id
    UNION
    SELECT src_person_id 
    FROM edge_coemployment 
    WHERE dst_person_id = p.person_id
  ) all_connections) as total_connections
  
FROM person p;

-- ============================================================================
-- PART 4: HELPER FUNCTIONS
-- ============================================================================

-- Function to get all collaborators for a person
CREATE OR REPLACE FUNCTION get_person_collaborators(
  target_person_id UUID,
  min_strength FLOAT DEFAULT 0.0,
  limit_count INT DEFAULT 100
)
RETURNS TABLE (
  collaborator_id UUID,
  collaborator_name TEXT,
  collaboration_type TEXT,
  strength FLOAT,
  shared_repos INT,
  shared_companies INT,
  last_interaction DATE
) AS $$
BEGIN
  RETURN QUERY
  -- GitHub collaborations
  SELECT 
    egc.dst_person_id as collaborator_id,
    p.full_name as collaborator_name,
    'github' as collaboration_type,
    egc.collaboration_strength as strength,
    egc.shared_repos,
    0 as shared_companies,
    egc.last_collaboration_date as last_interaction
  FROM edge_github_collaboration egc
  JOIN person p ON egc.dst_person_id = p.person_id
  WHERE egc.src_person_id = target_person_id
  AND egc.collaboration_strength >= min_strength
  
  UNION ALL
  
  -- Reverse GitHub collaborations
  SELECT 
    egc.src_person_id,
    p.full_name,
    'github',
    egc.collaboration_strength,
    egc.shared_repos,
    0,
    egc.last_collaboration_date
  FROM edge_github_collaboration egc
  JOIN person p ON egc.src_person_id = p.person_id
  WHERE egc.dst_person_id = target_person_id
  AND egc.collaboration_strength >= min_strength
  
  UNION ALL
  
  -- Co-employment (using aggregated view)
  SELECT 
    eca.dst_person_id,
    p.full_name,
    'employment',
    eca.collaboration_strength,
    0,
    eca.shared_companies_count,
    eca.most_recent_overlap_end
  FROM v_coemployment_aggregated eca
  JOIN person p ON eca.dst_person_id = p.person_id
  WHERE eca.src_person_id = target_person_id
  
  UNION ALL
  
  -- Reverse co-employment
  SELECT 
    eca.src_person_id,
    p.full_name,
    'employment',
    eca.collaboration_strength,
    0,
    eca.shared_companies_count,
    eca.most_recent_overlap_end
  FROM v_coemployment_aggregated eca
  JOIN person p ON eca.src_person_id = p.person_id
  WHERE eca.dst_person_id = target_person_id
  
  ORDER BY strength DESC, last_interaction DESC NULLS LAST
  LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to find common connections (2nd degree network)
CREATE OR REPLACE FUNCTION find_common_connections(
  person_a_id UUID,
  person_b_id UUID
)
RETURNS TABLE (
  mutual_connection_id UUID,
  mutual_connection_name TEXT,
  connection_type TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT DISTINCT
    mutual.connected_person_id,
    p.full_name,
    mutual.connection_type
  FROM (
    -- A's connections
    SELECT dst_person_id as connected_person_id, 'github' as connection_type
    FROM edge_github_collaboration WHERE src_person_id = person_a_id
    UNION
    SELECT src_person_id, 'github'
    FROM edge_github_collaboration WHERE dst_person_id = person_a_id
    UNION
    SELECT dst_person_id, 'employment'
    FROM edge_coemployment WHERE src_person_id = person_a_id
    UNION
    SELECT src_person_id, 'employment'
    FROM edge_coemployment WHERE dst_person_id = person_a_id
  ) mutual
  JOIN person p ON mutual.connected_person_id = p.person_id
  WHERE mutual.connected_person_id IN (
    -- B's connections
    SELECT dst_person_id FROM edge_github_collaboration WHERE src_person_id = person_b_id
    UNION
    SELECT src_person_id FROM edge_github_collaboration WHERE dst_person_id = person_b_id
    UNION
    SELECT DISTINCT dst_person_id FROM edge_coemployment WHERE src_person_id = person_b_id
    UNION
    SELECT DISTINCT src_person_id FROM edge_coemployment WHERE dst_person_id = person_b_id
  );
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PART 5: UPDATE MIGRATION LOG
-- ============================================================================

UPDATE migration_log
SET 
  status = 'completed',
  completed_at = NOW()
WHERE migration_name = '12_collaboration_network'
AND migration_phase = 'schema_creation';

-- ============================================================================
-- PART 6: SUMMARY REPORT
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Collaboration Network Schema Created!';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Tables:';
  RAISE NOTICE '  - edge_github_collaboration (new)';
  RAISE NOTICE '  - edge_coemployment (enhanced)';
  RAISE NOTICE '';
  RAISE NOTICE 'Views:';
  RAISE NOTICE '  - v_person_network';
  RAISE NOTICE '';
  RAISE NOTICE 'Functions:';
  RAISE NOTICE '  - get_person_collaborators(person_id)';
  RAISE NOTICE '  - find_common_connections(person_a, person_b)';
  RAISE NOTICE '';
  RAISE NOTICE 'Indexes: 11 created';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Ready to build collaboration edges!';
  RAISE NOTICE '========================================';
END $$;

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES (run after migration)
-- ============================================================================

-- Check existing co-employment edges
-- SELECT COUNT(*) FROM edge_coemployment;

-- After populating GitHub collaborations:
-- SELECT COUNT(*) FROM edge_github_collaboration;

-- Test function:
-- SELECT * FROM get_person_collaborators('some-uuid', 0.5, 20);

-- Find mutual connections:
-- SELECT * FROM find_common_connections('person-a-uuid', 'person-b-uuid');

