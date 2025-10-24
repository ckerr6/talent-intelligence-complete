-- ============================================================================
-- Skills Taxonomy Schema
-- Creates tables for skills extraction, proficiency tracking, and skill-repo linkage
-- Created: 2025-10-24
-- Part of Tier 1 Priority #3
-- ============================================================================

BEGIN;

-- Log migration start
INSERT INTO migration_log (migration_name, migration_phase, status, records_processed)
VALUES ('11_skills_taxonomy', 'schema_creation', 'started', 0);

-- ============================================================================
-- PART 1: CREATE SKILLS TABLES
-- ============================================================================

-- Main skills table - canonical list of all skills
CREATE TABLE IF NOT EXISTS skills (
  skill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  skill_name TEXT UNIQUE NOT NULL,
  category TEXT, -- 'language', 'framework', 'tool', 'protocol', 'concept', 'platform'
  aliases TEXT[] DEFAULT '{}', -- Alternative names: ['Solidity', 'solidity', 'Sol']
  description TEXT, -- Optional description of the skill
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  CONSTRAINT skill_name_not_empty CHECK (length(trim(skill_name)) > 0)
);

-- Person skills junction table - tracks which people have which skills
CREATE TABLE IF NOT EXISTS person_skills (
  person_skills_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  person_id UUID NOT NULL REFERENCES person(person_id) ON DELETE CASCADE,
  skill_id UUID NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
  proficiency_score FLOAT CHECK (proficiency_score >= 0 AND proficiency_score <= 100),
  evidence_sources TEXT[] DEFAULT '{}', -- ['title', 'repos', 'bio', 'llm', 'manual']
  confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
  merged_prs_count INT DEFAULT 0, -- PRs merged using this skill
  repos_using_skill INT DEFAULT 0, -- Repos contributed to using this skill
  lines_of_code INT DEFAULT 0, -- Estimated lines of code in this skill
  first_seen DATE, -- When skill was first detected
  last_used DATE, -- When skill was last detected (e.g., last contribution)
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(person_id, skill_id)
);

-- Repository skills junction table - tracks which repos use which skills
CREATE TABLE IF NOT EXISTS repository_skills (
  repo_skills_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_id UUID NOT NULL REFERENCES github_repository(repo_id) ON DELETE CASCADE,
  skill_id UUID NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
  is_primary BOOLEAN DEFAULT FALSE, -- Is this the primary language/skill of the repo?
  confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
  source TEXT, -- 'github_language', 'description', 'readme', 'manual'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(repo_id, skill_id)
);

-- ============================================================================
-- PART 2: CREATE INDEXES FOR PERFORMANCE
-- ============================================================================

-- Skills table indexes
CREATE INDEX IF NOT EXISTS idx_skills_name_lower ON skills(LOWER(skill_name));
CREATE INDEX IF NOT EXISTS idx_skills_category ON skills(category) WHERE category IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_skills_aliases ON skills USING GIN(aliases);

-- Person skills indexes
CREATE INDEX IF NOT EXISTS idx_person_skills_person ON person_skills(person_id);
CREATE INDEX IF NOT EXISTS idx_person_skills_skill ON person_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_person_skills_proficiency ON person_skills(proficiency_score DESC);
CREATE INDEX IF NOT EXISTS idx_person_skills_confidence ON person_skills(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_person_skills_evidence ON person_skills USING GIN(evidence_sources);
CREATE INDEX IF NOT EXISTS idx_person_skills_last_used ON person_skills(last_used DESC NULLS LAST);

-- Repository skills indexes
CREATE INDEX IF NOT EXISTS idx_repository_skills_repo ON repository_skills(repo_id);
CREATE INDEX IF NOT EXISTS idx_repository_skills_skill ON repository_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_repository_skills_primary ON repository_skills(is_primary) WHERE is_primary = TRUE;

-- ============================================================================
-- PART 3: SEED COMMON SKILLS
-- ============================================================================

INSERT INTO skills (skill_name, category, aliases, description) VALUES
  -- Programming Languages
  ('Solidity', 'language', ARRAY['solidity', 'Sol'], 'Smart contract programming language for Ethereum'),
  ('Rust', 'language', ARRAY['rust', 'rs'], 'Systems programming language'),
  ('Python', 'language', ARRAY['python', 'py'], 'High-level general-purpose programming language'),
  ('JavaScript', 'language', ARRAY['javascript', 'js', 'JS'], 'Dynamic programming language for web development'),
  ('TypeScript', 'language', ARRAY['typescript', 'ts', 'TS'], 'Typed superset of JavaScript'),
  ('Go', 'language', ARRAY['go', 'golang', 'Golang'], 'Statically typed programming language'),
  ('Java', 'language', ARRAY['java'], 'Object-oriented programming language'),
  ('C++', 'language', ARRAY['c++', 'cpp', 'C plus plus'], 'General-purpose programming language'),
  ('C', 'language', ARRAY['c'], 'Low-level programming language'),
  ('Swift', 'language', ARRAY['swift'], 'Programming language for iOS/macOS'),
  ('Kotlin', 'language', ARRAY['kotlin'], 'Modern programming language for JVM'),
  ('Ruby', 'language', ARRAY['ruby', 'rb'], 'Dynamic programming language'),
  ('PHP', 'language', ARRAY['php'], 'Server-side scripting language'),
  ('Shell', 'language', ARRAY['shell', 'bash', 'sh'], 'Command-line scripting'),
  ('SQL', 'language', ARRAY['sql'], 'Database query language'),
  ('Cairo', 'language', ARRAY['cairo'], 'Programming language for StarkNet'),
  ('Move', 'language', ARRAY['move'], 'Programming language for Aptos/Sui'),
  ('Vyper', 'language', ARRAY['vyper'], 'Pythonic smart contract language'),
  ('Haskell', 'language', ARRAY['haskell', 'hs'], 'Functional programming language'),
  ('Scala', 'language', ARRAY['scala'], 'JVM-based programming language'),
  
  -- Web Frameworks & Libraries
  ('React', 'framework', ARRAY['react', 'reactjs', 'React.js', 'react.js'], 'JavaScript library for building UIs'),
  ('Vue', 'framework', ARRAY['vue', 'vuejs', 'Vue.js'], 'Progressive JavaScript framework'),
  ('Angular', 'framework', ARRAY['angular', 'angularjs'], 'TypeScript-based web framework'),
  ('Next.js', 'framework', ARRAY['nextjs', 'next'], 'React framework for production'),
  ('Svelte', 'framework', ARRAY['svelte'], 'Compiler-based web framework'),
  ('Express', 'framework', ARRAY['express', 'expressjs', 'express.js'], 'Node.js web framework'),
  ('FastAPI', 'framework', ARRAY['fastapi'], 'Modern Python web framework'),
  ('Django', 'framework', ARRAY['django'], 'Python web framework'),
  ('Flask', 'framework', ARRAY['flask'], 'Lightweight Python web framework'),
  ('Rails', 'framework', ARRAY['rails', 'ruby on rails'], 'Ruby web framework'),
  ('Spring', 'framework', ARRAY['spring', 'spring boot'], 'Java framework'),
  
  -- Blockchain Protocols
  ('Ethereum', 'protocol', ARRAY['ethereum', 'eth', 'ETH'], 'Decentralized blockchain platform'),
  ('Bitcoin', 'protocol', ARRAY['bitcoin', 'btc', 'BTC'], 'Decentralized digital currency'),
  ('Solana', 'protocol', ARRAY['solana', 'sol', 'SOL'], 'High-performance blockchain'),
  ('Polygon', 'protocol', ARRAY['polygon', 'matic'], 'Ethereum scaling solution'),
  ('Arbitrum', 'protocol', ARRAY['arbitrum'], 'Ethereum Layer 2 scaling'),
  ('Optimism', 'protocol', ARRAY['optimism'], 'Ethereum Layer 2 scaling'),
  ('Base', 'protocol', ARRAY['base'], 'Coinbase Layer 2 network'),
  ('Avalanche', 'protocol', ARRAY['avalanche', 'avax'], 'Smart contracts platform'),
  ('Cosmos', 'protocol', ARRAY['cosmos', 'atom'], 'Interoperable blockchain network'),
  ('Polkadot', 'protocol', ARRAY['polkadot', 'dot'], 'Multi-chain network'),
  ('Near', 'protocol', ARRAY['near'], 'Sharded blockchain'),
  ('Aptos', 'protocol', ARRAY['aptos', 'apt'], 'Layer 1 blockchain'),
  ('Sui', 'protocol', ARRAY['sui'], 'Layer 1 blockchain'),
  ('StarkNet', 'protocol', ARRAY['starknet', 'stark'], 'Ethereum Layer 2 using ZK-rollups'),
  ('zkSync', 'protocol', ARRAY['zksync'], 'Ethereum Layer 2 scaling'),
  
  -- Blockchain Concepts
  ('Smart Contracts', 'concept', ARRAY['smart contracts', 'smartcontracts'], 'Self-executing contracts on blockchain'),
  ('DeFi', 'concept', ARRAY['defi', 'decentralized finance'], 'Decentralized finance'),
  ('NFT', 'concept', ARRAY['nft', 'nfts', 'non-fungible token'], 'Non-fungible tokens'),
  ('DAO', 'concept', ARRAY['dao', 'decentralized autonomous organization'], 'Decentralized governance'),
  ('Zero Knowledge Proofs', 'concept', ARRAY['zk', 'zero knowledge', 'zkp'], 'Cryptographic proofs'),
  ('MEV', 'concept', ARRAY['mev', 'maximal extractable value'], 'Blockchain value extraction'),
  ('Cross-chain', 'concept', ARRAY['cross-chain', 'cross chain', 'interoperability'], 'Blockchain interoperability'),
  ('Consensus Mechanisms', 'concept', ARRAY['consensus', 'proof of stake', 'proof of work'], 'Blockchain consensus'),
  ('Oracles', 'concept', ARRAY['oracle', 'oracles'], 'Off-chain data providers'),
  
  -- Dev Tools & Platforms
  ('Node.js', 'platform', ARRAY['nodejs', 'node'], 'JavaScript runtime'),
  ('Docker', 'tool', ARRAY['docker'], 'Containerization platform'),
  ('Kubernetes', 'tool', ARRAY['kubernetes', 'k8s'], 'Container orchestration'),
  ('Git', 'tool', ARRAY['git'], 'Version control system'),
  ('GitHub', 'platform', ARRAY['github'], 'Code hosting platform'),
  ('AWS', 'platform', ARRAY['aws', 'amazon web services'], 'Cloud platform'),
  ('Google Cloud', 'platform', ARRAY['gcp', 'google cloud'], 'Cloud platform'),
  ('Azure', 'platform', ARRAY['azure', 'microsoft azure'], 'Cloud platform'),
  ('PostgreSQL', 'tool', ARRAY['postgresql', 'postgres'], 'Relational database'),
  ('MongoDB', 'tool', ARRAY['mongodb', 'mongo'], 'NoSQL database'),
  ('Redis', 'tool', ARRAY['redis'], 'In-memory data store'),
  ('GraphQL', 'tool', ARRAY['graphql'], 'Query language for APIs'),
  ('REST', 'concept', ARRAY['rest', 'restful', 'rest api'], 'API architectural style'),
  ('WebAssembly', 'platform', ARRAY['wasm', 'webassembly'], 'Binary instruction format'),
  
  -- Blockchain-Specific Tools
  ('Hardhat', 'tool', ARRAY['hardhat'], 'Ethereum development environment'),
  ('Foundry', 'tool', ARRAY['foundry'], 'Ethereum development toolkit'),
  ('Truffle', 'tool', ARRAY['truffle'], 'Ethereum development framework'),
  ('Remix', 'tool', ARRAY['remix'], 'Solidity IDE'),
  ('ethers.js', 'tool', ARRAY['ethers', 'ethersjs'], 'Ethereum JavaScript library'),
  ('web3.js', 'tool', ARRAY['web3', 'web3js'], 'Ethereum JavaScript library'),
  ('Anchor', 'framework', ARRAY['anchor'], 'Solana development framework'),
  ('CosmWasm', 'framework', ARRAY['cosmwasm'], 'Cosmos smart contract platform'),
  ('The Graph', 'tool', ARRAY['the graph', 'graph protocol'], 'Blockchain indexing protocol'),
  ('IPFS', 'protocol', ARRAY['ipfs'], 'Decentralized storage'),
  ('Chainlink', 'protocol', ARRAY['chainlink', 'link'], 'Decentralized oracle network'),
  
  -- DeFi Protocols
  ('Uniswap', 'protocol', ARRAY['uniswap', 'uni'], 'Decentralized exchange'),
  ('Aave', 'protocol', ARRAY['aave'], 'Lending protocol'),
  ('Compound', 'protocol', ARRAY['compound', 'comp'], 'Lending protocol'),
  ('Curve', 'protocol', ARRAY['curve', 'crv'], 'Stablecoin DEX'),
  ('MakerDAO', 'protocol', ARRAY['maker', 'makerdao', 'dai'], 'Stablecoin protocol'),
  ('Balancer', 'protocol', ARRAY['balancer', 'bal'], 'Automated portfolio manager'),
  ('Yearn', 'protocol', ARRAY['yearn', 'yfi'], 'Yield aggregator'),
  ('Synthetix', 'protocol', ARRAY['synthetix', 'snx'], 'Synthetic assets protocol'),
  ('Lido', 'protocol', ARRAY['lido', 'ldo'], 'Liquid staking'),
  
  -- Testing & Quality
  ('Testing', 'concept', ARRAY['testing', 'unit testing', 'integration testing'], 'Software testing'),
  ('Security Auditing', 'concept', ARRAY['security', 'audit', 'auditing'], 'Code security review'),
  ('CI/CD', 'concept', ARRAY['cicd', 'ci/cd', 'continuous integration'], 'Automated deployment'),
  
  -- Additional Languages
  ('Zig', 'language', ARRAY['zig'], 'Systems programming language')
  
ON CONFLICT (skill_name) DO NOTHING;

-- ============================================================================
-- PART 4: CREATE HELPER FUNCTIONS
-- ============================================================================

-- Function to find skill by name or alias
CREATE OR REPLACE FUNCTION find_skill_by_name(skill_search TEXT)
RETURNS UUID AS $$
DECLARE
  skill_uuid UUID;
BEGIN
  -- Try exact match first
  SELECT skill_id INTO skill_uuid
  FROM skills
  WHERE LOWER(TRIM(skill_name)) = LOWER(TRIM(skill_search))
  LIMIT 1;
  
  IF skill_uuid IS NOT NULL THEN
    RETURN skill_uuid;
  END IF;
  
  -- Try alias match
  SELECT skill_id INTO skill_uuid
  FROM skills
  WHERE LOWER(TRIM(skill_search)) = ANY(
    SELECT LOWER(TRIM(unnest(aliases)))
  )
  LIMIT 1;
  
  RETURN skill_uuid;
END;
$$ LANGUAGE plpgsql;

-- Function to get or create skill
CREATE OR REPLACE FUNCTION get_or_create_skill(
  skill_search TEXT,
  skill_category TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
  skill_uuid UUID;
BEGIN
  -- Try to find existing skill
  skill_uuid := find_skill_by_name(skill_search);
  
  IF skill_uuid IS NOT NULL THEN
    RETURN skill_uuid;
  END IF;
  
  -- Create new skill
  INSERT INTO skills (skill_name, category)
  VALUES (TRIM(skill_search), skill_category)
  ON CONFLICT (skill_name) DO UPDATE
  SET updated_at = NOW()
  RETURNING skill_id INTO skill_uuid;
  
  RETURN skill_uuid;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PART 5: CREATE VIEWS FOR EASY QUERYING
-- ============================================================================

-- View: People with their skills and proficiency
CREATE OR REPLACE VIEW v_person_skills AS
SELECT 
  p.person_id,
  p.full_name,
  p.location,
  p.headline,
  s.skill_name,
  s.category as skill_category,
  ps.proficiency_score,
  ps.confidence_score,
  ps.evidence_sources,
  ps.repos_using_skill,
  ps.merged_prs_count,
  ps.last_used
FROM person p
JOIN person_skills ps ON p.person_id = ps.person_id
JOIN skills s ON ps.skill_id = s.skill_id
ORDER BY p.full_name, ps.proficiency_score DESC;

-- View: Skills distribution (how many people have each skill)
CREATE OR REPLACE VIEW v_skills_distribution AS
SELECT 
  s.skill_name,
  s.category,
  COUNT(DISTINCT ps.person_id) as people_count,
  AVG(ps.proficiency_score) as avg_proficiency,
  SUM(ps.repos_using_skill) as total_repos,
  SUM(ps.merged_prs_count) as total_prs
FROM skills s
LEFT JOIN person_skills ps ON s.skill_id = ps.skill_id
GROUP BY s.skill_id, s.skill_name, s.category
ORDER BY people_count DESC;

-- View: Repositories with their skills
CREATE OR REPLACE VIEW v_repository_skills AS
SELECT 
  gr.repo_id,
  gr.full_name as repo_name,
  gr.stars,
  gr.forks,
  s.skill_name,
  s.category as skill_category,
  rs.is_primary,
  rs.confidence_score,
  rs.source
FROM github_repository gr
JOIN repository_skills rs ON gr.repo_id = rs.repo_id
JOIN skills s ON rs.skill_id = s.skill_id
ORDER BY gr.stars DESC, gr.full_name;

-- ============================================================================
-- PART 6: UPDATE MIGRATION LOG
-- ============================================================================

UPDATE migration_log
SET 
  status = 'completed',
  completed_at = NOW(),
  records_created = (SELECT COUNT(*) FROM skills)
WHERE migration_name = '11_skills_taxonomy'
AND migration_phase = 'schema_creation';

-- ============================================================================
-- PART 7: GENERATE SUMMARY REPORT
-- ============================================================================

DO $$
DECLARE
  skill_count INT;
BEGIN
  SELECT COUNT(*) INTO skill_count FROM skills;
  
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Skills Taxonomy Schema Created!';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Tables Created:';
  RAISE NOTICE '  - skills';
  RAISE NOTICE '  - person_skills';
  RAISE NOTICE '  - repository_skills';
  RAISE NOTICE '';
  RAISE NOTICE 'Indexes Created: 12';
  RAISE NOTICE 'Helper Functions: 2';
  RAISE NOTICE 'Views Created: 3';
  RAISE NOTICE '';
  RAISE NOTICE 'Seeded Skills: %', skill_count;
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Ready for skill extraction!';
  RAISE NOTICE '========================================';
END $$;

-- Display summary
SELECT 
  'Skills Taxonomy Setup' as summary,
  (SELECT COUNT(*) FROM skills) as skills_seeded,
  (SELECT COUNT(*) FROM person_skills) as person_skills_populated,
  (SELECT COUNT(*) FROM repository_skills) as repo_skills_populated;

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES (run after migration)
-- ============================================================================

-- Check skills by category
-- SELECT category, COUNT(*) 
-- FROM skills 
-- WHERE category IS NOT NULL
-- GROUP BY category 
-- ORDER BY COUNT(*) DESC;

-- Find a skill by name or alias
-- SELECT * FROM skills WHERE find_skill_by_name('solidity') = skill_id;
-- SELECT * FROM skills WHERE find_skill_by_name('typescript') = skill_id;

-- Test get_or_create function
-- SELECT get_or_create_skill('Solidity', 'language');
-- SELECT get_or_create_skill('NewSkill', 'tool');

