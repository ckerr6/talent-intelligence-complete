import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, Users, Calendar } from 'lucide-react';

interface HiringTrendsChartProps {
  data: any;
  companyName: string;
}

export default function HiringTrendsChart({ data, companyName }: HiringTrendsChartProps) {
  if (!data || !data.monthly_hires) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Hiring Trends</h3>
        <p className="text-gray-500">No hiring data available</p>
      </div>
    );
  }

  // Transform data for recharts
  const chartData = data.monthly_hires.map((item: any) => ({
    month: new Date(item.month).toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
    hires: item.hires,
  }));

  // Calculate stats
  const totalHires = data.total_hires || 0;
  const avgMonthlyHires = totalHires / (data.time_period_months || 1);
  const avgTenureYears = data.avg_tenure_days ? (data.avg_tenure_days / 365.25).toFixed(1) : 'N/A';

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-purple-600" />
            <span>Hiring Trends</span>
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Last {data.time_period_months} months at {companyName}
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-purple-700 font-medium">Total Hires</p>
              <p className="text-2xl font-bold text-purple-900 mt-1">{totalHires}</p>
            </div>
            <Users className="w-8 h-8 text-purple-400" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-700 font-medium">Avg/Month</p>
              <p className="text-2xl font-bold text-blue-900 mt-1">{avgMonthlyHires.toFixed(1)}</p>
            </div>
            <Calendar className="w-8 h-8 text-blue-400" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-green-700 font-medium">Avg Tenure</p>
              <p className="text-2xl font-bold text-green-900 mt-1">{avgTenureYears}<span className="text-base">y</span></p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-400" />
          </div>
        </div>
      </div>

      {/* Chart */}
      {chartData.length > 0 ? (
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="month" 
                tick={{ fill: '#6b7280', fontSize: 12 }}
                tickLine={{ stroke: '#9ca3af' }}
              />
              <YAxis 
                tick={{ fill: '#6b7280', fontSize: 12 }}
                tickLine={{ stroke: '#9ca3af' }}
                label={{ value: 'Hires', angle: -90, position: 'insideLeft', fill: '#6b7280' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  padding: '8px 12px'
                }}
                labelStyle={{ color: '#111827', fontWeight: 600 }}
              />
              <Bar 
                dataKey="hires" 
                fill="url(#colorHires)" 
                radius={[8, 8, 0, 0]}
                maxBarSize={60}
              />
              <defs>
                <linearGradient id="colorHires" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.8} />
                  <stop offset="100%" stopColor="#6366f1" stopOpacity={0.6} />
                </linearGradient>
              </defs>
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="h-64 flex items-center justify-center text-gray-500">
          No monthly data available
        </div>
      )}

      {/* Top Roles */}
      {data.top_roles && data.top_roles.length > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h4 className="text-sm font-semibold text-gray-900 mb-3">Top Roles Hired</h4>
          <div className="space-y-2">
            {data.top_roles.slice(0, 5).map((role: any, idx: number) => (
              <div key={idx} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-gray-900">{role.title}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full"
                      style={{ width: `${(role.count / data.top_roles[0].count) * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm text-gray-600 w-8 text-right">{role.count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

