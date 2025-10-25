#!/usr/bin/env python3
"""
ABOUTME: Test script for graph reasoning service.
ABOUTME: Demonstrates graph analysis, community detection, and path sampling capabilities.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import get_db_context
from api.services.graph_reasoning_service import GraphReasoningService


def main():
    """Test graph reasoning capabilities"""
    
    print("=" * 80)
    print("🔬 Graph Reasoning Service Test")
    print("=" * 80)
    print()
    
    with get_db_context() as conn:
        # Initialize service
        print("📊 Initializing Graph Reasoning Service...")
        service = GraphReasoningService(db_connection=conn)
        
        # Build graph from database
        print("🔨 Building graph from database (limit: 1000 nodes for testing)...")
        graph = service.build_graph_from_database(limit=1000)
        print(f"   ✅ Graph built: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        print()
        
        # Compute statistics
        print("📈 Computing graph statistics...")
        stats = service.compute_graph_statistics()
        print(f"   • Nodes: {stats['num_nodes']}")
        print(f"   • Edges: {stats['num_edges']}")
        print(f"   • Density: {stats['density']:.4f}")
        print(f"   • Average Clustering: {stats['avg_clustering']:.4f}")
        print(f"   • Connected: {stats['is_connected']}")
        print(f"   • Connected Components: {stats['num_components']}")
        print(f"   • Average Degree: {stats['avg_degree']:.2f}")
        print()
        
        # Compute embeddings
        print("🧮 Computing node embeddings...")
        embeddings = service.compute_node_embeddings(dimension=128)
        print(f"   ✅ Computed embeddings for {len(embeddings)} nodes")
        print()
        
        # Find key connectors
        print("🔗 Finding key connector nodes (high betweenness centrality)...")
        connectors = service.find_key_connectors(min_betweenness=0.001)
        print(f"   Found {len(connectors)} key connectors")
        
        if connectors:
            print("\n   Top 5 Key Connectors:")
            for i, connector in enumerate(connectors[:5], 1):
                print(f"      {i}. {connector['full_name']}")
                print(f"         • Betweenness: {connector['betweenness_centrality']:.4f}")
                print(f"         • Degree: {connector['degree']}")
                print(f"         • GitHub: @{connector['github_username'] or 'N/A'}")
        print()
        
        # Detect communities
        print("🏘️  Detecting communities...")
        try:
            communities = service.detect_communities(algorithm='label_propagation')
            print(f"   ✅ Detected {len(communities)} communities")
            
            # Show size distribution
            sizes = sorted([len(c) for c in communities], reverse=True)
            print(f"   • Largest community: {sizes[0]} members")
            print(f"   • Top 10 community sizes: {sizes[:10]}")
            
            # Get details of largest community
            if len(communities) > 0:
                print("\n   📊 Analyzing largest community...")
                comm_info = service.get_community_info(0)
                print(f"      • Size: {comm_info['size']} members")
                print(f"      • Density: {comm_info['density']:.4f}")
                print(f"      • Avg Clustering: {comm_info['avg_clustering']:.4f}")
                
                print("\n      Top 5 Members by Influence:")
                for i, member in enumerate(comm_info['members'][:5], 1):
                    print(f"         {i}. {member['full_name']} (degree: {member['degree']})")
        except Exception as e:
            print(f"   ⚠️  Community detection failed: {e}")
        print()
        
        # Test similarity
        if len(embeddings) >= 2:
            print("🔍 Testing node similarity...")
            node_ids = list(embeddings.keys())
            node1_id = node_ids[0]
            
            similar = service.find_similar_nodes(node1_id, top_k=5, min_similarity=0.3)
            
            node1_name = graph.nodes[node1_id].get('full_name', 'Unknown')
            print(f"   Finding people similar to: {node1_name}")
            
            if similar:
                print("\n   Top 5 Similar People:")
                for i, person in enumerate(similar, 1):
                    print(f"      {i}. {person['full_name']}")
                    print(f"         • Similarity: {person['similarity_score']:.4f}")
                    print(f"         • GitHub: @{person['github_username'] or 'N/A'}")
            else:
                print("   No similar people found (try lowering min_similarity)")
        print()
        
        # Test path sampling (if we have nodes with different concepts)
        print("🛤️  Testing path sampling between concepts...")
        print("   (Looking for paths between 'engineer' and 'developer' roles)")
        try:
            paths = service.sample_path_between_concepts(
                start_concept='engineer',
                end_concept='developer',
                max_length=4
            )
            
            if paths:
                print(f"   ✅ Found {len(paths)} paths")
                
                # Show most novel path
                if len(paths) > 0:
                    path = paths[0]
                    print(f"\n   Most Novel Path (novelty score: {path.get('novelty_score', 0):.4f}):")
                    for i, node in enumerate(path['nodes']):
                        print(f"      {i + 1}. {node['full_name']}")
                        if node['headline']:
                            print(f"         {node['headline']}")
            else:
                print("   No paths found between these concepts")
        except Exception as e:
            print(f"   ⚠️  Path sampling failed: {e}")
        print()
        
        # Export graph
        print("💾 Exporting graph...")
        try:
            import os
            os.makedirs("./exports", exist_ok=True)
            
            service.export_graph_to_json("./exports/test_graph.json")
            print("   ✅ Graph exported to ./exports/test_graph.json")
            
            service.export_graph_to_graphml("./exports/test_graph.graphml")
            print("   ✅ Graph exported to ./exports/test_graph.graphml")
        except Exception as e:
            print(f"   ⚠️  Export failed: {e}")
        print()
        
        print("=" * 80)
        print("✅ Graph Reasoning Test Complete!")
        print("=" * 80)


if __name__ == "__main__":
    main()

