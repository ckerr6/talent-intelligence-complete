import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Search, Github, Filter, Star, TrendingUp, Mail } from 'lucide-react';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import { SkeletonList } from '../../components/common/Skeleton';

interface SearchFilters {
  seniority_levels: string[];
  languages: string[];
  domains: string[];
  min_influence: number | null;
  min_reachability: number | null;
  limit: number;
}

interface SearchResult {
  username: string;
  seniority: string;
  influence_score: number;
  reachability_score: number;
}

export default function GitHubSearch() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<SearchFilters>({
    seniority_levels: [],
    languages: [],
    domains: [],
    min_influence: null,
    min_reachability: null,
    limit: 50
  });
  
  const [showFilters, setShowFilters] = useState(true);

  const { data: results, isLoading } = useQuery({
    queryKey: ['github-search', filters],
    queryFn: async () => {
      const response = await fetch('/api/github-intelligence/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(filters)
      });
      if (!response.ok) throw new Error('Search failed');
      return response.json();
    }
  });

  const { data: stats } = useQuery({
    queryKey: ['github-stats'],
    queryFn: async () => {
      const response = await fetch('/api/github-intelligence/stats');
      if (!response.ok) throw new Error('Failed to fetch stats');
      return response.json();
    }
  });

  const toggleSeniority = (level: string) => {
    setFilters(prev => ({
      ...prev,
      seniority_levels: prev.seniority_levels.includes(level)
        ? prev.seniority_levels.filter(l => l !== level)
        : [...prev.seniority_levels, level]
    }));
  };

  const toggleLanguage = (lang: string) => {
    setFilters(prev => ({
      ...prev,
      languages: prev.languages.includes(lang)
        ? prev.languages.filter(l => l !== lang)
        : [...prev.languages, lang]
    }));
  };

  const commonLanguages = ['Solidity', 'TypeScript', 'JavaScript', 'Python', 'Rust', 'Go'];
  const seniorityLevels = ['Principal', 'Staff', 'Senior', 'Mid-Level', 'Junior'];

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">GitHub Developer Search</h1>
        <p className="text-gray-600">
          Search {stats?.total_enriched || 0} enriched developer profiles by skills, seniority, and reach ability
        </p>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-5 gap-4 mb-6">
          {Object.entries(stats.by_seniority).map(([level, count]: [string, any]) => (
            <Card key={level} className="p-4">
              <div className="text-sm text-gray-600 mb-1">{level}</div>
              <div className="text-2xl font-bold">{count}</div>
            </Card>
          ))}
        </div>
      )}

      <div className="grid grid-cols-4 gap-6">
        {/* Filters Sidebar */}
        <div className="col-span-1">
          <Card className="p-6 sticky top-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold">Filters</h2>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => setFilters({
                  seniority_levels: [],
                  languages: [],
                  domains: [],
                  min_influence: null,
                  min_reachability: null,
                  limit: 50
                })}
              >
                Clear
              </Button>
            </div>

            {/* Seniority Filter */}
            <div className="mb-6">
              <div className="text-sm font-medium text-gray-700 mb-2">Seniority Level</div>
              <div className="space-y-2">
                {seniorityLevels.map(level => (
                  <label key={level} className="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={filters.seniority_levels.includes(level)}
                      onChange={() => toggleSeniority(level)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm">{level}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Language Filter */}
            <div className="mb-6">
              <div className="text-sm font-medium text-gray-700 mb-2">Languages</div>
              <div className="space-y-2">
                {commonLanguages.map(lang => (
                  <label key={lang} className="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={filters.languages.includes(lang)}
                      onChange={() => toggleLanguage(lang)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm">{lang}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Influence Slider */}
            <div className="mb-6">
              <div className="text-sm font-medium text-gray-700 mb-2">
                Min Influence: {filters.min_influence || 0}
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={filters.min_influence || 0}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  min_influence: parseInt(e.target.value)
                }))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            {/* Reachability Slider */}
            <div>
              <div className="text-sm font-medium text-gray-700 mb-2">
                Min Reachability: {filters.min_reachability || 0}
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={filters.min_reachability || 0}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  min_reachability: parseInt(e.target.value)
                }))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>
          </Card>
        </div>

        {/* Results */}
        <div className="col-span-3">
          {isLoading ? (
            <SkeletonList count={5} />
          ) : (
            <>
              <div className="mb-4 flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  {results?.total || 0} developers found
                </div>
                <Button size="sm" variant="outline">
                  Export Results
                </Button>
              </div>

              <div className="space-y-4">
                {results?.profiles?.map((profile: SearchResult) => (
                  <Card 
                    key={profile.username}
                    className="p-6 hover:shadow-lg transition-shadow cursor-pointer"
                    onClick={() => navigate(`/github/${profile.username}`)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <Github className="w-5 h-5 text-gray-600" />
                          <h3 className="text-lg font-bold">@{profile.username}</h3>
                          <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                            {profile.seniority}
                          </span>
                        </div>
                        
                        <div className="flex items-center space-x-6 text-sm text-gray-600">
                          <span className="flex items-center">
                            <Star className="w-4 h-4 mr-1 text-yellow-500" />
                            {profile.influence_score} Influence
                          </span>
                          <span className="flex items-center">
                            <Mail className="w-4 h-4 mr-1 text-green-500" />
                            {profile.reachability_score} Reachability
                          </span>
                        </div>
                      </div>

                      <Button size="sm">
                        View Profile
                      </Button>
                    </div>
                  </Card>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

