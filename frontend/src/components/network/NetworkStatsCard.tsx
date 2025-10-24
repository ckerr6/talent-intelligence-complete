import React, { useState, useEffect } from 'react';
import Card from '../common/Card';
import LoadingSpinner from '../common/LoadingSpinner';

interface NetworkStats {
  github_collaborators: number;
  employment_connections: number;
  total_collaborators: number;
}

interface NetworkStatsCardProps {
  personId: string;
}

export const NetworkStatsCard: React.FC<NetworkStatsCardProps> = ({ personId }) => {
  const [stats, setStats] = useState<NetworkStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    fetchStats();
  }, [personId]);
  
  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch collaborators to get stats
      const response = await fetch(`/api/network/collaborators/${personId}?min_strength=0&limit=500`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch network stats');
      }
      
      const data = await response.json();
      setStats({
        github_collaborators: data.github_collaborators || 0,
        employment_connections: data.employment_connections || 0,
        total_collaborators: data.total_collaborators || 0
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center py-4">
          <LoadingSpinner />
        </div>
      </Card>
    );
  }
  
  if (error || !stats) {
    return (
      <Card className="p-6">
        <div className="text-center py-4 text-red-600">
          <p className="text-sm">Error loading network stats</p>
        </div>
      </Card>
    );
  }
  
  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
          <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Network Overview</h3>
          <p className="text-sm text-gray-600">Professional connections and collaborations</p>
        </div>
      </div>
      
      <div className="grid grid-cols-3 gap-4">
        {/* Total Connections */}
        <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg">
          <div className="text-3xl font-bold text-blue-600">
            {stats.total_collaborators}
          </div>
          <div className="text-xs text-gray-600 mt-1">Total Connections</div>
        </div>
        
        {/* GitHub Collaborators */}
        <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg">
          <div className="text-3xl font-bold text-purple-600">
            {stats.github_collaborators}
          </div>
          <div className="text-xs text-gray-600 mt-1">
            <span className="inline-block mr-1">💻</span>
            GitHub Collaborators
          </div>
        </div>
        
        {/* Co-workers */}
        <div className="text-center p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg">
          <div className="text-3xl font-bold text-green-600">
            {stats.employment_connections}
          </div>
          <div className="text-xs text-gray-600 mt-1">
            <span className="inline-block mr-1">🏢</span>
            Co-workers
          </div>
        </div>
      </div>
      
      {/* Network Strength Visualization */}
      {stats.total_collaborators > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Network Breakdown</span>
            <span className="text-xs text-gray-500">{stats.total_collaborators} total</span>
          </div>
          <div className="flex h-3 rounded-full overflow-hidden bg-gray-200">
            {stats.github_collaborators > 0 && (
              <div
                className="bg-purple-500"
                style={{
                  width: `${(stats.github_collaborators / stats.total_collaborators) * 100}%`
                }}
                title={`${stats.github_collaborators} GitHub collaborators`}
              />
            )}
            {stats.employment_connections > 0 && (
              <div
                className="bg-green-500"
                style={{
                  width: `${(stats.employment_connections / stats.total_collaborators) * 100}%`
                }}
                title={`${stats.employment_connections} co-workers`}
              />
            )}
          </div>
          <div className="flex justify-between mt-2 text-xs text-gray-600">
            <span>
              💻 {((stats.github_collaborators / stats.total_collaborators) * 100).toFixed(0)}% GitHub
            </span>
            <span>
              🏢 {((stats.employment_connections / stats.total_collaborators) * 100).toFixed(0)}% Employment
            </span>
          </div>
        </div>
      )}
      
      {stats.total_collaborators === 0 && (
        <div className="mt-6 pt-6 border-t border-gray-200 text-center text-sm text-gray-500">
          <p>No network connections found yet</p>
          <p className="text-xs mt-1">Connections will appear as the collaboration network is built</p>
        </div>
      )}
    </Card>
  );
};

export default NetworkStatsCard;

