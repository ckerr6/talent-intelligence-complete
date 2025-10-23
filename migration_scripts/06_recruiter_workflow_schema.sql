-- Migration: Recruiter Workflow Schema
-- Date: 2025-10-22
-- Purpose: Add tables for recruiter workflow features (lists, notes, tags, scoring, network caching)

-- Saved searches
CREATE TABLE IF NOT EXISTS saved_searches (
    search_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    name VARCHAR(255) NOT NULL,
    filters JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP
);

-- Candidate lists
CREATE TABLE IF NOT EXISTS candidate_lists (
    list_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS candidate_list_members (
    list_id UUID REFERENCES candidate_lists(list_id) ON DELETE CASCADE,
    person_id UUID REFERENCES person(person_id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    PRIMARY KEY (list_id, person_id)
);

-- Notes and tags
CREATE TABLE IF NOT EXISTS person_notes (
    note_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID REFERENCES person(person_id) ON DELETE CASCADE,
    user_id UUID,
    note_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS person_tags (
    person_id UUID REFERENCES person(person_id) ON DELETE CASCADE,
    tag VARCHAR(100) NOT NULL,
    tag_type VARCHAR(50) DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (person_id, tag)
);

-- Twitter profiles (for Phase 2+)
CREATE TABLE IF NOT EXISTS twitter_profile (
    twitter_id BIGINT PRIMARY KEY,
    person_id UUID REFERENCES person(person_id) ON DELETE SET NULL,
    username VARCHAR(100) NOT NULL,
    display_name VARCHAR(255),
    bio TEXT,
    followers_count INT,
    following_count INT,
    location VARCHAR(255),
    website VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Match scores
CREATE TABLE IF NOT EXISTS candidate_scores (
    score_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID REFERENCES person(person_id) ON DELETE CASCADE,
    job_description_hash VARCHAR(64),
    relevance_score FLOAT,
    code_quality_score FLOAT,
    reachability_score FLOAT,
    overall_score FLOAT,
    explanation JSONB,
    scored_at TIMESTAMP DEFAULT NOW()
);

-- Network path cache
CREATE TABLE IF NOT EXISTS network_paths (
    source_person_id UUID,
    target_person_id UUID,
    path_length INT,
    path_nodes JSONB,
    path_type VARCHAR(50),
    cached_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (source_person_id, target_person_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_saved_searches_user ON saved_searches(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_searches_last_used ON saved_searches(last_used DESC);

CREATE INDEX IF NOT EXISTS idx_candidate_lists_user ON candidate_lists(user_id);
CREATE INDEX IF NOT EXISTS idx_candidate_lists_updated ON candidate_lists(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_list_members_list ON candidate_list_members(list_id);
CREATE INDEX IF NOT EXISTS idx_list_members_person ON candidate_list_members(person_id);

CREATE INDEX IF NOT EXISTS idx_person_notes_person ON person_notes(person_id);
CREATE INDEX IF NOT EXISTS idx_person_notes_created ON person_notes(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_person_tags_person ON person_tags(person_id);
CREATE INDEX IF NOT EXISTS idx_person_tags_tag ON person_tags(tag);
CREATE INDEX IF NOT EXISTS idx_person_tags_type ON person_tags(tag_type);

CREATE INDEX IF NOT EXISTS idx_candidate_scores_person ON candidate_scores(person_id);
CREATE INDEX IF NOT EXISTS idx_candidate_scores_overall ON candidate_scores(overall_score DESC);
CREATE INDEX IF NOT EXISTS idx_candidate_scores_hash ON candidate_scores(job_description_hash);

CREATE INDEX IF NOT EXISTS idx_twitter_profile_person ON twitter_profile(person_id);
CREATE INDEX IF NOT EXISTS idx_twitter_profile_username ON twitter_profile(username);

CREATE INDEX IF NOT EXISTS idx_network_paths_source ON network_paths(source_person_id);
CREATE INDEX IF NOT EXISTS idx_network_paths_target ON network_paths(target_person_id);
CREATE INDEX IF NOT EXISTS idx_network_paths_cached ON network_paths(cached_at);

-- Add migration log entry
INSERT INTO migration_log (migration_name, description, status, started_at, completed_at)
VALUES (
    '06_recruiter_workflow_schema',
    'Added tables for recruiter workflow: saved_searches, candidate_lists, person_notes, person_tags, candidate_scores, twitter_profile, network_paths',
    'completed',
    NOW(),
    NOW()
);

-- Grant permissions (adjust as needed for your user)
-- GRANT ALL ON saved_searches TO charlie_kerr;
-- GRANT ALL ON candidate_lists TO charlie_kerr;
-- etc.

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Migration 06_recruiter_workflow_schema completed successfully';
    RAISE NOTICE 'Created 8 new tables with indexes';
    RAISE NOTICE 'Ready for recruiter workflow features';
END $$;

