# Tier 2: Platform Enhancement Plan (60 Days)

**Status:** Ready to begin  
**Prerequisites:** ✅ Tier 1 Complete (80% platform completeness)  
**Target:** 95% completeness in 90 days total (30 days for Tier 2)

---

## Overview

Build on Tier 1 foundation to add:
1. Recruiter workflow features
2. Advanced relationship mapping
3. ML-based improvements
4. Temporal analytics
5. Quality prediction systems

---

## Priority Rankings

Based on user value and technical complexity:

| Priority | Feature | User Value | Complexity | Days |
|----------|---------|------------|------------|------|
| 1 | Saved Searches & Lists | ⭐⭐⭐⭐⭐ | Low | 3 |
| 2 | Person Notes & Tags | ⭐⭐⭐⭐⭐ | Low | 2 |
| 3 | Collaboration Network | ⭐⭐⭐⭐ | Medium | 7 |
| 4 | ML-Based Skill Extraction | ⭐⭐⭐ | High | 10 |
| 5 | Temporal Snapshots | ⭐⭐⭐ | Medium | 5 |
| 6 | Quality Prediction | ⭐⭐⭐ | High | 8 |

**Total: ~35 days** (with buffer)

---

## Week 1-2: Recruiter Workflows

### Priority 1: Saved Searches & Candidate Lists (Days 1-3)

**Problem:** Recruiters can't save their searches or build candidate pipelines

**Deliverables:**
- Migration: `migration_scripts/12_recruiter_workflows.sql`
- API endpoints: `/api/saved_searches`, `/api/candidate_lists`
- Frontend: Search save buttons, list management UI

**Tasks:**

**Day 1: Schema**
```sql
CREATE TABLE saved_searches (
  search_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
  search_name TEXT NOT NULL,
  search_criteria JSONB NOT NULL, -- Filters: skills, location, etc.
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE candidate_lists (
  list_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
  list_name TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'active', -- active, archived
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE candidate_list_members (
  member_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  list_id UUID REFERENCES candidate_lists(list_id) ON DELETE CASCADE,
  person_id UUID REFERENCES person(person_id) ON DELETE CASCADE,
  status TEXT DEFAULT 'new', -- new, contacted, interviewing, rejected, hired
  notes TEXT,
  added_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(list_id, person_id)
);
```

**Day 2: API Implementation**
- POST `/api/saved_searches` - Save a search
- GET `/api/saved_searches` - List user's saved searches
- POST `/api/candidate_lists` - Create a list
- POST `/api/candidate_lists/{id}/members` - Add person to list
- PUT `/api/candidate_lists/{id}/members/{person_id}` - Update status

**Day 3: Frontend Integration**
- "Save Search" button on search results
- "Add to List" button on profile pages
- List management dashboard
- Candidate pipeline view (Kanban-style)

**Success Metrics:**
- Recruiters can save unlimited searches
- Lists can hold 100s of candidates
- Status tracking per candidate

---

### Priority 2: Person Notes & Tags (Days 4-5)

**Problem:** Can't add context or categorize people

**Deliverables:**
- Extend schema: `person_notes`, `person_tags` tables
- API endpoints: `/api/people/{id}/notes`, `/api/people/{id}/tags`
- Frontend: Notes sidebar, tag chips

**Tasks:**

**Day 4: Schema & API**
```sql
-- Note: These tables may already exist from earlier migrations
-- If so, just add API endpoints

CREATE TABLE IF NOT EXISTS person_notes (
  note_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  person_id UUID REFERENCES person(person_id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
  note_text TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS person_tags (
  tag_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  person_id UUID REFERENCES person(person_id) ON DELETE CASCADE,
  tag_name TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(person_id, tag_name)
);
```

API:
- POST `/api/people/{id}/notes`
- GET `/api/people/{id}/notes`
- POST `/api/people/{id}/tags`
- DELETE `/api/people/{id}/tags/{tag_name}`

**Day 5: Frontend**
- Notes section on profile page
- Tag input with autocomplete
- Filter by tags in search

**Success Metrics:**
- Can add multiple notes per person
- Tag-based filtering works
- Notes are private per user

---

## Week 2-3: Relationship Mapping

### Priority 3: GitHub Collaboration Network (Days 6-12)

**Problem:** Can't find "who has worked with whom"

**Deliverables:**
- Migration: `migration_scripts/13_collaboration_network.sql`
- Script: `scripts/network/build_collaboration_edges.py`
- API endpoint: `/api/people/{id}/network`
- Frontend: Network visualization

**Tasks:**

**Day 6-7: Schema**
```sql
CREATE TABLE edge_github_collaboration (
  edge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  src_person_id UUID REFERENCES person(person_id) ON DELETE CASCADE,
  dst_person_id UUID REFERENCES person(person_id) ON DELETE CASCADE,
  shared_repos INT DEFAULT 0,
  collaboration_strength FLOAT, -- 0-1 score
  first_collaboration_date DATE,
  last_collaboration_date DATE,
  repos_list UUID[], -- Array of repo_ids
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(src_person_id, dst_person_id)
);

CREATE INDEX idx_github_collab_src ON edge_github_collaboration(src_person_id);
CREATE INDEX idx_github_collab_dst ON edge_github_collaboration(dst_person_id);
CREATE INDEX idx_github_collab_strength ON edge_github_collaboration(collaboration_strength DESC);
```

**Day 8-10: Build Collaboration Edges**
Create `scripts/network/build_collaboration_edges.py`:
- For each repo with 2+ contributors
- Create edges between all contributor pairs
- Weight by: shared commits, shared PRs, time overlap
- Aggregate across all repos
- Target: 500K-1M edges

**Day 11: API**
- GET `/api/people/{id}/network` - Returns collaborators
- GET `/api/people/{id}/network/graph` - D3.js-ready graph data

**Day 12: Frontend**
- Network visualization (force-directed graph)
- "Find people who worked with X" search
- Collaboration strength slider

**Success Metrics:**
- 500K+ collaboration edges
- Can find "developers who worked at Uniswap with Vitalik"
- Network viz loads in <2s

---

## Week 3-4: Intelligence Enhancements

### Priority 4: ML-Based Skill Extraction (Days 13-22)

**Problem:** Rule-based extraction misses 30% of skills

**Deliverables:**
- Script: `scripts/skills/extract_skills_with_llm.py`
- Enhanced profiles with soft skills
- Confidence score improvements

**Tasks:**

**Day 13-15: LLM Integration**
- Set up OpenAI API integration
- Create prompt templates for skill extraction
- Batch processing logic (100 profiles/batch)

**Day 16-18: Execution**
- Process 20K high-value profiles:
  - Profiles with emails + GitHub
  - Profiles with 10+ repos
  - Profiles in priority ecosystems
- Extract skills not caught by rules
- Add soft skills (leadership, communication, etc.)

**Day 19-21: Validation & Iteration**
- Manual spot-check 100 profiles
- Adjust prompts for better accuracy
- Re-run on corrected patterns

**Day 22: Integration**
- Update person_skills with LLM results
- Merge with rule-based extractions
- Boost confidence scores for dual-sourced skills

**Success Metrics:**
- Skills coverage: 63% → 75%+
- Soft skills added: 20K+ entries
- Confidence scores improved

**Budget:** $300-500 for GPT-4 API calls

---

### Priority 5: Temporal Snapshots (Days 23-27)

**Problem:** Can't track changes over time ("Show me hiring trends")

**Deliverables:**
- Migration: `migration_scripts/14_temporal_snapshots.sql`
- Script: `scripts/analytics/create_snapshots.py`
- API: `/api/analytics/trends`

**Tasks:**

**Day 23-24: Schema**
```sql
CREATE TABLE employment_snapshots (
  snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  snapshot_date DATE NOT NULL,
  company_id UUID REFERENCES company(company_id),
  employee_count INT,
  new_hires INT,
  departures INT,
  top_skills JSONB, -- {skill_name: count}
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE ecosystem_snapshots (
  snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  snapshot_date DATE NOT NULL,
  ecosystem_id UUID REFERENCES crypto_ecosystem(ecosystem_id),
  developer_count INT,
  repo_count INT,
  contribution_count INT,
  top_contributors UUID[], -- Array of person_ids
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_employment_snapshots_date ON employment_snapshots(snapshot_date);
CREATE INDEX idx_ecosystem_snapshots_date ON ecosystem_snapshots(snapshot_date);
```

**Day 25-26: Create Snapshots**
- Run `create_snapshots.py` to create baseline (current state)
- Set up monthly cron job for future snapshots
- Backfill historical data if possible (from employment dates)

**Day 27: API & Frontend**
- GET `/api/analytics/trends/employment` - Company growth trends
- GET `/api/analytics/trends/ecosystems` - Ecosystem activity trends
- Frontend: Trend charts (line graphs)

**Success Metrics:**
- Baseline snapshot created
- Can query "Show me Ethereum growth over 6 months"
- Historical backfill covers 12+ months

---

### Priority 6: Quality Prediction (Days 28-35)

**Problem:** Can't predict who will be a high-quality hire

**Deliverables:**
- Script: `scripts/ml/train_quality_model.py`
- Prediction scores in database
- API: `/api/people/{id}/quality_score`

**Tasks:**

**Day 28-30: Feature Engineering**
- Collect features:
  - Skills proficiency scores
  - GitHub metrics (PRs, commits, quality scores)
  - Ecosystem participation
  - Employment history (tenure, company quality)
  - Network centrality (collaborators)
- Create training dataset from high-quality profiles

**Day 31-33: Model Training**
- Train gradient boosting model (XGBoost or LightGBM)
- Features → Quality score (0-100)
- Validate on holdout set
- Save model artifact

**Day 34-35: Integration**
- Add `quality_prediction_score` to person table
- Run inference on all profiles
- Create API endpoint
- Frontend: Show prediction score on profiles

**Success Metrics:**
- Model AUC > 0.75
- Scores distributed across range
- "Top 10% quality" filter works

---

## File Changes Summary

### New Migration Files (5)
- `migration_scripts/12_recruiter_workflows.sql`
- `migration_scripts/13_collaboration_network.sql`
- `migration_scripts/14_temporal_snapshots.sql`
- `migration_scripts/15_quality_prediction.sql` (if needed)

### New Python Scripts (8)
- `scripts/network/build_collaboration_edges.py`
- `scripts/skills/extract_skills_with_llm.py`
- `scripts/analytics/create_snapshots.py`
- `scripts/ml/train_quality_model.py`
- `scripts/ml/predict_quality_scores.py`

### New API Endpoints (15+)
- Saved searches (4 endpoints)
- Candidate lists (6 endpoints)
- Notes & tags (4 endpoints)
- Network (2 endpoints)
- Trends (2 endpoints)
- Quality predictions (1 endpoint)

### Frontend Features (10+)
- Saved search management
- Candidate list pipeline
- Notes & tags UI
- Network visualization
- Trend charts
- Quality score display

---

## Expected Outcomes (30 Days)

### Data Completeness
| Metric | Before Tier 2 | After Tier 2 | Improvement |
|--------|---------------|--------------|-------------|
| Skills Coverage | 63% | 75%+ | +12% |
| Collaboration Edges | 7.8K | 500K+ | +63,000% |
| Temporal Snapshots | 0 | 12+ months | New |
| Quality Scores | 0 | 156K | New |

### New Capabilities
- ✅ Save searches and build candidate pipelines
- ✅ Track candidates through hiring process
- ✅ Find "who worked with whom"
- ✅ Discover network connections
- ✅ Predict candidate quality
- ✅ Track hiring trends over time
- ✅ Soft skills extraction
- ✅ Advanced filtering and sorting

### Platform Completeness
- **Before Tier 2**: 80% complete
- **After Tier 2**: 95% complete
- **Production Ready**: ✅ Yes

---

## Risk Mitigation

1. **LLM Costs**: Budget $500, can reduce coverage if needed
2. **Graph Computation**: May be slow, run overnight
3. **ML Model Quality**: Start simple, iterate
4. **Frontend Complexity**: Network viz may be slow for large graphs
5. **Temporal Backfill**: May not have complete historical data

---

## Deferred to Future (Tier 3)

Lower priority items for later:
1. Real-time notifications
2. Email outreach tracking
3. Interview scheduling integration
4. Advanced ML models (entity resolution, recommendations)
5. Mobile app
6. Public API for external use
7. Data export features
8. Advanced permissions & teams
9. Audit logging
10. Custom fields & workflows

---

## Decision Points

### Before Starting Tier 2

**Question 1:** Should we execute Tier 1 batches first?
- **Option A:** Yes - Complete PR enrichment & importance scoring (5-7 nights)
- **Option B:** No - Start Tier 2 now, execute batches in parallel
- **Recommendation:** Option B (parallel execution)

**Question 2:** Which Tier 2 priorities are highest value?
- **Must Have:** Priorities 1-2 (Recruiter workflows) - 5 days
- **High Value:** Priority 3 (Collaboration network) - 7 days
- **Nice to Have:** Priorities 4-6 (ML/Analytics) - 23 days

**Question 3:** LLM skill extraction worth the cost?
- **Cost:** $300-500
- **Benefit:** +12% skill coverage, soft skills
- **Decision:** TBD (can defer to later)

---

## Next Steps

1. ✅ Review this Tier 2 plan
2. **Decide:** Which priorities to tackle first
3. **Decide:** Parallel execution of Tier 1 batches?
4. **Start:** Day 1 of selected priorities

---

**Created:** October 24, 2025  
**Status:** Ready for review and execution  
**Estimated Completion:** 30 days from start

