import { useState, useEffect } from 'react';
import { Search, TrendingUp, Users, Code2, Sparkles, BarChart3 } from 'lucide-react';
import api from '../services/api';
import HiringTrendsChart from '../components/market/HiringTrendsChart';
import TalentFlowChart from '../components/market/TalentFlowChart';
import TechnologyDistributionChart from '../components/market/TechnologyDistributionChart';
import AIChartBuilder from '../components/market/AIChartBuilder';

export default function MarketIntelligencePage() {
  const [selectedCompany, setSelectedCompany] = useState<string>('');
  const [selectedCompanyName, setSelectedCompanyName] = useState<string>('');
  const [companySearch, setCompanySearch] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'ai-builder'>('overview');
  
  // Data states
  const [hiringData, setHiringData] = useState<any>(null);
  const [talentFlowData, setTalentFlowData] = useState<any>(null);
  const [techData, setTechData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Search for companies
  const handleSearch = async (query: string) => {
    if (!query.trim() || query.length < 2) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    try {
      const response = await fetch(`/api/market/companies/search?query=${encodeURIComponent(query)}&limit=10`);
      const data = await response.json();
      setSearchResults(data.companies || []);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setSearching(false);
    }
  };

  // Select company and load data
  const handleSelectCompany = async (companyId: string, companyName: string) => {
    setSelectedCompany(companyId);
    setSelectedCompanyName(companyName);
    setCompanySearch(companyName);
    setSearchResults([]);
    
    // Load all market intelligence data
    await loadMarketData(companyId, companyName);
  };

  const loadMarketData = async (companyId: string, companyName: string) => {
    setLoading(true);
    
    try {
      // Load all data in parallel
      const [hiring, flow, tech] = await Promise.all([
        fetch(`/api/market/hiring-patterns?company_id=${companyId}&time_period_months=24`).then(r => r.json()),
        fetch(`/api/market/talent-flow?company_id=${companyId}&direction=both`).then(r => r.json()),
        fetch(`/api/market/technology-distribution?company_id=${companyId}&limit=15`).then(r => r.json())
      ]);

      setHiringData(hiring.data);
      setTalentFlowData(flow.data);
      setTechData(tech.data);
    } catch (error) {
      console.error('Error loading market data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (companySearch) {
        handleSearch(companySearch);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [companySearch]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Market Intelligence</h1>
        <p className="mt-2 text-gray-600">
          AI-powered insights about hiring patterns, talent flow, and technology trends
        </p>
      </div>

      {/* Company Search */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="relative">
          <div className="flex items-center space-x-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                value={companySearch}
                onChange={(e) => setCompanySearch(e.target.value)}
                placeholder="Search for a company to analyze..."
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
            {selectedCompany && (
              <button
                onClick={() => loadMarketData(selectedCompany, selectedCompanyName)}
                disabled={loading}
                className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors font-medium"
              >
                {loading ? 'Loading...' : 'Refresh Data'}
              </button>
            )}
          </div>

          {/* Search Results Dropdown */}
          {searchResults.length > 0 && (
            <div className="absolute z-10 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-y-auto">
              {searchResults.map((company) => (
                <button
                  key={company.company_id}
                  onClick={() => handleSelectCompany(company.company_id, company.company_name)}
                  className="w-full px-4 py-3 text-left hover:bg-purple-50 transition-colors border-b border-gray-100 last:border-b-0"
                >
                  <div className="font-medium text-gray-900">{company.company_name}</div>
                  <div className="text-sm text-gray-500">
                    {company.employee_count} employees in database
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {searching && (
          <div className="mt-2 text-sm text-gray-500">Searching...</div>
        )}
      </div>

      {/* No Company Selected State */}
      {!selectedCompany && (
        <div className="bg-gradient-to-br from-purple-50 to-blue-50 border-2 border-purple-200 rounded-lg p-12 text-center">
          <BarChart3 className="w-16 h-16 text-purple-400 mx-auto mb-4" />
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            Get Started
          </h2>
          <p className="text-gray-600 max-w-md mx-auto">
            Search for a company above to explore hiring patterns, talent flow, and technology trends
          </p>
          <div className="mt-6 flex items-center justify-center space-x-4 text-sm text-gray-500">
            <span className="flex items-center">
              <TrendingUp className="w-4 h-4 mr-1" />
              Hiring Trends
            </span>
            <span className="flex items-center">
              <Users className="w-4 h-4 mr-1" />
              Talent Flow
            </span>
            <span className="flex items-center">
              <Code2 className="w-4 h-4 mr-1" />
              Tech Stacks
            </span>
            <span className="flex items-center">
              <Sparkles className="w-4 h-4 mr-1" />
              AI Insights
            </span>
          </div>
        </div>
      )}

      {/* Dashboard Content */}
      {selectedCompany && (
        <>
          {/* Tabs */}
          <div className="bg-white rounded-lg shadow-md">
            <div className="border-b border-gray-200">
              <div className="flex space-x-8 px-6">
                <button
                  onClick={() => setActiveTab('overview')}
                  className={`py-4 px-1 border-b-2 font-medium transition-colors ${
                    activeTab === 'overview'
                      ? 'border-purple-600 text-purple-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <BarChart3 className="w-5 h-5" />
                    <span>Overview Dashboard</span>
                  </div>
                </button>
                <button
                  onClick={() => setActiveTab('ai-builder')}
                  className={`py-4 px-1 border-b-2 font-medium transition-colors ${
                    activeTab === 'ai-builder'
                      ? 'border-purple-600 text-purple-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <Sparkles className="w-5 h-5" />
                    <span>AI Chart Builder</span>
                  </div>
                </button>
              </div>
            </div>
          </div>

          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {loading ? (
                <div className="bg-white rounded-lg shadow-md p-12 text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">Loading market intelligence data...</p>
                </div>
              ) : (
                <>
                  {/* Hiring Trends */}
                  <HiringTrendsChart
                    data={hiringData}
                    companyName={selectedCompanyName}
                  />

                  {/* Two Column Layout */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Talent Flow */}
                    <TalentFlowChart
                      data={talentFlowData}
                      companyName={selectedCompanyName}
                    />

                    {/* Technology Distribution */}
                    <TechnologyDistributionChart
                      data={techData}
                      companyName={selectedCompanyName}
                    />
                  </div>
                </>
              )}
            </div>
          )}

          {/* AI Chart Builder Tab */}
          {activeTab === 'ai-builder' && (
            <AIChartBuilder
              companyId={selectedCompany}
              companyName={selectedCompanyName}
            />
          )}
        </>
      )}
    </div>
  );
}

