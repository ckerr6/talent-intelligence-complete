import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import type { Person, SearchFilters } from '../types';

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
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Search Candidates</h1>
        <p className="mt-2 text-gray-600">
          Discover talent across LinkedIn, GitHub, and our network
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6">
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
          <button
            onClick={handleSearch}
            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
          >
            Search
          </button>
          <button
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
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="bg-white rounded-lg shadow">
        {isLoading && (
          <div className="p-12 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-300 border-t-primary-600"></div>
            <p className="mt-4 text-gray-600">Searching...</p>
          </div>
        )}

        {error && (
          <div className="p-12 text-center">
            <p className="text-red-600">Error loading results. Please try again.</p>
          </div>
        )}

        {data && !isLoading && (
          <>
            <div className="p-6 border-b border-gray-200">
              <p className="text-sm text-gray-600">
                Found <span className="font-semibold">{data.pagination.total}</span> candidates
              </p>
            </div>

            <div className="divide-y divide-gray-200">
              {data.data.map((person: Person) => (
                <div
                  key={person.person_id}
                  className="p-6 hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/profile/${person.person_id}`)}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {person.full_name}
                      </h3>
                      {person.headline && (
                        <p className="mt-1 text-sm text-gray-600">{person.headline}</p>
                      )}
                      {person.location && (
                        <p className="mt-1 text-sm text-gray-500">📍 {person.location}</p>
                      )}
                    </div>
                    <button className="ml-4 px-3 py-1 text-sm text-primary-600 hover:bg-primary-50 rounded transition-colors">
                      View Profile →
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {data.pagination.total > pageSize && (
              <div className="p-6 border-t border-gray-200 flex items-center justify-between">
                <button
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <span className="text-sm text-gray-600">
                  Page {page + 1} of {Math.ceil(data.pagination.total / pageSize)}
                </span>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={(page + 1) * pageSize >= data.pagination.total}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

