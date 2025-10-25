#!/usr/bin/env python3
"""
ABOUTME: Minimal standalone test for graph reasoning service.
ABOUTME: Tests core functionality without API complexity.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 80)
print("🧪 Graph Reasoning - Minimal Standalone Test")
print("=" * 80)
print()

# Test 1: Imports
print("Test 1: Importing modules...")
try:
    from config import get_db_context
    from api.services.graph_reasoning_service import GraphReasoningService
    print("✅ Imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Database connection
print("\nTest 2: Database connection...")
try:
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM person")
        result = cursor.fetchone()
        # Handle both dict and tuple results
        if isinstance(result, dict):
            count = result['count']
        else:
            count = result[0]
        print(f"✅ Database connected: {count} people in database")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Initialize service
print("\nTest 3: Initialize graph service...")
try:
    with get_db_context() as conn:
        service = GraphReasoningService(db_connection=conn)
        print("✅ Service initialized")
except Exception as e:
    print(f"❌ Service initialization failed: {e}")
    sys.exit(1)

# Test 4: Build small graph (100 nodes)
print("\nTest 4: Build small graph (100 nodes)...")
try:
    with get_db_context() as conn:
        service = GraphReasoningService(db_connection=conn)
        graph = service.build_graph_from_database(limit=100)
        print(f"✅ Graph built: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
except Exception as e:
    print(f"❌ Graph build failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Quick stats (no betweenness)
print("\nTest 5: Compute fast statistics...")
try:
    stats = service.compute_graph_statistics(compute_betweenness=False)
    print(f"✅ Stats computed:")
    print(f"   - Nodes: {stats['num_nodes']}")
    print(f"   - Edges: {stats['num_edges']}")
    print(f"   - Density: {stats['density']:.4f}")
    print(f"   - Avg Degree: {stats['avg_degree']:.2f}")
except Exception as e:
    print(f"❌ Stats computation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Graph info
print("\nTest 6: Get graph info...")
try:
    info = service.get_graph_info()
    print(f"✅ Graph info retrieved:")
    print(f"   - Status: {info['status']}")
    print(f"   - Has embeddings: {info['has_embeddings']}")
except Exception as e:
    print(f"❌ Graph info failed: {e}")
    sys.exit(1)

print()
print("=" * 80)
print("✅ ALL TESTS PASSED - Graph Reasoning Works!")
print("=" * 80)
print()
print("Next step: The service works standalone. Issue is likely:")
print("1. API integration/routing")
print("2. Database connection management in async context")
print("3. Some unrelated API endpoint error")
print()
print("Recommendation: Use graph reasoning via Python directly,")
print("or fix API connectivity issues separately from graph logic.")

