#!/usr/bin/env python3
"""
ABOUTME: Full graph processing - all nodes, edges, and VC-funded companies.
ABOUTME: Processes entire database with progress monitoring and memory management.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_db_context
from api.services.graph_reasoning_service import GraphReasoningService
import json
import time
import psutil
import os

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def print_section(title, symbol="="):
    print("\n" + symbol * 80)
    print(f"{title}")
    print(symbol * 80)

def get_database_stats(conn):
    """Get stats about what's in the database"""
    cursor = conn.cursor()
    
    stats = {}
    
    def get_count(result):
        """Handle both dict and tuple cursor results"""
        if isinstance(result, dict):
            return result.get('count', 0) or result.get(list(result.keys())[0], 0)
        return result[0]
    
    # People count
    cursor.execute("SELECT COUNT(*) FROM person")
    stats['total_people'] = get_count(cursor.fetchone())
    
    # People with GitHub
    cursor.execute("SELECT COUNT(*) FROM person p JOIN github_profile gp ON p.person_id = gp.person_id")
    stats['people_with_github'] = get_count(cursor.fetchone())
    
    # Total collaborations
    cursor.execute("SELECT COUNT(*) FROM edge_github_collaboration")
    stats['github_collaborations'] = get_count(cursor.fetchone())
    
    # Coemployment edges
    cursor.execute("SELECT COUNT(*) FROM edge_coemployment")
    stats['coemployment_edges'] = get_count(cursor.fetchone())
    
    # Companies total
    cursor.execute("SELECT COUNT(*) FROM company")
    stats['total_companies'] = get_count(cursor.fetchone())
    
    # Companies with funding data (if column exists)
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM company 
            WHERE funding_total IS NOT NULL OR funding_stage IS NOT NULL
        """)
        stats['companies_with_funding'] = get_count(cursor.fetchone())
    except:
        stats['companies_with_funding'] = 0
    
    cursor.close()
    return stats

def main():
    print_section("🚀 FULL GRAPH PROCESSING - ENTIRE DATABASE", "=")
    print("\nThis will process ALL nodes and edges in the database.")
    print("Processing will be monitored for memory usage and progress.")
    print()
    
    start_time = time.time()
    
    # Get database statistics
    print_section("📊 Step 1: Database Statistics")
    with get_db_context() as conn:
        db_stats = get_database_stats(conn)
        
        print(f"Database contains:")
        print(f"   • Total people: {db_stats['total_people']:,}")
        print(f"   • People with GitHub: {db_stats['people_with_github']:,}")
        print(f"   • GitHub collaborations: {db_stats['github_collaborations']:,}")
        print(f"   • Coemployment edges: {db_stats['coemployment_edges']:,}")
        print(f"   • Total companies: {db_stats['total_companies']:,}")
        print(f"   • Companies with funding: {db_stats['companies_with_funding']:,}")
        
        total_edges = db_stats['github_collaborations'] + db_stats['coemployment_edges']
        print(f"\n   Total graph: ~{db_stats['total_people']:,} nodes, ~{total_edges:,} edges")
        print(f"   Initial memory: {get_memory_usage():.1f} MB")
    
    # Build full graph
    print_section("📊 Step 2: Build Full Graph")
    print("Building graph with ALL nodes (no limit)...")
    print("This may take a few minutes for 156K+ nodes...")
    
    build_start = time.time()
    
    with get_db_context() as conn:
        service = GraphReasoningService(db_connection=conn)
        
        print("\n⏳ Loading nodes and edges from database...")
        graph = service.build_graph_from_database(limit=None)  # NO LIMIT
        
        build_time = time.time() - build_start
        
        print(f"\n✅ Graph built successfully!")
        print(f"   • Nodes: {graph.number_of_nodes():,}")
        print(f"   • Edges: {graph.number_of_edges():,}")
        print(f"   • Build time: {build_time:.1f} seconds")
        print(f"   • Memory usage: {get_memory_usage():.1f} MB")
        
        # Save checkpoint
        print_section("📊 Step 3: Save Initial Checkpoint")
        os.makedirs("./exports/full_graph", exist_ok=True)
        
        checkpoint_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'nodes': graph.number_of_nodes(),
            'edges': graph.number_of_edges(),
            'build_time_seconds': build_time,
            'memory_mb': get_memory_usage()
        }
        
        with open('./exports/full_graph/checkpoint.json', 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        print("✅ Checkpoint saved to ./exports/full_graph/checkpoint.json")
        
        # Fast statistics
        print_section("📊 Step 4: Compute Fast Statistics")
        print("Computing statistics (without betweenness for speed)...")
        
        stats_start = time.time()
        stats = service.compute_graph_statistics(compute_betweenness=False)
        stats_time = time.time() - stats_start
        
        print(f"\n✅ Statistics computed in {stats_time:.2f} seconds:")
        print(f"   • Nodes: {stats['num_nodes']:,}")
        print(f"   • Edges: {stats['num_edges']:,}")
        print(f"   • Density: {stats['density']:.8f}")
        print(f"   • Average Clustering: {stats['avg_clustering']:.4f}")
        print(f"   • Connected: {stats['is_connected']}")
        print(f"   • Components: {stats['num_components']:,}")
        print(f"   • Average Degree: {stats['avg_degree']:.2f}")
        print(f"   • Max Degree: {stats['max_degree']}")
        print(f"   • Min Degree: {stats['min_degree']}")
        
        # Save stats
        with open('./exports/full_graph/statistics.json', 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        print("\n✅ Statistics saved to ./exports/full_graph/statistics.json")
        
        # Node embeddings (this is memory intensive)
        print_section("📊 Step 5: Compute Node Embeddings")
        print(f"Computing embeddings for {stats['num_nodes']:,} nodes...")
        print("This may take several minutes...")
        
        embed_start = time.time()
        embeddings = service.compute_node_embeddings(dimension=128)
        embed_time = time.time() - embed_start
        
        print(f"\n✅ Embeddings computed in {embed_time:.1f} seconds")
        print(f"   • Embeddings: {len(embeddings):,}")
        print(f"   • Dimension: 128")
        print(f"   • Memory usage: {get_memory_usage():.1f} MB")
        
        # Community detection
        print_section("📊 Step 6: Detect Communities")
        print("Running community detection (label propagation algorithm)...")
        print("This works well for large graphs...")
        
        comm_start = time.time()
        communities = service.detect_communities(algorithm='label_propagation')
        comm_time = time.time() - comm_start
        
        print(f"\n✅ Communities detected in {comm_time:.1f} seconds")
        print(f"   • Communities: {len(communities):,}")
        
        # Analyze community sizes
        community_sizes = sorted([len(c) for c in communities], reverse=True)
        print(f"\n   Community size distribution:")
        print(f"   • Largest: {community_sizes[0]:,} members")
        print(f"   • Top 10: {community_sizes[:10]}")
        print(f"   • Median: {community_sizes[len(community_sizes)//2]:,}")
        print(f"   • Singleton communities: {sum(1 for s in community_sizes if s == 1):,}")
        
        # Save community info
        community_summary = {
            'total_communities': len(communities),
            'size_distribution': {
                'largest': community_sizes[0],
                'smallest': community_sizes[-1],
                'median': community_sizes[len(community_sizes)//2],
                'mean': sum(community_sizes) / len(community_sizes),
                'top_20_sizes': community_sizes[:20],
                'singletons': sum(1 for s in community_sizes if s == 1)
            }
        }
        
        with open('./exports/full_graph/communities.json', 'w') as f:
            json.dump(community_summary, f, indent=2)
        print("\n✅ Community summary saved to ./exports/full_graph/communities.json")
        
        # Analyze largest communities
        print_section("📊 Step 7: Analyze Top Communities")
        print("Analyzing top 5 largest communities...")
        
        top_communities = []
        community_list = sorted(enumerate(communities), key=lambda x: len(x[1]), reverse=True)
        
        for i, (comm_id, members) in enumerate(community_list[:5], 1):
            print(f"\n{i}. Community {comm_id} ({len(members)} members):")
            
            comm_info = service.get_community_info(comm_id)
            print(f"   • Density: {comm_info['density']:.4f}")
            print(f"   • Clustering: {comm_info['avg_clustering']:.4f}")
            
            # Top members
            print(f"   • Top 3 members:")
            for j, member in enumerate(comm_info['members'][:3], 1):
                print(f"      {j}. {member['full_name']} (degree: {member['degree']})")
            
            top_communities.append({
                'rank': i,
                'community_id': comm_id,
                'size': len(members),
                'density': comm_info['density'],
                'avg_clustering': comm_info['avg_clustering'],
                'top_members': [m['full_name'] for m in comm_info['members'][:10]]
            })
        
        with open('./exports/full_graph/top_communities.json', 'w') as f:
            json.dump(top_communities, f, indent=2)
        
        # Export full graph
        print_section("📊 Step 8: Export Full Graph")
        print("Exporting complete graph...")
        
        print("\n1. Exporting to JSON...")
        export_start = time.time()
        service.export_graph_to_json('./exports/full_graph/complete_graph.json')
        json_time = time.time() - export_start
        print(f"   ✅ JSON export complete ({json_time:.1f}s)")
        
        print("\n2. Exporting to GraphML...")
        export_start = time.time()
        service.export_graph_to_graphml('./exports/full_graph/complete_graph.graphml')
        graphml_time = time.time() - export_start
        print(f"   ✅ GraphML export complete ({graphml_time:.1f}s)")
        
        # Betweenness (optional - can be slow for large graphs)
        print_section("📊 Step 9: Key Connectors (Betweenness)")
        print("Computing betweenness centrality for large graph...")
        print("Using sampling for performance (200 nodes)...")
        
        betweenness_start = time.time()
        stats_with_betweenness = service.compute_graph_statistics(
            compute_betweenness=True,
            use_cache=False
        )
        betweenness_time = time.time() - betweenness_start
        
        print(f"\n✅ Betweenness computed in {betweenness_time:.1f} seconds")
        
        if 'top_central_nodes' in stats_with_betweenness:
            print(f"\n   Top 10 most central nodes (key connectors):")
            for i, node in enumerate(stats_with_betweenness['top_central_nodes'][:10], 1):
                print(f"      {i}. {node['full_name']}")
                print(f"         Betweenness: {node['betweenness']:.6f}")
            
            # Save key connectors
            with open('./exports/full_graph/key_connectors.json', 'w') as f:
                json.dump(stats_with_betweenness['top_central_nodes'][:50], f, indent=2)
            print("\n✅ Top 50 key connectors saved to ./exports/full_graph/key_connectors.json")
        
        # Final summary
        total_time = time.time() - start_time
        
        print_section("🎉 PROCESSING COMPLETE!", "=")
        print("\n✅ Full graph processed successfully!")
        print(f"\n📊 Final Statistics:")
        print(f"   • Total nodes: {graph.number_of_nodes():,}")
        print(f"   • Total edges: {graph.number_of_edges():,}")
        print(f"   • Communities: {len(communities):,}")
        print(f"   • Embeddings: {len(embeddings):,}")
        print(f"   • Processing time: {total_time/60:.1f} minutes")
        print(f"   • Peak memory: {get_memory_usage():.1f} MB")
        
        print(f"\n📁 All results saved to: ./exports/full_graph/")
        print(f"   • checkpoint.json - Build metadata")
        print(f"   • statistics.json - Graph statistics")
        print(f"   • communities.json - Community summary")
        print(f"   • top_communities.json - Top 5 communities analyzed")
        print(f"   • key_connectors.json - Top 50 key connectors")
        print(f"   • complete_graph.json - Full graph (JSON)")
        print(f"   • complete_graph.graphml - Full graph (GraphML)")
        
        print(f"\n🎯 Next steps:")
        print(f"   • Use key_connectors.json to identify influencers")
        print(f"   • Visualize complete_graph.graphml in Gephi")
        print(f"   • Query communities for talent clusters")
        print(f"   • Use embeddings for similarity search")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Processing interrupted by user")
        print("Partial results may be saved in ./exports/full_graph/")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

