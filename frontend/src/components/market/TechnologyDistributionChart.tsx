import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Code2, Users } from 'lucide-react';
import { useState } from 'react';

interface TechnologyDistributionChartProps {
  data: any;
  companyName: string;
}

const COLORS = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#6366f1', '#14b8a6', '#f97316', '#84cc16'];

export default function TechnologyDistributionChart({ data, companyName }: TechnologyDistributionChartProps) {
  const [viewMode, setViewMode] = useState<'bar' | 'pie'>('bar');

  if (!data || !data.languages || data.languages.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Technology Distribution</h3>
        <p className="text-gray-500">No technology data available</p>
      </div>
    );
  }

  const languages = data.languages.slice(0, 10);
  
  // Prepare data for charts
  const chartData = languages.map((lang: any) => ({
    name: lang.language,
    developers: lang.developer_count,
    contributions: lang.total_contributions,
    repos: lang.repo_count,
  }));

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
            <Code2 className="w-5 h-5 text-blue-600" />
            <span>Technology Distribution</span>
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Languages & tools at {companyName}
          </p>
        </div>

        {/* View Toggle */}
        <div className="flex bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setViewMode('bar')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              viewMode === 'bar'
                ? 'bg-white text-gray-900 shadow'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Bar
          </button>
          <button
            onClick={() => setViewMode('pie')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              viewMode === 'pie'
                ? 'bg-white text-gray-900 shadow'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Pie
          </button>
        </div>
      </div>

      {/* Chart */}
      <div className="h-64 mb-6">
        {viewMode === 'bar' ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="name" 
                tick={{ fill: '#6b7280', fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis 
                tick={{ fill: '#6b7280', fontSize: 12 }}
                label={{ value: 'Developers', angle: -90, position: 'insideLeft', fill: '#6b7280' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  padding: '8px 12px'
                }}
                formatter={(value: any, name: string) => {
                  if (name === 'developers') return [value, 'Developers'];
                  if (name === 'contributions') return [value, 'Contributions'];
                  if (name === 'repos') return [value, 'Repositories'];
                  return [value, name];
                }}
              />
              <Bar dataKey="developers" fill="url(#colorDevelopers)" radius={[8, 8, 0, 0]} maxBarSize={50} />
              <defs>
                <linearGradient id="colorDevelopers" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.8} />
                  <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0.6} />
                </linearGradient>
              </defs>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="developers"
              >
                {chartData.map((entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  padding: '8px 12px'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Technology List */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Language Breakdown</h4>
        {languages.map((lang: any, idx: number) => (
          <div 
            key={idx}
            className="flex items-center justify-between p-3 bg-gradient-to-r from-gray-50 to-white rounded-lg border border-gray-100 hover:border-blue-200 transition-colors"
          >
            <div className="flex items-center space-x-3">
              <div 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: COLORS[idx % COLORS.length] }}
              ></div>
              <span className="font-medium text-gray-900">{lang.language}</span>
            </div>
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-1">
                <Users className="w-3 h-3 text-gray-400" />
                <span className="text-gray-600">{lang.developer_count} devs</span>
              </div>
              <span className="text-gray-400">•</span>
              <span className="text-gray-600">{lang.total_contributions.toLocaleString()} commits</span>
              <span className="text-gray-400">•</span>
              <span className="text-gray-600">{lang.repo_count} repos</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

