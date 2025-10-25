#!/usr/bin/env python3
"""Quick test to see if enrichment orchestrator runs"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.github_intelligence.intelligence_orchestrator import IntelligenceOrchestrator

print("🧪 Testing Intelligence Orchestrator...")

try:
    orch = IntelligenceOrchestrator()
    print("✅ Orchestrator initialized")
    
    # Try enriching 1 profile
    print("\n📊 Attempting to enrich 1 profile...")
    result = orch.enrich_existing_profiles(limit=1)
    print(f"✅ Result: {result}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()





