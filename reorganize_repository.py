#!/usr/bin/env python3
"""
Repository Reorganization Script
Automatically reorganizes the talent-intelligence-complete repository
according to REPOSITORY_AUDIT_2025.md

Author: System
Date: October 22, 2025
"""

import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

# Base directory
BASE_DIR = Path(__file__).parent.resolve()

# Reorganization plan - all paths relative to BASE_DIR
MOVES = {
    # Log files to logs/diagnostics/
    'logs/diagnostics/': [
        'diagnostic_results_20251022_144451.log',
        'emergency_fix_20251022_145538.log',
        'full_diagnostic_20251022_150837.log',
    ],
    
    # Log files to logs/imports/
    'logs/imports/': [
        'company_import_log.txt',
        'import_log.txt',
        'batch_discovery_log.txt',
        'github_matching_20251022_150638.log',
    ],
    
    # Log files to logs/enrichment/
    'logs/enrichment/': [
        'enrichment_continuous.log',
        'enrichment_1000.log',
        'enrichment_run.log',
        'github_enrichment_log.txt',
    ],
    
    # Log files to logs/deduplication/
    'logs/deduplication/': [
        'deduplication_live_run.log',
        'company_deduplication_20251022_111938.log',
    ],
    
    # Reports to reports/current/
    'reports/current/': [
        'DATABASE_STATE_OCTOBER_22_2025.md',
        'PERFORMANCE_FIX_SUMMARY.md',
    ],
    
    # Reports to reports/historical/
    'reports/historical/': [
        'clay_import_report_20251022_103702.txt',
        'company_import_report_20251021_202320.txt',
        'company_import_report_20251021_202435.txt',
        'company_import_report_20251021_202505.txt',
        'database_deep_dive_report.txt',
        'import_report_20251021_175543.txt',
        'import_report_20251021_175813.txt',
        'import_report_20251021_180151.txt',
        'import_report_20251021_183146.txt',
        'import_analysis_report.txt',
        'database_analysis_report.txt',
        'github_enrichment_report.txt',
        'deduplication_report.txt',
        'data_quality_report.txt',
        'company_quality_report.txt',
        'post_enrichment_analysis.txt',
    ],
    
    # CSV/Data files to data/imports/
    'data/imports/': [
        'companies_need_github_org.csv',
        'companies_to_discover.csv',
        'sample_200_candidates.csv',
    ],
    
    # GitHub CSV files to data/github/
    'data/github/': [
        'GitHub_Contributors-Default-view-export-1760735472022.csv',
        'GitHub_Org-Default-view-export-1760738884784.csv',
    ],
    
    # Database files to archived_databases/
    'archived_databases/': [
        'talent_intelligence_backup_20251019_115502.db',
    ],
    
    # Scripts to scripts/database/
    'scripts/database/': [
        'backup_database.py',
        'query_database_secure.py',
        'check_data_quality.py',
    ],
    
    # Scripts to scripts/diagnostics/
    'scripts/diagnostics/': [
        'diagnostic_check.py',
        'emergency_diagnostic.py',
        'verify_performance.py',
        'monitor_hung_queries.py',
        'kill_hung_queries.py',
    ],
    
    # Scripts to scripts/imports/
    'scripts/imports/': [
        'import_clay_people.py',
        'import_csv_datablend.py',
        'import_company_portfolio.py',
    ],
    
    # Scripts to scripts/github/
    'scripts/github/': [
        'match_github_profiles.py',
        'discover_company_github.py',
        'enrich_github_continuous.py',
    ],
    
    # Scripts to scripts/maintenance/
    'scripts/maintenance/': [
        'deduplicate_companies.py',
        'populate_coemployment_graph.py',
    ],
    
    # SQL files to sql/maintenance/
    'sql/maintenance/': [
        'emergency_performance_fix.sql',
    ],
    
    # SQL files to sql/queries/
    'sql/queries/': [
        'sample_queries.sql',
        'enrichment_summary.sql',
    ],
    
    # SQL files to sql/analysis/
    'sql/analysis/': [
        'comprehensive_analysis.sql',
    ],
    
    # Status docs to archived_documentation/milestones/
    'archived_documentation/milestones/': [
        'API_AND_DASHBOARD_COMPLETE.md',
        'GITHUB_AUTOMATION_COMPLETE.md',
        'GITHUB_CONSOLIDATION.md',
        'MIGRATION_COMPLETE.md',
        'SCRIPT_CONSOLIDATION_COMPLETE.md',
        'SCRIPT_ORGANIZATION_COMPLETE.md',
        'DOCUMENTATION_ORGANIZATION_COMPLETE.md',
        'IMPLEMENTATION_STATUS.md',
        'AUDIT_RESULTS_README.md',
    ],
    
    # Docs to docs/
    'docs/': [
        'CLAY_IMPORT_README.md',
        'GITHUB_DISCOVERY_SUMMARY.md',
        'IMPORT_STRATEGY_CHANGES.md',
    ],
}

# Files to rename during move
RENAMES = {
    'CLAY_IMPORT_README.md': 'CLAY_IMPORT.md',
    'GITHUB_DISCOVERY_SUMMARY.md': 'GITHUB_DISCOVERY.md',
    'IMPORT_STRATEGY_CHANGES.md': 'IMPORT_STRATEGY.md',
}


def create_directories():
    """Create all necessary directories"""
    print("📁 Creating directory structure...")
    directories = list(MOVES.keys())
    
    for directory in directories:
        dir_path = BASE_DIR / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created: {directory}")
    
    print()


def move_files(dry_run=True):
    """Move files according to the plan"""
    print(f"📦 {'[DRY RUN]' if dry_run else '[LIVE]'} Moving files...")
    
    moved_count = 0
    skipped_count = 0
    error_count = 0
    
    for dest_dir, files in MOVES.items():
        for file in files:
            src_path = BASE_DIR / file
            
            # Check if file should be renamed
            new_name = RENAMES.get(file, file)
            dest_path = BASE_DIR / dest_dir / new_name
            
            # Check if source exists
            if not src_path.exists():
                print(f"  ⚠️  SKIP: {file} (not found)")
                skipped_count += 1
                continue
            
            # Check if destination already exists
            if dest_path.exists():
                print(f"  ⚠️  SKIP: {file} (destination exists)")
                skipped_count += 1
                continue
            
            try:
                if not dry_run:
                    shutil.move(str(src_path), str(dest_path))
                    print(f"  ✓ Moved: {file} → {dest_dir}{new_name}")
                else:
                    print(f"  📋 Would move: {file} → {dest_dir}{new_name}")
                moved_count += 1
            except Exception as e:
                print(f"  ❌ ERROR: {file} - {str(e)}")
                error_count += 1
    
    print()
    print(f"Summary: {moved_count} moved, {skipped_count} skipped, {error_count} errors")
    print()


def create_readme_files():
    """Create README files for new directories"""
    print("📝 Creating README files...")
    
    readmes = {
        'reports/README.md': """# Reports Directory

This directory contains analysis reports and audit results.

## Structure

- `current/` - Active reports reflecting the current system state
- `historical/` - Historical reports and analyses from previous dates

## Recent Reports

Check `current/` for the most up-to-date information:
- `DATABASE_STATE_*.md` - Current database statistics
- `PERFORMANCE_FIX_*.md` - Performance optimization reports
""",
        
        'scripts/README.md': """# Scripts Directory

User-facing scripts for database operations, imports, and maintenance.

## Structure

- `database/` - Database operations (backup, query, quality checks)
- `diagnostics/` - Diagnostic and monitoring tools
- `imports/` - Data import scripts (Clay, CSV, etc.)
- `github/` - GitHub profile matching and discovery
- `maintenance/` - System maintenance (deduplication, graph population)

## Usage

All scripts can be run directly from this directory:

```bash
# Database operations
python database/backup_database.py
python database/check_data_quality.py

# Diagnostics
python diagnostics/diagnostic_check.py
python diagnostics/monitor_hung_queries.py

# Imports
python imports/import_clay_people.py

# GitHub
python github/match_github_profiles.py

# Maintenance
python maintenance/deduplicate_companies.py
```
""",
        
        'sql/README.md': """# SQL Directory

SQL scripts and queries for database operations.

## Structure

- `schema/` - Schema definitions and migrations
- `maintenance/` - Database maintenance scripts (VACUUM, indexing)
- `queries/` - Common queries and examples
- `analysis/` - Complex analysis queries

## Usage

Run SQL scripts with:

```bash
psql -d talent -f sql/maintenance/emergency_performance_fix.sql
psql -d talent -f sql/queries/sample_queries.sql
```
""",
        
        'data/README.md': """# Data Directory

CSV files and data exports.

## Structure

- `imports/` - Source CSV files for imports
- `github/` - GitHub data exports
- `exports/` - Database exports and samples

## Note

CSV files are typically ignored by git (see `.gitignore`).
This directory is for organizing local data files.
""",
    }
    
    for path, content in readmes.items():
        readme_path = BASE_DIR / path
        if not readme_path.exists():
            readme_path.parent.mkdir(parents=True, exist_ok=True)
            readme_path.write_text(content)
            print(f"  ✓ Created: {path}")
    
    print()


def generate_log():
    """Generate a detailed log of the reorganization"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = BASE_DIR / f'reorganization_log_{timestamp}.txt'
    
    with open(log_path, 'w') as f:
        f.write(f"Repository Reorganization Log\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*80}\n\n")
        
        f.write(f"Files to be moved: {sum(len(files) for files in MOVES.values())}\n")
        f.write(f"New directories: {len(MOVES)}\n\n")
        
        f.write(f"{'='*80}\n")
        f.write(f"DETAILED PLAN\n")
        f.write(f"{'='*80}\n\n")
        
        for dest_dir, files in MOVES.items():
            f.write(f"\n{dest_dir}\n")
            f.write(f"{'-'*len(dest_dir)}\n")
            for file in files:
                new_name = RENAMES.get(file, file)
                if new_name != file:
                    f.write(f"  {file} → {new_name}\n")
                else:
                    f.write(f"  {file}\n")
    
    print(f"📄 Generated log: {log_path.name}")
    print()
    return log_path


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("TALENT INTELLIGENCE REPOSITORY REORGANIZATION")
    print("="*80 + "\n")
    
    # Check if we're in the right directory
    if not (BASE_DIR / 'talent_intelligence.db').exists() and \
       not (BASE_DIR / 'config.py').exists():
        print("❌ Error: Not in the correct directory!")
        print(f"   Current: {BASE_DIR}")
        sys.exit(1)
    
    # Parse arguments
    dry_run = '--execute' not in sys.argv
    
    if dry_run:
        print("🔍 DRY RUN MODE - No files will be moved")
        print("   Use --execute flag to perform actual reorganization\n")
    else:
        print("⚠️  LIVE MODE - Files will be moved!")
        print("   Press Ctrl+C within 5 seconds to cancel...")
        import time
        for i in range(5, 0, -1):
            print(f"   {i}...", end='\r')
            time.sleep(1)
        print("   Starting reorganization...\n")
    
    # Execute reorganization
    try:
        create_directories()
        move_files(dry_run=dry_run)
        
        if not dry_run:
            create_readme_files()
            log_path = generate_log()
        
        print("="*80)
        if dry_run:
            print("✅ DRY RUN COMPLETE")
            print("   Run with --execute flag to perform actual reorganization")
        else:
            print("✅ REORGANIZATION COMPLETE")
            print(f"   Log saved to: {log_path.name}")
        print("="*80 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()

