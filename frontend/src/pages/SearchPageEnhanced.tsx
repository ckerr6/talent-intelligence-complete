import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Search, Users, Github, Sparkles, CheckSquare } from 'lucide-react';
import api from '../services/api';
import type { Person, SearchFilters } from '../types';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import EmptyState from '../components/common/EmptyState';
import { SkeletonList } from '../components/common/Skeleton';
import SmartFilters, { SmartFilterValues } from '../components/search/SmartFilters';
import SearchResultCard from '../components/search/SearchResultCard';
import QuickPreviewModal from '../components/search/QuickPreviewModal';
import GitHubIngestionModal from '../components/github/GitHubIngestionModal';

export default function SearchPageEnhanced() {
  const navigate = useNavigate();
  const [smartFilters, setSmartFilters] = useState<SmartFilterValues>({
    companies: [],
    locations: [],
    titles: [],
    skills: []
  });
  const [page, setPage] = useState(0);
  const pageSize = 50;
  const [showGitHubModal, setShowGitHubModal] = useState(false);
  const [previewPerson, setPreviewPerson] = useState<Person | null>(null);
  const [selectedPeople, setSelectedPeople] = useState<Set<string>>(new Set());
  const [showBulkActions, setShowBulkActions] = useState(false);

  // Convert SmartFilterValues to SearchFilters for API
  const apiFilters: SearchFilters = {
    company: smartFilters.companies?.[0] || '', // TODO: Support multiple companies
    location: smartFilters.locations?.[0] || '', // TODO: Support multiple locations
    headline: smartFilters.titles?.[0] || '', // TODO: Support multiple titles
    has_email: smartFilters.has_email,
    has_github: smartFilters.has_github,
  };

  const { data, isLoading, error } = useQuery({
    queryKey: ['people', apiFilters, page],
    queryFn: () => api.searchPeople(apiFilters, page * pageSize, pageSize),
  });

  const handleSearch = () => {
    setPage(0);
  };

  const handleSelectPerson = (personId: string, selected: boolean) => {
    setSelectedPeople(prev => {
      const newSet = new Set(prev);
      if (selected) {
        newSet.add(personId);
      } else {
        newSet.delete(personId);
      }
      setShowBulkActions(newSet.size > 0);
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (data?.data) {
      const allIds = new Set(data.data.map((p: Person) => p.person_id));
      setSelectedPeople(allIds);
      setShowBulkActions(true);
    }
  };

  const handleClearSelection = () => {
    setSelectedPeople(new Set());
    setShowBulkActions(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <Search className="w-8 h-8 mr-3 text-indigo-600" />
            Search Candidates
          </h1>
          <p className="mt-2 text-gray-600">
            AI-powered search with smart filters and match scoring
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Button
            variant="secondary"
            onClick={() => setShowGitHubModal(true)}
            icon={<Github className="w-4 h-4" />}
          >
            Add GitHub Data
          </Button>
          <Button
            variant="secondary"
            onClick={() => navigate('/network/enhanced')}
            icon={<Users className="w-4 h-4" />}
          >
            Network Explorer
          </Button>
          <Button
            variant="primary"
            onClick={() => navigate('/search/advanced')}
            icon={<Sparkles className="w-4 h-4" />}
          >
            Advanced Search
          </Button>
        </div>
      </div>

      {/* GitHub Ingestion Modal */}
      <GitHubIngestionModal
        isOpen={showGitHubModal}
        onClose={() => setShowGitHubModal(false)}
        onSuccess={(result) => {
          console.log('Ingestion completed:', result);
          setShowGitHubModal(false);
        }}
      />

      {/* Smart Filters */}
      <SmartFilters
        initialFilters={smartFilters}
        onFiltersChange={setSmartFilters}
        onSearch={handleSearch}
        resultCount={data?.pagination.total}
        isLoading={isLoading}
      />

      {/* Bulk Actions Bar */}
      {showBulkActions && selectedPeople.size > 0 && (
        <Card className="bg-indigo-50 border-2 border-indigo-500">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <CheckSquare className="w-5 h-5 text-indigo-600" />
              <span className="font-semibold text-gray-900">
                {selectedPeople.size} candidate{selectedPeople.size !== 1 ? 's' : ''} selected
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="ghost"
                icon={<Sparkles className="w-4 h-4" />}
                onClick={() => {
                  // TODO: Bulk AI summary generation
                }}
              >
                Generate AI Summaries
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  // TODO: Add to list
                }}
              >
                Add to List
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  // TODO: Export
                }}
              >
                Export
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={handleClearSelection}
              >
                Clear Selection
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Results */}
      {isLoading && <SkeletonList count={5} />}

      {error && (
        <Card>
          <EmptyState
            icon={<Search className="w-8 h-8" />}
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
                description="Try adjusting your filters or use AI filter suggestions to find more results."
                action={
                  <Button
                    variant="outline"
                    onClick={() => {
                      setSmartFilters({
                        companies: [],
                        locations: [],
                        titles: [],
                        skills: []
                      });
                      setPage(0);
                    }}
                  >
                    Clear All Filters
                  </Button>
                }
              />
            </Card>
          ) : (
            <>
              {/* Results Header */}
              <Card>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-900 font-semibold">
                      {data.pagination.total.toLocaleString()} candidates found
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      Showing {page * pageSize + 1} - {Math.min((page + 1) * pageSize, data.pagination.total)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={handleSelectAll}
                    >
                      Select All
                    </Button>
                    {selectedPeople.size > 0 && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={handleClearSelection}
                      >
                        Deselect All
                      </Button>
                    )}
                  </div>
                </div>
              </Card>

              {/* Search Results Grid */}
              <div className="space-y-4">
                {data.data.map((person: Person) => (
                  <SearchResultCard
                    key={person.person_id}
                    person={person as any} // TODO: Fix type
                    onQuickPreview={(p) => setPreviewPerson(p)}
                    isSelected={selectedPeople.has(person.person_id)}
                    onSelect={handleSelectPerson}
                    showCheckbox={showBulkActions || selectedPeople.size > 0}
                  />
                ))}
              </div>

              {/* Pagination */}
              {data.pagination.total > pageSize && (
                <Card>
                  <div className="flex items-center justify-between">
                    <Button
                      variant="outline"
                      onClick={() => setPage((p) => Math.max(0, p - 1))}
                      disabled={page === 0}
                    >
                      ← Previous
                    </Button>
                    <div className="flex items-center gap-2">
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
                </Card>
              )}
            </>
          )}
        </>
      )}

      {/* Quick Preview Modal */}
      {previewPerson && (
        <QuickPreviewModal
          person={previewPerson}
          onClose={() => setPreviewPerson(null)}
          onViewFull={(id) => {
            setPreviewPerson(null);
            navigate(`/profile/${id}`);
          }}
        />
      )}
    </div>
  );
}

