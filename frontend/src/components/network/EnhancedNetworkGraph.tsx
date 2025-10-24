import { useEffect, useRef, useState } from 'react';
import { Network, Options, Data } from 'vis-network/standalone';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { Users, GitBranch, AlertCircle } from 'lucide-react';

interface EnhancedNetworkGraphProps {
  personIds: string[];
  maxDegree: number;
  technologies?: string[];
  connectionTypes: string[];
  employmentStatus: string;
  companyFilter?: string;
  layoutType: string;
}

interface GraphNode {
  person_id: string;
  name: string;
  title?: string;
  location?: string;
  degree: number;
  is_center: boolean;
  is_connector: boolean;
  connects?: string[];
}

interface GraphEdge {
  source: string;
  target: string;
  connection_type: string;
  company_id?: string;
  overlap_months?: number;
  employment_status?: string;
}

interface GraphData {
  center_people: string[];
  node_count: number;
  edge_count: number;
  connector_count: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
  connectors: GraphNode[];
}

export default function EnhancedNetworkGraph({
  personIds,
  maxDegree,
  technologies = [],
  connectionTypes,
  employmentStatus,
  companyFilter,
  layoutType,
}: EnhancedNetworkGraphProps) {
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);

  // Fetch graph data
  useEffect(() => {
    const fetchGraphData = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await axios.post('http://localhost:8000/api/network/multi-node-graph', {
          person_ids: personIds,
          max_degree: maxDegree,
          limit: 200,
          technologies: technologies.length > 0 ? technologies : null,
          connection_types: connectionTypes.length > 0 ? connectionTypes : null,
          employment_status: employmentStatus,
          company_filter: companyFilter || null,
        });

        setGraphData(response.data);
        setLoading(false);
      } catch (err: any) {
        console.error('Error loading multi-node graph:', err);
        setError(err.response?.data?.detail || 'Failed to load network graph');
        setLoading(false);
      }
    };

    fetchGraphData();
  }, [personIds, maxDegree, technologies, connectionTypes, employmentStatus, companyFilter]);

  // Render visualization
  useEffect(() => {
    if (!graphData || !containerRef.current || loading) {
      return;
    }

    const visNodes = graphData.nodes.map((node) => ({
      id: node.person_id,
      label: node.name,
      title: `${node.name}\n${node.title || 'No title'}\n${node.location || ''}\n${
        node.is_connector ? '🔗 Connector' : ''
      }`,
      level: node.degree,
      color: getNodeColor(node),
      size: node.is_center ? 35 : node.is_connector ? 25 : 20,
      font: {
        size: node.is_center ? 16 : node.is_connector ? 14 : 12,
        color: '#333',
        bold: node.is_center || node.is_connector,
      },
      borderWidth: node.is_connector ? 4 : 2,
      borderWidthSelected: node.is_connector ? 6 : 4,
    }));

    const visEdges = graphData.edges.map((edge, idx) => ({
      id: `edge-${idx}`,
      from: edge.source,
      to: edge.target,
      color: getEdgeColor(edge.connection_type, edge.employment_status),
      title: getEdgeTitle(edge),
      width: edge.connection_type === 'coworker' ? 2 : 1.5,
      dashes: edge.employment_status === 'former' ? [5, 5] : false,
      smooth: {
        type: 'continuous',
      },
    }));

    const options: Options = {
      nodes: {
        shape: 'dot',
        shadow: true,
      },
      edges: {
        arrows: {
          to: { enabled: false },
        },
        smooth: {
          enabled: true,
          type: 'continuous',
          roundness: 0.5,
        },
      },
      physics: getPhysicsOptions(layoutType),
      interaction: {
        hover: true,
        tooltipDelay: 100,
        zoomView: true,
        dragView: true,
        navigationButtons: true,
      },
      layout: getLayoutOptions(layoutType),
    };

    // Destroy existing network
    if (networkRef.current) {
      networkRef.current.destroy();
    }

    // Create new network
    const network = new Network(
      containerRef.current,
      { nodes: visNodes, edges: visEdges },
      options
    );
    networkRef.current = network;

    // Add click event
    network.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0] as string;
        navigate(`/profile/${nodeId}`);
      }
    });

    // Add hover effects
    network.on('hoverNode', () => {
      if (containerRef.current) {
        containerRef.current.style.cursor = 'pointer';
      }
    });

    network.on('blurNode', () => {
      if (containerRef.current) {
        containerRef.current.style.cursor = 'default';
      }
    });

    // Cleanup
    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [graphData, layoutType, navigate, loading]);

  const getNodeColor = (node: GraphNode) => {
    if (node.is_center) {
      return { background: '#4F46E5', border: '#312E81' }; // Primary - center people
    }
    if (node.is_connector) {
      return { background: '#F59E0B', border: '#D97706' }; // Amber - connectors
    }
    if (node.degree === 1) {
      return { background: '#10B981', border: '#059669' }; // Green - 1st degree
    }
    return { background: '#6B7280', border: '#4B5563' }; // Gray - 2nd degree+
  };

  const getEdgeColor = (type: string, status?: string) => {
    if (status === 'former') {
      return { color: '#9CA3AF', opacity: 0.6 }; // Gray for former
    }
    if (type === 'coworker') {
      return { color: '#3B82F6' }; // Blue for co-workers
    }
    return { color: '#8B5CF6' }; // Purple for GitHub
  };

  const getEdgeTitle = (edge: GraphEdge) => {
    let title = edge.connection_type === 'coworker' ? 'Co-worker' : 'GitHub Collaborator';
    if (edge.employment_status) {
      title += ` (${edge.employment_status})`;
    }
    if (edge.overlap_months) {
      title += ` - ${edge.overlap_months} months overlap`;
    }
    return title;
  };

  const getPhysicsOptions = (layout: string) => {
    if (layout === 'hierarchical' || layout === 'circular') {
      return { enabled: false };
    }
    return {
      enabled: true,
      barnesHut: {
        gravitationalConstant: -8000,
        centralGravity: 0.3,
        springLength: 150,
        springConstant: 0.04,
        damping: 0.09,
      },
      stabilization: {
        iterations: 200,
      },
    };
  };

  const getLayoutOptions = (layout: string) => {
    if (layout === 'hierarchical') {
      return {
        hierarchical: {
          enabled: true,
          direction: 'UD',
          sortMethod: 'directed',
          levelSeparation: 150,
        },
      };
    }
    if (layout === 'circular') {
      return {
        hierarchical: false,
        randomSeed: 2,
      };
    }
    return {
      improvedLayout: true,
      hierarchical: false,
    };
  };

  if (loading) {
    return (
      <Card>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading network graph...</p>
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <div className="flex items-center justify-center h-96">
          <div className="text-center text-red-600">
            <AlertCircle className="w-12 h-12 mx-auto mb-4" />
            <p className="font-medium">{error}</p>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Stats Cards */}
      {graphData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card padding="sm">
            <div className="text-center">
              <Users className="w-6 h-6 text-primary-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-gray-900">{graphData.node_count}</div>
              <div className="text-sm text-gray-600">Total People</div>
            </div>
          </Card>
          
          <Card padding="sm">
            <div className="text-center">
              <GitBranch className="w-6 h-6 text-blue-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-gray-900">{graphData.edge_count}</div>
              <div className="text-sm text-gray-600">Connections</div>
            </div>
          </Card>
          
          <Card padding="sm">
            <div className="text-center">
              <div className="w-6 h-6 bg-amber-500 rounded-full mx-auto mb-2"></div>
              <div className="text-2xl font-bold text-gray-900">{graphData.connector_count}</div>
              <div className="text-sm text-gray-600">Connectors</div>
            </div>
          </Card>
          
          <Card padding="sm">
            <div className="text-center">
              <div className="w-6 h-6 bg-primary-600 rounded-full mx-auto mb-2"></div>
              <div className="text-2xl font-bold text-gray-900">{graphData.center_people.length}</div>
              <div className="text-sm text-gray-600">Center People</div>
            </div>
          </Card>
        </div>
      )}

      {/* Connectors List */}
      {graphData && graphData.connectors.length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            🔗 Key Connectors
          </h3>
          <p className="text-sm text-gray-600 mb-3">
            These people connect 2 or more of your selected people
          </p>
          <div className="space-y-2">
            {graphData.connectors.slice(0, 10).map((connector) => (
              <div
                key={connector.person_id}
                className="flex items-center justify-between p-3 bg-amber-50 border border-amber-200 rounded-lg hover:bg-amber-100 cursor-pointer"
                onClick={() => navigate(`/profile/${connector.person_id}`)}
              >
                <div>
                  <div className="font-medium text-gray-900">{connector.name}</div>
                  {connector.title && (
                    <div className="text-sm text-gray-600">{connector.title}</div>
                  )}
                </div>
                <Badge variant="warning" size="sm">
                  Connects {connector.connects?.length || 0} people
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Graph Visualization */}
      <Card>
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Network Visualization</h3>
          <div className="flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-primary-600 rounded-full"></div>
              <span className="text-gray-600">Center People</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-amber-500 rounded-full"></div>
              <span className="text-gray-600">Connectors</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-500 rounded-full"></div>
              <span className="text-gray-600">1st Degree</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-0.5 bg-blue-600"></div>
              <span className="text-gray-600">Co-worker</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-0.5 bg-purple-600"></div>
              <span className="text-gray-600">GitHub</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-0.5 border-t-2 border-dashed border-gray-400"></div>
              <span className="text-gray-600">Former</span>
            </div>
          </div>
        </div>
        <div
          ref={containerRef}
          className="w-full h-[600px] border border-gray-200 rounded-lg bg-white"
        />
      </Card>
    </div>
  );
}

