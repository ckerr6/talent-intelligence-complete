/*
GitHub PR Enrichment Schema
Adds fields for PR merge status, lines of code, and quality metrics
Based on expert sourcer feedback for identifying high-quality contributors
*/

-- Add columns to github_contribution table (one at a time)
ALTER TABLE github_contribution ADD COLUMN IF NOT EXISTS pr_count INTEGER DEFAULT 0;
ALTER TABLE github_contribution ADD COLUMN IF NOT EXISTS merged_pr_count INTEGER DEFAULT 0;          -- CRITICAL: Merged PRs to official repo
ALTER TABLE github_contribution ADD COLUMN IF NOT EXISTS open_pr_count INTEGER DEFAULT 0;
ALTER TABLE github_contribution ADD COLUMN IF NOT EXISTS closed_unmerged_pr_count INTEGER DEFAULT 0;
ALTER TABLE github_contribution ADD COLUMN IF NOT EXISTS lines_added INTEGER DEFAULT 0;              -- Code volume indicator
ALTER TABLE github_contribution ADD COLUMN IF NOT EXISTS lines_deleted INTEGER DEFAULT 0;            -- Code volume indicator
ALTER TABLE github_contribution ADD COLUMN IF NOT EXISTS files_changed INTEGER DEFAULT 0;            -- Complexity indicator
ALTER TABLE github_contribution ADD COLUMN IF NOT EXISTS last_merged_pr_date TIMESTAMP;              -- Recency signal
ALTER TABLE github_contribution ADD COLUMN IF NOT EXISTS contribution_quality_score FLOAT;           -- Computed 0-100 score
ALTER TABLE github_contribution ADD COLUMN IF NOT EXISTS has_code_contributions BOOLEAN DEFAULT TRUE;
ALTER TABLE github_contribution ADD COLUMN IF NOT EXISTS has_doc_contributions BOOLEAN DEFAULT FALSE;

-- Add columns to github_profile table (one at a time)
ALTER TABLE github_profile ADD COLUMN IF NOT EXISTS is_pro_account BOOLEAN DEFAULT FALSE;       -- GitHub Pro/Verified indicator
ALTER TABLE github_profile ADD COLUMN IF NOT EXISTS total_merged_prs INTEGER DEFAULT 0;         -- Career total merged PRs
ALTER TABLE github_profile ADD COLUMN IF NOT EXISTS total_stars_earned INTEGER DEFAULT 0;       -- Stars on personal repos
ALTER TABLE github_profile ADD COLUMN IF NOT EXISTS code_review_count INTEGER DEFAULT 0;        -- Reviews given (quality signal)
ALTER TABLE github_profile ADD COLUMN IF NOT EXISTS total_lines_contributed INTEGER DEFAULT 0;  -- Career total lines
ALTER TABLE github_profile ADD COLUMN IF NOT EXISTS enriched_at TIMESTAMP;                      -- Last PR data enrichment

-- Create index for quality filtering
CREATE INDEX IF NOT EXISTS idx_github_contribution_quality 
  ON github_contribution(contribution_quality_score DESC) 
  WHERE contribution_quality_score IS NOT NULL;

-- Create index for merged PR filtering
CREATE INDEX IF NOT EXISTS idx_github_contribution_merged_prs 
  ON github_contribution(merged_pr_count DESC) 
  WHERE merged_pr_count > 0;

-- Create index for enrichment tracking
CREATE INDEX IF NOT EXISTS idx_github_profile_enriched 
  ON github_profile(enriched_at) 
  WHERE enriched_at IS NOT NULL;

-- Create index for pro accounts
CREATE INDEX IF NOT EXISTS idx_github_profile_pro 
  ON github_profile(is_pro_account) 
  WHERE is_pro_account = TRUE;

-- Add comments for documentation
COMMENT ON COLUMN github_contribution.merged_pr_count IS 'Number of merged pull requests (CRITICAL quality signal)';
COMMENT ON COLUMN github_contribution.contribution_quality_score IS 'Computed quality score 0-100 based on multiple signals';
COMMENT ON COLUMN github_profile.is_pro_account IS 'GitHub Pro/paid account (indicates private repos exist)';
COMMENT ON COLUMN github_profile.total_merged_prs IS 'Career total merged PRs across all repositories';

ANALYZE github_contribution;
ANALYZE github_profile;

SELECT 'GitHub PR enrichment schema created successfully!' AS status;

