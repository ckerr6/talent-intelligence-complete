# Diagnostic Tools

This directory contains debugging and diagnostic scripts that are useful for troubleshooting but not part of regular operations.

## Contents

- `diagnose_github.py` - GitHub debugging and diagnostics
- `investigate_talent_schema.py` - Schema investigation and analysis
- `diagnose_duplicates.sh` - Duplicate detection and analysis

## Usage

These tools are kept for debugging purposes and can be run when investigating issues:

```bash
# GitHub diagnostics
python diagnostic_tools/diagnose_github.py

# Schema investigation  
python diagnostic_tools/investigate_talent_schema.py

# Duplicate analysis
bash diagnostic_tools/diagnose_duplicates.sh
```

## Status

These scripts are maintained for debugging but are not part of the regular workflow. Use them when investigating data quality issues or system problems.
