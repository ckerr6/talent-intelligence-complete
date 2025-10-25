// ABOUTME: Bloomberg Terminal-style enhanced GitHub developer profile with data-dense visualizations
// ABOUTME: Shows comprehensive developer intelligence with charts, graphs, and detailed metrics

import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { 
  Github, TrendingUp, Star, Mail, Users, Code, Building, 
  Calendar, Activity, Target, Award, Briefcase 
} from 'lucide-react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

interface ProfileData {
  username: string;
  seniority: string;
  seniority_confidence: number;
  primary_languages: Record<string, { bytes: number; percentage: number; proficiency: string }>;
  frameworks: string[];
  domains: string[];
  influence_score: number;
  reachability_score: number;
  activity_trend: string;
  organizations: string[];
}

// Bloomberg Terminal color scheme
const COLORS = {
  primary: '#FF9500',  // Bloomberg orange
  success: '#00D563',  // Green
  danger: '#FF453A',   // Red
  warning: '#FFD60A',  // Yellow
  info: '#0A84FF',     // Blue
  bg: '#0A0A0A',       // Dark background
  card: '#1C1C1E',     // Card background
  border: '#2C2C2E',   // Border
  text: '#E5E5E7'      // Text
};

const CHART_COLORS = ['#FF9500', '#0A84FF', '#00D563', '#FFD60A', '#FF453A', '#AF52DE'];

export default function EnhancedGitHubProfile() {
  const { username } = useParams();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/github-intelligence/profile/${username}`);
        if (!response.ok) throw new Error('Profile not found');
        const data = await response.json();
        setProfile(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load profile');
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [username]);

  if (loading) {
    return (
      <div style={{ background: COLORS.bg, minHeight: '100vh', color: COLORS.text, padding: '20px' }}>
        <div style={{ maxWidth: '1800px', margin: '0 auto' }}>
          <div style={{ fontSize: '18px' }}>Loading profile...</div>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div style={{ background: COLORS.bg, minHeight: '100vh', color: COLORS.text, padding: '20px' }}>
        <div style={{ maxWidth: '1800px', margin: '0 auto' }}>
          <div style={{ color: COLORS.danger }}>Error: {error || 'Profile not found'}</div>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const languageData = Object.entries(profile.primary_languages)
    .filter(([_, data]) => data.percentage > 0.5)
    .map(([lang, data]) => ({
      name: lang,
      value: data.percentage,
      proficiency: data.proficiency
    }))
    .slice(0, 10);

  const skillsRadarData = [
    { skill: 'Technical', value: profile.influence_score },
    { skill: 'Reach', value: profile.reachability_score },
    { skill: 'Activity', value: profile.activity_trend === 'growing' ? 85 : profile.activity_trend === 'stable' ? 65 : 45 },
    { skill: 'Collaboration', value: profile.organizations.length * 10 },
    { skill: 'Seniority', value: profile.seniority_confidence * 100 }
  ];

  const proficiencyData = Object.entries(
    profile.primary_languages
  ).reduce((acc, [_, data]) => {
    const prof = data.proficiency;
    acc[prof] = (acc[prof] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const proficiencyChartData = Object.entries(proficiencyData).map(([level, count]) => ({
    level,
    count
  }));

  return (
    <div style={{ background: COLORS.bg, minHeight: '100vh', color: COLORS.text, fontFamily: 'monospace' }}>
      <div style={{ maxWidth: '1800px', margin: '0 auto', padding: '20px' }}>
        
        {/* Header - Bloomberg style */}
        <div style={{ 
          background: COLORS.card, 
          border: `2px solid ${COLORS.primary}`,
          padding: '20px',
          marginBottom: '20px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '15px' }}>
            <Github size={40} color={COLORS.primary} />
            <div>
              <h1 style={{ fontSize: '32px', margin: 0, color: COLORS.primary }}>@{profile.username}</h1>
              <div style={{ fontSize: '14px', color: COLORS.text, opacity: 0.7 }}>
                DEVELOPER INTELLIGENCE REPORT
              </div>
            </div>
          </div>

          {/* Key Metrics Strip */}
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: '15px',
            marginTop: '20px'
          }}>
            <MetricCard
              label="SENIORITY"
              value={profile.seniority}
              subtitle={`${(profile.seniority_confidence * 100).toFixed(0)}% confidence`}
              icon={<Award size={20} />}
              color={COLORS.primary}
            />
            <MetricCard
              label="INFLUENCE"
              value={profile.influence_score.toString()}
              subtitle="Network reach"
              icon={<TrendingUp size={20} />}
              color={COLORS.success}
            />
            <MetricCard
              label="REACHABILITY"
              value={profile.reachability_score.toString()}
              subtitle="Contact score"
              icon={<Mail size={20} />}
              color={COLORS.info}
            />
            <MetricCard
              label="ORGANIZATIONS"
              value={profile.organizations.length.toString()}
              subtitle="Active memberships"
              icon={<Building size={20} />}
              color={COLORS.warning}
            />
            <MetricCard
              label="LANGUAGES"
              value={Object.keys(profile.primary_languages).length.toString()}
              subtitle="Technical breadth"
              icon={<Code size={20} />}
              color={COLORS.primary}
            />
            <MetricCard
              label="TREND"
              value={profile.activity_trend.toUpperCase()}
              subtitle="Activity pattern"
              icon={<Activity size={20} />}
              color={profile.activity_trend === 'growing' ? COLORS.success : COLORS.warning}
            />
          </div>
        </div>

        {/* Charts Grid - Data Dense Layout */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px', marginBottom: '20px' }}>
          
          {/* Language Distribution */}
          <ChartCard title="LANGUAGE PROFICIENCY DISTRIBUTION">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={languageData}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                <XAxis dataKey="name" stroke={COLORS.text} angle={-45} textAnchor="end" height={80} />
                <YAxis stroke={COLORS.text} />
                <Tooltip 
                  contentStyle={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}
                  labelStyle={{ color: COLORS.text }}
                />
                <Bar dataKey="value" fill={COLORS.primary} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Skills Radar */}
          <ChartCard title="DEVELOPER SKILL RADAR">
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={skillsRadarData}>
                <PolarGrid stroke={COLORS.border} />
                <PolarAngleAxis dataKey="skill" stroke={COLORS.text} />
                <PolarRadiusAxis stroke={COLORS.text} />
                <Radar dataKey="value" stroke={COLORS.primary} fill={COLORS.primary} fillOpacity={0.6} />
              </RadarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Language Pie */}
          <ChartCard title="TOP LANGUAGES BY PERCENTAGE">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={languageData.slice(0, 6)}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {languageData.slice(0, 6).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}
                />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Proficiency Breakdown */}
          <ChartCard title="PROFICIENCY LEVELS">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={proficiencyChartData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
                <XAxis type="number" stroke={COLORS.text} />
                <YAxis type="category" dataKey="level" stroke={COLORS.text} />
                <Tooltip 
                  contentStyle={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}
                />
                <Bar dataKey="count" fill={COLORS.info} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Detailed Lists */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
          
          {/* Top Languages */}
          <ListCard title="TOP LANGUAGES" icon={<Code size={18} />}>
            {languageData.slice(0, 8).map((lang, i) => (
              <div key={i} style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                padding: '8px 0',
                borderBottom: `1px solid ${COLORS.border}`
              }}>
                <span>{lang.name}</span>
                <span style={{ color: COLORS.primary }}>{lang.value.toFixed(1)}%</span>
              </div>
            ))}
          </ListCard>

          {/* Organizations */}
          <ListCard title="ORGANIZATIONS" icon={<Building size={18} />}>
            {profile.organizations.slice(0, 8).map((org, i) => (
              <div key={i} style={{ 
                padding: '8px 0',
                borderBottom: `1px solid ${COLORS.border}`
              }}>
                {org}
              </div>
            ))}
            {profile.organizations.length === 0 && (
              <div style={{ opacity: 0.5, padding: '8px 0' }}>No public organizations</div>
            )}
          </ListCard>

          {/* Domains */}
          <ListCard title="DOMAINS" icon={<Target size={18} />}>
            {profile.domains.slice(0, 8).map((domain, i) => (
              <div key={i} style={{ 
                padding: '8px 0',
                borderBottom: `1px solid ${COLORS.border}`
              }}>
                {domain}
              </div>
            ))}
            {profile.domains.length === 0 && (
              <div style={{ opacity: 0.5, padding: '8px 0' }}>No domains identified</div>
            )}
          </ListCard>
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
      <div style={{ fontSize: '11px', opacity: 0.6 }}>{subtitle}</div>
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

function ListCard({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div style={{ 
      background: COLORS.card,
      border: `1px solid ${COLORS.border}`,
      padding: '20px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '15px' }}>
        <span style={{ color: COLORS.primary }}>{icon}</span>
        <h3 style={{ 
          margin: 0,
          fontSize: '14px',
          color: COLORS.primary,
          letterSpacing: '1px'
        }}>
          {title}
        </h3>
      </div>
      <div style={{ fontSize: '13px' }}>
        {children}
      </div>
    </div>
  );
}

