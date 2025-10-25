"""
ABOUTME: Graph reasoning service for talent intelligence network analysis.
ABOUTME: Implements sophisticated graph reasoning algorithms inspired by GraphReasoning library.
"""

from typing import List, Dict, Optional, Set, Tuple, Any
import networkx as nx
import numpy as np
from collections import defaultdict, deque
from dataclasses import dataclass
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """Represents a person node in the network graph"""
    person_id: str
    full_name: str
    headline: Optional[str] = None
    location: Optional[str] = None
    github_username: Optional[str] = None
    embedding: Optional[np.ndarray] = None
    attributes: Dict[str, Any] = None


@dataclass
class GraphEdge:
    """Represents a connection edge in the network graph"""
    source_id: str
    target_id: str
    edge_type: str  # 'github_collaboration' or 'coemployment'
    strength: float
    attributes: Dict[str, Any] = None


class GraphReasoningService:
    """
    Advanced graph reasoning for talent network intelligence.
    
    Implements:
    - Node embeddings and similarity
    - Path sampling and reasoning
    - Community detection
    - Isomorphic pattern matching
    - Knowledge graph construction from collaboration data
    """
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self.graph: Optional[nx.Graph] = None
        self.node_embeddings: Dict[str, np.ndarray] = {}
        self.communities: Optional[List[Set[str]]] = None
        
    def build_graph_from_database(self, limit: Optional[int] = None) -> nx.Graph:
        """
        Build NetworkX graph from database collaboration data.
        
        Args:
            limit: Optional limit on number of nodes to load
            
        Returns:
            NetworkX graph with person nodes and collaboration edges
        """
        logger.info("Building graph from database...")
        
        G = nx.Graph()
        
        cursor = self.db.cursor()
        
        # Load person nodes
        node_query = """
            SELECT 
                p.person_id,
                p.full_name,
                p.headline,
                p.location,
                gp.github_username,
                gp.followers,
                gp.public_repos
            FROM person p
            LEFT JOIN github_profile gp ON p.github_profile_id = gp.github_profile_id
            WHERE p.person_id IS NOT NULL
        """
        
        if limit:
            node_query += f" LIMIT {limit}"
        
        cursor.execute(node_query)
        
        for row in cursor.fetchall():
            person_id = str(row[0])
            G.add_node(person_id, 
                      full_name=row[1],
                      headline=row[2],
                      location=row[3],
                      github_username=row[4],
                      github_followers=row[5] or 0,
                      github_repos=row[6] or 0)
        
        logger.info(f"Loaded {G.number_of_nodes()} person nodes")
        
        # Load GitHub collaboration edges
        github_edge_query = """
            SELECT 
                egc.src_person_id,
                egc.dst_person_id,
                egc.collaboration_strength,
                egc.shared_repos,
                egc.shared_contributions
            FROM edge_github_collaboration egc
            WHERE egc.src_person_id IN (SELECT person_id FROM person)
            AND egc.dst_person_id IN (SELECT person_id FROM person)
        """
        
        cursor.execute(github_edge_query)
        
        github_edges = 0
        for row in cursor.fetchall():
            src_id = str(row[0])
            dst_id = str(row[1])
            
            if G.has_node(src_id) and G.has_node(dst_id):
                G.add_edge(src_id, dst_id,
                          edge_type='github_collaboration',
                          strength=row[2] or 0,
                          shared_repos=row[3] or 0,
                          shared_contributions=row[4] or 0)
                github_edges += 1
        
        logger.info(f"Loaded {github_edges} GitHub collaboration edges")
        
        # Load coemployment edges
        coemployment_edge_query = """
            SELECT 
                ec.src_person_id,
                ec.dst_person_id,
                ec.overlap_months,
                c.company_name
            FROM edge_coemployment ec
            JOIN company c ON ec.company_id = c.company_id
            WHERE ec.src_person_id IN (SELECT person_id FROM person)
            AND ec.dst_person_id IN (SELECT person_id FROM person)
        """
        
        cursor.execute(coemployment_edge_query)
        
        coemployment_edges = 0
        for row in cursor.fetchall():
            src_id = str(row[0])
            dst_id = str(row[1])
            
            if G.has_node(src_id) and G.has_node(dst_id):
                # If edge already exists (GitHub collab), add coemployment as attribute
                if G.has_edge(src_id, dst_id):
                    G[src_id][dst_id]['coemployment'] = True
                    G[src_id][dst_id]['overlap_months'] = row[2] or 0
                    G[src_id][dst_id]['company_name'] = row[3]
                else:
                    G.add_edge(src_id, dst_id,
                              edge_type='coemployment',
                              overlap_months=row[2] or 0,
                              company_name=row[3],
                              strength=min((row[2] or 0) / 12.0, 1.0))  # Normalize by year
                coemployment_edges += 1
        
        logger.info(f"Loaded {coemployment_edges} coemployment edges")
        
        cursor.close()
        
        self.graph = G
        return G
    
    def compute_node_embeddings(self, dimension: int = 128) -> Dict[str, np.ndarray]:
        """
        Compute node embeddings using Node2Vec approach.
        
        For production: would use proper Node2Vec or DeepWalk.
        For now: using network-based features as embeddings.
        
        Args:
            dimension: Embedding dimension
            
        Returns:
            Dictionary mapping person_id to embedding vector
        """
        if not self.graph:
            raise ValueError("Graph not built. Call build_graph_from_database() first")
        
        logger.info("Computing node embeddings...")
        
        embeddings = {}
        
        for node in self.graph.nodes():
            # Build feature vector from graph properties
            features = []
            
            # Degree centrality
            features.append(self.graph.degree(node))
            
            # Betweenness centrality
            betweenness = nx.betweenness_centrality(self.graph, k=min(100, self.graph.number_of_nodes()))
            features.append(betweenness.get(node, 0))
            
            # Clustering coefficient
            features.append(nx.clustering(self.graph, node))
            
            # Average neighbor degree
            features.append(nx.average_neighbor_degree(self.graph)[node])
            
            # GitHub metrics
            features.append(self.graph.nodes[node].get('github_followers', 0) / 1000.0)
            features.append(self.graph.nodes[node].get('github_repos', 0) / 100.0)
            
            # Collaboration strength (sum of edge weights)
            total_strength = sum(
                self.graph[node][neighbor].get('strength', 0)
                for neighbor in self.graph.neighbors(node)
            )
            features.append(total_strength)
            
            # Pad to dimension
            feature_vec = np.array(features)
            if len(feature_vec) < dimension:
                padding = np.zeros(dimension - len(feature_vec))
                feature_vec = np.concatenate([feature_vec, padding])
            else:
                feature_vec = feature_vec[:dimension]
            
            embeddings[node] = feature_vec
        
        self.node_embeddings = embeddings
        logger.info(f"Computed embeddings for {len(embeddings)} nodes")
        
        return embeddings
    
    def compute_node_similarity(self, node1_id: str, node2_id: str) -> float:
        """
        Compute cosine similarity between two nodes based on embeddings.
        
        Args:
            node1_id: First person ID
            node2_id: Second person ID
            
        Returns:
            Similarity score (0-1)
        """
        if not self.node_embeddings:
            logger.warning("No embeddings computed. Computing now...")
            self.compute_node_embeddings()
        
        if node1_id not in self.node_embeddings or node2_id not in self.node_embeddings:
            return 0.0
        
        vec1 = self.node_embeddings[node1_id]
        vec2 = self.node_embeddings[node2_id]
        
        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def find_similar_nodes(self, node_id: str, top_k: int = 10, min_similarity: float = 0.5) -> List[Dict]:
        """
        Find most similar nodes to a given node.
        
        Args:
            node_id: Person ID to find similar people for
            top_k: Number of similar nodes to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar nodes with similarity scores
        """
        if not self.node_embeddings:
            self.compute_node_embeddings()
        
        if node_id not in self.node_embeddings:
            return []
        
        similarities = []
        
        for other_id in self.node_embeddings:
            if other_id != node_id:
                sim = self.compute_node_similarity(node_id, other_id)
                if sim >= min_similarity:
                    similarities.append({
                        'person_id': other_id,
                        'full_name': self.graph.nodes[other_id].get('full_name', 'Unknown'),
                        'headline': self.graph.nodes[other_id].get('headline'),
                        'similarity_score': float(sim),
                        'github_username': self.graph.nodes[other_id].get('github_username')
                    })
        
        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return similarities[:top_k]
    
    def detect_communities(self, algorithm: str = 'louvain') -> List[Set[str]]:
        """
        Detect communities (clusters) in the network.
        
        Args:
            algorithm: Community detection algorithm ('louvain', 'label_propagation', 'greedy_modularity')
            
        Returns:
            List of sets, each containing person_ids in that community
        """
        if not self.graph:
            raise ValueError("Graph not built")
        
        logger.info(f"Detecting communities using {algorithm}...")
        
        if algorithm == 'louvain':
            try:
                import community as community_louvain
                partition = community_louvain.best_partition(self.graph)
                communities = defaultdict(set)
                for node, comm_id in partition.items():
                    communities[comm_id].add(node)
                result = list(communities.values())
            except ImportError:
                logger.warning("python-louvain not installed, using label propagation")
                algorithm = 'label_propagation'
        
        if algorithm == 'label_propagation':
            communities_generator = nx.algorithms.community.label_propagation_communities(self.graph)
            result = [set(c) for c in communities_generator]
        
        elif algorithm == 'greedy_modularity':
            communities_generator = nx.algorithms.community.greedy_modularity_communities(self.graph)
            result = [set(c) for c in communities_generator]
        
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        self.communities = result
        logger.info(f"Detected {len(result)} communities")
        
        return result
    
    def get_community_info(self, community_id: int) -> Dict:
        """
        Get detailed information about a community.
        
        Args:
            community_id: Index of community in self.communities
            
        Returns:
            Dictionary with community statistics and members
        """
        if not self.communities:
            self.detect_communities()
        
        if community_id >= len(self.communities):
            raise ValueError(f"Community {community_id} does not exist")
        
        community = self.communities[community_id]
        
        # Get subgraph for this community
        subgraph = self.graph.subgraph(community)
        
        # Compute statistics
        density = nx.density(subgraph)
        avg_clustering = nx.average_clustering(subgraph)
        
        # Get member details
        members = []
        for node in community:
            members.append({
                'person_id': node,
                'full_name': self.graph.nodes[node].get('full_name', 'Unknown'),
                'headline': self.graph.nodes[node].get('headline'),
                'github_username': self.graph.nodes[node].get('github_username'),
                'degree': self.graph.degree(node)
            })
        
        # Sort by degree (influence within community)
        members.sort(key=lambda x: x['degree'], reverse=True)
        
        return {
            'community_id': community_id,
            'size': len(community),
            'density': float(density),
            'avg_clustering': float(avg_clustering),
            'members': members[:50]  # Top 50 by degree
        }
    
    def sample_path_between_concepts(self, 
                                     start_concept: str, 
                                     end_concept: str,
                                     max_length: int = 5) -> List[Dict]:
        """
        Sample paths between two concepts (skills, domains, etc.).
        
        This implements path sampling as in GraphReasoning to find
        innovative connections between dissimilar concepts.
        
        Args:
            start_concept: Starting concept (e.g., "blockchain")
            end_concept: Ending concept (e.g., "machine learning")
            max_length: Maximum path length to explore
            
        Returns:
            List of paths, each with nodes and connections
        """
        if not self.graph:
            raise ValueError("Graph not built")
        
        # Find nodes that match start concept
        start_nodes = self._find_nodes_by_concept(start_concept)
        end_nodes = self._find_nodes_by_concept(end_concept)
        
        if not start_nodes or not end_nodes:
            return []
        
        paths = []
        
        # Sample paths between random pairs
        for start_node in start_nodes[:5]:  # Limit to 5 start nodes
            for end_node in end_nodes[:5]:
                try:
                    # Find all simple paths up to max_length
                    simple_paths = nx.all_simple_paths(
                        self.graph, 
                        start_node, 
                        end_node, 
                        cutoff=max_length
                    )
                    
                    for path in simple_paths:
                        path_data = self._enrich_path(path)
                        paths.append(path_data)
                        
                        if len(paths) >= 10:  # Limit total paths
                            break
                    
                    if len(paths) >= 10:
                        break
                except nx.NetworkXNoPath:
                    continue
            
            if len(paths) >= 10:
                break
        
        # Rank paths by novelty (dissimilarity of intermediate nodes)
        paths = self._rank_paths_by_novelty(paths)
        
        return paths[:5]  # Return top 5 most novel paths
    
    def _find_nodes_by_concept(self, concept: str) -> List[str]:
        """Find nodes that match a concept (in headline or attributes)"""
        concept_lower = concept.lower()
        matching_nodes = []
        
        for node_id in self.graph.nodes():
            headline = self.graph.nodes[node_id].get('headline', '').lower()
            if concept_lower in headline:
                matching_nodes.append(node_id)
        
        return matching_nodes
    
    def _enrich_path(self, path: List[str]) -> Dict:
        """Add details to a path"""
        nodes = []
        edges = []
        
        for i, node_id in enumerate(path):
            node_data = self.graph.nodes[node_id]
            nodes.append({
                'person_id': node_id,
                'full_name': node_data.get('full_name', 'Unknown'),
                'headline': node_data.get('headline'),
                'position': i
            })
            
            if i < len(path) - 1:
                next_id = path[i + 1]
                edge_data = self.graph[node_id][next_id]
                edges.append({
                    'from': node_id,
                    'to': next_id,
                    'type': edge_data.get('edge_type', 'unknown'),
                    'strength': edge_data.get('strength', 0)
                })
        
        return {
            'path_length': len(path) - 1,
            'nodes': nodes,
            'edges': edges
        }
    
    def _rank_paths_by_novelty(self, paths: List[Dict]) -> List[Dict]:
        """Rank paths by how dissimilar intermediate nodes are (novelty)"""
        for path in paths:
            # Compute average dissimilarity of adjacent nodes
            novelty_scores = []
            
            for i in range(len(path['nodes']) - 1):
                node1_id = path['nodes'][i]['person_id']
                node2_id = path['nodes'][i + 1]['person_id']
                
                # Dissimilarity = 1 - similarity
                similarity = self.compute_node_similarity(node1_id, node2_id)
                novelty_scores.append(1.0 - similarity)
            
            path['novelty_score'] = np.mean(novelty_scores) if novelty_scores else 0
        
        # Sort by novelty (higher is more novel)
        paths.sort(key=lambda x: x['novelty_score'], reverse=True)
        
        return paths
    
    def compute_graph_statistics(self) -> Dict:
        """
        Compute comprehensive graph statistics.
        
        Returns:
            Dictionary with graph metrics
        """
        if not self.graph:
            raise ValueError("Graph not built")
        
        stats = {
            'num_nodes': self.graph.number_of_nodes(),
            'num_edges': self.graph.number_of_edges(),
            'density': float(nx.density(self.graph)),
            'avg_clustering': float(nx.average_clustering(self.graph)),
            'is_connected': nx.is_connected(self.graph),
            'num_components': nx.number_connected_components(self.graph)
        }
        
        # Degree distribution
        degrees = [d for n, d in self.graph.degree()]
        stats['avg_degree'] = float(np.mean(degrees))
        stats['max_degree'] = int(np.max(degrees))
        stats['min_degree'] = int(np.min(degrees))
        
        # Centrality measures (sample for large graphs)
        sample_size = min(100, self.graph.number_of_nodes())
        sample_nodes = list(self.graph.nodes())[:sample_size]
        
        betweenness = nx.betweenness_centrality(self.graph, k=sample_size)
        stats['avg_betweenness'] = float(np.mean(list(betweenness.values())))
        
        # Most central nodes
        top_central = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]
        stats['top_central_nodes'] = [
            {
                'person_id': node_id,
                'full_name': self.graph.nodes[node_id].get('full_name', 'Unknown'),
                'betweenness': float(score)
            }
            for node_id, score in top_central
        ]
        
        return stats
    
    def find_key_connectors(self, min_betweenness: float = 0.01) -> List[Dict]:
        """
        Find key connector nodes (high betweenness centrality).
        
        These are people who bridge different communities.
        
        Args:
            min_betweenness: Minimum betweenness centrality threshold
            
        Returns:
            List of key connector people
        """
        if not self.graph:
            raise ValueError("Graph not built")
        
        logger.info("Computing betweenness centrality to find key connectors...")
        
        # Compute betweenness centrality
        betweenness = nx.betweenness_centrality(
            self.graph, 
            k=min(200, self.graph.number_of_nodes())
        )
        
        # Filter and enrich
        connectors = []
        for node_id, score in betweenness.items():
            if score >= min_betweenness:
                connectors.append({
                    'person_id': node_id,
                    'full_name': self.graph.nodes[node_id].get('full_name', 'Unknown'),
                    'headline': self.graph.nodes[node_id].get('headline'),
                    'github_username': self.graph.nodes[node_id].get('github_username'),
                    'betweenness_centrality': float(score),
                    'degree': self.graph.degree(node_id)
                })
        
        # Sort by betweenness
        connectors.sort(key=lambda x: x['betweenness_centrality'], reverse=True)
        
        logger.info(f"Found {len(connectors)} key connectors")
        
        return connectors
    
    def export_graph_to_graphml(self, output_path: str):
        """Export graph to GraphML format for external analysis"""
        if not self.graph:
            raise ValueError("Graph not built")
        
        nx.write_graphml(self.graph, output_path)
        logger.info(f"Graph exported to {output_path}")
    
    def export_graph_to_json(self, output_path: str):
        """Export graph to JSON format"""
        if not self.graph:
            raise ValueError("Graph not built")
        
        from networkx.readwrite import json_graph
        
        graph_data = json_graph.node_link_data(self.graph)
        
        with open(output_path, 'w') as f:
            json.dump(graph_data, f, indent=2)
        
        logger.info(f"Graph exported to {output_path}")


def get_graph_reasoning_service(db_connection) -> GraphReasoningService:
    """Factory function to create graph reasoning service"""
    return GraphReasoningService(db_connection=db_connection)

