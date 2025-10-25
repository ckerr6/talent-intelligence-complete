#!/usr/bin/env python3
"""
ABOUTME: Interactive graph reasoning demo - shows all features working.
ABOUTME: Uses Python directly (no API) for maximum reliability.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_db_context
from api.services.graph_reasoning_service import GraphReasoningService
import json

def print_section(title):
    print("\n" + "=" * 80)
    print(f"📊 {title}")
    print("=" * 80)

def main():
    print("=" * 80)
    print("🎯 GRAPH REASONING - COMPREHENSIVE DEMO")
    print("=" * 80)
    print("\nThis demo shows all graph reasoning features working via Python")
    print()
    
    # Initialize
    print_section("1. Initialize Service")
    with get_db_context() as conn:
        service = GraphReasoningService(db_connection=conn)
        print("✅ Service initialized")
        
        # Build graph
        print_section("2. Build Graph (1000 nodes)")
        print("Building graph from database...")
        graph = service.build_graph_from_database(limit=1000)
        print(f"✅ Graph built: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        
        # Fast statistics
        print_section("3. Fast Statistics (no betweenness)")
        print("Computing statistics...")
        stats = service.compute_graph_statistics(compute_betweenness=False)
        print(f"✅ Statistics computed:")
        print(f"   • Nodes: {stats['num_nodes']}")
        print(f"   • Edges: {stats['num_edges']}")
        print(f"   • Density: {stats['density']:.6f}")
        print(f"   • Average Clustering: {stats['avg_clustering']:.4f}")
        print(f"   • Connected: {stats['is_connected']}")
        print(f"   • Components: {stats['num_components']}")
        print(f"   • Average Degree: {stats['avg_degree']:.2f}")
        print(f"   • Max Degree: {stats['max_degree']}")
        
        # Compute embeddings
        print_section("4. Compute Node Embeddings")
        print("Computing 128-dimensional embeddings for all nodes...")
        embeddings = service.compute_node_embeddings(dimension=128)
        print(f"✅ Embeddings computed for {len(embeddings)} nodes")
        
        # Find similar people
        print_section("5. Find Similar People")
        if len(embeddings) >= 2:
            # Get a node with connections
            test_node = None
            for node_id in list(graph.nodes())[:50]:
                if graph.degree(node_id) > 0:
                    test_node = node_id
                    break
            
            if test_node:
                test_name = graph.nodes[test_node].get('full_name', 'Unknown')
                print(f"Finding people similar to: {test_name}")
                
                similar = service.find_similar_nodes(test_node, top_k=5, min_similarity=0.3)
                
                if similar:
                    print(f"\n✅ Found {len(similar)} similar people:")
                    for i, person in enumerate(similar, 1):
                        print(f"   {i}. {person['full_name']}")
                        print(f"      Similarity: {person['similarity_score']:.4f}")
                        if person['github_username']:
                            print(f"      GitHub: @{person['github_username']}")
                else:
                    print("   No similar people found (may need to lower threshold)")
            else:
                print("   No nodes with connections found in sample")
        
        # Detect communities
        print_section("6. Detect Communities")
        print("Detecting communities using label propagation...")
        communities = service.detect_communities(algorithm='label_propagation')
        print(f"✅ Detected {len(communities)} communities")
        
        # Show top 10 by size
        community_sizes = sorted([(i, len(c)) for i, c in enumerate(communities)], 
                                key=lambda x: x[1], reverse=True)
        print("\nTop 10 communities by size:")
        for i, (comm_id, size) in enumerate(community_sizes[:10], 1):
            print(f"   {i}. Community {comm_id}: {size} members")
        
        # Analyze largest community
        if len(communities) > 0:
            print_section("7. Analyze Largest Community")
            largest_comm_id = community_sizes[0][0]
            comm_info = service.get_community_info(largest_comm_id)
            
            print(f"Community {largest_comm_id} details:")
            print(f"   • Size: {comm_info['size']} members")
            print(f"   • Density: {comm_info['density']:.4f}")
            print(f"   • Avg Clustering: {comm_info['avg_clustering']:.4f}")
            
            print(f"\n   Top 5 members by influence:")
            for i, member in enumerate(comm_info['members'][:5], 1):
                print(f"      {i}. {member['full_name']} (degree: {member['degree']})")
        
        # Find key connectors
        print_section("8. Find Key Connectors")
        print("Computing betweenness centrality (this may take a moment)...")
        connectors = service.find_key_connectors(min_betweenness=0.001)
        
        if connectors:
            print(f"✅ Found {len(connectors)} key connectors")
            print("\nTop 5 key connectors:")
            for i, connector in enumerate(connectors[:5], 1):
                print(f"   {i}. {connector['full_name']}")
                print(f"      Betweenness: {connector['betweenness_centrality']:.6f}")
                print(f"      Degree: {connector['degree']}")
                if connector['github_username']:
                    print(f"      GitHub: @{connector['github_username']}")
        else:
            print("   No key connectors found (try lowering threshold)")
        
        # Graph info
        print_section("9. Graph Info & Cache Status")
        info = service.get_graph_info()
        print("Graph status:")
        print(f"   • Status: {info['status']}")
        print(f"   • Nodes: {info['num_nodes']}")
        print(f"   • Edges: {info['num_edges']}")
        print(f"   • Has embeddings: {info['has_embeddings']}")
        print(f"   • Has communities: {info['has_communities']}")
        
        cache_status = info['cache_status']
        print(f"\nCache status:")
        print(f"   • Stats cached: {cache_status['stats_cached']}")
        print(f"   • Betweenness cached: {cache_status['betweenness_cached']}")
        if cache_status['stats_age_seconds']:
            print(f"   • Stats age: {cache_status['stats_age_seconds']:.1f} seconds")
        
        # Test incremental update
        print_section("10. Test Incremental Update")
        test_person = {
            'person_id': 'test-uuid-12345',
            'full_name': 'Test Person',
            'headline': 'Software Engineer',
            'location': 'San Francisco',
            'github_username': 'testuser',
            'github_followers': 100,
            'github_repos': 50
        }
        
        print("Adding test person node...")
        added = service.add_person_node(test_person)
        if added:
            print("✅ Node added successfully")
            print("   (Cache automatically invalidated)")
            
            # Verify
            info_after = service.get_graph_info()
            print(f"   • New node count: {info_after['num_nodes']}")
        else:
            print("   Node already existed")
        
        # Export graph
        print_section("11. Export Graph")
        import os
        os.makedirs("./exports", exist_ok=True)
        
        print("Exporting graph to JSON...")
        service.export_graph_to_json("./exports/demo_graph.json")
        print("✅ Exported to ./exports/demo_graph.json")
        
        print("\nExporting graph to GraphML...")
        service.export_graph_to_graphml("./exports/demo_graph.graphml")
        print("✅ Exported to ./exports/demo_graph.graphml")
        
        # Final stats with betweenness
        print_section("12. Full Statistics (with betweenness - cached)")
        print("Getting full stats (should be fast since betweenness is cached)...")
        full_stats = service.compute_graph_statistics(compute_betweenness=True)
        
        if 'top_central_nodes' in full_stats:
            print("✅ Full stats with betweenness:")
            print(f"   • Avg Betweenness: {full_stats['avg_betweenness']:.8f}")
            print(f"\n   Top 3 most central nodes:")
            for i, node in enumerate(full_stats['top_central_nodes'][:3], 1):
                print(f"      {i}. {node['full_name']}")
                print(f"         Betweenness: {node['betweenness']:.6f}")
    
    print_section("DEMO COMPLETE!")
    print("✅ All graph reasoning features demonstrated successfully!")
    print()
    print("Key takeaways:")
    print("   • Graph builds in seconds")
    print("   • Statistics are cached for performance")
    print("   • Node embeddings enable similarity search")
    print("   • Community detection works")
    print("   • Key connectors identified")
    print("   • Incremental updates supported")
    print("   • Export to standard formats")
    print()
    print("All features ready for production use via Python!")
    print("=" * 80)

if __name__ == "__main__":
    main()

