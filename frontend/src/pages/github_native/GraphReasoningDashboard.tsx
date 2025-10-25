import React, { useState, useEffect } from 'react';
import { 
  Network, 
  Users, 
  TrendingUp, 
  GitBranch, 
  Search,
  RefreshCw,
  Download,
  Info
} from 'lucide-react';

const GraphReasoningDashboard: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [keyConnectors, setKeyConnectors] = useState<any[]>([]);
  const [communities, setCommunities] = useState<any[]>([]);
  const [selectedCommunity, setSelectedCommunity] = useState<any>(null);
  const [similarPeople, setSimilarPeople] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('stats');
  
  // Form states
  const [similarityPersonId, setSimilarityPersonId] = useState('');
  const [pathStart, setPathStart] = useState('');
  const [pathEnd, setPathEnd] = useState('');
  const [paths, setPaths] = useState<any[]>([]);

  useEffect(() => {
    loadGraphStats();
    loadKeyConnectors();
  }, []);

  const loadGraphStats = async () => {
    try {
      const response = await fetch('/api/graph-reasoning/stats');
      const data = await response.json();
      if (data.status === 'success') {
        setStats(data.statistics);
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const loadKeyConnectors = async () => {
    try {
      const response = await fetch('/api/graph-reasoning/key-connectors?limit=20');
      const data = await response.json();
      if (data.status === 'success') {
        setKeyConnectors(data.key_connectors);
      }
    } catch (error) {
      console.error('Error loading key connectors:', error);
    }
  };

  const detectCommunities = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/graph-reasoning/detect-communities?algorithm=label_propagation', {
        method: 'POST'
      });
      const data = await response.json();
      if (data.status === 'success') {
        setCommunities(data.communities);
      }
    } catch (error) {
      console.error('Error detecting communities:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCommunityDetails = async (communityId: number) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/graph-reasoning/community/${communityId}`);
      const data = await response.json();
      if (data.status === 'success') {
        setSelectedCommunity(data.community);
      }
    } catch (error) {
      console.error('Error loading community details:', error);
    } finally {
      setLoading(false);
    }
  };

  const findSimilarPeople = async () => {
    if (!similarityPersonId) return;
    
    setLoading(true);
    try {
      const response = await fetch(
        `/api/graph-reasoning/similar-people/${similarityPersonId}?top_k=10&min_similarity=0.3`
      );
      const data = await response.json();
      if (data.status === 'success') {
        setSimilarPeople(data.similar_people);
      }
    } catch (error) {
      console.error('Error finding similar people:', error);
    } finally {
      setLoading(false);
    }
  };

  const samplePaths = async () => {
    if (!pathStart || !pathEnd) return;
    
    setLoading(true);
    try {
      const response = await fetch('/api/graph-reasoning/path-sampling', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_concept: pathStart,
          end_concept: pathEnd,
          max_length: 5
        })
      });
      const data = await response.json();
      if (data.status === 'success') {
        setPaths(data.paths);
      }
    } catch (error) {
      console.error('Error sampling paths:', error);
    } finally {
      setLoading(false);
    }
  };

  const rebuildGraph = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/graph-reasoning/rebuild-graph?limit=10000', {
        method: 'POST'
      });
      const data = await response.json();
      if (data.status === 'success') {
        setStats(data.statistics);
        alert('Graph rebuilt successfully!');
      }
    } catch (error) {
      console.error('Error rebuilding graph:', error);
      alert('Failed to rebuild graph');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Network className="w-8 h-8 text-indigo-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Graph Reasoning</h1>
                <p className="text-gray-600">Advanced network analysis and intelligence</p>
              </div>
            </div>
            <button
              onClick={rebuildGraph}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Rebuild Graph
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm mb-6">
          <div className="flex border-b">
            {[
              { id: 'stats', label: 'Statistics', icon: TrendingUp },
              { id: 'connectors', label: 'Key Connectors', icon: Users },
              { id: 'communities', label: 'Communities', icon: GitBranch },
              { id: 'similarity', label: 'Similarity', icon: Search },
              { id: 'paths', label: 'Path Sampling', icon: Network }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-6 py-4 font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="space-y-6">
          {/* Statistics Tab */}
          {activeTab === 'stats' && stats && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <StatCard 
                title="Nodes" 
                value={stats.num_nodes.toLocaleString()} 
                subtitle="People in network"
                color="blue"
              />
              <StatCard 
                title="Edges" 
                value={stats.num_edges.toLocaleString()} 
                subtitle="Collaborations"
                color="green"
              />
              <StatCard 
                title="Density" 
                value={stats.density.toFixed(4)} 
                subtitle="Network connectivity"
                color="purple"
              />
              <StatCard 
                title="Avg Degree" 
                value={stats.avg_degree.toFixed(2)} 
                subtitle="Connections per person"
                color="orange"
              />
              <StatCard 
                title="Avg Clustering" 
                value={stats.avg_clustering.toFixed(4)} 
                subtitle="Local clustering"
                color="pink"
              />
              <StatCard 
                title="Components" 
                value={stats.num_components} 
                subtitle="Separate networks"
                color="teal"
              />

              {/* Top Central Nodes */}
              <div className="col-span-full bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Most Central Nodes (Betweenness)
                </h3>
                <div className="space-y-3">
                  {stats.top_central_nodes?.map((node: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <div>
                        <div className="font-medium text-gray-900">{node.full_name}</div>
                        <div className="text-sm text-gray-600">
                          Betweenness: {node.betweenness.toFixed(4)}
                        </div>
                      </div>
                      <div className="text-indigo-600 font-semibold">#{idx + 1}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Key Connectors Tab */}
          {activeTab === 'connectors' && (
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Key Connector Nodes</h3>
                <div className="text-sm text-gray-600">
                  {keyConnectors.length} connectors found
                </div>
              </div>
              <div className="space-y-3">
                {keyConnectors.map((connector: any, idx: number) => (
                  <div key={idx} className="p-4 border border-gray-200 rounded-lg hover:border-indigo-300 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900">{connector.full_name}</div>
                        <div className="text-sm text-gray-600 mt-1">{connector.headline}</div>
                        {connector.github_username && (
                          <div className="text-sm text-indigo-600 mt-1">
                            @{connector.github_username}
                          </div>
                        )}
                      </div>
                      <div className="text-right ml-4">
                        <div className="text-2xl font-bold text-indigo-600">
                          {connector.betweenness_centrality.toFixed(4)}
                        </div>
                        <div className="text-sm text-gray-600">Betweenness</div>
                        <div className="text-sm text-gray-600 mt-1">
                          Degree: {connector.degree}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Communities Tab */}
          {activeTab === 'communities' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Communities</h3>
                  <button
                    onClick={detectCommunities}
                    disabled={loading}
                    className="px-4 py-2 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700 disabled:opacity-50"
                  >
                    Detect Communities
                  </button>
                </div>
                <div className="space-y-2">
                  {communities.map((comm: any) => (
                    <div
                      key={comm.community_id}
                      onClick={() => loadCommunityDetails(comm.community_id)}
                      className="p-3 border border-gray-200 rounded hover:border-indigo-300 cursor-pointer transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">Community {comm.community_id}</div>
                          <div className="text-sm text-gray-600">{comm.size} members</div>
                        </div>
                        <div className="text-indigo-600">→</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {selectedCommunity && (
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Community {selectedCommunity.community_id} Details
                  </h3>
                  <div className="space-y-4">
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center p-3 bg-blue-50 rounded">
                        <div className="text-2xl font-bold text-blue-600">
                          {selectedCommunity.size}
                        </div>
                        <div className="text-sm text-gray-600">Members</div>
                      </div>
                      <div className="text-center p-3 bg-green-50 rounded">
                        <div className="text-2xl font-bold text-green-600">
                          {selectedCommunity.density.toFixed(3)}
                        </div>
                        <div className="text-sm text-gray-600">Density</div>
                      </div>
                      <div className="text-center p-3 bg-purple-50 rounded">
                        <div className="text-2xl font-bold text-purple-600">
                          {selectedCommunity.avg_clustering.toFixed(3)}
                        </div>
                        <div className="text-sm text-gray-600">Clustering</div>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Top Members</h4>
                      <div className="space-y-2">
                        {selectedCommunity.members?.slice(0, 10).map((member: any, idx: number) => (
                          <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                            <div className="text-sm">{member.full_name}</div>
                            <div className="text-sm text-gray-600">Degree: {member.degree}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Similarity Tab */}
          {activeTab === 'similarity' && (
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Find Similar People</h3>
              <div className="flex gap-4 mb-6">
                <input
                  type="text"
                  value={similarityPersonId}
                  onChange={(e) => setSimilarityPersonId(e.target.value)}
                  placeholder="Enter person UUID..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
                <button
                  onClick={findSimilarPeople}
                  disabled={loading || !similarityPersonId}
                  className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  Find Similar
                </button>
              </div>
              <div className="space-y-3">
                {similarPeople.map((person: any, idx: number) => (
                  <div key={idx} className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">{person.full_name}</div>
                        <div className="text-sm text-gray-600">{person.headline}</div>
                        {person.github_username && (
                          <div className="text-sm text-indigo-600">@{person.github_username}</div>
                        )}
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-indigo-600">
                          {person.similarity_score.toFixed(3)}
                        </div>
                        <div className="text-sm text-gray-600">Similarity</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Path Sampling Tab */}
          {activeTab === 'paths' && (
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Path Sampling Between Concepts</h3>
              <div className="grid grid-cols-2 gap-4 mb-6">
                <input
                  type="text"
                  value={pathStart}
                  onChange={(e) => setPathStart(e.target.value)}
                  placeholder="Start concept (e.g., 'blockchain')"
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
                <input
                  type="text"
                  value={pathEnd}
                  onChange={(e) => setPathEnd(e.target.value)}
                  placeholder="End concept (e.g., 'machine learning')"
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <button
                onClick={samplePaths}
                disabled={loading || !pathStart || !pathEnd}
                className="w-full px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 mb-6"
              >
                Sample Paths
              </button>
              <div className="space-y-4">
                {paths.map((path: any, idx: number) => (
                  <div key={idx} className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <div className="font-medium text-gray-900">Path {idx + 1}</div>
                      <div className="text-sm text-gray-600">
                        Novelty: {path.novelty_score?.toFixed(3)}
                      </div>
                    </div>
                    <div className="space-y-2">
                      {path.nodes?.map((node: any, nodeIdx: number) => (
                        <div key={nodeIdx} className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-semibold text-sm">
                            {nodeIdx + 1}
                          </div>
                          <div className="flex-1">
                            <div className="font-medium text-sm">{node.full_name}</div>
                            <div className="text-xs text-gray-600">{node.headline}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Helper component for stat cards
const StatCard: React.FC<{
  title: string;
  value: string | number;
  subtitle: string;
  color: string;
}> = ({ title, value, subtitle, color }) => {
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    orange: 'bg-orange-50 text-orange-600',
    pink: 'bg-pink-50 text-pink-600',
    teal: 'bg-teal-50 text-teal-600',
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="text-sm font-medium text-gray-600 mb-1">{title}</div>
      <div className={`text-3xl font-bold mb-1 ${colorClasses[color]?.split(' ')[1] || 'text-gray-900'}`}>
        {value}
      </div>
      <div className="text-sm text-gray-500">{subtitle}</div>
    </div>
  );
};

export default GraphReasoningDashboard;

