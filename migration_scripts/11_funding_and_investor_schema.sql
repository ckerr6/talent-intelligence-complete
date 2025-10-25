-- ABOUTME: Database schema for VC funding rounds and investor tracking
-- ABOUTME: Stores fundraising data scraped from cryptorank.io and other sources

-- Migration: Funding & Investor Schema
-- Date: 2025-10-25
-- Purpose: Track VC funding rounds, investors, and company cap tables

-- =============================================================================
-- INVESTOR TABLE
-- =============================================================================
-- Track VC funds, angel investors, and other funding sources

CREATE TABLE IF NOT EXISTS investor (
    investor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investor_name TEXT NOT NULL,
    investor_type TEXT, -- 'vc_fund', 'angel', 'corporate', 'accelerator', 'other'
    website_url TEXT,
    linkedin_url TEXT,
    twitter_url TEXT,
    cryptorank_slug TEXT UNIQUE, -- e.g., 'outlier-ventures'
    description TEXT,
    thesis TEXT, -- Investment thesis or focus areas
    portfolio_count INTEGER DEFAULT 0, -- Number of portfolio companies
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT investor_name_not_empty CHECK (length(trim(investor_name)) > 0)
);

-- Indexes for investor
CREATE INDEX IF NOT EXISTS idx_investor_name_lower ON investor(LOWER(investor_name));
CREATE INDEX IF NOT EXISTS idx_investor_type ON investor(investor_type) WHERE investor_type IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_investor_cryptorank ON investor(cryptorank_slug) WHERE cryptorank_slug IS NOT NULL;

COMMENT ON TABLE investor IS 'VC funds, angels, and other funding sources';
COMMENT ON COLUMN investor.cryptorank_slug IS 'Unique identifier from cryptorank.io';
COMMENT ON COLUMN investor.portfolio_count IS 'Number of known portfolio companies';

-- =============================================================================
-- ENHANCE COMPANY_FUNDING_ROUND TABLE
-- =============================================================================
-- Enhance existing funding round table with additional fields

-- Add new columns for more detailed funding data
ALTER TABLE company_funding_round
    ADD COLUMN IF NOT EXISTS valuation_usd NUMERIC, -- Post-money valuation
    ADD COLUMN IF NOT EXISTS round_stage TEXT, -- 'seed', 'series_a', 'series_b', etc.
    ADD COLUMN IF NOT EXISTS cryptorank_slug TEXT, -- Link to cryptorank.io
    ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'manual', -- 'cryptorank', 'crunchbase', 'manual'
    ADD COLUMN IF NOT EXISTS investors JSONB DEFAULT '[]'::jsonb, -- Array of investor_ids with participation details
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Update existing round_id to use gen_random_uuid() as default
ALTER TABLE company_funding_round
    ALTER COLUMN round_id SET DEFAULT gen_random_uuid();

-- Create indexes for enhanced funding round queries
CREATE INDEX IF NOT EXISTS idx_funding_round_announced_date ON company_funding_round(announced_date DESC);
CREATE INDEX IF NOT EXISTS idx_funding_round_stage ON company_funding_round(round_stage) WHERE round_stage IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_funding_round_source ON company_funding_round(source);
CREATE INDEX IF NOT EXISTS idx_funding_round_investors ON company_funding_round USING GIN(investors);
CREATE INDEX IF NOT EXISTS idx_funding_round_cryptorank ON company_funding_round(cryptorank_slug) WHERE cryptorank_slug IS NOT NULL;

COMMENT ON COLUMN company_funding_round.investors IS 'JSONB array: [{"investor_id": "uuid", "role": "lead|participant", "amount_usd": 1000000}]';
COMMENT ON COLUMN company_funding_round.source IS 'Data source: cryptorank, crunchbase, manual';
COMMENT ON COLUMN company_funding_round.cryptorank_slug IS 'Link to cryptorank.io project page';

-- =============================================================================
-- COMPANY SOCIAL LINKS
-- =============================================================================
-- Store social media and web presence for companies

-- Add social link columns to company table
ALTER TABLE company
    ADD COLUMN IF NOT EXISTS twitter_url TEXT,
    ADD COLUMN IF NOT EXISTS github_url TEXT,
    ADD COLUMN IF NOT EXISTS telegram_url TEXT,
    ADD COLUMN IF NOT EXISTS discord_url TEXT,
    ADD COLUMN IF NOT EXISTS cryptorank_slug TEXT;

-- Indexes for social links
CREATE INDEX IF NOT EXISTS idx_company_twitter ON company(twitter_url) WHERE twitter_url IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_company_github_url ON company(github_url) WHERE github_url IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_company_cryptorank ON company(cryptorank_slug) WHERE cryptorank_slug IS NOT NULL;

COMMENT ON COLUMN company.twitter_url IS 'Official Twitter/X account';
COMMENT ON COLUMN company.github_url IS 'Official GitHub organization or repo';
COMMENT ON COLUMN company.cryptorank_slug IS 'Unique identifier from cryptorank.io';

-- =============================================================================
-- FUNDING ANALYTICS VIEWS
-- =============================================================================

-- View: Recent funding activity
CREATE OR REPLACE VIEW recent_funding AS
SELECT 
    c.company_name,
    c.website_url,
    c.cryptorank_slug as company_cryptorank_slug,
    cfr.round_type,
    cfr.round_stage,
    cfr.announced_date,
    cfr.amount_usd,
    cfr.valuation_usd,
    cfr.investors,
    cfr.source
FROM company_funding_round cfr
JOIN company c ON cfr.company_id = c.company_id
WHERE cfr.announced_date IS NOT NULL
ORDER BY cfr.announced_date DESC;

COMMENT ON VIEW recent_funding IS 'Recent funding rounds with company details';

-- View: Investor portfolio summary
CREATE OR REPLACE VIEW investor_portfolio_summary AS
SELECT 
    i.investor_id,
    i.investor_name,
    i.investor_type,
    COUNT(DISTINCT cfr.company_id) as portfolio_size,
    SUM(cfr.amount_usd) as total_invested_usd,
    MIN(cfr.announced_date) as first_investment_date,
    MAX(cfr.announced_date) as latest_investment_date
FROM investor i
LEFT JOIN company_funding_round cfr ON cfr.investors @> jsonb_build_array(jsonb_build_object('investor_id', i.investor_id::text))
GROUP BY i.investor_id, i.investor_name, i.investor_type;

COMMENT ON VIEW investor_portfolio_summary IS 'Investor activity and portfolio metrics';

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to investor table
DROP TRIGGER IF EXISTS update_investor_updated_at ON investor;
CREATE TRIGGER update_investor_updated_at
    BEFORE UPDATE ON investor
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to company_funding_round table
DROP TRIGGER IF EXISTS update_funding_round_updated_at ON company_funding_round;
CREATE TRIGGER update_funding_round_updated_at
    BEFORE UPDATE ON company_funding_round
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- SEED DATA
-- =============================================================================

-- Add some common crypto VCs to seed the database
INSERT INTO investor (investor_name, investor_type, cryptorank_slug, description)
VALUES
    ('Outlier Ventures', 'vc_fund', 'outlier-ventures', 'Web3 accelerator and venture fund'),
    ('Animoca Brands', 'corporate', 'animoca-brands', 'Digital entertainment, blockchain, and gamification'),
    ('Maven 11 Capital', 'vc_fund', 'maven11', 'Crypto-native venture capital'),
    ('Accel', 'vc_fund', 'accel', 'Early and growth stage venture capital'),
    ('Castle Island Ventures', 'vc_fund', 'castle-island-ventures', 'Public blockchain-focused VC'),
    ('a16z crypto', 'vc_fund', 'andreessen-horowitz-crypto', 'Crypto venture fund by Andreessen Horowitz'),
    ('Paradigm', 'vc_fund', 'paradigm', 'Crypto/Web3 investment firm'),
    ('Coinbase Ventures', 'corporate', 'coinbase-ventures', 'Crypto startup investment arm of Coinbase'),
    ('Pantera Capital', 'vc_fund', 'pantera-capital', 'Blockchain investment firm'),
    ('Polychain Capital', 'vc_fund', 'polychain-capital', 'Cryptocurrency and blockchain investment fund')
ON CONFLICT (cryptorank_slug) DO NOTHING;

-- =============================================================================

COMMIT;

