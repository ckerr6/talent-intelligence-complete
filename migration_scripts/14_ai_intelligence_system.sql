-- ============================================================================
-- AI Intelligence System Schema Migration
-- Created: 2025-10-24
-- Purpose: Add tables for AI-first recruiting: notifications, user events, preferences
-- ============================================================================

-- ============================================================================
-- PART 1: NOTIFICATIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,  -- Will be hardcoded 'default_user' for single-user MVP
    notification_type TEXT NOT NULL CHECK (notification_type IN (
        'new_match', 'job_change', 'github_activity', 'rising_talent', 
        'network_connection', 'ai_suggestion'
    )),
    priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN (
        'low', 'medium', 'high', 'urgent'
    )),
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    person_id UUID REFERENCES person(person_id) ON DELETE CASCADE,
    person_name TEXT,
    action_url TEXT,
    action_label TEXT DEFAULT 'View Profile',
    metadata JSONB DEFAULT '{}',  -- Store match_score, reason, search_name, etc.
    is_read BOOLEAN DEFAULT FALSE,
    is_dismissed BOOLEAN DEFAULT FALSE,
    is_actioned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE,
    actioned_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for notifications
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_notifications_person ON notifications(person_id);
CREATE INDEX IF NOT EXISTS idx_notifications_priority ON notifications(priority, created_at DESC);

COMMENT ON TABLE notifications IS 'AI-generated notifications for talent discoveries and events';
COMMENT ON COLUMN notifications.metadata IS 'JSONB storing match_score, reason, search_name, repo_name, etc.';

-- ============================================================================
-- PART 2: ENHANCE SAVED SEARCHES FOR AUTO-MONITORING
-- ============================================================================

-- Extends existing saved_searches table from migration 06
ALTER TABLE saved_searches ADD COLUMN IF NOT EXISTS auto_monitor BOOLEAN DEFAULT FALSE;
ALTER TABLE saved_searches ADD COLUMN IF NOT EXISTS monitor_frequency TEXT DEFAULT 'daily' CHECK (monitor_frequency IN ('daily', 'weekly', 'manual'));
ALTER TABLE saved_searches ADD COLUMN IF NOT EXISTS min_match_score INTEGER DEFAULT 70 CHECK (min_match_score BETWEEN 0 AND 100);
ALTER TABLE saved_searches ADD COLUMN IF NOT EXISTS last_monitored_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE saved_searches ADD COLUMN IF NOT EXISTS notification_enabled BOOLEAN DEFAULT TRUE;

CREATE INDEX IF NOT EXISTS idx_saved_searches_auto_monitor ON saved_searches(auto_monitor) WHERE auto_monitor = TRUE;

COMMENT ON COLUMN saved_searches.auto_monitor IS 'If true, AI monitors this search daily for new matches';
COMMENT ON COLUMN saved_searches.min_match_score IS 'Minimum match score to create notification (0-100)';

-- ============================================================================
-- PART 3: USER EVENTS TABLE (FOR PATTERN LEARNING)
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'profile_view', 'list_addition', 'search', 'outreach', 
        'notification_click', 'feedback', 'dismissal'
    )),
    person_id UUID REFERENCES person(person_id) ON DELETE SET NULL,
    list_id UUID,
    search_filters JSONB,
    source TEXT,  -- 'search', 'notification', 'network', 'recommendation', 'direct'
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for user_events
CREATE INDEX IF NOT EXISTS idx_user_events_user ON user_events(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_events_type ON user_events(event_type);
CREATE INDEX IF NOT EXISTS idx_user_events_person ON user_events(person_id);
CREATE INDEX IF NOT EXISTS idx_user_events_created ON user_events(created_at DESC);

COMMENT ON TABLE user_events IS 'Tracks user behavior for AI pattern learning and personalization';
COMMENT ON COLUMN user_events.source IS 'How user found this person/action (for attribution)';

-- ============================================================================
-- PART 4: USER PREFERENCES TABLE (LEARNED PATTERNS)
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_preferences (
    preference_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE,
    preferred_companies JSONB DEFAULT '[]',  -- [{name: string, weight: float}]
    preferred_locations JSONB DEFAULT '[]',  -- [{name: string, weight: float}]
    valued_skills JSONB DEFAULT '[]',  -- [{skill: string, importance: float}]
    feature_importance JSONB DEFAULT '{}',  -- {has_github: 0.95, has_email: 0.85, ...}
    common_filters JSONB DEFAULT '[]',  -- Most used filter combinations
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sample_size INTEGER DEFAULT 0  -- Number of interactions learned from
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user ON user_preferences(user_id);

COMMENT ON TABLE user_preferences IS 'AI-learned user preferences for personalized recommendations';
COMMENT ON COLUMN user_preferences.sample_size IS 'Number of user events used to calculate preferences';
COMMENT ON COLUMN user_preferences.feature_importance IS 'Weights showing which features user values most';

-- ============================================================================
-- PART 5: HELPER FUNCTIONS
-- ============================================================================

-- Function to clean up old notifications
CREATE OR REPLACE FUNCTION cleanup_old_notifications(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM notifications
    WHERE created_at < NOW() - (days_to_keep || ' days')::INTERVAL
    AND is_read = TRUE
    AND is_actioned = FALSE;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_notifications IS 'Delete read notifications older than N days to keep table size manageable';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify tables were created
DO $$
BEGIN
    RAISE NOTICE 'AI Intelligence System Migration Complete!';
    RAISE NOTICE 'Created tables:';
    RAISE NOTICE '  - notifications (for AI discoveries)';
    RAISE NOTICE '  - user_events (for behavior tracking)';
    RAISE NOTICE '  - user_preferences (for learned patterns)';
    RAISE NOTICE 'Enhanced tables:';
    RAISE NOTICE '  - saved_searches (added auto_monitor columns)';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Start backend services (NotificationService, MonitoringService)';
    RAISE NOTICE '  2. Configure APScheduler for daily monitoring';
    RAISE NOTICE '  3. Build notification UI components';
END $$;

