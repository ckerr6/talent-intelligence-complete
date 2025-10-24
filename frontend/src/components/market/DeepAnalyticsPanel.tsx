import { useState, useEffect } from 'react';
import { TrendingUp, Target, Network, Award } from 'lucide-react';
import Card from '../common/Card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

interface DeepAnalyticsPanelProps {
  companyId?: string;
}

export default function DeepAnalyticsPanel({ companyId }: DeepAnalyticsPanelProps) {
  const [ecosystems, setEcosystems] = useState<any[]>([]);
  const [skills, setSkills] = useState<any[]>([]);
  const [networkStats, setNetworkStats] = useState<any>(null);
  const [companyTeam, setCompanyTeam] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDeepAnalytics();
  }, [companyId]);

  const loadDeepAnalytics = async () => {
    setLoading(true);
    try {
      if (companyId) {
        // Load company-specific deep analytics
        const [team] = await Promise.all([
          fetch(`/api/market/deep/company/${companyId}/team-composition`).then(r => r.json())
        ]);
        
        if (team.success) setCompanyTeam(team.data);
      } else {
        // Load market-wide deep analytics
        const [ecosystemsRes, skillsRes, networkRes] = await Promise.all([
          fetch('/api/market/deep/ecosystem-trends?months=12&limit=10').then(r => r.json()),
          fetch('/api/market/deep/skills-demand?months=6&limit=15').then(r => r.json()),
          fetch('/api/market/deep/network-density').then(r => r.json())
        ]);

        if (ecosystemsRes.success) setEcosystems(ecosystemsRes.data.ecosystems || []);
        if (skillsRes.success) setSkills(skillsRes.data.skills || []);
        if (networkRes.success) setNetworkStats(networkRes.data);
      }
    } catch (error) {
      console.error('Error loading deep analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </Card>
    );
  }

  // Company-specific view
  if (companyId && companyTeam) {
    const qualityData = companyTeam.quality_tiers?.map((tier: any) => ({
      name: tier.quality_tier,
      value: tier.employee_count
    })) || [];

    return (
      <div className="space-y-6">
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Award className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Deep Team Analytics</h2>
              <p className="text-gray-600">Comprehensive team composition and quality analysis</p>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-3xl font-bold text-blue-600">
                {companyTeam.team_stats?.current_employees || 0}
              </div>
              <div className="text-sm text-gray-600 mt-1">Current Team</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-3xl font-bold text-green-600">
                {companyTeam.team_stats?.with_github || 0}
              </div>
              <div className="text-sm text-gray-600 mt-1">GitHub Profiles</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-3xl font-bold text-purple-600">
                {companyTeam.team_stats?.avg_importance?.toFixed(1) || '0.0'}
              </div>
              <div className="text-sm text-gray-600 mt-1">Avg Importance</div>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-3xl font-bold text-yellow-600">
                {companyTeam.team_stats?.total_merged_prs || 0}
              </div>
              <div className="text-sm text-gray-600 mt-1">Total PRs</div>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Quality Distribution */}
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Team Quality Distribution</h3>
              {qualityData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={qualityData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {qualityData.map((_entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-gray-500 text-center py-8">No quality data available</p>
              )}
            </div>

            {/* Top Skills */}
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Top Team Skills</h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {companyTeam.skills_distribution?.slice(0, 10).map((skill: any, index: number) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="font-medium text-gray-700">{skill.skill_name}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-gray-600">{skill.employee_count} people</span>
                      <span className="text-xs text-purple-600">
                        {skill.avg_importance?.toFixed(1) || '0.0'} avg
                      </span>
                    </div>
                  </div>
                )) || <p className="text-gray-500 text-center py-4">No skills data</p>}
              </div>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  // Market-wide view
  return (
    <div className="space-y-6">
      {/* Ecosystem Trends */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-blue-100 rounded-lg">
            <TrendingUp className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Ecosystem Growth Trends</h2>
            <p className="text-gray-600">Hot markets and developer adoption rates</p>
          </div>
        </div>

        {ecosystems.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={ecosystems.slice(0, 8)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="ecosystem_name" angle={-45} textAnchor="end" height={100} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="developer_count" fill="#3B82F6" name="Developers" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-gray-500 text-center py-8">No ecosystem data available</p>
        )}

        {ecosystems.length > 0 && (
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            {ecosystems.slice(0, 3).map((eco, index) => (
              <div key={index} className="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg">
                <div className="font-semibold text-gray-900">{eco.ecosystem_name}</div>
                <div className="text-2xl font-bold text-blue-600 mt-2">
                  {eco.developer_count} devs
                </div>
                <div className="text-sm text-gray-600 mt-1">
                  Growth: {eco.growth_rate?.toFixed(1) || '0.0'}% (12mo)
                </div>
                <div className="text-xs text-purple-600 mt-1">
                  Avg Importance: {eco.avg_importance?.toFixed(1) || '0.0'}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Skills Demand */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-green-100 rounded-lg">
            <Target className="w-6 h-6 text-green-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Skills Demand Analysis</h2>
            <p className="text-gray-600">Most valuable skills in the market</p>
          </div>
        </div>

        <div className="space-y-3">
          {skills.slice(0, 10).map((skill, index) => (
            <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
              <div className="flex items-center gap-4">
                <div className="text-2xl font-bold text-gray-400 w-8">{index + 1}</div>
                <div>
                  <div className="font-semibold text-gray-900">{skill.skill_name}</div>
                  <div className="text-sm text-gray-600">{skill.category}</div>
                </div>
              </div>
              <div className="flex items-center gap-6">
                <div className="text-right">
                  <div className="text-sm text-gray-600">Developers</div>
                  <div className="font-bold text-gray-900">{skill.developer_count}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-600">Demand</div>
                  <div className="font-bold text-green-600">{skill.demand_score?.toFixed(1) || '0.0'}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-600">Avg Importance</div>
                  <div className="font-bold text-purple-600">
                    {skill.avg_developer_importance?.toFixed(1) || '0.0'}
                  </div>
                </div>
              </div>
            </div>
          )) || <p className="text-gray-500 text-center py-4">No skills data available</p>}
        </div>
      </Card>

      {/* Network Insights */}
      {networkStats && (
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Network className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Network Density</h2>
              <p className="text-gray-600">Collaboration patterns and connectivity</p>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-3xl font-bold text-purple-600">
                {networkStats.network_stats?.total_connected_people?.toLocaleString() || '0'}
              </div>
              <div className="text-sm text-gray-600 mt-1">Connected People</div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-3xl font-bold text-blue-600">
                {networkStats.network_stats?.total_edges?.toLocaleString() || '0'}
              </div>
              <div className="text-sm text-gray-600 mt-1">Collaboration Edges</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-3xl font-bold text-green-600">
                {networkStats.network_stats?.avg_connections_per_person?.toFixed(1) || '0.0'}
              </div>
              <div className="text-sm text-gray-600 mt-1">Avg Connections</div>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-3xl font-bold text-yellow-600">
                {networkStats.network_stats?.avg_shared_repos?.toFixed(1) || '0.0'}
              </div>
              <div className="text-sm text-gray-600 mt-1">Avg Shared Repos</div>
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Top Collaboration Hubs</h3>
            <div className="space-y-2">
              {networkStats.top_collaboration_hubs?.slice(0, 10).map((hub: any, index: number) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-medium text-gray-900">{hub.full_name}</div>
                    <div className="text-sm text-gray-600">@{hub.github_username}</div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-sm text-gray-600">Connections</div>
                      <div className="font-bold text-gray-900">{hub.connection_count}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-600">Importance</div>
                      <div className="font-bold text-purple-600">
                        {hub.importance_score?.toFixed(1) || '0.0'}
                      </div>
                    </div>
                  </div>
                </div>
              )) || <p className="text-gray-500 text-center py-4">No hub data</p>}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

