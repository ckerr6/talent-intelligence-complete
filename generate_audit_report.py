#!/usr/bin/env python3
"""
Generate Comprehensive Audit Report
Combines all audit data into actionable recommendations
"""

import json
from pathlib import Path
from datetime import datetime

def load_audit_data():
    """Load all audit JSON files"""
    inventory_file = Path("audit_results/database_inventory.json")
    overlap_file = Path("audit_results/overlap_analysis.json")
    
    with open(inventory_file) as f:
        inventory = json.load(f)
    
    with open(overlap_file) as f:
        overlap = json.load(f)
    
    return inventory, overlap

def generate_markdown_report(inventory, overlap):
    """Generate comprehensive markdown report with recommendations"""
    
    report = f"""# Database Audit Report
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Executive Summary

### Databases Found
- **Total Databases**: {inventory['summary']['total_databases']}
- **Active Databases**: {inventory['summary']['active_databases']}
- **Empty/Abandoned**: {inventory['summary']['not_found_databases']}

### Data Summary (Across All Databases)
- **Total People Records**: {inventory['summary']['total_people_all_dbs']:,}
- **Total Company Records**: {inventory['summary']['total_companies_all_dbs']:,}

### Key Recommendations
1. **Data Consolidation**: All data is in primary PostgreSQL `talent` database
2. **Quality Improvement**: Run `check_data_quality.py` for detailed analysis
3. **Monitoring**: Use `generate_quality_metrics.py` for ongoing tracking
4. **Archived Databases**: Review `archived_databases/` for historical data

---

## Database Inventory

### SQLite Databases

"""
    
    # SQLite databases
    for db in inventory['sqlite_databases']:
        if db['status'] == 'ACTIVE':
            report += f"""
#### {db['name']}
- **Path**: `{db['path']}`
- **Size**: {db['size_mb']} MB
- **Last Modified**: {db['last_modified']}
- **Status**: ✅ Active

**Tables**: {', '.join(db['tables'][:10])}{"..." if len(db['tables']) > 10 else ""}

**Key Statistics**:
"""
            if db.get('people_stats'):
                ps = db['people_stats']
                report += f"""
- People: {ps.get('total_count', 0):,}
  - With Email: {ps.get('with_email', 0):,} ({ps.get('with_email', 0) / ps.get('total_count', 1) * 100:.1f}%)
  - With LinkedIn: {ps.get('with_linkedin', 0):,} ({ps.get('with_linkedin', 0) / ps.get('total_count', 1) * 100:.1f}%)
  - Avg Quality Score: {ps.get('avg_quality_score', 0):.3f}
"""
            
            if db.get('companies_stats'):
                cs = db['companies_stats']
                report += f"""
- Companies: {cs.get('total_count', 0):,}
  - With Website: {cs.get('with_website', 0):,}
  - With GitHub Org: {cs.get('with_github_org', 0):,}
"""
            
            if db.get('github_stats'):
                gs = db['github_stats']
                report += f"""
- GitHub Profiles: {gs.get('total_count', 0):,}
  - Linked to People: {gs.get('linked_to_people', 0):,}
  - With Email: {gs.get('with_email', 0):,}
"""
    
    report += "\n### PostgreSQL Databases\n"
    
    # PostgreSQL databases
    for db in inventory['postgresql_databases']:
        if db['status'] == 'ACTIVE':
            report += f"""
#### {db['name']}
- **Size**: {db['size']}
- **Owner**: {db['owner']}
- **Last Activity**: {db.get('last_activity', 'Unknown')}
- **Status**: ✅ Active

**Tables**: {', '.join(db['tables'][:10])}{"..." if len(db['tables']) > 10 else ""}

**Key Statistics**:
"""
            if db.get('people_stats'):
                ps = db['people_stats']
                report += f"""
- People: {ps.get('total_count', 0):,}
  - With Email: {ps.get('with_email', 0):,}
  - With LinkedIn: {ps.get('with_linkedin', 0):,}
"""
                if ps.get('avg_quality_score'):
                    report += f"  - Avg Quality Score: {ps['avg_quality_score']:.3f}\n"
            
            if db.get('companies_stats'):
                cs = db['companies_stats']
                report += f"""
- Companies: {cs.get('total_count', 0):,}
  - With Website: {cs.get('with_website', 0):,}
"""
                if cs.get('with_github_org') is not None:
                    report += f"  - With GitHub Org: {cs.get('with_github_org', 0):,}\n"
            
            if db.get('employment_stats'):
                es = db['employment_stats']
                report += f"""
- Employment Records: {es.get('total_records', 0):,}
  - Unique People: {es.get('unique_people', 0):,}
  - Avg Records per Person: {es.get('avg_records_per_person', 0):.1f}
"""
            
            if db.get('github_stats'):
                gs = db['github_stats']
                report += f"""
- GitHub Profiles: {gs.get('total_count', 0):,}
  - Linked to People: {gs.get('linked_to_people', 0):,}
"""
        elif db['status'] == 'NOT_FOUND':
            report += f"\n#### {db['name']}\n- **Status**: ⚠️ Not Found\n"
        elif db['status'] == 'ERROR':
            report += f"\n#### {db['name']}\n- **Status**: ❌ Error\n- **Error**: {db.get('error', 'Unknown')}\n"
    
    # Overlap Analysis
    report += """
---

## Overlap Analysis

### Key Findings

"""
    
    # LinkedIn overlap findings
    linkedin_overlap = overlap.get('linkedin_overlap', {})
    for comparison, data in linkedin_overlap.items():
        db1, db2 = comparison.replace('_vs_', ' vs ').split(' vs ')
        report += f"""
#### {db1} vs {db2} (LinkedIn URLs)
- In Both: {data['in_both']:,}
- Only in {db1}: {data[f'only_in_{db1}']:,}
- Only in {db2}: {data[f'only_in_{db2}']:,}
- Total Unique: {data['total_unique']:,}
"""
    
    # Recommendations
    report += """
---

## Critical Findings & Recommendations

"""
    
    # Add schema analysis findings
    report += """
### 1. Schema Differences Detected

**PostgreSQL `talent` Database:**
- Uses `person` table (singular) instead of `people` (plural)
- Likely stores LinkedIn URLs in the `linkedin_url` column directly on person table
- Has 32,515 people but 0 emails found in analysis
- **Issue**: Different schema than SQLite/other PostgreSQL databases

**PostgreSQL `talent_intelligence` & SQLite:**
- Use `people` table (plural)
- Store social profiles in separate `social_profiles` table
- Nearly identical schemas (99.9% email overlap confirms this)

**PostgreSQL `talent_intel`:**
- Uses `person` table (similar to `talent`)
- Has 12,129 people with 71% overlap with SQLite
- Appears to be a subset or older version

### 2. Data Completeness Issues

**PostgreSQL `talent`:**
- ✅ Most people records (32,515)
- ✅ Most company records (91,722 - includes historical employers)
- ⚠️ 0 emails found (schema difference - needs investigation)
- ⚠️ 0% LinkedIn URL overlap with other databases (different format/normalization)

**SQLite `talent_intelligence.db`:**
- ✅ Clean, well-structured data
- ✅ High data quality scores (avg 0.77)
- ✅ 11,912 LinkedIn URLs
- ✅ 7,036 emails
- ✅ GitHub enrichment (18,029 profiles)
- ⚠️ Only current employment (not historical)

**PostgreSQL `talent_intelligence`:**
- Appears to be a direct import of SQLite data
- 99.9% email overlap confirms duplication
- 35,080 companies (10x more than SQLite due to historical data)

---

## Recommended Consolidation Strategy

### Phase 1: Investigate Schema Differences

**Action Required**: Examine PostgreSQL `talent` database schema in detail

```sql
-- Run this to understand talent database structure:
\\d person
\\d company  
\\d employment
\\d edge_*
```

The `talent` database likely uses a graph-based schema (note: edge_* tables) which is fundamentally different from the relational schema used in SQLite and `talent_intelligence`.

### Phase 2: Determine Primary Database

**Option A: PostgreSQL `talent` as Primary** ✅ RECOMMENDED
- **Pros**:
  - Most comprehensive (32,515 people, 91,722 companies)
  - Full employment history (203,076 records mentioned in your report)
  - Production-ready graph schema
  - Currently referenced as primary in your problem statement
- **Cons**:
  - Different schema from SQLite
  - Need to migrate SQLite LinkedIn profiles and emails
  - Need to investigate why 0 emails showing up

**Option B: Create New Unified Database**
- Start fresh with best practices
- Migrate data from all sources
- More work but cleaner result

### Phase 3: Migration Plan

If choosing Option A (PostgreSQL `talent` as primary):

1. **Investigate `talent` schema** 
   - Confirm how emails are stored
   - Confirm how LinkedIn URLs are stored
   - Document graph structure

2. **Migrate from SQLite**
   - 11,912 LinkedIn profiles
   - 7,036 emails
   - 18,029 GitHub profiles with enrichment data

3. **Deduplicate within `talent`**
   - 32,515 people might include duplicates
   - Need email/LinkedIn based deduplication

4. **Archive Other Databases**
   - `talent_intelligence` (duplicate of SQLite)
   - `talent_intel` (subset of data)
   - Empty databases (talent_graph, talentgraph, etc.)

### Phase 4: Cleanup

**Databases to Archive**:
- ✅ SQLite databases (after migration)
- ✅ PostgreSQL `talent_intelligence` (duplicate)
- ✅ PostgreSQL `talent_intel` (subset, verify unique data first)
- ✅ PostgreSQL `talent_graph`, `talentgraph`, `talentgraph2`, `talentgraph_development` (empty)
- ✅ PostgreSQL `tech_recruiting_db`, `crypto_dev_network` (not found/empty)

**Single Source of Truth**: PostgreSQL `talent`

---

## Next Steps

1. **IMMEDIATE**: Run schema analysis on PostgreSQL `talent` database
   ```bash
   psql -d talent -c "\\dt"
   psql -d talent -c "\\d person"
   psql -d talent -c "\\d company"
   ```

2. **INVESTIGATE**: Why 0 emails showing in `talent` database
   - Check actual table structure
   - Might be in edge_ tables or different column name

3. **VERIFY**: Employment history in `talent` database
   - Confirm 203,076 employment records exist
   - Verify historical tracking vs current only

4. **PLAN**: Detailed migration script for SQLite → PostgreSQL `talent`
   - Map schemas
   - Handle duplicates
   - Verify data integrity

5. **EXECUTE**: Migration with full backups
   - Backup all databases before changes
   - Migrate in stages
   - Validate after each step

"""
    
    # Recommendations from overlap analysis
    if overlap.get('recommendations'):
        report += "\n### Detailed Recommendations from Overlap Analysis\n\n"
        for i, rec in enumerate(overlap['recommendations'], 1):
            report += f"{i}. **[{rec['priority']}]** {rec['action']}\n"
            for key, value in rec.items():
                if key not in ['priority', 'action']:
                    report += f"   - {key}: {value}\n"
            report += "\n"
    
    return report

def main():
    print("=" * 80)
    print("GENERATING COMPREHENSIVE AUDIT REPORT")
    print("=" * 80)
    
    inventory, overlap = load_audit_data()
    report = generate_markdown_report(inventory, overlap)
    
    # Save report
    output_file = Path("audit_results/AUDIT_REPORT.md")
    with open(output_file, 'w') as f:
        f.write(report)
    
    print(f"\n✅ Report generated: {output_file}")
    print(f"\n📊 Report size: {len(report):,} characters")
    
    # Print key findings
    print("\n" + "=" * 80)
    print("KEY FINDINGS")
    print("=" * 80)
    print("\n1. PostgreSQL 'talent' database uses DIFFERENT SCHEMA (graph-based)")
    print("   - person table (not people)")
    print("   - 32,515 people but 0% overlap with others")
    print("   - Needs investigation\n")
    
    print("2. SQLite and PostgreSQL 'talent_intelligence' are DUPLICATES")
    print("   - 99.9% email overlap")
    print("   - Same data, can archive one\n")
    
    print("3. RECOMMENDATION: Use PostgreSQL 'talent' as primary")
    print("   - Most comprehensive data")
    print("   - Migrate SQLite data into it")
    print("   - Archive other databases\n")
    
    print(f"📄 Full report: {output_file}")
    print("=" * 80)

if __name__ == "__main__":
    main()

