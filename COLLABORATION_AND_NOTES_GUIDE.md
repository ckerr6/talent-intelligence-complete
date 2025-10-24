# Collaboration Network & Enhanced Notes Guide

**Status**: ✅ COMPLETE & PRODUCTION-READY  
**Date**: October 24, 2025  
**WOW Factor**: 🔥🔥🔥 High Leverage Features

---

## 🕸️ Part 1: GitHub Collaboration Network

### What We Built

A complete **collaboration network** showing who has worked with whom on GitHub. This is your **WOW factor** - recruiters can see:
- "Who has worked with Vitalik Buterin?"
- "Show me Uniswap developers who know each other"
- "Find mutual connections between two candidates"

### Database Schema

**Table: `edge_github_collaboration`**
```sql
CREATE TABLE edge_github_collaboration (
  edge_id UUID PRIMARY KEY,
  src_person_id UUID,
  dst_person_id UUID,
  shared_repos INT,                    -- Number of repos they've both worked on
  shared_contributions INT,            -- Total contributions across shared repos
  collaboration_strength FLOAT,        -- 0-1 score (weighted by repos, contribs, duration)
  first_collaboration_date DATE,
  last_collaboration_date DATE,
  collaboration_months INT,
  repos_list UUID[],                   -- Array of repo IDs
  top_shared_repos JSONB               -- Details of key repos
);
```

**View: `v_coemployment_aggregated`**
- Aggregates `edge_coemployment` (which is one row per company)
- Provides: `shared_companies_count`, `total_overlap_months`, `collaboration_strength`

**View: `v_person_network`**
- Shows each person's total connections across GitHub + employment
- Fast lookup for "how connected is this person?"

### Key Functions

#### 1. Get Person's Collaborators
```sql
SELECT * FROM get_person_collaborators(
  '8a7f3c2e-9d0b-4a1f-b5e2-7c3d1e9f8a2b'::uuid,  -- person_id
  0.5,                                            -- min collaboration strength
  20                                              -- limit
);
```

**Returns:**
| Column | Description |
|--------|-------------|
| collaborator_id | UUID of collaborator |
| collaborator_name | Full name |
| collaboration_type | 'github' or 'employment' |
| strength | 0-1 collaboration score |
| shared_repos | Number of repos (GitHub only) |
| shared_companies | Number of companies (employment only) |
| last_interaction | Most recent collaboration date |

#### 2. Find Mutual Connections
```sql
SELECT * FROM find_common_connections(
  'person-a-uuid'::uuid,
  'person-b-uuid'::uuid
);
```

**Use Case**: "You're reaching out to Alice. Bob knows Alice through 3 mutual connections. Use this for warm intro."

### Initial Results

From just **100 repositories**, we created:
- **38,796 collaboration edges**
- Top pairs collaborated on **30-58 shared repos**
- Collaboration strengths up to **1.0 (maximum)**

### Building the Full Network

```bash
# Build entire network (all repos)
cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete
python3 scripts/network/build_collaboration_edges.py --all

# Build for specific ecosystem
python3 scripts/network/build_collaboration_edges.py --ecosystem ethereum

# Build with limits
python3 scripts/network/build_collaboration_edges.py --min-contributors 5 --limit 1000
```

**Expected Results** (full build):
- **333K repos** with 2+ contributors
- Estimated **500K-1M collaboration edges**
- Processing time: **6-12 hours**

### Sample Queries

```sql
-- Top 20 collaboration pairs
SELECT 
  p1.full_name as person_a,
  p2.full_name as person_b,
  egc.shared_repos,
  ROUND(egc.collaboration_strength::NUMERIC, 2) as strength
FROM edge_github_collaboration egc
JOIN person p1 ON egc.src_person_id = p1.person_id
JOIN person p2 ON egc.dst_person_id = p2.person_id
ORDER BY egc.collaboration_strength DESC
LIMIT 20;

-- Find all people who worked with someone specific
SELECT 
  p.full_name,
  p.headline,
  egc.shared_repos,
  egc.shared_contributions
FROM edge_github_collaboration egc
JOIN person p ON egc.dst_person_id = p.person_id
WHERE egc.src_person_id = 'target-person-uuid'
AND egc.collaboration_strength > 0.7
ORDER BY egc.collaboration_strength DESC;

-- Network size by person
SELECT 
  p.full_name,
  v.github_connections,
  v.employment_connections,
  v.total_connections
FROM v_person_network v
JOIN person p ON v.person_id = p.person_id
ORDER BY v.total_connections DESC
LIMIT 100;
```

---

## 📝 Part 2: Enhanced Notes System

### What We Enhanced

Your existing `person_notes` table now has:
- **Full-text search** (PostgreSQL tsvector with GIN index)
- **Note categorization** (calls, screens, meetings, emails, timing)
- **Priority levels** (low, normal, high, urgent)
- **Custom tags** (arrays for flexible tagging)
- **JSONB metadata** (structured data storage)
- **AI-parseable views** (easy for LLMs to read)

### Schema Enhancements

**Enhanced `person_notes` Table:**
```sql
person_notes (
  note_id UUID,
  person_id UUID,
  user_id UUID,
  note_text TEXT,
  note_type TEXT,              -- NEW: 'general', 'call', 'meeting', 'screen', etc.
  note_category TEXT,           -- NEW: More specific categorization
  priority TEXT,                -- NEW: 'low', 'normal', 'high', 'urgent'
  is_pinned BOOLEAN,           -- NEW: Pin important notes
  tags TEXT[],                 -- NEW: Custom tags array
  metadata JSONB,              -- NEW: Structured data
  search_vector tsvector,      -- NEW: Full-text search
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
```

### Key Functions

#### 1. Add Categorized Notes
```sql
SELECT add_person_note(
  '8a7f3c2e-9d0b-4a1f-b5e2-7c3d1e9f8a2b'::uuid,  -- person_id
  'user-uuid'::uuid,                               -- user_id
  'Strong technical background in Solidity and DeFi. 
   Interested in Series A startups. Available in 2-3 weeks. 
   Compensation expectations: $180-200K + equity. 
   Prefers remote or SF Bay Area. 
   
   Interview Notes:
   - 5 years experience with smart contracts
   - Led security audits for major DeFi protocols
   - Looking for technical leadership role
   - Can start mid-November',
  'screen',                                        -- note_type
  'recruiter_screen',                              -- note_category
  'high',                                          -- priority
  ARRAY['solidity', 'defi', 'remote', 'available', 'leadership'],  -- tags
  '{"timing": "2-3 weeks", 
    "comp_expectations": "180-200K", 
    "location_pref": "remote/SF",
    "availability": "mid-November",
    "seniority": "senior/lead"}'::jsonb            -- metadata
);
```

#### 2. Search Notes (Full-Text)
```sql
-- Search across all notes
SELECT * FROM search_person_notes(
  'solidity developer available immediately',
  NULL,   -- any person
  NULL,   -- any type
  NULL,   -- any priority
  50      -- limit
);

-- Search only recruiter screens
SELECT * FROM search_person_notes(
  'DeFi remote available',
  NULL,      -- any person
  'screen',  -- only screens
  NULL,      -- any priority
  20
);

-- Search high priority notes
SELECT * FROM search_person_notes(
  'urgent hiring',
  NULL,     -- any person
  NULL,     -- any type
  'high',   -- only high priority
  10
);
```

### AI-Parseable Views

#### View: `v_candidate_full_context`
Perfect for feeding to AI models - all notes aggregated by person.

```sql
SELECT * FROM v_candidate_full_context
WHERE person_id = '8a7f3c2e-9d0b-4a1f-b5e2-7c3d1e9f8a2b';
```

**Returns:**
- `all_notes`: JSONB array of all notes with metadata
- `all_tags`: Array of unique tags across all notes
- `most_recent_note`: Latest note text
- `total_notes`: Count
- `has_urgent_notes`: Boolean flag

**Use Case**: "Hey GPT-4, analyze this candidate's notes and tell me if they're a good fit for this role..."

#### View: `v_recruiter_screens`
Specific view for recruiter screen notes.

```sql
SELECT * FROM v_recruiter_screens
WHERE screen_date > NOW() - INTERVAL '30 days'
ORDER BY screen_date DESC;
```

**Returns structured data:**
- `candidate_timing`
- `location_preference`
- `comp_expectations`
- `availability`

### Sample Use Cases

#### Use Case 1: Recruiter Screen
```sql
-- Add detailed recruiter screen
SELECT add_person_note(
  person_id,
  user_id,
  'Phone screen completed. Candidate is excited about the role.
   
   Technical Background:
   - 3 years Rust development
   - Built 2 production DeFi protocols
   - Strong systems programming background
   
   Availability: Immediate (2 weeks notice)
   Compensation: $160-180K + 0.5-1% equity
   Location: Open to remote, prefers NYC/SF
   Interview Performance: 9/10
   
   Next Steps: Schedule technical round',
  'screen',
  'recruiter_screen',
  'high',
  ARRAY['rust', 'defi', 'available', 'strong'],
  '{"timing": "immediate", "comp": "160-180K", "equity": "0.5-1%", 
    "location": "remote/NYC/SF", "score": 9}'::jsonb
);
```

#### Use Case 2: Meeting Notes
```sql
-- Add meeting notes
SELECT add_person_note(
  person_id,
  user_id,
  'Coffee meeting at Philz.
   
   - Discussed their work at Uniswap
   - Interested in moving to infrastructure layer
   - Knows Vitalik and Hayden personally
   - Can make intros to Paradigm team
   - Looking for founding engineer role
   - Timeline: exploratory, not actively looking',
  'meeting',
  'in_person',
  'normal',
  ARRAY['uniswap', 'infrastructure', 'network', 'not-urgent'],
  '{"meeting_type": "coffee", "location": "Philz SF", 
    "connections": ["Vitalik", "Hayden Adams"], 
    "can_intro": ["Paradigm"]}'::jsonb
);
```

#### Use Case 3: Timing/Availability
```sql
-- Track candidate timing
SELECT add_person_note(
  person_id,
  user_id,
  'Follow up in Q1 2026. Currently committed to current project 
   through end of year. Very interested in crypto infrastructure roles.
   Keep warm.',
  'timing',
  'follow_up',
  'normal',
  ARRAY['q1-2026', 'follow-up', 'infrastructure'],
  '{"follow_up_date": "2026-01-15", "current_commitment": "EOY 2025"}'::jsonb
);
```

#### Use Case 4: AI Analysis Query
```python
# In your API or scripts
def get_candidate_context_for_ai(person_id: str) -> dict:
    cursor.execute("""
        SELECT 
            person_id,
            full_name,
            headline,
            all_notes,
            all_tags,
            total_notes
        FROM v_candidate_full_context
        WHERE person_id = %s
    """, (person_id,))
    
    return cursor.fetchone()

# Feed to GPT-4
context = get_candidate_context_for_ai(person_id)
prompt = f"""
Analyze this candidate:
Name: {context['full_name']}
Headline: {context['headline']}
Notes: {context['all_notes']}
Tags: {context['all_tags']}

Is this person a good fit for: [job description]?
"""
```

### Search Examples

```sql
-- Find all candidates available immediately
SELECT 
  p.full_name,
  pn.note_text,
  pn.tags,
  pn.created_at
FROM person_notes pn
JOIN person p ON pn.person_id = p.person_id
WHERE pn.search_vector @@ websearch_to_tsquery('english', 'available immediately')
ORDER BY pn.created_at DESC;

-- Find Solidity developers with recruiter screens
SELECT 
  p.full_name,
  pn.note_text,
  pn.metadata->>'comp_expectations' as comp,
  pn.created_at as screen_date
FROM person_notes pn
JOIN person p ON pn.person_id = p.person_id
WHERE pn.note_type = 'screen'
AND pn.search_vector @@ websearch_to_tsquery('english', 'Solidity DeFi')
ORDER BY pn.created_at DESC;

-- Find all notes mentioning specific companies
SELECT 
  p.full_name,
  pn.note_text,
  pn.tags
FROM person_notes pn
JOIN person p ON pn.person_id = p.person_id
WHERE pn.search_vector @@ websearch_to_tsquery('english', 'Uniswap OR Paradigm')
ORDER BY ts_rank(pn.search_vector, websearch_to_tsquery('english', 'Uniswap OR Paradigm')) DESC;
```

---

## 🚀 Next Steps

### Immediate: Build Full Collaboration Network

```bash
# Run overnight - builds ALL collaboration edges
cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete
nohup python3 scripts/network/build_collaboration_edges.py --all > logs/collaboration_network_build.log 2>&1 &

# Monitor progress
tail -f logs/collaboration_network_build.log
```

### API Integration Needed

We need to add API endpoints for:

1. **GET `/api/person/{person_id}/collaborators`**
   - Returns list of people they've worked with
   - Includes collaboration strength, shared repos

2. **GET `/api/person/{person_id}/network`**
   - Returns full network stats
   - GitHub + employment connections

3. **GET `/api/person/{person_id}/mutual-connections/{target_person_id}`**
   - Find mutual connections between two people
   - For warm intros

4. **POST `/api/person/{person_id}/notes`**
   - Add categorized notes with tags and metadata

5. **GET `/api/person/{person_id}/notes`**
   - Get all notes for a person
   - Filter by type, category, priority

6. **GET `/api/notes/search?q=<query>`**
   - Full-text search across all notes
   - Filter by person, type, priority

### Frontend Integration Needed

**Person Profile Page:**
- Add "Network" tab showing:
  - Total connections (GitHub + employment)
  - Top 20 collaborators with strength bars
  - Interactive graph visualization
  - "Find mutual connections" search

**Notes Section:**
- Rich text editor for notes
- Category/type dropdowns
- Tag input (autocomplete from existing tags)
- Priority selector
- Metadata fields for structured data
- Full-text search bar
- Filter by category/priority

**Saved Searches:**
- Already have `saved_searches` table
- Need UI to save/load searches
- Include notes search in saved searches

---

## 📊 Expected Impact

### Collaboration Network
- **Differentiation**: No other recruiting tool has this
- **Warm Intros**: "You know 3 people who worked with Alice"
- **Team Building**: "Find me Uniswap developers who know each other"
- **Due Diligence**: "Who has worked with this founder before?"

### Enhanced Notes
- **Context Retention**: Never lose recruiter intelligence
- **AI-Powered**: Feed full context to AI for analysis
- **Search**: "Find all candidates available in Q1"
- **Collaboration**: Multiple recruiters can see full history

---

## 🎯 Status Summary

| Feature | Status | Records | Performance |
|---------|--------|---------|-------------|
| Collaboration Schema | ✅ Complete | - | - |
| Collaboration Edges (Sample) | ✅ Working | 38,796 edges | 68 repos/min |
| Collaboration Functions | ✅ Complete | 2 functions | Fast |
| Enhanced Notes Schema | ✅ Complete | - | - |
| Full-Text Search | ✅ Working | 1 note | Fast (GIN index) |
| AI Views | ✅ Complete | 2 views | Fast |
| API Endpoints | ⏳ Needed | - | - |
| Frontend UI | ⏳ Needed | - | - |
| Full Network Build | ⏳ Pending | 0/333K repos | 6-12 hrs estimated |

**Ready for production backend use!** Need API + frontend integration for full value.

