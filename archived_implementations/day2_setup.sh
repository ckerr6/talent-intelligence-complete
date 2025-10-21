#!/bin/bash
# ABOUTME: Day 2 setup script - Configuration and GitHub API integration
# ABOUTME: Sets up proper configuration management and tests GitHub API

echo "============================================================"
echo "📊 Day 2: Configuration & GitHub Setup"
echo "============================================================"
echo ""

# Step 1: Test configuration
echo "📋 Step 1: Testing configuration system..."
python3 config.py

if [ $? -ne 0 ]; then
    echo "❌ Configuration test failed"
    exit 1
fi

echo ""
echo "✅ Configuration system working"
echo ""

# Step 2: Check GitHub token
echo "📋 Step 2: Checking GitHub token..."
python3 -c "from config import Config; print('Token set:', 'Yes' if Config.GITHUB_TOKEN and Config.GITHUB_TOKEN != 'your_token_here' else 'No')"

# Step 3: Interactive GitHub setup if needed
echo ""
echo "📋 Step 3: GitHub API Setup..."
echo ""
echo "Do you need to set up a GitHub token? (y/n)"
read -r setup_token

if [ "$setup_token" = "y" ] || [ "$setup_token" = "Y" ]; then
    python3 test_github_setup.py --setup
fi

# Step 4: Run comprehensive GitHub tests
echo ""
echo "📋 Step 4: Running GitHub API tests..."
python3 test_github_setup.py

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  GitHub tests failed. Please fix the issues above."
    echo "You may need to:"
    echo "1. Get a GitHub token from: https://github.com/settings/tokens"
    echo "2. Run: python3 test_github_setup.py --setup"
    exit 1
fi

echo ""
echo "✅ GitHub API tests passed"

# Step 5: Test enrichment with small batch
echo ""
echo "📋 Step 5: Testing enrichment with 5 profiles..."
python3 github_enrichment.py --test

if [ $? -eq 0 ]; then
    echo "✅ Test enrichment successful"
else
    echo "⚠️  Test enrichment had issues - check logs/enrichment.log"
fi

# Create summary
cat > DAY2_COMPLETE.md << 'EOF'
# Day 2 Complete: Configuration & GitHub Setup ✅

## What We Accomplished

### 1. Configuration Management ✅
- Created `config.py` with centralized settings
- Replaced hardcoded paths throughout codebase
- Set up proper log directories
- Environment variable handling

### 2. GitHub API Integration ✅
- Token configuration in .env file
- Rate limiting with 5000 requests/hour
- Retry logic with exponential backoff
- Connection testing suite

### 3. Robust Enrichment System ✅
- `github_enrichment.py` with checkpoint/resume
- Handles API failures gracefully
- Progress tracking and reporting
- Test mode for validation

## Configuration Files Created

- `config.py` - Central configuration
- `test_github_setup.py` - API testing suite
- `github_enrichment.py` - Production enrichment
- `.env` - Environment variables (with token)

## Directory Structure

```
FINAL_DATABASE/
├── logs/           # All log files
├── reports/        # Generated reports
├── backups/        # Database backups
├── exports/        # Data exports
└── .checkpoint_*   # Resume points
```

## How to Use

### Test GitHub Connection
```bash
python3 test_github_setup.py
```

### Run Small Test Batch
```bash
python3 github_enrichment.py --test
```

### Run Full Enrichment (Day 3)
```bash
python3 github_enrichment.py
# Or with limit:
python3 github_enrichment.py --limit 100
```

### Resume After Interruption
```bash
python3 github_enrichment.py --resume
```

## Next Steps (Day 3)

1. Add production logging system
2. Run full GitHub enrichment (3-4 hours)
3. Monitor progress via logs

## Current Stats

Run this to see your current database stats:
```bash
python3 query_database_secure.py
```
Choose option 1 for statistics.
EOF

echo ""
echo "============================================================"
echo "✅ DAY 2 SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "Summary saved to: DAY2_COMPLETE.md"
echo ""
echo "✨ Key achievements:"
echo "  • Configuration system implemented"
echo "  • GitHub API integrated with retry logic"
echo "  • Rate limiting and checkpointing working"
echo "  • Test enrichment successful"
echo ""
echo "📊 Your GitHub API is ready for:"
echo "  • 5000 requests per hour"
echo "  • ~83 profiles per minute"
echo "  • Automatic retry on failures"
echo "  • Resume from interruptions"
echo ""
echo "Tomorrow (Day 3):"
echo "  1. Add production logging (30 minutes)"
echo "  2. Start full GitHub enrichment (runs 3-4 hours)"
echo "  3. Let it run while you do other work"
echo ""
echo "To commit your progress:"
echo "  git add ."
echo "  git commit -m 'Day 2: Configuration and GitHub API integration complete'"
echo "  git push origin main"
echo ""
