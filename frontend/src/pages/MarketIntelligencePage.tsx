import { useState, useEffect } from 'react';
import { Search, TrendingUp, Users, MapPin, Building2, Github, Mail } from 'lucide-react';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import { Skeleton } from '../components/common/Skeleton';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend, LineChart, Line } from 'recharts';
import HiringTrendsChart from '../components/market/HiringTrendsChart';
import TalentFlowChart from '../components/market/TalentFlowChart';
import TechnologyDistributionChart from '../components/market/TechnologyDistributionChart';
import TechnologistsModal from '../components/market/TechnologistsModal';
import DeepAnalyticsPanel from '../components/market/DeepAnalyticsPanel';

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#A28DFF', '#FF6F61'];

export default function MarketIntelligencePage() {
  // Overall statistics state
  const [overallStats, setOverallStats] = useState<any>(null);
  const [hiringTrends, setHiringTrends] = useState<any>(null);
  const [techDistribution, setTechDistribution] = useState<any>(null);
  const [topCompanies, setTopCompanies] = useState<any>(null);
  const [locations, setLocations] = useState<any>(null);
  
  // Company filter state
  const [showCompanyFilter, setShowCompanyFilter] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState<string>('');
  const [selectedCompanyName, setSelectedCompanyName] = useState<string>('');
  const [companySearch, setCompanySearch] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  
  // Company-specific data
  const [companyHiring, setCompanyHiring] = useState<any>(null);
  const [companyTalentFlow, setCompanyTalentFlow] = useState<any>(null);
  const [companyTech, setCompanyTech] = useState<any>(null);
  
  // Interactive features
  const [showTechnologistsModal, setShowTechnologistsModal] = useState(false);
  const [selectedTechnology, setSelectedTechnology] = useState<string>('');
  
  // View state
  const [viewMode, setViewMode] = useState<'standard' | 'deep'>('standard');
  
  const [loading, setLoading] = useState(true);

  // Load overall dataset statistics on mount
  useEffect(() => {
    loadOverallData();
  }, []);

  const loadOverallData = async () => {
    setLoading(true);
    try {
      const [stats, trends, tech, companies, locs] = await Promise.all([
        fetch('/api/market/overall/statistics').then(r => r.json()),
        fetch('/api/market/overall/hiring-trends?months=24').then(r => r.json()),
        fetch('/api/market/overall/technology-distribution?limit=15').then(r => r.json()),
        fetch('/api/market/overall/top-companies?limit=15').then(r => r.json()),
        fetch('/api/market/overall/location-distribution?limit=10').then(r => r.json())
      ]);

      setOverallStats(stats.data);
      setHiringTrends(trends.data);
      setTechDistribution(tech.data);
      setTopCompanies(companies.data);
      setLocations(locs.data);
    } catch (error) {
      console.error('Error loading overall data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Company search
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

  const handleSelectCompany = async (companyId: string, companyName: string) => {
    setSelectedCompany(companyId);
    setSelectedCompanyName(companyName);
    setCompanySearch(companyName);
    setSearchResults([]);
    setShowCompanyFilter(false);

    // Load company-specific data
    try {
      const [hiring, flow, tech] = await Promise.all([
        fetch(`/api/market/hiring-patterns?company_id=${companyId}&time_period_months=24`).then(r => r.json()),
        fetch(`/api/market/talent-flow?company_id=${companyId}&direction=both`).then(r => r.json()),
        fetch(`/api/market/technology-distribution?company_id=${companyId}&limit=15`).then(r => r.json())
      ]);

      setCompanyHiring(hiring.data);
      setCompanyTalentFlow(flow.data);
      setCompanyTech(tech.data);
    } catch (error) {
      console.error('Error loading company data:', error);
    }
  };

  const handleTechnologyClick = (technology: string) => {
    setSelectedTechnology(technology);
    setShowTechnologistsModal(true);
  };

  const clearCompanyFilter = () => {
    setSelectedCompany('');
    setSelectedCompanyName('');
    setCompanySearch('');
    setCompanyHiring(null);
    setCompanyTalentFlow(null);
    setCompanyTech(null);
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

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
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
            <TrendingUp className="w-8 h-8 mr-3 text-primary-600" />
            Market Intelligence
          </h1>
          <p className="mt-2 text-gray-600">
            Comprehensive insights across {overallStats?.total_people?.toLocaleString()} professionals
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* View Toggle */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('standard')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'standard'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Standard View
            </button>
            <button
              onClick={() => setViewMode('deep')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'deep'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              🔬 Deep Analytics
            </button>
          </div>
          <Button
            variant={selectedCompany ? 'primary' : 'outline'}
            onClick={() => setShowCompanyFilter(!showCompanyFilter)}
            icon={<Search className="w-4 h-4" />}
          >
            {selectedCompany ? `Viewing: ${selectedCompanyName}` : 'Filter by Company'}
          </Button>
        </div>
      </div>

      {/* Company Filter Dropdown */}
      {showCompanyFilter && (
        <Card>
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="Search companies..."
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  value={companySearch}
                  onChange={(e) => setCompanySearch(e.target.value)}
                />
              </div>
              {selectedCompany && (
                <Button variant="outline" onClick={clearCompanyFilter}>
                  Show All
                </Button>
              )}
            </div>
            
            {searching && <p className="text-sm text-gray-500">Searching...</p>}
            
            {searchResults.length > 0 && (
              <div className="max-h-64 overflow-y-auto space-y-2">
                {searchResults.map((company) => (
                  <button
                    key={company.company_id}
                    onClick={() => handleSelectCompany(company.company_id, company.company_name)}
                    className="w-full text-left px-4 py-2 hover:bg-gray-50 rounded-lg transition-colors flex items-center justify-between"
                  >
                    <span className="font-medium">{company.company_name}</span>
                    <Badge size="sm">{company.employee_count} people</Badge>
                  </button>
                ))}
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Deep Analytics View */}
      {viewMode === 'deep' && (
        <DeepAnalyticsPanel companyId={selectedCompany || undefined} />
      )}

      {/* Standard View */}
      {viewMode === 'standard' && (
        <>
          {/* Overall Statistics Cards */}
          {!selectedCompany && overallStats && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-100 text-sm font-medium">Total Professionals</p>
                  <p className="text-3xl font-bold mt-2">{overallStats.total_people.toLocaleString()}</p>
                </div>
                <Users className="w-12 h-12 text-blue-200" />
              </div>
            </Card>

            <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-sm font-medium">GitHub Profiles</p>
                  <p className="text-3xl font-bold mt-2">{overallStats.people_with_github.toLocaleString()}</p>
                  <p className="text-purple-200 text-xs mt-1">{overallStats.github_percentage}% coverage</p>
                </div>
                <Github className="w-12 h-12 text-purple-200" />
              </div>
            </Card>

            <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-green-100 text-sm font-medium">Email Contacts</p>
                  <p className="text-3xl font-bold mt-2">{overallStats.people_with_email.toLocaleString()}</p>
                  <p className="text-green-200 text-xs mt-1">{overallStats.email_percentage}% coverage</p>
                </div>
                <Mail className="w-12 h-12 text-green-200" />
              </div>
            </Card>

            <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-orange-100 text-sm font-medium">Companies Tracked</p>
                  <p className="text-3xl font-bold mt-2">{overallStats.total_companies.toLocaleString()}</p>
                  <p className="text-orange-200 text-xs mt-1">{overallStats.total_repositories.toLocaleString()} repositories</p>
                </div>
                <Building2 className="w-12 h-12 text-orange-200" />
              </div>
            </Card>
          </div>

          {/* Hiring Trends Chart */}
          {hiringTrends && hiringTrends.monthly_hires && (
            <Card>
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Market Hiring Trends (24 Months)</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-blue-600 font-medium">Total Hires</p>
                  <p className="text-2xl font-bold text-blue-900">{hiringTrends.total_hires.toLocaleString()}</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <p className="text-sm text-green-600 font-medium">Avg/Month</p>
                  <p className="text-2xl font-bold text-green-900">{hiringTrends.average_per_month.toLocaleString()}</p>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <p className="text-sm text-purple-600 font-medium">Time Period</p>
                  <p className="text-2xl font-bold text-purple-900">{hiringTrends.time_period_months} months</p>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={350}>
                <LineChart data={hiringTrends.monthly_hires.map((m: any) => ({
                  month: new Date(m.month).toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
                  hires: m.hires,
                  companies: m.companies_hiring
                }))}>
                  <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.3} />
                  <XAxis dataKey="month" tick={{ fill: '#6B7280', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#6B7280', fontSize: 12 }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '0.5rem' }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="hires" stroke="#8884d8" strokeWidth={2} name="New Hires" />
                  <Line type="monotone" dataKey="companies" stroke="#82ca9d" strokeWidth={2} name="Companies Hiring" />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          )}

          {/* Technology Distribution */}
          {techDistribution && techDistribution.languages && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-semibold text-gray-900">Top Technologies</h2>
                  <Badge variant="info" size="sm">Click bars to view developers</Badge>
                </div>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart 
                    data={techDistribution.languages.slice(0, 10)} 
                    layout="vertical"
                    onClick={(data) => {
                      if (data && data.activeLabel) {
                        handleTechnologyClick(data.activeLabel);
                      }
                    }}
                    style={{ cursor: 'pointer' }}
                  >
                    <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.3} />
                    <XAxis type="number" tick={{ fill: '#6B7280', fontSize: 12 }} />
                    <YAxis dataKey="language" type="category" width={100} tick={{ fill: '#6B7280', fontSize: 12 }} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '0.5rem' }}
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          return (
                            <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
                              <p className="font-semibold text-gray-900">{payload[0].payload.language}</p>
                              <p className="text-sm text-gray-600">{payload[0].value} developers</p>
                              <p className="text-xs text-primary-600 mt-1">Click to view profiles →</p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Bar dataKey="developer_count" name="Developers">
                      {techDistribution.languages.slice(0, 10).map((_entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Card>

              <Card>
                <h2 className="text-2xl font-semibold text-gray-900 mb-6">Technology Distribution</h2>
                <ResponsiveContainer width="100%" height={400}>
                  <PieChart>
                    <Pie
                      data={techDistribution.languages.slice(0, 8)}
                      dataKey="developer_count"
                      nameKey="language"
                      cx="50%"
                      cy="50%"
                      outerRadius={120}
                      label
                    >
                      {techDistribution.languages.slice(0, 8).map((_entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            </div>
          )}

          {/* Top Companies and Locations */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Companies */}
            {topCompanies && topCompanies.companies && (
              <Card>
                <h2 className="text-2xl font-semibold text-gray-900 mb-6 flex items-center">
                  <Building2 className="w-6 h-6 mr-2 text-primary-600" />
                  Top Companies by Headcount
                </h2>
                <div className="space-y-3">
                  {topCompanies.companies.slice(0, 10).map((company: any, index: number) => (
                    <div 
                      key={company.company_id}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                      onClick={() => handleSelectCompany(company.company_id, company.company_name)}
                    >
                      <div className="flex items-center space-x-3">
                        <span className="text-lg font-bold text-primary-600 w-8">{index + 1}</span>
                        <span className="font-medium text-gray-900">{company.company_name}</span>
                      </div>
                      <Badge variant="primary">{company.total_people} people</Badge>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Top Locations */}
            {locations && locations.locations && (
              <Card>
                <h2 className="text-2xl font-semibold text-gray-900 mb-6 flex items-center">
                  <MapPin className="w-6 h-6 mr-2 text-primary-600" />
                  Top Locations
                </h2>
                <div className="space-y-3">
                  {locations.locations.slice(0, 10).map((location: any, index: number) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <span className="text-lg font-bold text-primary-600 w-8">{index + 1}</span>
                        <span className="font-medium text-gray-900">{location.location}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge variant="success">{location.person_count} total</Badge>
                        <Badge variant="info">{location.with_github} GitHub</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        </>
      )}

      {/* Company-Specific View */}
      {selectedCompany && (
        <div className="space-y-6">
          <Card className="bg-gradient-to-r from-primary-500 to-primary-600 text-white">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold">{selectedCompanyName}</h2>
                <p className="text-primary-100 mt-1">Company-specific market intelligence</p>
              </div>
              <Button 
                variant="outline" 
                onClick={clearCompanyFilter}
                className="text-white border-white hover:bg-white hover:text-primary-600"
              >
                View All Companies
              </Button>
            </div>
          </Card>

          {/* Company-specific charts */}
          {companyHiring && (
            <HiringTrendsChart 
              data={companyHiring}
              companyName={selectedCompanyName}
            />
          )}

          {companyTalentFlow && (
            <TalentFlowChart 
              data={companyTalentFlow}
              companyName={selectedCompanyName}
            />
          )}

          {companyTech && (
            <TechnologyDistributionChart 
              data={companyTech}
              companyName={selectedCompanyName}
            />
          )}

          {!companyHiring && !companyTalentFlow && !companyTech && (
            <Card>
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-300 border-t-primary-600 mb-4"></div>
                <p className="text-gray-500">Loading company data...</p>
              </div>
            </Card>
          )}
        </div>
      )}

        </>
      )}

      {/* Technologists Modal */}
      <TechnologistsModal
        isOpen={showTechnologistsModal}
        onClose={() => setShowTechnologistsModal(false)}
        technology={selectedTechnology}
      />
    </div>
  );
}
