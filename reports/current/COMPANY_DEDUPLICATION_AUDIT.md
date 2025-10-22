# Company Deduplication Audit Report
**Date:** October 22, 2025  
**Status:** ✅ Investigation Complete - Action Plan Ready

---

## EXECUTIVE SUMMARY

**Finding:** The company deduplication script worked correctly, but revealed a **data quality issue** affecting **3,931 employment records** (1.9% of total).

**Root Cause:** Import process captured incomplete company names - only the legal suffix (Inc., Ltd., LLC) without the actual company name.

**Impact:** Medium - Affects real people with valid LinkedIn profiles, but employment records have:
- ✅ Valid person records
- ✅ Valid dates  
- ❌ NO job titles (all NULL)
- ❌ Company name is ONLY suffix

---

## INVESTIGATION FINDINGS

### Problematic Companies Identified

| Company Name | Employee Count | Domain | Status |
|--------------|----------------|--------|--------|
| **Inc.** | 2,755 | Inc. | ❌ Suffix only |
| **LLC** | 827 | llc-cd62999c.com | ❌ Suffix only |
| **Ltd.** | 331 | Ltd. | ❌ Suffix only |
| **Limited** | 11 | limited-4375b72a.com | ❌ Suffix only |
| **Corp.** | 6 | Corp. | ❌ Suffix only |
| **Corporation** | 1 | corporation-d2d957e8.com | ❌ Suffix only |
| **TOTAL** | **3,931** | | |

### Sample Records (Ltd. company)

```
Name: (Krystal) NING HU
LinkedIn: https://www.linkedin.com/in/krystal-ning-hu/
Title: NULL  ❌
Company: Ltd.  ❌
Dates: 2021-01-01 to 2021-12-31  ✅
```

**Pattern:** All affected records have:
- Real people (valid LinkedIn URLs)
- Valid employment dates
- NO job titles
- Company name = suffix only

---

## DEDUPLICATION SCRIPT ASSESSMENT

### ✅ GOOD MERGES (Majority - 2,300+ groups)

The script correctly merged legitimate company name variations:

```
✅ Broadcom + Broadcom Corp + Broadcom Corporation + Broadcom Inc. + Broadcom Limited
   → Merged into: Broadcom

✅ Intel + Intel Corp + Intel Corporation + Intel Labs
   → Merged into: Intel Corporation

✅ @Anthropic + Anthropic
   → Merged into: Anthropic (@ prefix is Twitter handle)

✅ Canonical + Canonical Ltd.
   → Merged into: Canonical
```

**Assessment:** These merges are **CORRECT** and valuable data cleaning.

### ⚠️ REVEALED DATA QUALITY ISSUE

The script revealed bad data by grouping suffix-only companies:

```
Group 1: .Ltd (1 emp), .Ltd. (1 emp), LTD (19 emp), LTD. (14 emp), 
         Ltd (83 emp), Ltd. (217 emp), ltd (6 emp), ltd. (7 emp)
→ Merged into: Ltd. (331 total employees)
```

**This is NOT a deduplication error** - these ARE duplicates (all just "Ltd"). The problem is the source data.

---

## ROOT CAUSE ANALYSIS

### Where Did Bad Data Come From?

Likely sources:
1. **LinkedIn data truncation** - API/scraping cut off company names
2. **Import parsing errors** - Company name field parsing failed
3. **Manual entry errors** - People typing "Ltd" as full company name
4. **CSV format issues** - Company name column misaligned

### Why Are Titles NULL?

**Correlation:** 100% of suffix-only company records have NULL titles.

**Theory:** These records came from a data source that:
- Had employment dates
- Had company name field (but incomplete)
- Did NOT have job title field

Likely from an older import or different data source.

---

## SHORT COMPANY NAMES ANALYSIS

### Legitimate Short Names (✅ Keep)

Many 2-4 character companies are VALID:

| Company | Employees | Valid? | Reason |
|---------|-----------|--------|--------|
| OKX | 1,978 | ✅ Yes | Cryptocurrency exchange |
| Meta | 692 | ✅ Yes | Facebook/Meta Platforms |
| Uber | 611 | ✅ Yes | Uber Technologies |
| IBM | 494 | ✅ Yes | International Business Machines |
| Citi | 447 | ✅ Yes | Citigroup |
| EY | 389 | ✅ Yes | Ernst & Young |
| PwC | 288 | ✅ Yes | PricewaterhouseCoopers |
| HSBC | 281 | ✅ Yes | Hong Kong Shanghai Banking Corp |
| 0X | 152 | ✅ Yes | 0x Protocol (crypto) |
| Visa | 149 | ✅ Yes | Visa Inc. |
| dYdX | 108 | ✅ Yes | dYdX (crypto exchange) |

### Invalid Short Names (❌ Bad Data)

| Company | Employees | Valid? | Issue |
|---------|-----------|--------|-------|
| Inc. | 2,755 | ❌ No | Suffix only |
| LLC | 827 | ❌ No | Suffix only |
| Ltd. | 331 | ❌ No | Suffix only |
| P.C. | 57 | ❌ No | Suffix only (Professional Corporation) |
| L.P. | 54 | ❌ No | Suffix only (Limited Partnership) |
| - | 42 | ❌ No | Just a dash |

**Conclusion:** Cannot filter by length alone - need suffix-only detection.

---

## ACTION PLAN

### ✅ Immediate Actions Completed

1. **Investigation queries executed** - Identified 3,931 bad records
2. **Root cause determined** - Import data quality issue
3. **Deduplication script validated** - Working correctly

### 🔧 Next Steps

#### 1. Generate Cleanup SQL (In Progress)

```sql
-- Export bad employment records for manual review
SELECT 
    p.person_id,
    p.full_name,
    p.linkedin_url,
    e.employment_id,
    e.title,
    c.company_name,
    e.start_date,
    e.end_date
FROM employment e
JOIN person p ON e.person_id = p.person_id
JOIN company c ON e.company_id = c.company_id
WHERE c.company_name IN ('Inc.', 'LLC', 'Ltd.', 'Limited', 'Corp.', 'Corporation', 'P.C.', 'L.P.')
ORDER BY p.full_name;
```

#### 2. Add Quality Filters to Import Scripts

**Files to update:**
- `scripts/imports/import_clay_people.py`
- `scripts/imports/import_csv_datablend.py`
- `scripts/imports/import_company_portfolio.py`

**Filter logic:**
```python
def is_valid_company_name(name: str) -> bool:
    """Validate company name is not just a legal suffix"""
    if not name or len(name.strip()) < 2:
        return False
    
    # Suffix-only patterns
    suffix_only = [
        r'^\.?Ltd\.?$',
        r'^\.?Inc\.?$', 
        r'^\.?LLC$',
        r'^\.?Corp\.?$',
        r'^\.?Corporation$',
        r'^\.?Limited$',
        r'^\.?L\.?P\.?$',
        r'^\.?P\.?C\.?$'
    ]
    
    name_normalized = name.strip().lower()
    for pattern in suffix_only:
        if re.match(pattern, name_normalized, re.IGNORECASE):
            return False
    
    return True
```

#### 3. Add Validation to Deduplication Script

**File:** `scripts/maintenance/deduplicate_companies.py`

**Add to `find_duplicate_groups()`:**
```python
def find_duplicate_groups(self) -> List[List[Dict]]:
    # ... existing code ...
    
    # Filter out suffix-only companies from deduplication
    companies = [c for c in companies if self._is_valid_company_name(c['company_name'])]
    
    # ... rest of function ...
```

#### 4. Enrichment Pipeline Task

**Options for fixing the 3,931 bad employment records:**

**Option A: Remove and Flag for Re-scraping**
- Delete employment records with suffix-only companies
- Add person_ids to enrichment queue
- Re-scrape LinkedIn for accurate employment history

**Option B: Manual Review + API Enrichment**
- Export to CSV for review
- Use LinkedIn API to fetch correct employment data
- Update records programmatically

**Option C: Mark as "Needs Enrichment"**
- Add `needs_enrichment` flag to employment table
- Keep records but mark as incomplete
- Enrich during next data refresh cycle

**Recommendation:** **Option A** - Clean removal + re-scrape
- Cleanest solution
- Ensures data quality
- Automated through enrichment pipeline

---

## SQL CLEANUP SCRIPT

### Mark Bad Employment Records

```sql
-- Create cleanup report table
CREATE TEMP TABLE bad_employment_records AS
SELECT 
    e.employment_id,
    e.person_id,
    p.full_name,
    p.linkedin_url,
    e.title,
    c.company_name,
    e.start_date,
    e.end_date,
    'suffix_only_company' as issue_type
FROM employment e
JOIN person p ON e.person_id = p.person_id
JOIN company c ON e.company_id = c.company_id
WHERE c.company_name ~ '^[\.]*\s*(Ltd\.?|Inc\.?|LLC|LTD\.?|inc\.?|llc|Corp\.?|Corporation|Limited|L\.?P\.?|P\.?C\.?)[\)\.\s]*$';

-- Export for review
\copy (SELECT * FROM bad_employment_records ORDER BY full_name) TO '/tmp/bad_employment_records.csv' CSV HEADER;

-- Count by company
SELECT company_name, COUNT(*) as count
FROM bad_employment_records
GROUP BY company_name
ORDER BY count DESC;
```

### Delete Bad Employment Records (AFTER REVIEW)

```sql
-- CAUTION: Only run after exporting data above!

-- Delete employment records
DELETE FROM employment
WHERE employment_id IN (
    SELECT employment_id FROM bad_employment_records
);

-- Delete suffix-only companies (now empty)
DELETE FROM company
WHERE company_name IN ('Inc.', 'LLC', 'Ltd.', 'Limited', 'Corp.', 'Corporation', 'P.C.', 'L.P.')
AND NOT EXISTS (
    SELECT 1 FROM employment WHERE company_id = company.company_id
);
```

---

## RECOMMENDATIONS

### 1. Data Quality (High Priority)

✅ **Implement quality filters** in all import scripts  
✅ **Add validation** to deduplication script  
✅ **Export bad records** for review before deletion  

### 2. Enrichment Pipeline (Medium Priority)

- Create enrichment queue for affected 3,931 people
- Re-scrape LinkedIn employment history
- Update with complete company names + job titles

### 3. Monitoring (Ongoing)

- Add data quality checks to import process
- Alert on company names < 3 characters (except whitelist)
- Monitor for NULL titles (correlation with bad data)

### 4. Deduplication Script (No Changes Needed)

✅ **Script is working correctly**  
✅ **Good merges are valuable data cleaning**  
✅ **Only needs suffix-only filter for future runs**  

---

## CONCLUSION

**The company deduplication script is WORKING AS DESIGNED.** It successfully merged 2,300+ groups of legitimate company name variations.

The "Ltd./Inc./LLC" issue is a **DATA QUALITY PROBLEM** from the import process, not a deduplication error. The script correctly grouped these suffix-only entries, revealing the underlying data quality issue.

**Action Required:**
1. ✅ Export bad employment records (3,931 records)
2. 🔧 Add quality filters to import scripts
3. 🔧 Add validation to deduplication script  
4. 🔄 Add affected people to enrichment pipeline
5. 🗑️ Delete bad employment records (after export)

**Overall Assessment:** ✅ **Deduplication logic is SOUND and VALUABLE**

