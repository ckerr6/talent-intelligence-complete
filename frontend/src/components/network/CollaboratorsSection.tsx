import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Card from '../common/Card';
import LoadingSpinner from '../common/LoadingSpinner';
import EmptyState from '../common/EmptyState';

interface Collaborator {
  person_id: string;
  full_name: string;
  connection_type: 'github' | 'employment';
  strength: number;
  shared_repos?: number;
  shared_companies?: number;
  last_interaction: string;
}

interface CollaboratorsSectionProps {
  personId: string;
}

export const CollaboratorsSection: React.FC<CollaboratorsSectionProps> = ({ personId }) => {
  const [collaborators, setCollaborators] = useState<Collaborator[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [minStrength, setMinStrength] = useState(0.3);
  const [filterType, setFilterType] = useState<'all' | 'github' | 'employment'>('all');
  
  useEffect(() => {
    fetchCollaborators();
  }, [personId, minStrength]);
  
  const fetchCollaborators = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(
        `/api/network/collaborators/${personId}?min_strength=${minStrength}&limit=100`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch collaborators');
      }
      
      const data = await response.json();
      setCollaborators(data.collaborators || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  const filteredCollaborators = collaborators.filter(c => {
    if (filterType === 'all') return true;
    return c.connection_type === filterType;
  });
  
  const renderStars = (strength: number) => {
    const starCount = Math.ceil(strength * 5);
    return '⭐'.repeat(starCount);
  };
  
  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };
  
  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner />
        </div>
      </Card>
    );
  }
  
  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center py-8 text-red-600">
          <p>Error loading collaborators: {error}</p>
          <button 
            onClick={fetchCollaborators}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }
  
  if (collaborators.length === 0) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Collaborators</h3>
        <EmptyState
          icon={
            <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          }
          title="No collaborators found"
          description="This person hasn't collaborated with others in our database yet, or the collaboration network hasn't been built."
        />
      </Card>
    );
  }
  
  return (
    <Card className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Collaborators ({collaborators.length})
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          People who have worked with or collaborated with this person
        </p>
      </div>
      
      {/* Controls */}
      <div className="mb-6 space-y-4">
        {/* Strength Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Minimum Collaboration Strength: {(minStrength * 100).toFixed(0)}%
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={minStrength}
            onChange={(e) => setMinStrength(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Any (0%)</span>
            <span>Strong (50%)</span>
            <span>Very Strong (100%)</span>
          </div>
        </div>
        
        {/* Type Filter */}
        <div className="flex gap-2">
          <button
            onClick={() => setFilterType('all')}
            className={`px-4 py-2 text-sm rounded-md transition-colors ${
              filterType === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All ({collaborators.length})
          </button>
          <button
            onClick={() => setFilterType('github')}
            className={`px-4 py-2 text-sm rounded-md transition-colors ${
              filterType === 'github'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            💻 GitHub ({collaborators.filter(c => c.connection_type === 'github').length})
          </button>
          <button
            onClick={() => setFilterType('employment')}
            className={`px-4 py-2 text-sm rounded-md transition-colors ${
              filterType === 'employment'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            🏢 Co-workers ({collaborators.filter(c => c.connection_type === 'employment').length})
          </button>
        </div>
      </div>
      
      {/* Collaborators List */}
      <div className="space-y-3">
        {filteredCollaborators.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No {filterType === 'all' ? '' : filterType} collaborators at this strength level</p>
            <p className="text-sm mt-2">Try lowering the minimum strength filter</p>
          </div>
        ) : (
          filteredCollaborators.map((collaborator) => (
            <div
              key={collaborator.person_id}
              className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              {/* Connection Type Icon */}
              <div className="flex-shrink-0 w-10 h-10 bg-white rounded-full flex items-center justify-center text-2xl">
                {collaborator.connection_type === 'github' ? '💻' : '🏢'}
              </div>
              
              {/* Collaborator Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <Link
                    to={`/profile/${collaborator.person_id}`}
                    className="text-blue-600 hover:text-blue-800 font-medium truncate"
                  >
                    {collaborator.full_name}
                  </Link>
                  <span className="text-sm text-gray-500">
                    {renderStars(collaborator.strength)}
                  </span>
                </div>
                
                <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600">
                  {collaborator.connection_type === 'github' && collaborator.shared_repos && (
                    <span className="flex items-center gap-1">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.167 22 16.418 22 12c0-5.523-4.477-10-10-10z"/>
                      </svg>
                      {collaborator.shared_repos} shared repos
                    </span>
                  )}
                  
                  {collaborator.connection_type === 'employment' && collaborator.shared_companies && (
                    <span className="flex items-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                      {collaborator.shared_companies} shared companies
                    </span>
                  )}
                  
                  {collaborator.last_interaction && (
                    <span className="flex items-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Last: {formatDate(collaborator.last_interaction)}
                    </span>
                  )}
                </div>
                
                <div className="mt-2">
                  <span className={`inline-block px-2 py-1 text-xs rounded-full ${
                    collaborator.strength >= 0.7
                      ? 'bg-green-100 text-green-800'
                      : collaborator.strength >= 0.4
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {collaborator.strength >= 0.7
                      ? 'Very Strong'
                      : collaborator.strength >= 0.4
                      ? 'Strong'
                      : 'Moderate'} Connection
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
};

export default CollaboratorsSection;

