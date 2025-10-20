#!/bin/bash
# ABOUTME: Fix GitHub enrichment not finding profiles
# ABOUTME: Diagnose and repair the connection between tables

echo "============================================================"
echo "🔍 Diagnosing GitHub Profile Issue"
echo "============================================================"
echo ""

# Run diagnostic
python3 diagnose_github.py

echo ""
echo "============================================================"
echo "✅ Diagnostic Complete"
echo "============================================================"
echo ""

# Now test enrichment again
echo "Testing enrichment with 10 profiles..."
python3 github_enrichment.py --limit 10

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Enrichment is now working!"
    echo ""
    echo "📊 Next steps:"
    echo ""
    echo "1. Run a batch of 100 profiles (~2 minutes):"
    echo "   python3 github_enrichment.py --limit 100"
    echo ""
    echo "2. Or run all profiles (~45 minutes):"
    echo "   python3 github_enrichment.py"
    echo ""
    echo "3. Check progress in another terminal:"
    echo "   tail -f logs/enrichment.log"
else
    echo ""
    echo "⚠️  Check the error messages above"
fi
