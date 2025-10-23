import { useEffect, useRef, useState } from 'react';
import { Network, Options, Data } from 'vis-network/standalone';
import { useNavigate } from 'react-router-dom';

interface NetworkGraphProps {
  centerPersonId: string;
  centerPersonName: string;
  maxDegree: number;
  companyFilter?: string;
  repoFilter?: string;
  onNodeClick?: (personId: string) => void;
}

interface NetworkNode {
  person_id: string;
  name: string;
  title?: string;
  location?: string;
  degree: number;
}

interface NetworkEdge {
  source: string;
  target: string;
  connection_type: string;
}

export default function NetworkGraph({
  centerPersonId,
  centerPersonName,
  maxDegree,
  companyFilter,
  repoFilter,
  onNodeClick,
}: NetworkGraphProps) {
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState({ nodeCount: 0, edgeCount: 0 });

  useEffect(() => {
    if (!containerRef.current) return;

    const fetchGraphData = async () => {
      setLoading(true);
      setError(null);

      try {
        const params = new URLSearchParams({
          center: centerPersonId,
          max_degree: maxDegree.toString(),
          limit: '200',
        });

        if (companyFilter) params.append('company_filter', companyFilter);
        if (repoFilter) params.append('repo_filter', repoFilter);

        const response = await fetch(`/api/network/graph?${params}`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch network graph data');
        }

        const data = await response.json();
        
        setStats({
          nodeCount: data.node_count,
          edgeCount: data.edge_count,
        });

        // Transform data for vis-network
        const visNodes = data.nodes.map((node: NetworkNode) => ({
          id: node.person_id,
          label: node.name,
          title: `${node.name}\n${node.title || 'No title'}\n${node.location || ''}`,
          level: node.degree,
          color: getNodeColor(node.degree, node.person_id === centerPersonId),
          size: node.degree === 0 ? 30 : 20 - (node.degree * 3),
          font: {
            size: node.degree === 0 ? 16 : 14,
            color: '#333',
            bold: node.degree === 0,
          },
        }));

        const visEdges = data.edges.map((edge: NetworkEdge, idx: number) => ({
          id: `edge-${idx}`,
          from: edge.source,
          to: edge.target,
          color: getEdgeColor(edge.connection_type),
          title: edge.connection_type === 'coworker' ? 'Co-worker' : 'GitHub Collaborator',
          width: 2,
          smooth: {
            type: 'continuous',
          },
        }));

        const graphData: Data = {
          nodes: visNodes,
          edges: visEdges,
        };

        const options: Options = {
          nodes: {
            shape: 'dot',
            borderWidth: 2,
            borderWidthSelected: 4,
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
          physics: {
            enabled: true,
            barnesHut: {
              gravitationalConstant: -8000,
              centralGravity: 0.3,
              springLength: 150,
              springConstant: 0.04,
              damping: 0.09,
            },
            stabilization: {
              iterations: 150,
            },
          },
          interaction: {
            hover: true,
            tooltipDelay: 100,
            zoomView: true,
            dragView: true,
          },
          layout: {
            improvedLayout: true,
            hierarchical: {
              enabled: false,
            },
          },
        };

        // Destroy existing network if it exists
        if (networkRef.current) {
          networkRef.current.destroy();
        }

        // Create new network
        if (!containerRef.current) {
          throw new Error('Container ref is null');
        }
        const network = new Network(containerRef.current, graphData, options);
        networkRef.current = network;

        // Add click event
        network.on('click', (params) => {
          if (params.nodes.length > 0) {
            const nodeId = params.nodes[0] as string;
            if (onNodeClick) {
              onNodeClick(nodeId);
            } else {
              navigate(`/profile/${nodeId}`);
            }
          }
        });

        // Add hover effect
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

        setLoading(false);
      } catch (err) {
        console.error('Error loading network graph:', err);
        setError(err instanceof Error ? err.message : 'Failed to load network graph');
        setLoading(false);
      }
    };

    fetchGraphData();

    // Cleanup
    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [centerPersonId, maxDegree, companyFilter, repoFilter, navigate, onNodeClick]);

  const getNodeColor = (degree: number, isCenter: boolean) => {
    if (isCenter) {
      return { background: '#4F46E5', border: '#312E81' }; // Primary color
    }
    switch (degree) {
      case 1:
        return { background: '#10B981', border: '#059669' }; // Green
      case 2:
        return { background: '#F59E0B', border: '#D97706' }; // Orange
      case 3:
        return { background: '#EF4444', border: '#DC2626' }; // Red
      default:
        return { background: '#6B7280', border: '#4B5563' }; // Gray
    }
  };

  const getEdgeColor = (connectionType: string) => {
    return connectionType === 'coworker' 
      ? { color: '#3B82F6', highlight: '#2563EB' } // Blue
      : { color: '#8B5CF6', highlight: '#7C3AED' }; // Purple
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full min-h-[600px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          <p className="mt-4 text-gray-600">Building network graph...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-red-900 mb-2">Error Loading Network</h3>
        <p className="text-red-700">{error}</p>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Stats Bar */}
      <div className="absolute top-4 left-4 z-10 bg-white rounded-lg shadow-md p-4">
        <div className="space-y-2 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-primary-600"></div>
            <span className="font-medium">{centerPersonName} (Center)</span>
          </div>
          <div className="text-gray-600">
            <span className="font-medium">{stats.nodeCount}</span> people
          </div>
          <div className="text-gray-600">
            <span className="font-medium">{stats.edgeCount}</span> connections
          </div>
          <div className="pt-2 border-t border-gray-200">
            <div className="text-xs text-gray-500 space-y-1">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
                <span>1st degree</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                <span>2nd degree</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 rounded-full bg-red-500"></div>
                <span>3rd degree</span>
              </div>
            </div>
          </div>
          <div className="pt-2 border-t border-gray-200">
            <div className="text-xs text-gray-500 space-y-1">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-0.5 bg-blue-500"></div>
                <span>Co-worker</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-8 h-0.5 bg-purple-500"></div>
                <span>GitHub</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Network Container */}
      <div
        ref={containerRef}
        className="w-full h-[600px] border border-gray-200 rounded-lg bg-gray-50"
        style={{ minHeight: '600px' }}
      />

      {/* Instructions */}
      <div className="mt-4 text-sm text-gray-600">
        <p><strong>Tip:</strong> Click on any node to view their profile. Scroll to zoom, drag to pan.</p>
      </div>
    </div>
  );
}

