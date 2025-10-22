# Employment History Re-scraping - Enrichment Pipeline

**Date:** October 22, 2025  
**Priority:** Medium  
**Status:** 📋 Queue Ready

---

## OVERVIEW

**Affected People:** 3,811 unique individuals  
**Bad Employment Records:** 4,175 records with suffix-only company names  
**Data Export:** `/tmp/enrichment_queue_employment.csv`

---

## ISSUE DESCRIPTION

These people have employment records where the company name is ONLY a legal suffix:
- "Inc." (2,860 records)
- "LLC" (836 records)
- "Ltd." (350 records)
- "P.C." (57 records)
- "L.P." (54 records)
- Other suffixes (18 records)

**Common Pattern:**
- ❌ NO job title (all NULL)
- ❌ Company name = suffix only
- ✅ Valid employment dates (avg 2.5 years duration)
- ✅ Real people (valid LinkedIn URLs)

---

## ROOT CAUSE

**Import Data Quality Issue:** Company name field was truncated or parsing failed during historical imports. Likely from:
1. LinkedIn scraping API truncation
2. CSV parsing errors
3. Older import process with bugs

---

## ENRICHMENT STRATEGY

### Option 1: LinkedIn Profile Re-scraping (RECOMMENDED)

**Approach:**
1. Use LinkedIn API or scraper to fetch full employment history
2. Extract complete company names + job titles
3. Match employment records by dates
4. Update existing records or create new ones

**Pros:**
- Gets most accurate, current data
- Includes job titles
- Captures any employment changes since original import

**Cons:**
- Requires LinkedIn API access or scraping
- Rate-limited (may take days for 3,811 people)
- May hit API quotas

**Implementation:**
```python
# Pseudocode
for person_id in enrichment_queue:
    linkedin_url = get_linkedin_url(person_id)
    profile_data = scrape_linkedin_profile(linkedin_url)
    
    for employment in profile_data['employment']:
        if matches_bad_record_dates(employment, person_id):
            update_employment_record(employment)
        else:
            create_new_employment_record(employment)
    
    delete_bad_employment_records(person_id)
```

---

### Option 2: Manual Review + Bulk Update

**Approach:**
1. Export bad records to CSV
2. Manual team reviews LinkedIn profiles
3. Fills in correct company names + titles
4. Bulk import corrected data

**Pros:**
- 100% accuracy
- No API limits
- Can verify edge cases

**Cons:**
- Labor intensive (3,811 people × ~5 min each = 317 hours)
- Expensive
- Slow

**Use Case:** Small high-value subset only

---

### Option 3: Keep + Flag for Future Enrichment

**Approach:**
1. Add `needs_enrichment` boolean to employment table
2. Mark all 4,175 records as `needs_enrichment = TRUE`
3. Enrich opportunistically during normal data refreshes

**Pros:**
- Non-destructive
- Can enrich gradually
- Preserves date information

**Cons:**
- Bad data remains in database
- May confuse analytics
- No clear timeline for completion

---

## RECOMMENDED APPROACH

**Hybrid Strategy:**

### Phase 1: Immediate Cleanup (Now)
- ✅ Export bad records (DONE - `/tmp/bad_employment_records_export.csv`)
- 🔄 Delete bad employment records (pending user approval)
- 🔄 Remove suffix-only companies

### Phase 2: High-Value Re-scraping (Week 1-2)
Target people with:
- Recent employment (end_date >= 2023)
- Multiple bad records
- Frequent LinkedIn engagement (high follower count)

**Estimated:** 500-1,000 priority people

### Phase 3: Bulk Enrichment (Ongoing)
- Add remaining 2,811 people to regular enrichment queue
- Re-scrape during routine LinkedIn data refreshes
- Update as people are accessed in the system

---

## IMPLEMENTATION TASKS

### Task 1: Setup Enrichment Queue Table

```sql
CREATE TABLE IF NOT EXISTS enrichment_queue (
    queue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID REFERENCES person(person_id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    priority INT DEFAULT 0,
    status TEXT DEFAULT 'pending', -- pending, in_progress, completed, failed
    attempts INT DEFAULT 0,
    last_attempt TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB
);

CREATE INDEX idx_enrichment_queue_status ON enrichment_queue(status, priority DESC);
CREATE INDEX idx_enrichment_queue_person ON enrichment_queue(person_id);
```

### Task 2: Load Initial Queue

```sql
INSERT INTO enrichment_queue (person_id, reason, priority, metadata)
SELECT 
    person_id::uuid,
    'bad_employment_data_suffix_only' as reason,
    CASE 
        WHEN end_date >= '2023-01-01' THEN 10  -- Recent employment
        WHEN end_date >= '2020-01-01' THEN 5   -- Mid-recent
        ELSE 0                                  -- Older
    END as priority,
    jsonb_build_object(
        'company_name', company_name,
        'start_date', start_date,
        'end_date', end_date,
        'identified_at', identified_at
    ) as metadata
FROM bad_employment_records
ON CONFLICT (person_id) DO NOTHING;
```

### Task 3: Build LinkedIn Scraper Integration

**File:** `enrichment_scripts/04_rescrape_employment_history.py`

```python
#!/usr/bin/env python3
"""
Re-scrape employment history for people with bad employment data
"""

import psycopg2
from linkedin_api import Linkedin  # or your scraping library
import time

class EmploymentEnricher:
    def __init__(self):
        self.conn = psycopg2.connect(...)
        self.linkedin = Linkedin()  # Setup authentication
    
    def process_queue(self, batch_size=50):
        """Process enrichment queue in batches"""
        while True:
            # Get next batch
            people = self.get_next_batch(batch_size)
            if not people:
                break
            
            for person in people:
                try:
                    self.enrich_person(person)
                    self.mark_completed(person['person_id'])
                except Exception as e:
                    self.mark_failed(person['person_id'], str(e))
                
                time.sleep(2)  # Rate limiting
    
    def enrich_person(self, person):
        """Fetch and update employment data for one person"""
        # Scrape LinkedIn
        linkedin_data = self.linkedin.get_profile(person['linkedin_url'])
        
        # Update employment records
        for job in linkedin_data['experience']:
            self.update_or_create_employment(person['person_id'], job)
        
        # Delete old bad records
        self.delete_bad_employment(person['person_id'])
```

### Task 4: Monitoring Dashboard

Track enrichment progress:
```sql
-- Enrichment queue status
SELECT 
    status,
    priority,
    COUNT(*) as count,
    MIN(created_at) as oldest,
    MAX(created_at) as newest
FROM enrichment_queue
WHERE reason = 'bad_employment_data_suffix_only'
GROUP BY status, priority
ORDER BY priority DESC, status;
```

---

## TIMELINE & RESOURCE REQUIREMENTS

### Phase 1: Immediate Cleanup (Day 1)
- **Time:** 1 hour
- **Resources:** Database access, SQL execution
- **Deliverables:** Bad records deleted, companies cleaned

### Phase 2: High-Priority Enrichment (Weeks 1-2)
- **Time:** 2 weeks (automated)
- **Resources:** LinkedIn API access, scraper setup
- **Deliverables:** 500-1,000 priority people enriched

### Phase 3: Bulk Enrichment (Ongoing, 3-6 months)
- **Time:** Background process
- **Resources:** Continued API access
- **Deliverables:** Remaining 2,811 people enriched

---

## SUCCESS METRICS

### Completion Metrics
- [ ] 4,175 bad employment records deleted
- [ ] 8 suffix-only companies removed
- [ ] 3,811 people added to enrichment queue
- [ ] 500+ high-priority people enriched (Phase 2)
- [ ] 80%+ total enrichment completion (Phase 3)

### Quality Metrics
- [ ] Employment records have non-NULL titles
- [ ] Company names are > 4 characters (except whitelisted)
- [ ] Average data completeness score improves
- [ ] No new suffix-only companies created

---

## DATA FILES

### Exports Created
1. **Bad Employment Records:** `/tmp/bad_employment_records_export.csv` (4,175 records)
2. **Enrichment Queue:** `/tmp/enrichment_queue_employment.csv` (3,811 people)

### File Locations
- **SQL Scripts:** `sql/maintenance/cleanup_bad_employment_records.sql`
- **Audit Report:** `reports/current/COMPANY_DEDUPLICATION_AUDIT.md`
- **This Plan:** `ENRICHMENT_PIPELINE_TASKS.md`

---

## NEXT ACTIONS

### Immediate (Today)
1. ✅ Export bad records (DONE)
2. ⏳ Review `/tmp/bad_employment_records_export.csv`
3. ⏳ Approve deletion of bad records
4. ⏳ Run DELETE MODE in `cleanup_bad_employment_records.sql`

### This Week
1. ⏳ Setup enrichment_queue table
2. ⏳ Load initial queue with priorities
3. ⏳ Implement LinkedIn scraper integration
4. ⏳ Test enrichment on 10 sample people

### Ongoing
1. ⏳ Monitor enrichment progress
2. ⏳ Adjust priorities based on system usage
3. ⏳ Handle failed enrichments
4. ⏳ Report completion metrics

---

## ROLLBACK PLAN

If enrichment causes issues:
1. **Restore from export:** `/tmp/bad_employment_records_export.csv` contains all deleted data
2. **Re-import command:**
```sql
\copy employment (employment_id, person_id, title, company_name, start_date, end_date, ...) FROM '/tmp/bad_employment_records_export.csv' CSV HEADER;
```

---

## CONTACT

For questions or issues with this enrichment pipeline:
- **Documentation:** This file (`ENRICHMENT_PIPELINE_TASKS.md`)
- **SQL Scripts:** `sql/maintenance/cleanup_bad_employment_records.sql`
- **Audit Report:** `reports/current/COMPANY_DEDUPLICATION_AUDIT.md`

