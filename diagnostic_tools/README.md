# Diagnostic Tools

This directory contains debugging and diagnostic scripts that are useful for troubleshooting but not part of regular operations.

## Contents

### Core Diagnostic Tools
- `diagnose_github.py` - GitHub debugging and diagnostics
- `investigate_talent_schema.py` - Schema investigation and analysis
- `diagnose_duplicates.sh` - Duplicate detection and analysis

### Database Analysis Tools
- `analyze_database_overlap.py` - Database overlap analysis and comparison
- `test_github_setup.py` - GitHub setup testing and validation

## Usage

These tools are kept for debugging purposes and can be run when investigating issues:

```bash
# GitHub diagnostics
python diagnostic_tools/diagnose_github.py

# Schema investigation  
python diagnostic_tools/investigate_talent_schema.py

# Duplicate analysis
bash diagnostic_tools/diagnose_duplicates.sh

# Database overlap analysis
python diagnostic_tools/analyze_database_overlap.py

# GitHub setup testing
python diagnostic_tools/test_github_setup.py
```

## When to Use Each Tool

### `diagnose_github.py`
- **When**: GitHub automation issues, API problems, rate limiting
- **What**: Tests GitHub API connectivity, token validity, rate limits
- **Output**: Connection status, API limits, error diagnostics

### `investigate_talent_schema.py`
- **When**: Database schema issues, migration problems
- **What**: Analyzes database schema, checks constraints, validates structure
- **Output**: Schema analysis, constraint violations, data integrity issues

### `diagnose_duplicates.sh`
- **When**: Suspected duplicate data, data quality issues
- **What**: Finds duplicate records across tables, analyzes patterns
- **Output**: Duplicate reports, data quality metrics

### `analyze_database_overlap.py`
- **When**: Database migration issues, data consistency problems
- **What**: Compares databases, finds overlaps, analyzes differences
- **Output**: Overlap analysis, migration recommendations

### `test_github_setup.py`
- **When**: GitHub integration setup, configuration validation
- **What**: Tests GitHub API setup, validates configuration
- **Output**: Setup validation, configuration status

## Status

These scripts are maintained for debugging but are not part of the regular workflow. Use them when investigating data quality issues or system problems.

## Integration with Main System

These diagnostic tools complement the main system's monitoring capabilities:
- **Regular Monitoring**: `python generate_quality_metrics.py`
- **Data Quality**: `python check_data_quality.py`
- **Audit Reports**: `python generate_audit_report.py`
- **Diagnostic Tools**: This directory (for deep investigation)
