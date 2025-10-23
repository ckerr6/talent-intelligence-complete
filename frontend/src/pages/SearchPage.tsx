import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Search, MapPin, Briefcase, Mail, Github, X, Users } from 'lucide-react';
import api from '../services/api';
import type { Person, SearchFilters } from '../types';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import EmptyState from '../components/common/EmptyState';
import { SkeletonList } from '../components/common/Skeleton';

export default function SearchPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<SearchFilters>({
    company: '',
    location: '',
    headline: '',
    has_email: undefined,
    has_github: undefined,
  });
  const [page, setPage] = useState(0);
  const pageSize = 50;

  const { data, isLoading, error } = useQuery({
    queryKey: ['people', filters, page],
    queryFn: () => api.searchPeople(filters, page * pageSize, pageSize),
  });

  const handleSearch = () => {
    setPage(0);
  };

  const handleFilterChange = (key: keyof SearchFilters, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <Search className="w-8 h-8 mr-3 text-primary-600" />
            Search Candidates
          </h1>
          <p className="mt-2 text-gray-600">
            Discover talent across LinkedIn, GitHub, and our network
          </p>
        </div>
        {data && (
          <div className="text-right">
            <p className="text-3xl font-bold text-gray-900">{data.pagination.total.toLocaleString()}</p>
            <p className="text-sm text-gray-500">Total Candidates</p>
          </div>
        )}
      </div>

      {/* Filters */}
      <Card padding="lg">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Company
            </label>
            <input
              type="text"
              placeholder="e.g. Google, Coinbase"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              value={filters.company || ''}
              onChange={(e) => handleFilterChange('company', e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Location
            </label>
            <input
              type="text"
              placeholder="e.g. San Francisco, Remote"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              value={filters.location || ''}
              onChange={(e) => handleFilterChange('location', e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Title / Headline
            </label>
            <input
              type="text"
              placeholder="e.g. Senior Engineer"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              value={filters.headline || ''}
              onChange={(e) => handleFilterChange('headline', e.target.value)}
            />
          </div>
        </div>

        <div className="mt-4 flex items-center space-x-6">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              checked={filters.has_email === true}
              onChange={(e) =>
                handleFilterChange('has_email', e.target.checked ? true : undefined)
              }
            />
            <span className="text-sm text-gray-700">Has Email</span>
          </label>

          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              checked={filters.has_github === true}
              onChange={(e) =>
                handleFilterChange('has_github', e.target.checked ? true : undefined)
              }
            />
            <span className="text-sm text-gray-700">Has GitHub</span>
          </label>
        </div>

        <div className="mt-6 flex space-x-3">
          <Button 
            onClick={handleSearch}
            icon={<Search className="w-4 h-4" />}
            loading={isLoading}
          >
            Search
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              setFilters({
                company: '',
                location: '',
                headline: '',
                has_email: undefined,
                has_github: undefined,
              });
              setPage(0);
            }}
            icon={<X className="w-4 h-4" />}
          >
            Clear
          </Button>
        </div>
      </Card>

      {/* Results */}
      {isLoading && <SkeletonList count={5} />}

      {error && (
        <Card>
          <EmptyState
            icon={<X className="w-8 h-8" />}
            title="Error loading results"
            description="Something went wrong. Please try again."
            action={
              <Button onClick={() => window.location.reload()}>
                Reload Page
              </Button>
            }
          />
        </Card>
      )}

      {data && !isLoading && (
        <>
          {data.data.length === 0 ? (
            <Card>
              <EmptyState
                icon={<Users className="w-8 h-8" />}
                title="No candidates found"
                description="Try adjusting your filters to see more results."
                action={
                  <Button
                    variant="outline"
                    onClick={() => {
                      setFilters({
                        company: '',
                        location: '',
                        headline: '',
                        has_email: undefined,
                        has_github: undefined,
                      });
                      setPage(0);
                    }}
                  >
                    Clear Filters
                  </Button>
                }
              />
            </Card>
          ) : (
            <Card padding="none">
              <div className="p-6 border-b border-gray-200 bg-gray-50">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-600">
                    Showing <span className="font-semibold">{page * pageSize + 1}</span> - <span className="font-semibold">{Math.min((page + 1) * pageSize, data.pagination.total)}</span> of <span className="font-semibold">{data.pagination.total}</span> candidates
                  </p>
                  <Badge variant="info">
                    Page {page + 1} of {Math.ceil(data.pagination.total / pageSize)}
                  </Badge>
                </div>
              </div>

              <div className="divide-y divide-gray-200">
                {data.data.map((person: Person) => (
                  <div
                    key={person.person_id}
                    className="p-6 hover:bg-gray-50 cursor-pointer transition-all duration-200 hover:shadow-inner"
                    onClick={() => navigate(`/profile/${person.person_id}`)}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-start space-x-3">
                          <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                            {person.full_name.charAt(0)}
                          </div>
                          <div className="flex-1">
                            <h3 className="text-lg font-semibold text-gray-900 hover:text-primary-600 transition-colors">
                              {person.full_name}
                            </h3>
                            {person.headline && (
                              <p className="mt-1 text-sm text-gray-600 flex items-center">
                                <Briefcase className="w-4 h-4 mr-1 text-gray-400" />
                                {person.headline}
                              </p>
                            )}
                            {person.location && (
                              <p className="mt-1 text-sm text-gray-500 flex items-center">
                                <MapPin className="w-4 h-4 mr-1 text-gray-400" />
                                {person.location}
                              </p>
                            )}
                            {/* Quick Stats */}
                            <div className="mt-3 flex items-center space-x-2">
                              {person.has_email && (
                                <Badge variant="success" size="sm" rounded>
                                  <Mail className="w-3 h-3 mr-1 inline" />
                                  Email
                                </Badge>
                              )}
                              {person.has_github && (
                                <Badge variant="info" size="sm" rounded>
                                  <Github className="w-3 h-3 mr-1 inline" />
                                  GitHub
                                </Badge>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/profile/${person.person_id}`);
                        }}
                      >
                        View Profile →
                      </Button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {data.pagination.total > pageSize && (
                <div className="p-6 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
                  <Button
                    variant="outline"
                    onClick={() => setPage((p) => Math.max(0, p - 1))}
                    disabled={page === 0}
                  >
                    ← Previous
                  </Button>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600">
                      Page {page + 1} of {Math.ceil(data.pagination.total / pageSize)}
                    </span>
                  </div>
                  <Button
                    variant="outline"
                    onClick={() => setPage((p) => p + 1)}
                    disabled={(page + 1) * pageSize >= data.pagination.total}
                  >
                    Next →
                  </Button>
                </div>
              )}
            </Card>
          )}
        </>
      )}
    </div>
  );
}

