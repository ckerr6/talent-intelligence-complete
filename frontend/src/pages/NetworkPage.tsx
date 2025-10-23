import { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Users, Building2, Code2, Network, Search, X } from 'lucide-react';
import api from '../services/api';
import NetworkGraph from '../components/network/NetworkGraph';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import EmptyState from '../components/common/EmptyState';
import { Skeleton } from '../components/common/Skeleton';

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
  const [connectionTypes, setConnectionTypes] = useState<string[]>([
    'coworker',
    'github_collaborator',
  ]);
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
  }, [centerPersonId, maxDegree, companyFilter, repoFilter]); // Removed setSearchParams to prevent infinite loop

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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center">
              <Network className="w-8 h-8 mr-3 text-primary-600" />
              Network Graph
            </h1>
            <p className="mt-2 text-gray-600">
              Explore professional networks and discover connection paths
            </p>
          </div>
        </div>

        {/* Search for a person to start */}
        <Card>
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
            <Button
              onClick={handleSearch}
              disabled={searching}
              loading={searching}
              icon={<Search className="w-4 h-4" />}
            >
              Search
            </Button>
          </div>

          {searchResults.length > 0 && (
            <div className="mt-4 space-y-2">
              <h3 className="font-medium text-gray-900">Results:</h3>
              {searchResults.map((person) => (
                <Card
                  key={person.person_id}
                  hover
                  padding="md"
                  onClick={() => setCenterPersonId(person.person_id)}
                  className="cursor-pointer"
                >
                  <div className="font-medium text-gray-900">{person.full_name}</div>
                  {person.headline && (
                    <div className="text-sm text-gray-600 mt-1">{person.headline}</div>
                  )}
                  {person.location && (
                    <div className="text-xs text-gray-500 mt-1">{person.location}</div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </Card>

        {/* Example use cases */}
        <Card className="bg-gradient-to-br from-blue-50 to-purple-50 border-2 border-blue-200">
          <h3 className="text-lg font-semibold text-blue-900 mb-3 flex items-center">
            <Network className="w-5 h-5 mr-2" />
            What You Can Do:
          </h3>
          <ul className="space-y-2 text-blue-800">
            <li className="flex items-start">
              <span className="text-blue-600 mr-2">•</span>
              <span>Visualize professional networks up to 3 degrees of separation</span>
            </li>
            <li className="flex items-start">
              <span className="text-blue-600 mr-2">•</span>
              <span>Discover connection paths between people</span>
            </li>
            <li className="flex items-start">
              <span className="text-blue-600 mr-2">•</span>
              <span>Filter by company or GitHub repository</span>
            </li>
            <li className="flex items-start">
              <span className="text-blue-600 mr-2">•</span>
              <span>See both co-employment and GitHub collaboration connections</span>
            </li>
            <li className="flex items-start">
              <span className="text-blue-600 mr-2">•</span>
              <span>Click on any person to view their full profile</span>
            </li>
          </ul>
        </Card>
      </div>
    );
  }

  if (loadingPerson) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <Network className="w-8 h-8 mr-3 text-primary-600" />
            Network: {centerPerson?.full_name || 'Unknown'}
          </h1>
          <p className="mt-2 text-gray-600">
            {centerPerson?.headline || 'Professional network visualization'}
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => setCenterPersonId('')}
          icon={<Search className="w-4 h-4" />}
        >
          Change Person
        </Button>
      </div>

      {/* Network Statistics - Placeholder for now, would be real data from graph */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white" padding="md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm">Network Size</p>
              <p className="text-2xl font-bold mt-1">View Graph</p>
            </div>
            <Users className="w-8 h-8 text-blue-200" />
          </div>
        </Card>
        
        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white" padding="md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100 text-sm">Companies</p>
              <p className="text-2xl font-bold mt-1">Multiple</p>
            </div>
            <Building2 className="w-8 h-8 text-green-200" />
          </div>
        </Card>
        
        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white" padding="md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100 text-sm">Repositories</p>
              <p className="text-2xl font-bold mt-1">Shared</p>
            </div>
            <Code2 className="w-8 h-8 text-purple-200" />
          </div>
        </Card>
        
        <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white" padding="md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-orange-100 text-sm">Max Degree</p>
              <p className="text-2xl font-bold mt-1">{maxDegree}°</p>
            </div>
            <Network className="w-8 h-8 text-orange-200" />
          </div>
        </Card>
      </div>

      {/* Controls */}
      <Card className="space-y-6">
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

        {/* Connection Type Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Connection Types
          </label>
          <div className="flex gap-4">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={connectionTypes.includes('coworker')}
                onChange={(e) => {
                  if (e.target.checked) {
                    setConnectionTypes([...connectionTypes, 'coworker']);
                  } else {
                    setConnectionTypes(connectionTypes.filter((t) => t !== 'coworker'));
                  }
                }}
                className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700 font-medium">
                Co-workers
              </span>
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                <span className="w-2 h-2 mr-1 rounded-full bg-green-500"></span>
                Employment
              </span>
            </label>

            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={connectionTypes.includes('github_collaborator')}
                onChange={(e) => {
                  if (e.target.checked) {
                    setConnectionTypes([...connectionTypes, 'github_collaborator']);
                  } else {
                    setConnectionTypes(connectionTypes.filter((t) => t !== 'github_collaborator'));
                  }
                }}
                className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700 font-medium">
                GitHub Collaborators
              </span>
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                <span className="w-2 h-2 mr-1 rounded-full bg-purple-500"></span>
                Code
              </span>
            </label>
          </div>
        </div>

        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => {
              setCompanyFilter('');
              setRepoFilter('');
              setConnectionTypes(['coworker', 'github_collaborator']);
            }}
            icon={<X className="w-4 h-4" />}
          >
            Clear All Filters
          </Button>
        </div>
      </Card>

      {/* Legend Card */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 Graph Legend</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Node Types */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Node Colors (By Degree)</h4>
            <div className="space-y-2">
              <div className="flex items-center space-x-3">
                <div className="w-6 h-6 rounded-full bg-blue-500 border-2 border-blue-600"></div>
                <span className="text-sm text-gray-700">Center Person (You're viewing)</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-6 h-6 rounded-full bg-green-500 border-2 border-green-600"></div>
                <span className="text-sm text-gray-700">1st Degree (Direct connections)</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-6 h-6 rounded-full bg-yellow-500 border-2 border-yellow-600"></div>
                <span className="text-sm text-gray-700">2nd Degree (Friend of friend)</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-6 h-6 rounded-full bg-orange-500 border-2 border-orange-600"></div>
                <span className="text-sm text-gray-700">3rd Degree (Extended network)</span>
              </div>
            </div>
          </div>

          {/* Connection Types */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Connection Types</h4>
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-0.5 bg-green-500"></div>
                <Badge variant="success" size="sm">Co-workers</Badge>
                <span className="text-xs text-gray-600">Worked at same company</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-12 h-0.5 bg-purple-500"></div>
                <Badge variant="primary" size="sm">GitHub</Badge>
                <span className="text-xs text-gray-600">Contributed to same repository</span>
              </div>
            </div>
            
            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-xs text-gray-500">
                💡 <strong>Pro Tip:</strong> Click any node to view that person's profile. 
                Larger nodes indicate more connections in the network.
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* Network Graph */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          🕸️ Interactive Network Visualization
        </h3>
        <NetworkGraph
          centerPersonId={centerPersonId}
          centerPersonName={centerPerson?.full_name || 'Unknown'}
          maxDegree={maxDegree}
          companyFilter={companyFilter || undefined}
          repoFilter={repoFilter || undefined}
          connectionTypes={connectionTypes}
        />
      </Card>
    </div>
  );
}
