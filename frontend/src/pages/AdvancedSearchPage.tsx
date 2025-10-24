import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Sparkles,
  MapPin,
  Briefcase,
  Mail,
  Github,
  Users,
  TrendingUp,
  X,
  Loader2,
} from 'lucide-react';
import api from '../services/api';
import type {
  AdvancedSearchFilters,
  SearchResultWithMatch,
  Technology,
  CompanyOption,
} from '../types/search';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import EmptyState from '../components/common/EmptyState';
import MultiSelect, { MultiSelectOption } from '../components/common/MultiSelect';

export default function AdvancedSearchPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'filters' | 'jd'>('filters');

  // Filter search state
  const [filters, setFilters] = useState<AdvancedSearchFilters>({});
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<SearchResultWithMatch[]>([]);
  const [totalResults, setTotalResults] = useState(0);
  const [searchTime, setSearchTime] = useState(0);
  const [page, setPage] = useState(0);
  const pageSize = 50;

  // JD parser state
  const [jdText, setJdText] = useState('');
  const [parsing, setParsing] = useState(false);
  const [parsedCriteria, setParsedCriteria] = useState<any>(null);

  // Available options
  const [technologies, setTechnologies] = useState<Technology[]>([]);
  const [companies, setCompanies] = useState<CompanyOption[]>([]);
  const [loadingOptions, setLoadingOptions] = useState(true);

  // Load technologies on mount
  useEffect(() => {
    loadTechnologies();
  }, []);

  const loadTechnologies = async () => {
    try {
      setLoadingOptions(true);
      const techs = await api.getAvailableTechnologies(100);
      setTechnologies(techs);
    } catch (error) {
      console.error('Failed to load technologies:', error);
    } finally {
      setLoadingOptions(false);
    }
  };

  // Debounced company search
  const [companySearchQuery, setCompanySearchQuery] = useState('');
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (companySearchQuery.length >= 2) {
        try {
          const results = await api.autocompleteCompanies(companySearchQuery, 20);
          setCompanies(results);
        } catch (error) {
          console.error('Failed to search companies:', error);
        }
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [companySearchQuery]);

  const handleFilterSearch = async () => {
    setSearching(true);
    setPage(0);
    console.log('[Advanced Search] Executing search with filters:', filters);
    
    try {
      const response = await api.advancedSearch(filters, 0, pageSize);
      setResults(response.results);
      setTotalResults(response.total_results);
      setSearchTime(response.search_time_ms);
      console.log(`[Advanced Search] Found ${response.total_results} results in ${response.search_time_ms}ms`);
    } catch (error) {
      console.error('[Advanced Search] Search failed:', error);
    } finally {
      setSearching(false);
    }
  };

  const handleJDParse = async () => {
    setParsing(true);
    console.log('[JD Parser] Parsing job description, length:', jdText.length);
    
    try {
      const response = await api.parseJobDescription(jdText, true, 0, pageSize);
      setParsedCriteria(response.parsed_jd);
      
      if (response.search_results) {
        setResults(response.search_results.results);
        setTotalResults(response.search_results.total_results);
        setSearchTime(response.search_results.search_time_ms);
        console.log(`[JD Parser] Auto-search found ${response.search_results.total_results} results`);
      }
    } catch (error) {
      console.error('[JD Parser] Parsing failed:', error);
    } finally {
      setParsing(false);
    }
  };

  const handleClearFilters = () => {
    setFilters({});
    setResults([]);
    setTotalResults(0);
  };

  const handlePageChange = async (newPage: number) => {
    setSearching(true);
    setPage(newPage);
    
    try {
      const response = await api.advancedSearch(filters, newPage * pageSize, pageSize);
      setResults(response.results);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (error) {
      console.error('Page change failed:', error);
    } finally {
      setSearching(false);
    }
  };

  // Convert technologies to MultiSelect options
  const technologyOptions: MultiSelectOption[] = technologies.map((tech) => ({
    value: tech.name,
    label: tech.name,
    meta: `${tech.developer_count} devs`,
  }));

  // Convert companies to MultiSelect options
  const companyOptions: MultiSelectOption[] = companies.map((company) => ({
    value: company.company_name,
    label: company.company_name,
    meta: `${company.employee_count} employees`,
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <Sparkles className="w-8 h-8 mr-3 text-primary-600" />
            Advanced Search
          </h1>
          <p className="mt-2 text-gray-600">
            Discover talent using AI-powered multi-criteria search
          </p>
        </div>
        {totalResults > 0 && (
          <div className="text-right">
            <p className="text-3xl font-bold text-gray-900">{totalResults.toLocaleString()}</p>
            <p className="text-sm text-gray-500">Matching Candidates</p>
            <p className="text-xs text-gray-400 mt-1">{searchTime.toFixed(0)}ms search time</p>
          </div>
        )}
      </div>

      {/* Tab Selector */}
      <Card>
        <div className="flex gap-2">
          <Button
            variant={activeTab === 'filters' ? 'primary' : 'outline'}
            onClick={() => setActiveTab('filters')}
            icon={<Search className="w-4 h-4" />}
          >
            Filter Search
          </Button>
          <Button
            variant={activeTab === 'jd' ? 'primary' : 'outline'}
            onClick={() => setActiveTab('jd')}
            icon={<Sparkles className="w-4 h-4" />}
          >
            Job Description Match
          </Button>
        </div>
      </Card>

      {/* Filter Search Tab */}
      {activeTab === 'filters' && (
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Search Filters</h2>
          
          <div className="space-y-4">
            {/* Technologies */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Technologies / Languages
              </label>
              {loadingOptions ? (
                <div className="flex items-center gap-2 text-gray-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Loading technologies...</span>
                </div>
              ) : (
                <MultiSelect
                  options={technologyOptions}
                  value={filters.technologies || []}
                  onChange={(selected) => setFilters({ ...filters, technologies: selected })}
                  placeholder="Select technologies (e.g., Rust, Solidity, TypeScript)"
                  searchable
                />
              )}
            </div>

            {/* Companies */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Companies (Current or Past)
              </label>
              <MultiSelect
                options={companyOptions}
                value={filters.companies || []}
                onChange={(selected) => setFilters({ ...filters, companies: selected })}
                placeholder="Start typing to search companies..."
                searchable
                onSearchChange={setCompanySearchQuery}
              />
              {companies.length === 0 && (
                <p className="text-xs text-gray-500 mt-1">
                  Start typing to search companies (e.g., "Uniswap", "Paradigm")
                </p>
              )}
            </div>

            {/* Keywords */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Job Titles
                </label>
                <input
                  type="text"
                  placeholder="e.g., Senior Engineer, Protocol Developer"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  value={filters.titles?.join(', ') || ''}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      titles: e.target.value
                        .split(',')
                        .map((t) => t.trim())
                        .filter((t) => t),
                    })
                  }
                />
                <p className="text-xs text-gray-500 mt-1">Separate multiple titles with commas</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Keywords & Skills
                </label>
                <input
                  type="text"
                  placeholder="e.g., DeFi, smart contracts, trading systems"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  value={filters.keywords?.join(', ') || ''}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      keywords: e.target.value
                        .split(',')
                        .map((k) => k.trim())
                        .filter((k) => k),
                    })
                  }
                />
                <p className="text-xs text-gray-500 mt-1">Separate multiple keywords with commas</p>
              </div>
            </div>

            {/* Location and Experience */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Location
                </label>
                <input
                  type="text"
                  placeholder="e.g., San Francisco, Remote"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  value={filters.location || ''}
                  onChange={(e) => setFilters({ ...filters, location: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Minimum Years Experience
                </label>
                <input
                  type="number"
                  min="0"
                  max="50"
                  placeholder="e.g., 5"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  value={filters.min_experience_years || ''}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      min_experience_years: e.target.value ? parseInt(e.target.value) : undefined,
                    })
                  }
                />
              </div>
            </div>

            {/* Filters */}
            <div className="flex items-center space-x-6">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  checked={filters.has_email === true}
                  onChange={(e) =>
                    setFilters({ ...filters, has_email: e.target.checked ? true : undefined })
                  }
                />
                <span className="text-sm text-gray-700 font-medium">Has Email</span>
              </label>

              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  checked={filters.has_github === true}
                  onChange={(e) =>
                    setFilters({ ...filters, has_github: e.target.checked ? true : undefined })
                  }
                />
                <span className="text-sm text-gray-700 font-medium">Has GitHub</span>
              </label>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4 border-t border-gray-200">
              <Button
                onClick={handleFilterSearch}
                icon={<Search className="w-4 h-4" />}
                loading={searching}
                disabled={
                  !filters.technologies?.length &&
                  !filters.companies?.length &&
                  !filters.titles?.length &&
                  !filters.keywords?.length &&
                  !filters.location
                }
              >
                Search Candidates
              </Button>
              <Button variant="outline" onClick={handleClearFilters} icon={<X className="w-4 h-4" />}>
                Clear Filters
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Job Description Tab */}
      {activeTab === 'jd' && (
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            AI-Powered Job Description Parsing
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Paste Job Description
              </label>
              <textarea
                rows={15}
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                placeholder="Paste the full job description here...&#10;&#10;The AI will extract:&#10;• Required technologies & programming languages&#10;• Preferred company backgrounds&#10;• Job level & seniority&#10;• Domain expertise keywords&#10;• Experience requirements"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent font-mono text-sm"
              />
              <p className="text-xs text-gray-500 mt-1">
                {jdText.length} characters • AI will extract structured requirements
              </p>
            </div>

            <Button
              onClick={handleJDParse}
              icon={<Sparkles className="w-4 h-4" />}
              loading={parsing}
              disabled={jdText.length < 50}
            >
              Parse & Search
            </Button>

            {/* Parsed Criteria Display */}
            {parsedCriteria && (
              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h3 className="font-semibold text-blue-900 mb-3">Extracted Criteria:</h3>
                <div className="space-y-2">
                  {parsedCriteria.technologies.length > 0 && (
                    <div>
                      <span className="text-sm font-medium text-blue-700">Technologies:</span>
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {parsedCriteria.technologies.map((tech: string) => (
                          <Badge key={tech} variant="info" size="sm">
                            {tech}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {parsedCriteria.companies.length > 0 && (
                    <div>
                      <span className="text-sm font-medium text-blue-700">Companies:</span>
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {parsedCriteria.companies.map((company: string) => (
                          <Badge key={company} variant="success" size="sm">
                            {company}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {parsedCriteria.job_level && (
                    <div>
                      <span className="text-sm font-medium text-blue-700">Level:</span>
                      <Badge variant="warning" size="sm" className="ml-2">
                        {parsedCriteria.job_level}
                      </Badge>
                    </div>
                  )}
                  {parsedCriteria.domain_expertise.length > 0 && (
                    <div>
                      <span className="text-sm font-medium text-blue-700">Domain:</span>
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {parsedCriteria.domain_expertise.map((domain: string) => (
                          <Badge key={domain} variant="primary" size="sm">
                            {domain}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  <div className="text-xs text-blue-600 mt-2">
                    Confidence: {(parsedCriteria.extraction_confidence * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Search Results */}
      {results.length > 0 && (
        <Card padding="none">
          <div className="p-6 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600">
                Showing <span className="font-semibold">{page * pageSize + 1}</span> -{' '}
                <span className="font-semibold">{Math.min((page + 1) * pageSize, totalResults)}</span> of{' '}
                <span className="font-semibold">{totalResults.toLocaleString()}</span> candidates
              </p>
              <Badge variant="info">Page {page + 1}</Badge>
            </div>
          </div>

          <div className="divide-y divide-gray-200">
            {results.map((result) => (
              <div
                key={result.person.person_id}
                className="p-6 hover:bg-gray-50 cursor-pointer transition-all duration-200"
                onClick={() => navigate(`/profile/${result.person.person_id}`)}
              >
                {/* Person Info */}
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                        {result.person.full_name.charAt(0)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="text-lg font-semibold text-gray-900 hover:text-primary-600 transition-colors">
                            {result.person.full_name}
                          </h3>
                          <Badge variant="success" size="sm">
                            {result.match_explanation.relevance_score.toFixed(0)}% match
                          </Badge>
                        </div>
                        {result.person.headline && (
                          <p className="mt-1 text-sm text-gray-600 flex items-center">
                            <Briefcase className="w-4 h-4 mr-1 text-gray-400" />
                            {result.person.headline}
                          </p>
                        )}
                        {result.person.location && (
                          <p className="mt-1 text-sm text-gray-500 flex items-center">
                            <MapPin className="w-4 h-4 mr-1 text-gray-400" />
                            {result.person.location}
                          </p>
                        )}

                        {/* Match Explanation */}
                        <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                          <p className="text-xs font-medium text-blue-700 mb-1">Match Reasons:</p>
                          <p className="text-sm text-blue-900">{result.match_explanation.match_summary}</p>
                        </div>

                        {/* Quick Stats */}
                        <div className="mt-3 flex items-center flex-wrap gap-2">
                          {result.person.has_email && (
                            <Badge variant="success" size="sm" rounded>
                              <Mail className="w-3 h-3 mr-1 inline" />
                              Email
                            </Badge>
                          )}
                          {result.person.has_github && (
                            <Badge variant="info" size="sm" rounded>
                              <Github className="w-3 h-3 mr-1 inline" />
                              GitHub
                            </Badge>
                          )}
                          {result.person.years_experience && (
                            <Badge variant="warning" size="sm" rounded>
                              <TrendingUp className="w-3 h-3 mr-1 inline" />
                              {result.person.years_experience} years
                            </Badge>
                          )}
                          {result.person.total_github_stars && result.person.total_github_stars > 0 && (
                            <Badge variant="primary" size="sm" rounded>
                              ⭐ {result.person.total_github_stars} stars
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
                      navigate(`/profile/${result.person.person_id}`);
                    }}
                  >
                    View Profile →
                  </Button>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalResults > pageSize && (
            <div className="p-6 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
              <Button
                variant="outline"
                onClick={() => handlePageChange(page - 1)}
                disabled={page === 0 || searching}
              >
                ← Previous
              </Button>
              <span className="text-sm text-gray-600">
                Page {page + 1} of {Math.ceil(totalResults / pageSize)}
              </span>
              <Button
                variant="outline"
                onClick={() => handlePageChange(page + 1)}
                disabled={(page + 1) * pageSize >= totalResults || searching}
              >
                Next →
              </Button>
            </div>
          )}
        </Card>
      )}

      {/* Empty State */}
      {!searching && results.length === 0 && totalResults === 0 && (
        <Card>
          <EmptyState
            icon={<Users className="w-8 h-8" />}
            title="No search executed yet"
            description="Use the filters above or paste a job description to find matching candidates"
          />
        </Card>
      )}
    </div>
  );
}

