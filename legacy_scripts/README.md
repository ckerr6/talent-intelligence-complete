# Legacy Scripts

This directory contains scripts that have overlapping functionality with newer implementations. These are kept for reference but should not be used for new work.

## GitHub Enrichment Overlaps

### Superseded by `github_automation/` package:
- `github_enrichment.py` - Original enrichment script
- `github_api_enrichment.py` - API-based enrichment  
- `build_github_enrichment.py` - Build enrichment
- `github_queue_manager.py` - Old queue manager

**Issue**: 4 different GitHub enrichment approaches. The `github_automation/` package supersedes these.

**Recommendation**: Use `github_automation/` package instead.

### GitHub Matching Overlaps
- `match_github_profiles.py` - Standalone matching script

**Issue**: Duplicate matching logic with `github_automation/matcher.py`

**Recommendation**: Use `github_automation/matcher.py` instead.

### Import Script Overlaps
- `import_github_orgs.py` - Standalone GitHub org import

**Issue**: Import logic is now consolidated in enrichment process

**Recommendation**: Use enrichment scripts instead.

## Current Active Alternatives

- **GitHub Automation**: `github_automation/` directory
- **Enrichment**: `enrichment_scripts/` directory  
- **Matching**: `github_automation/matcher.py`
- **Import**: `enrichment_scripts/01_import_sqlite_people.py`
