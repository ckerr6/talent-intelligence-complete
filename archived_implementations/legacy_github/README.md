# Legacy GitHub Scripts Archive

This directory contains legacy GitHub-related scripts that have been superseded by the modern `github_automation/` package and `enrich_github_continuous.py`.

## Archived Scripts

### Enrichment Scripts
- `github_enrichment.py` - Original GitHub enrichment script
  - **Replaced by:** `enrich_github_continuous.py`
  - **Reason:** Superseded by continuous enrichment system

- `github_api_enrichment.py` - GitHub API enrichment functionality
  - **Replaced by:** `github_automation/github_client.py`
  - **Reason:** Integrated into modern GitHub automation package

### Queue Management
- `github_queue_manager.py` - GitHub queue management
  - **Replaced by:** `github_automation/queue_manager.py`
  - **Reason:** Improved queue management in automation package

### Building Scripts
- `build_github_enrichment.py` - GitHub enrichment building script
  - **Replaced by:** `github_automation/enrichment_engine.py`
  - **Reason:** Core functionality moved to enrichment engine

### Matching Scripts
- `match_github_profiles.py` - GitHub profile matching
  - **Replaced by:** `github_automation/matcher.py`
  - **Reason:** Improved matching logic in automation package

## Migration History

These scripts represent the evolution of GitHub functionality:

1. **Phase 1:** Individual scripts for specific GitHub tasks
2. **Phase 2:** Consolidated into `github_automation/` package
3. **Phase 3:** Continuous enrichment system with `enrich_github_continuous.py`

## Current System

The current GitHub system uses:
- `github_automation/` - Modern package with all core functionality
- `enrich_github_continuous.py` - Continuous enrichment system
- `diagnostic_tools/diagnose_github.py` - System diagnostics

## Note

These scripts are preserved for historical reference and should not be used in the current system. All functionality has been migrated to the modern GitHub automation package.
