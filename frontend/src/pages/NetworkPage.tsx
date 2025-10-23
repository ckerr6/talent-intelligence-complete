import { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import NetworkGraph from '../components/network/NetworkGraph';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function NetworkPage() {
  const { personId } = useParams<{ personId?: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  
  // State for filters and controls
  const [centerPersonId, setCenterPersonId] = useState(
    personId || searchParams.get('center') || ''
  );
  const [searchQuery, setSearchQuery] = useState('');
  const [maxDegree, setMaxDegree] = useState(
    parseInt(searchParams.get('degree') || '2')
  );
  const [companyFilter, setCompanyFilter] = useState(
    searchParams.get('company') || ''
  );
  const [repoFilter, setRepoFilter] = useState(
    searchParams.get('repo') || ''
  );
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);

  // Fetch center person details
  const { data: centerPerson, isLoading: loadingPerson } = useQuery({
    queryKey: ['person', centerPersonId],
    queryFn: () => api.getPerson(centerPersonId),
    enabled: !!centerPersonId,
  });

  // Update URL when filters change
  useEffect(() => {
    if (centerPersonId) {
      const params = new URLSearchParams();
      params.set('center', centerPersonId);
      params.set('degree', maxDegree.toString());
      if (companyFilter) params.set('company', companyFilter);
      if (repoFilter) params.set('repo', repoFilter);
      setSearchParams(params);
    }
  }, [centerPersonId, maxDegree, companyFilter, repoFilter, setSearchParams]);

  // Search for people
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setSearching(true);
    try {
      const response = await api.searchPeople(
        { company: searchQuery },
        0,
        10
      );
      setSearchResults(response.data);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setSearching(false);
    }
  };

  if (!centerPersonId) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Network Graph</h1>
          <p className="mt-2 text-gray-600">
            Explore professional networks and discover connection paths
          </p>
        </div>

        {/* Search for a person to start */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Search for a person to explore their network
          </h2>
          
          <div className="flex gap-3">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search by name or company..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <button
              onClick={handleSearch}
              disabled={searching}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {searching ? 'Searching...' : 'Search'}
            </button>
          </div>

          {searchResults.length > 0 && (
            <div className="mt-4 space-y-2">
              <h3 className="font-medium text-gray-900">Results:</h3>
              {searchResults.map((person) => (
                <button
                  key={person.person_id}
                  onClick={() => setCenterPersonId(person.person_id)}
                  className="w-full text-left px-4 py-3 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors"
                >
                  <div className="font-medium text-gray-900">{person.full_name}</div>
                  {person.headline && (
                    <div className="text-sm text-gray-600">{person.headline}</div>
                  )}
                  {person.location && (
                    <div className="text-xs text-gray-500">{person.location}</div>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Example use cases */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">
            What You Can Do:
          </h3>
          <ul className="space-y-2 text-blue-800">
            <li>• Visualize professional networks up to 3 degrees of separation</li>
            <li>• Discover connection paths between people</li>
            <li>• Filter by company or GitHub repository</li>
            <li>• See both co-employment and GitHub collaboration connections</li>
            <li>• Click on any person to view their full profile</li>
          </ul>
        </div>
      </div>
    );
  }

  if (loadingPerson) {
    return <LoadingSpinner message="Loading network..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Network: {centerPerson?.full_name || 'Unknown'}
        </h1>
        <p className="mt-2 text-gray-600">
          {centerPerson?.headline || 'Professional network visualization'}
        </p>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Degrees of Separation */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Degrees of Separation
            </label>
            <select
              value={maxDegree}
              onChange={(e) => setMaxDegree(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            >
              <option value="1">1 degree (direct connections)</option>
              <option value="2">2 degrees</option>
              <option value="3">3 degrees</option>
            </select>
          </div>

          {/* Company Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Filter by Company
            </label>
            <input
              type="text"
              value={companyFilter}
              onChange={(e) => setCompanyFilter(e.target.value)}
              placeholder="e.g., Uniswap"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Repository Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Filter by Repository
            </label>
            <input
              type="text"
              value={repoFilter}
              onChange={(e) => setRepoFilter(e.target.value)}
              placeholder="e.g., interface"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>

        <div className="mt-4 flex gap-3">
          <button
            onClick={() => {
              setCompanyFilter('');
              setRepoFilter('');
            }}
            className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            Clear Filters
          </button>
          <button
            onClick={() => setCenterPersonId('')}
            className="px-4 py-2 text-sm text-primary-700 bg-primary-100 rounded-lg hover:bg-primary-200"
          >
            Change Center Person
          </button>
        </div>
      </div>

      {/* Network Graph */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <NetworkGraph
          centerPersonId={centerPersonId}
          centerPersonName={centerPerson?.full_name || 'Unknown'}
          maxDegree={maxDegree}
          companyFilter={companyFilter || undefined}
          repoFilter={repoFilter || undefined}
        />
      </div>
    </div>
  );
}
