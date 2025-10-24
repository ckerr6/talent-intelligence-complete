-- ============================================================================
-- Enhanced Notes for Recruiter Context
-- Makes person_notes searchable and AI-parseable with rich categorization
-- Created: 2025-10-24
-- ============================================================================

BEGIN;

-- Log migration start
INSERT INTO migration_log (migration_name, migration_phase, status, records_processed)
VALUES ('13_enhanced_notes', 'schema_enhancement', 'started', 0);

-- ============================================================================
-- PART 1: ENHANCE PERSON_NOTES TABLE
-- ============================================================================

-- Add metadata columns to person_notes
ALTER TABLE person_notes
  ADD COLUMN IF NOT EXISTS note_type TEXT DEFAULT 'general',
  ADD COLUMN IF NOT EXISTS note_category TEXT, -- 'call', 'meeting', 'screen', 'email', 'timing', 'context'
  ADD COLUMN IF NOT EXISTS priority TEXT DEFAULT 'normal', -- 'low', 'normal', 'high', 'urgent'
  ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS tags TEXT[], -- Array of custom tags
  ADD COLUMN IF NOT EXISTS metadata JSONB; -- Flexible storage for structured data

-- Add constraints (use DO block for IF NOT EXISTS behavior)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'check_note_type') THEN
    ALTER TABLE person_notes ADD CONSTRAINT check_note_type 
      CHECK (note_type IN ('general', 'call', 'meeting', 'screen', 'email', 'timing', 'reference', 'ai_generated'));
  END IF;
  
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'check_priority') THEN
    ALTER TABLE person_notes ADD CONSTRAINT check_priority
      CHECK (priority IN ('low', 'normal', 'high', 'urgent'));
  END IF;
END $$;

-- ============================================================================
-- PART 2: FULL-TEXT SEARCH
-- ============================================================================

-- Add tsvector column for full-text search
ALTER TABLE person_notes
  ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Create function to update search vector
CREATE OR REPLACE FUNCTION update_person_notes_search_vector()
RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector := 
    setweight(to_tsvector('english', COALESCE(NEW.note_text, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(array_to_string(NEW.tags, ' '), '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(NEW.note_category, '')), 'C');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-update search vector
DROP TRIGGER IF EXISTS person_notes_search_vector_update ON person_notes;
CREATE TRIGGER person_notes_search_vector_update
  BEFORE INSERT OR UPDATE ON person_notes
  FOR EACH ROW
  EXECUTE FUNCTION update_person_notes_search_vector();

-- Update existing notes
UPDATE person_notes SET updated_at = NOW();

-- Create GIN index for fast full-text search
CREATE INDEX IF NOT EXISTS idx_person_notes_search ON person_notes USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_person_notes_type ON person_notes(note_type);
CREATE INDEX IF NOT EXISTS idx_person_notes_category ON person_notes(note_category) WHERE note_category IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_person_notes_priority ON person_notes(priority) WHERE priority != 'normal';
CREATE INDEX IF NOT EXISTS idx_person_notes_pinned ON person_notes(is_pinned) WHERE is_pinned = TRUE;
CREATE INDEX IF NOT EXISTS idx_person_notes_tags ON person_notes USING GIN(tags) WHERE tags IS NOT NULL;

-- ============================================================================
-- PART 3: NOTE TEMPLATES & HELPERS
-- ============================================================================

-- Function to add a categorized note
CREATE OR REPLACE FUNCTION add_person_note(
  p_person_id UUID,
  p_user_id UUID,
  p_note_text TEXT,
  p_note_type TEXT DEFAULT 'general',
  p_note_category TEXT DEFAULT NULL,
  p_priority TEXT DEFAULT 'normal',
  p_tags TEXT[] DEFAULT NULL,
  p_metadata JSONB DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
  new_note_id UUID;
BEGIN
  INSERT INTO person_notes (
    person_id, user_id, note_text, note_type, note_category,
    priority, tags, metadata
  )
  VALUES (
    p_person_id, p_user_id, p_note_text, p_note_type, p_note_category,
    p_priority, p_tags, p_metadata
  )
  RETURNING note_id INTO new_note_id;
  
  RETURN new_note_id;
END;
$$ LANGUAGE plpgsql;

-- Function to search notes
CREATE OR REPLACE FUNCTION search_person_notes(
  search_query TEXT,
  p_person_id UUID DEFAULT NULL,
  p_note_type TEXT DEFAULT NULL,
  p_priority TEXT DEFAULT NULL,
  limit_count INT DEFAULT 50
)
RETURNS TABLE (
  note_id UUID,
  person_id UUID,
  person_name TEXT,
  note_text TEXT,
  note_type TEXT,
  note_category TEXT,
  priority TEXT,
  tags TEXT[],
  created_at TIMESTAMP,
  relevance FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    pn.note_id,
    pn.person_id,
    p.full_name as person_name,
    pn.note_text,
    pn.note_type,
    pn.note_category,
    pn.priority,
    pn.tags,
    pn.created_at,
    ts_rank(pn.search_vector, websearch_to_tsquery('english', search_query)) as relevance
  FROM person_notes pn
  JOIN person p ON pn.person_id = p.person_id
  WHERE pn.search_vector @@ websearch_to_tsquery('english', search_query)
  AND (p_person_id IS NULL OR pn.person_id = p_person_id)
  AND (p_note_type IS NULL OR pn.note_type = p_note_type)
  AND (p_priority IS NULL OR pn.priority = p_priority)
  ORDER BY relevance DESC, pn.created_at DESC
  LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PART 4: NOTE VIEWS FOR AI PARSING
-- ============================================================================

-- View: All candidate context for AI models
CREATE OR REPLACE VIEW v_candidate_full_context AS
WITH note_tags AS (
  SELECT 
    person_id,
    ARRAY_AGG(DISTINCT tag_elem) as all_tags
  FROM person_notes,
  LATERAL unnest(COALESCE(tags, ARRAY[]::TEXT[])) as tag_elem
  GROUP BY person_id
)
SELECT 
  p.person_id,
  p.full_name,
  p.headline,
  p.location,
  
  -- Aggregated notes as JSON array
  jsonb_agg(
    jsonb_build_object(
      'note_id', pn.note_id,
      'text', pn.note_text,
      'type', pn.note_type,
      'category', pn.note_category,
      'priority', pn.priority,
      'created_at', pn.created_at,
      'tags', pn.tags
    ) ORDER BY pn.created_at DESC
  ) FILTER (WHERE pn.note_id IS NOT NULL) as all_notes,
  
  -- All tags
  nt.all_tags,
  
  -- Most recent note
  (SELECT note_text FROM person_notes 
   WHERE person_id = p.person_id 
   ORDER BY created_at DESC LIMIT 1) as most_recent_note,
  
  -- Note count
  COUNT(pn.note_id) as total_notes,
  
  -- Has high priority notes
  BOOL_OR(pn.priority IN ('high', 'urgent')) as has_urgent_notes

FROM person p
LEFT JOIN person_notes pn ON p.person_id = pn.person_id
LEFT JOIN note_tags nt ON p.person_id = nt.person_id
GROUP BY p.person_id, p.full_name, p.headline, p.location, nt.all_tags;

-- View: Recruiter screen notes (for AI analysis)
CREATE OR REPLACE VIEW v_recruiter_screens AS
SELECT 
  p.person_id,
  p.full_name,
  pn.note_id,
  pn.note_text as screen_notes,
  pn.created_at as screen_date,
  pn.metadata,
  pn.tags,
  
  -- Extract structured data from metadata if present
  pn.metadata->>'timing' as candidate_timing,
  pn.metadata->>'location_pref' as location_preference,
  pn.metadata->>'comp_expectations' as comp_expectations,
  pn.metadata->>'availability' as availability
  
FROM person p
JOIN person_notes pn ON p.person_id = pn.person_id
WHERE pn.note_type = 'screen' OR pn.note_category = 'screen'
ORDER BY pn.created_at DESC;

-- ============================================================================
-- PART 5: UPDATE MIGRATION LOG
-- ============================================================================

UPDATE migration_log
SET 
  status = 'completed',
  completed_at = NOW(),
  records_created = (SELECT COUNT(*) FROM person_notes)
WHERE migration_name = '13_enhanced_notes'
AND migration_phase = 'schema_enhancement';

-- ============================================================================
-- PART 6: SUMMARY REPORT
-- ============================================================================

DO $$
DECLARE
  note_count INT;
BEGIN
  SELECT COUNT(*) INTO note_count FROM person_notes;
  
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Enhanced Notes System Complete!';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Enhancements:';
  RAISE NOTICE '  - Full-text search enabled';
  RAISE NOTICE '  - Note categorization (calls, screens, meetings)';
  RAISE NOTICE '  - Priority levels';
  RAISE NOTICE '  - Custom tags';
  RAISE NOTICE '  - JSONB metadata for structured data';
  RAISE NOTICE '';
  RAISE NOTICE 'Functions:';
  RAISE NOTICE '  - add_person_note(...)';
  RAISE NOTICE '  - search_person_notes(query)';
  RAISE NOTICE '';
  RAISE NOTICE 'Views for AI:';
  RAISE NOTICE '  - v_candidate_full_context';
  RAISE NOTICE '  - v_recruiter_screens';
  RAISE NOTICE '';
  RAISE NOTICE 'Existing notes: %', note_count;
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Ready for rich recruiter context!';
  RAISE NOTICE '========================================';
END $$;

COMMIT;

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

/*
-- Add a recruiter screen note
SELECT add_person_note(
  'person-uuid'::uuid,
  'user-uuid'::uuid,
  'Strong technical background. Interested in Series A startups. 
   Available in 2-3 weeks. Compensation expectations: $180-200K + equity.
   Prefers remote or SF Bay Area.',
  'screen',
  'recruiter_screen',
  'normal',
  ARRAY['solidity', 'defi', 'remote', 'available'],
  '{"timing": "2-3 weeks", "comp_expectations": "180-200K", 
    "location_pref": "remote/SF", "availability": "immediate"}'::jsonb
);

-- Search all notes
SELECT * FROM search_person_notes(
  'solidity developer available immediately',
  NULL,  -- any person
  NULL,  -- any type
  NULL,  -- any priority
  20     -- limit
);

-- Get full context for AI
SELECT * FROM v_candidate_full_context
WHERE person_id = 'some-uuid';

-- Find all recruiter screens
SELECT * FROM v_recruiter_screens
WHERE screen_date > NOW() - INTERVAL '30 days';
*/

