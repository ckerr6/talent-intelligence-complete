# Graph Reasoning for Talent Intelligence

**Status**: ✅ IMPLEMENTED  
**Date**: October 25, 2025  
**Based on**: [GraphReasoning Library](https://github.com/lamm-mit/GraphReasoning)

---

## 🎯 What is Graph Reasoning?

Graph reasoning applies advanced network science and machine learning to understand relationships in our talent network. Instead of just seeing "who worked with whom", we can:

- **Find hidden connections** between seemingly unrelated people
- **Detect communities** of tightly-connected professionals
- **Identify key connectors** who bridge different groups
- **Discover novel paths** between different domains (e.g., blockchain → AI)
- **Compute similarity** between people based on network position

This is inspired by MIT's GraphReasoning research, which uses knowledge graphs to discover unprecedented interdisciplinary relationships.

---

## 🏗️ Architecture

### Components

1. **GraphReasoningService** (`api/services/graph_reasoning_service.py`)
   - Core graph reasoning logic
   - NetworkX-based graph construction
   - Node embeddings and similarity calculations
   - Community detection algorithms
   - Path sampling and reasoning

2. **Graph Reasoning Router** (`api/routers/graph_reasoning.py`)
   - REST API endpoints for graph operations
   - Exposes all graph reasoning capabilities via HTTP

3. **Database Integration**
   - Loads from `edge_github_collaboration` and `edge_coemployment`
   - Builds in-memory NetworkX graph for fast analysis
   - Computes embeddings on-demand

---

## 🚀 API Endpoints

### 1. Get Graph Statistics

```http
GET /api/graph-reasoning/stats
```

Returns comprehensive graph metrics:
- Node/edge counts
- Density and clustering coefficients
- Top central nodes (influencers)

**Example Response:**
```json
{
  "status": "success",
  "statistics": {
    "num_nodes": 5234,
    "num_edges": 12456,
    "density": 0.0009,
    "avg_clustering": 0.43,
    "is_connected": false,
    "num_components": 15,
    "avg_degree": 4.76,
    "top_central_nodes": [
      {
        "person_id": "uuid-here",
        "full_name": "Jane Smith",
        "betweenness": 0.125
      }
    ]
  }
}
```

### 2. Find Similar People

```http
GET /api/graph-reasoning/similar-people/{person_id}?top_k=10&min_similarity=0.5
```

Find people similar to a given person based on network embeddings.

**Parameters:**
- `person_id` (path): UUID of person
- `top_k` (query): Number of results (max 50)
- `min_similarity` (query): Threshold 0.0-1.0

**Use Cases:**
- "Find people like this candidate"
- "Who else has a similar network position?"
- "Suggest alternatives to this hire"

### 3. Find Key Connectors

```http
GET /api/graph-reasoning/key-connectors?min_betweenness=0.01&limit=20
```

Identify people who bridge different communities (high betweenness centrality).

**Use Cases:**
- "Who are the influencers in our network?"
- "Find people who can introduce me to multiple communities"
- "Identify talent scouts or connectors"

**Example Response:**
```json
{
  "status": "success",
  "key_connectors": [
    {
      "person_id": "uuid",
      "full_name": "John Doe",
      "headline": "Engineering Manager at Coinbase",
      "github_username": "johndoe",
      "betweenness_centrality": 0.0875,
      "degree": 147
    }
  ]
}
```

### 4. Detect Communities

```http
POST /api/graph-reasoning/detect-communities?algorithm=louvain
```

Detect tightly-connected communities in the network.

**Algorithms:**
- `louvain`: Best quality (requires python-louvain)
- `label_propagation`: Fast, good quality
- `greedy_modularity`: Greedy optimization

**Use Cases:**
- "Find clusters of developers who work together"
- "Identify talent pools by community"
- "Understand sub-networks (e.g., Ethereum devs, L2 teams)"

### 5. Get Community Details

```http
GET /api/graph-reasoning/community/{community_id}
```

Get detailed info about a specific community.

**Returns:**
- Community size
- Density (how interconnected)
- Clustering coefficient
- Top members by influence

### 6. Sample Paths Between Concepts

```http
POST /api/graph-reasoning/path-sampling
Content-Type: application/json

{
  "start_concept": "blockchain",
  "end_concept": "machine learning",
  "max_length": 5
}
```

Find innovative connection paths between different domains.

**Use Cases:**
- "How do I connect blockchain experts to AI researchers?"
- "Find interdisciplinary talent bridges"
- "Discover unexpected collaborations"

This implements **path sampling** from GraphReasoning to find novel, non-obvious connections.

### 7. Compute Similarity Between Two People

```http
GET /api/graph-reasoning/similarity/{person1_id}/{person2_id}
```

Get cosine similarity score between two people (0-1).

### 8. Get Node Embedding

```http
GET /api/graph-reasoning/node-embedding/{person_id}
```

Get the embedding vector for a person (for custom analysis).

### 9. Rebuild Graph

```http
POST /api/graph-reasoning/rebuild-graph?limit=10000
```

Rebuild graph from database (use after significant data changes).

### 10. Export Graph

```http
GET /api/graph-reasoning/export/graphml?output_filename=talent_graph.graphml
GET /api/graph-reasoning/export/json?output_filename=talent_graph.json
```

Export graph for external analysis (Gephi, Cytoscape, etc.).

---

## 🧪 Testing

### Run Test Script

```bash
python scripts/test_graph_reasoning.py
```

This will:
1. Build graph from database
2. Compute statistics
3. Find key connectors
4. Detect communities
5. Test similarity calculations
6. Sample paths between concepts
7. Export graph

### Example Output

```
🔬 Graph Reasoning Service Test
================================================================================

📊 Initializing Graph Reasoning Service...
🔨 Building graph from database (limit: 1000 nodes for testing)...
   ✅ Graph built: 847 nodes, 1523 edges

📈 Computing graph statistics...
   • Nodes: 847
   • Edges: 1523
   • Density: 0.0042
   • Average Clustering: 0.38
   • Connected: False
   • Connected Components: 12
   • Average Degree: 3.6

🔗 Finding key connector nodes...
   Found 23 key connectors

   Top 5 Key Connectors:
      1. Vitalik Buterin
         • Betweenness: 0.1234
         • Degree: 156
         • GitHub: @vbuterin
```

---

## 📊 Graph Concepts Explained

### Node Embeddings

Each person is represented as a vector in high-dimensional space based on:
- Degree centrality (how connected they are)
- Betweenness centrality (how much they bridge communities)
- Clustering coefficient (how clustered their neighbors are)
- GitHub metrics (followers, repos)
- Collaboration strength

**Similarity** is computed as cosine similarity between these vectors.

### Betweenness Centrality

Measures how many shortest paths pass through a node. High betweenness = key connector who bridges different groups.

**Example:** A developer who worked at both Coinbase (DeFi) and OpenAI (AI) would have high betweenness, bridging two communities.

### Community Detection

Identifies clusters of highly interconnected nodes. Uses algorithms like:

1. **Louvain**: Optimizes modularity (best quality, slower)
2. **Label Propagation**: Fast, assigns labels based on neighbors
3. **Greedy Modularity**: Iteratively merges communities

**Example Communities:**
- Ethereum core developers
- L2 teams (Optimism, Arbitrum, zkSync)
- DeFi protocol developers (Uniswap, Aave)

### Path Sampling

Finds paths between dissimilar concepts by:
1. Finding nodes matching start concept (e.g., "blockchain" in headline)
2. Finding nodes matching end concept (e.g., "machine learning")
3. Computing all simple paths between them
4. Ranking by **novelty** (how dissimilar intermediate nodes are)

This reveals unexpected connections and interdisciplinary bridges.

---

## 🎯 Use Cases

### 1. Talent Discovery

**Problem:** "Find candidates similar to this great hire"

**Solution:**
```bash
GET /api/graph-reasoning/similar-people/{person_id}?top_k=20
```

Returns people with similar network positions and collaboration patterns.

### 2. Network Intelligence

**Problem:** "Who are the most influential people in our network?"

**Solution:**
```bash
GET /api/graph-reasoning/key-connectors?limit=50
```

Identify people with high betweenness centrality who can unlock multiple networks.

### 3. Community Mapping

**Problem:** "Map the Ethereum developer ecosystem"

**Solution:**
1. Detect communities: `POST /api/graph-reasoning/detect-communities`
2. Analyze each community: `GET /api/graph-reasoning/community/{id}`
3. Identify overlap between communities

### 4. Interdisciplinary Talent

**Problem:** "Find someone who bridges blockchain and AI"

**Solution:**
```bash
POST /api/graph-reasoning/path-sampling
{
  "start_concept": "blockchain",
  "end_concept": "machine learning",
  "max_length": 3
}
```

Returns novel paths connecting the two domains.

### 5. Talent Pool Segmentation

**Problem:** "Segment developers into meaningful groups"

**Solution:**
1. Detect communities
2. Analyze community characteristics
3. Label communities by dominant skills/companies

---

## 🔧 Implementation Details

### Performance

- **Graph Building**: O(N + E) where N = nodes, E = edges
- **Node Embeddings**: O(N * D) where D = embedding dimension
- **Community Detection**: 
  - Louvain: O(E * log N)
  - Label Propagation: O(E)
- **Path Sampling**: O(N^2) worst case (limited by cutoff)

**Optimization:**
- Limit graph size (default: 10,000 nodes)
- Cache embeddings after computation
- Use sampling for large graphs
- Rebuild graph only when needed

### Memory Usage

For 10,000 nodes:
- Graph: ~50 MB
- Embeddings (128-dim): ~5 MB
- Communities: ~1 MB

**Scaling:** For production with 155K people, use:
- Incremental loading
- Distributed graph processing
- Pre-computed embeddings
- Cached results

### Algorithms Used

1. **Betweenness Centrality**: Brandes algorithm
2. **Community Detection**: 
   - Louvain: Modularity optimization
   - Label Propagation: Iterative label spreading
3. **Similarity**: Cosine similarity on embeddings
4. **Path Sampling**: All simple paths with cutoff

---

## 📈 Future Enhancements

### Short-term
- [ ] Pre-compute embeddings for all people
- [ ] Cache community detection results
- [ ] Add temporal analysis (network evolution)
- [ ] Implement proper Node2Vec embeddings

### Long-term
- [ ] Graph neural networks for better embeddings
- [ ] Temporal path sampling (how networks change)
- [ ] Isomorphic pattern matching (à la GraphReasoning)
- [ ] Knowledge graph reasoning (ontological relationships)

---

## 🔗 Related GraphReasoning Concepts

Our implementation is inspired by:

### 1. **Ontological Knowledge Graphs**
GraphReasoning transforms scientific papers into knowledge graphs. We do the same for talent:
- Papers → People
- Citations → Collaborations
- Concepts → Skills/Domains

### 2. **Path Sampling**
GraphReasoning uses path sampling to find "never-before-seen connections" (e.g., biological materials ↔ Beethoven's 9th Symphony).

We use it to find:
- Blockchain developer ↔ AI researcher
- DeFi expert ↔ GameFi expert
- Core protocol dev ↔ Application dev

### 3. **Isomorphic Mapping**
GraphReasoning finds structural parallels across domains. Future work: detect similar collaboration patterns across different ecosystems.

### 4. **Deep Node Embeddings**
We compute embeddings from network features. Future: use proper Node2Vec or DeepWalk for richer representations.

---

## 📚 References

1. **GraphReasoning Paper**: [arXiv:2403.11996](https://arxiv.org/abs/2403.11996)
2. **GraphReasoning Library**: [github.com/lamm-mit/GraphReasoning](https://github.com/lamm-mit/GraphReasoning)
3. **NetworkX Documentation**: [networkx.org](https://networkx.org)
4. **Louvain Algorithm**: [arxiv.org/abs/0803.0476](https://arxiv.org/abs/0803.0476)

---

## 🆘 Troubleshooting

### "Graph not built" error

Run rebuild-graph endpoint first:
```bash
POST /api/graph-reasoning/rebuild-graph
```

### "python-louvain not installed"

Install optional dependency:
```bash
pip install python-louvain
```

Or use `label_propagation` algorithm instead.

### Slow performance

- Reduce graph size: `rebuild-graph?limit=5000`
- Use faster algorithms: `label_propagation` instead of `louvain`
- Pre-compute and cache results

### Out of memory

Large graphs (>50K nodes) may need:
- Distributed processing
- Graph databases (Neo4j)
- Sampling strategies

---

## 🎉 Getting Started

1. **Install dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Start API:**
   ```bash
   python run_api.py
   ```

3. **Build graph:**
   ```bash
   curl -X POST http://localhost:8000/api/graph-reasoning/rebuild-graph
   ```

4. **Test endpoints:**
   ```bash
   curl http://localhost:8000/api/graph-reasoning/stats
   ```

5. **Or run test script:**
   ```bash
   python scripts/test_graph_reasoning.py
   ```

---

**Last Updated**: October 25, 2025  
**Contact**: @charlie.kerr


