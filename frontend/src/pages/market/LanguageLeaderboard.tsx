// ABOUTME: Language Ecosystem Leaderboard - Bloomberg Terminal style
// ABOUTME: Shows top programming languages by developer count with detailed metrics

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Code, TrendingUp, Users, Award, Star } from 'lucide-react';
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

// Bloomberg Terminal colors
const COLORS = {
  primary: '#FF9500',
  success: '#00D563',
  danger: '#FF453A',
  warning: '#FFD60A',
  info: '#0A84FF',
  bg: '#0A0A0A',
  card: '#1C1C1E',
  border: '#2C2C2E',
  text: '#E5E5E7'
};

const CHART_COLORS = ['#FF9500', '#0A84FF', '#00D563', '#FFD60A', '#FF453A', '#AF52DE', '#5E5CE6', '#FF375F'];

interface LanguageData {
  language: string;
  developer_count: number;
  avg_influence: number;
  seniority_distribution: Record<string, number>;
  top_developers: Array<{
    username: string;
    seniority: string;
    percentage: number;
  }>;
}

export default function LanguageLeaderboard() {
  const navigate = useNavigate();
  const [languages, setLanguages] = useState<LanguageData[]>([]);
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [langResponse, overviewResponse] = await Promise.all([
          fetch('http://localhost:8000/api/market/languages?limit=20'),
          fetch('http://localhost:8000/api/market/overview')
        ]);
        
        const langData = await langResponse.json();
        const overviewData = await overviewResponse.json();
        
        setLanguages(langData.languages);
        setOverview(overviewData);
      } catch (err) {
        console.error('Failed to load language data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div style={{ background: COLORS.bg, minHeight: '100vh', color: COLORS.text, padding: '20px' }}>
        <div style={{ maxWidth: '1800px', margin: '0 auto' }}>
          <div style={{ fontSize: '18px' }}>Loading ecosystem data...</div>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const top10Languages = languages.slice(0, 10);
  const chartData = top10Languages.map(lang => ({
    name: lang.language,
    developers: lang.developer_count,
    influence: lang.avg_influence
  }));

  const pieData = top10Languages.slice(0, 8).map(lang => ({
    name: lang.language,
    value: lang.developer_count
  }));

  return (
    <div style={{ background: COLORS.bg, minHeight: '100vh', color: COLORS.text, fontFamily: 'monospace' }}>
      <div style={{ maxWidth: '1800px', margin: '0 auto', padding: '20px' }}>
        
        {/* Header */}
        <div style={{ 
          background: COLORS.card, 
          border: `2px solid ${COLORS.primary}`,
          padding: '20px',
          marginBottom: '20px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '15px' }}>
            <Code size={40} color={COLORS.primary} />
            <div>
              <h1 style={{ fontSize: '32px', margin: 0, color: COLORS.primary }}>LANGUAGE ECOSYSTEM LEADERBOARD</h1>
              <div style={{ fontSize: '14px', color: COLORS.text, opacity: 0.7 }}>
                GLOBAL DEVELOPER MARKET INTELLIGENCE
              </div>
            </div>
          </div>

          {/* Market Overview Strip */}
          {overview && (
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
              gap: '15px',
              marginTop: '20px'
            }}>
              <MetricCard
                label="TOTAL PROFILES"
                value={overview.total_profiles.toLocaleString()}
                icon={<Users size={20} />}
                color={COLORS.primary}
              />
              <MetricCard
                label="ENRICHED"
                value={overview.total_enriched.toLocaleString()}
                icon={<Star size={20} />}
                color={COLORS.success}
              />
              <MetricCard
                label="LANGUAGES TRACKED"
                value={overview.languages_tracked.toString()}
                icon={<Code size={20} />}
                color={COLORS.info}
              />
              <MetricCard
                label="TOP LANGUAGE"
                value={overview.top_languages[0]?.language || 'N/A'}
                subtitle={`${overview.top_languages[0]?.developers || 0} devs`}
                icon={<TrendingUp size={20} />}
                color={COLORS.warning}
              />
            </div>
          )}
        </div>

        {/* Charts Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px', marginBottom: '20px' }}>
          
          {/* Developer Count Bar Chart */}
          <ChartCard title="TOP LANGUAGES BY DEVELOPER COUNT">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                <XAxis dataKey="name" stroke={COLORS.text} angle={-45} textAnchor="end" height={100} />
                <YAxis stroke={COLORS.text} />
                <Tooltip 
                  contentStyle={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}
                  labelStyle={{ color: COLORS.text }}
                />
                <Bar dataKey="developers" fill={COLORS.primary} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Influence Score Bar Chart */}
          <ChartCard title="AVERAGE DEVELOPER INFLUENCE">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                <XAxis dataKey="name" stroke={COLORS.text} angle={-45} textAnchor="end" height={100} />
                <YAxis stroke={COLORS.text} />
                <Tooltip 
                  contentStyle={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}
                  labelStyle={{ color: COLORS.text }}
                />
                <Bar dataKey="influence" fill={COLORS.success} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Market Share Pie Chart */}
          <ChartCard title="LANGUAGE MARKET SHARE (BY DEVELOPERS)">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}
                />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Seniority Distribution */}
          <ChartCard title="OVERALL SENIORITY DISTRIBUTION">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={
                Object.entries(overview?.seniority_distribution || {}).map(([level, count]) => ({
                  level,
                  count
                }))
              } layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                <XAxis type="number" stroke={COLORS.text} />
                <YAxis type="category" dataKey="level" stroke={COLORS.text} width={100} />
                <Tooltip 
                  contentStyle={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}
                />
                <Bar dataKey="count" fill={COLORS.info} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Language Leaderboard Table */}
        <div style={{ 
          background: COLORS.card,
          border: `1px solid ${COLORS.border}`,
          padding: '20px'
        }}>
          <h3 style={{ 
            margin: '0 0 20px 0',
            fontSize: '14px',
            color: COLORS.primary,
            letterSpacing: '1px'
          }}>
            DETAILED RANKINGS
          </h3>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: `2px solid ${COLORS.border}` }}>
                  <th style={{ padding: '12px', textAlign: 'left', color: COLORS.primary }}>RANK</th>
                  <th style={{ padding: '12px', textAlign: 'left', color: COLORS.primary }}>LANGUAGE</th>
                  <th style={{ padding: '12px', textAlign: 'right', color: COLORS.primary }}>DEVELOPERS</th>
                  <th style={{ padding: '12px', textAlign: 'right', color: COLORS.primary }}>AVG INFLUENCE</th>
                  <th style={{ padding: '12px', textAlign: 'left', color: COLORS.primary }}>TOP SENIORITY</th>
                  <th style={{ padding: '12px', textAlign: 'left', color: COLORS.primary }}>TOP CONTRIBUTOR</th>
                </tr>
              </thead>
              <tbody>
                {languages.map((lang, index) => {
                  const topSeniority = Object.entries(lang.seniority_distribution)
                    .sort((a, b) => b[1] - a[1])[0]?.[0] || 'N/A';
                  const topDev = lang.top_developers[0];

                  return (
                    <tr 
                      key={lang.language}
                      style={{ 
                        borderBottom: `1px solid ${COLORS.border}`,
                        cursor: 'pointer',
                        transition: 'background 0.2s'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = COLORS.border}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                      onClick={() => navigate(`/github/${topDev?.username}/enhanced`)}
                    >
                      <td style={{ padding: '12px', color: COLORS.primary, fontWeight: 'bold' }}>
                        #{index + 1}
                      </td>
                      <td style={{ padding: '12px', fontSize: '14px', fontWeight: 'bold' }}>
                        {lang.language}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', color: COLORS.success }}>
                        {lang.developer_count}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', color: COLORS.info }}>
                        {lang.avg_influence.toFixed(1)}
                      </td>
                      <td style={{ padding: '12px' }}>
                        <span style={{ 
                          padding: '4px 8px', 
                          background: COLORS.border, 
                          borderRadius: '4px',
                          color: COLORS.warning
                        }}>
                          {topSeniority}
                        </span>
                      </td>
                      <td style={{ padding: '12px' }}>
                        {topDev && (
                          <div>
                            <span style={{ color: COLORS.text }}>@{topDev.username}</span>
                            <span style={{ color: COLORS.primary, marginLeft: '8px' }}>
                              ({topDev.percentage.toFixed(1)}%)
                            </span>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

// Helper Components
function MetricCard({ label, value, subtitle, icon, color }: any) {
  return (
    <div style={{ 
      background: COLORS.card,
      border: `1px solid ${COLORS.border}`,
      padding: '15px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '5px' }}>
        <span style={{ color }}>{icon}</span>
        <div style={{ fontSize: '11px', opacity: 0.7 }}>{label}</div>
      </div>
      <div style={{ fontSize: '24px', fontWeight: 'bold', color, marginBottom: '3px' }}>
        {value}
      </div>
      {subtitle && <div style={{ fontSize: '11px', opacity: 0.6 }}>{subtitle}</div>}
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ 
      background: COLORS.card,
      border: `1px solid ${COLORS.border}`,
      padding: '20px'
    }}>
      <h3 style={{ 
        margin: '0 0 15px 0',
        fontSize: '14px',
        color: COLORS.primary,
        letterSpacing: '1px'
      }}>
        {title}
      </h3>
      {children}
    </div>
  );
}

