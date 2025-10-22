# CSV Import Strategy Changes

## Date: October 21, 2025

## Summary
Updated the import strategy to be more inclusive and maximize profile capture for future enrichment.

## Key Changes

### 1. **Relaxed Requirements**
- **OLD**: Required Full Name OR (First Name + Last Name) to create a profile
- **NEW**: Only requires LinkedIn URL **OR** GitHub URL

### 2. **Placeholder Names**
When a name is missing, we now generate placeholders:
- LinkedIn-only: `[LinkedIn] {username}` (extracted from URL)
- GitHub-only: `[GitHub] {username}`
- No identifier: `[Unknown Profile]`

These profiles are flagged for priority enrichment.

### 3. **GitHub-Only Profiles**
- **OLD**: Skipped if no LinkedIn URL
- **NEW**: Creates profile with NULL LinkedIn URL, links GitHub account

### 4. **LinkedIn-Only Profiles**  
- **OLD**: Required name and other data
- **NEW**: Creates profile even with just LinkedIn URL

### 5. **New Tracking Statistics**
Added three new stats to monitor:
- `github_only_profiles`: Count of profiles created with only GitHub
- `linkedin_only_profiles`: Count of profiles created with only LinkedIn
- `profiles_needing_enrichment`: Profiles with placeholder names or minimal data

## Implementation Details

### Validation Logic
```python
# Only requirement: LinkedIn URL OR GitHub URL
if not linkedin_url and not github_url:
    skip()
```

### Profile Creation
- First tries to build real name from First/Last Name
- Falls back to placeholder based on available identifier
- Tracks enrichment needs
- Inserts with NULL values for missing fields

### Deduplication Strategy
1. Match by normalized LinkedIn URL (cache lookup)
2. Match by GitHub username (cache lookup)
3. If neither match, create new profile

## Expected Outcomes

### From Current CSV (68,329 rows)
- **Previously skipped**: ~13,328 records with LinkedIn/GitHub but no name
- **Now will be imported**: All 13,328+ records
- **Total new profiles**: ~47k+ (from current ~34k enriched)

### Profile Quality
- **High quality**: Profiles with names, jobs, locations
- **Medium quality**: LinkedIn/GitHub only, need enrichment
- **Placeholder profiles**: Marked for priority enrichment

## Benefits

1. **Maximum Data Capture**: No valuable LinkedIn/GitHub URLs lost
2. **Future Enrichment Ready**: All profiles stored for API enrichment
3. **GitHub Account Tracking**: All GitHub profiles linked for contribution analysis
4. **Deduplication**: Still prevents duplicate profiles via LinkedIn/GitHub matching

## Next Steps

1. Run updated import on CSV
2. Review new profiles marked for enrichment
3. Set up automated enrichment pipeline for placeholder profiles
4. Consider LinkedIn/GitHub API integration for batch enrichment

## Query for Priority Enrichment Profiles

```sql
-- Find all profiles needing enrichment
SELECT 
    person_id,
    full_name,
    linkedin_url,
    location,
    headline
FROM person
WHERE 
    full_name LIKE '[%'  -- Placeholder names start with [
    OR (linkedin_url IS NOT NULL AND full_name IS NULL)
    OR (headline IS NULL AND location IS NULL)
ORDER BY refreshed_at DESC NULLS LAST;
```

## Rollback Instructions

If needed, the old validation can be restored by:
1. Reverting to previous version of `import_csv_datablend.py`
2. Or manually removing placeholder profiles:

```sql
-- Remove placeholder profiles (CAUTION: TEST FIRST)
DELETE FROM person 
WHERE full_name LIKE '[LinkedIn]%' 
   OR full_name LIKE '[GitHub]%'
   OR full_name = '[Unknown Profile]';
```

