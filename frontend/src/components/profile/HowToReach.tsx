import { useQuery } from '@tanstack/react-query';
import api from '../../services/api';

interface HowToReachProps {
  targetPersonId: string;
  sourcePersonId?: string; // If provided, show path from source to target
}

export default function HowToReach({ targetPersonId, sourcePersonId }: HowToReachProps) {
  // For MVP, we'll use a placeholder source (you, the founder)
  // In production, this would be the logged-in user
  const effectiveSourceId = sourcePersonId || 'current-user-placeholder';

  const { data: path, isLoading, error } = useQuery({
    queryKey: ['networkPath', effectiveSourceId, targetPersonId],
    queryFn: () => api.findPath(effectiveSourceId, targetPersonId),
    enabled: effectiveSourceId !== 'current-user-placeholder', // Don't query if no real source
    retry: false,
  });

  // For MVP demo, show placeholder
  if (effectiveSourceId === 'current-user-placeholder') {
    return (
      <div className="bg-gradient-to-br from-primary-50 to-secondary-50 rounded-lg shadow-md p-6 border-2 border-primary-200">
        <div className="flex items-center space-x-2 mb-4">
          <span className="text-2xl">🔗</span>
          <h2 className="text-xl font-semibold text-gray-900">How to Reach</h2>
        </div>
        
        <div className="bg-white rounded-lg p-4 mb-4">
          <p className="text-gray-600 mb-2">
            Connect your profile to discover warm introduction paths to candidates.
          </p>
          <p className="text-sm text-gray-500">
            Our AI will analyze your network and show you the shortest path through mutual connections.
          </p>
        </div>

        <div className="flex items-center justify-center space-x-3 py-4">
          <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center">
            <span className="text-gray-600 font-medium">You</span>
          </div>
          <div className="flex-1 h-0.5 bg-gray-300 relative">
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white px-2">
              <span className="text-xs text-gray-500">? connections</span>
            </div>
          </div>
          <div className="w-12 h-12 rounded-full bg-primary-200 flex items-center justify-center">
            <span className="text-primary-700 font-medium text-sm">👤</span>
          </div>
        </div>

        <button className="w-full mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium">
          Connect Your Profile
        </button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">How to Reach</h2>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-4 border-gray-300 border-t-primary-600"></div>
          <span className="ml-3 text-gray-600">Finding connection path...</span>
        </div>
      </div>
    );
  }

  if (error || !path) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">How to Reach</h2>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800">
            No connection path found within 3 degrees of separation.
          </p>
          <p className="mt-2 text-sm text-yellow-700">
            Consider reaching out via LinkedIn or expanding your network.
          </p>
        </div>
      </div>
    );
  }

  const degreesText = path.path_length === 1 ? '1st degree' : path.path_length === 2 ? '2nd degree' : '3rd degree';

  return (
    <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-lg shadow-md p-6 border-2 border-green-200">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <span className="text-2xl">🎯</span>
          <h2 className="text-xl font-semibold text-gray-900">How to Reach</h2>
        </div>
        <span className="px-3 py-1 bg-green-100 text-green-800 text-sm font-semibold rounded-full">
          {degreesText}
        </span>
      </div>

      {/* Path Visualization */}
      <div className="bg-white rounded-lg p-6 mb-4">
        <div className="flex items-center justify-between">
          {path.nodes.map((node, index) => (
            <div key={node.person_id} className="flex items-center">
              {/* Node */}
              <div className="flex flex-col items-center">
                <div className={`w-16 h-16 rounded-full flex items-center justify-center ${
                  index === 0 ? 'bg-blue-500' :
                  index === path.nodes.length - 1 ? 'bg-green-500' :
                  'bg-gray-400'
                } text-white font-bold text-sm`}>
                  {node.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                </div>
                <p className="mt-2 text-sm font-medium text-gray-900 text-center max-w-[100px] truncate">
                  {node.name}
                </p>
                {node.headline && (
                  <p className="text-xs text-gray-500 text-center max-w-[100px] truncate">
                    {node.headline}
                  </p>
                )}
              </div>

              {/* Arrow */}
              {index < path.nodes.length - 1 && path.edges[index] && (
                <div className="flex flex-col items-center mx-4">
                  <div className="text-2xl text-gray-400">→</div>
                  <p className="text-xs text-gray-500 mt-1">
                    {path.edges[index].type === 'coworker' ? '👔' : '💻'}
                    {path.edges[index].company || path.edges[index].repo}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Action */}
      {path.nodes.length > 1 && (
        <div className="space-y-3">
          <button className="w-full px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium">
            Request Intro via {path.nodes[1].name}
          </button>
          <p className="text-sm text-gray-600 text-center">
            {path.edges[0]?.type === 'coworker' 
              ? `You worked together at ${path.edges[0]?.company}`
              : `You collaborated on ${path.edges[0]?.repo}`
            }
          </p>
        </div>
      )}
    </div>
  );
}

