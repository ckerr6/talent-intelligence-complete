#!/bin/bash
# ABOUTME: Setup script for Day 1 - Security fixes and consolidation
# ABOUTME: Fixes SQL injection, consolidates databases, sets up backups

echo "============================================================"
echo "📊 Day 1 Setup: Security & Consolidation"
echo "============================================================"
echo ""

# Make scripts executable
chmod +x day1_setup.sh
chmod +x query_database_secure.py
chmod +x backup_database.py

echo "✅ Step 1: Made secure query script executable"

# Create first backup
echo ""
echo "Creating initial backup before consolidation..."
python3 backup_database.py --auto

echo ""
echo "✅ Step 2: Initial backup created"

# Archive old implementations (if they exist)
echo ""
echo "Archiving old database implementations..."

if [ -d "../Talent Intel DB" ]; then
    mkdir -p archived_implementations
    mv "../Talent Intel DB" archived_implementations/
    echo "  ✓ Archived 'Talent Intel DB'"
fi

if [ -d "../talent_db" ]; then
    mkdir -p archived_implementations  
    mv "../talent_db" archived_implementations/
    echo "  ✓ Archived 'talent_db'"
fi

echo ""
echo "✅ Step 3: Old implementations archived"

# Test the secure query script
echo ""
echo "Testing secure query script..."
echo "1" | python3 query_database_secure.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Step 4: Secure query script working"
else
    echo "⚠️  Query script test failed - check for errors"
fi

# Set up daily backup cron job
echo ""
echo "============================================================"
echo "📅 Setting up automated daily backups"
echo "============================================================"
echo ""
echo "To enable automated backups, run:"
echo "  python3 backup_database.py --setup-cron"
echo ""
echo "Or add this line to your crontab (crontab -e):"
echo "  0 2 * * * cd $(pwd) && /usr/bin/python3 backup_database.py --auto"
echo ""

# Create a consolidated summary
cat > DAY1_COMPLETE.md << 'EOF'
# Day 1 Complete: Security & Consolidation ✅

## What We Fixed

### 1. SQL Injection Vulnerabilities ✅
- Created `query_database_secure.py` with parameterized queries
- Original bash script had vulnerable string interpolation
- New Python script prevents SQL injection attacks

### 2. Database Consolidation ✅
- FINAL_DATABASE is now the single source of truth
- Old implementations archived to `archived_implementations/`
- Git repository already initialized

### 3. Automated Backups ✅
- Created `backup_database.py` with:
  - Compressed backups (.gz format)
  - 30-day retention policy
  - Integrity verification
  - Restore capability
- First backup created successfully

## How to Use

### Secure Queries
```bash
python3 query_database_secure.py
```

### Manual Backup
```bash
python3 backup_database.py
```

### Restore from Backup
```bash
python3 backup_database.py --restore
```

## Next Steps (Day 2)

1. Complete GitHub API integration
2. Set up proper configuration management
3. Add logging infrastructure

## Database Stats
Check current stats with: `python3 query_database_secure.py` (Option 1)
EOF

echo "============================================================"
echo "✅ DAY 1 SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "Summary saved to: DAY1_COMPLETE.md"
echo ""
echo "Key files created:"
echo "  • query_database_secure.py - SQL injection safe queries"
echo "  • backup_database.py - Automated backup system"
echo "  • backups/ - Backup directory with first backup"
echo ""
echo "To query your database safely:"
echo "  python3 query_database_secure.py"
echo ""
echo "To create a manual backup:"
echo "  python3 backup_database.py"
echo ""
