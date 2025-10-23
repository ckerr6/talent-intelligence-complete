import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ArrowRight, ArrowLeft, Building2 } from 'lucide-react';

interface TalentFlowChartProps {
  data: any;
  companyName: string;
}

export default function TalentFlowChart({ data, companyName }: TalentFlowChartProps) {
  if (!data) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Talent Flow</h3>
        <p className="text-gray-500">No talent flow data available</p>
      </div>
    );
  }

  const feederCompanies = data.feeder_companies || [];
  const destinationCompanies = data.destination_companies || [];

  // Prepare chart data (top 5 each)
  const inboundData = feederCompanies.slice(0, 5).map((company: any) => ({
    name: company.company_name.length > 20 ? company.company_name.substring(0, 20) + '...' : company.company_name,
    fullName: company.company_name,
    value: company.person_count,
    type: 'inbound'
  }));

  const outboundData = destinationCompanies.slice(0, 5).map((company: any) => ({
    name: company.company_name.length > 20 ? company.company_name.substring(0, 20) + '...' : company.company_name,
    fullName: company.company_name,
    value: company.person_count,
    type: 'outbound'
  }));

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
          <Building2 className="w-5 h-5 text-green-600" />
          <span>Talent Flow</span>
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          Where talent comes from and goes to
        </p>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* Inbound */}
        <div>
          <div className="flex items-center space-x-2 mb-3">
            <ArrowRight className="w-4 h-4 text-green-600" />
            <span className="text-sm font-semibold text-gray-900">Feeder Companies</span>
          </div>
          <div className="space-y-2">
            {inboundData.length > 0 ? (
              inboundData.map((company: any, idx: number) => (
                <div key={idx} className="flex items-center justify-between p-2 bg-green-50 rounded">
                  <span className="text-sm text-gray-900 font-medium truncate" title={company.fullName}>
                    {company.name}
                  </span>
                  <span className="text-sm text-green-700 font-bold ml-2">{company.value}</span>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500 italic">No feeder data</p>
            )}
          </div>
        </div>

        {/* Outbound */}
        <div>
          <div className="flex items-center space-x-2 mb-3">
            <ArrowLeft className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-semibold text-gray-900">Destination Companies</span>
          </div>
          <div className="space-y-2">
            {outboundData.length > 0 ? (
              outboundData.map((company: any, idx: number) => (
                <div key={idx} className="flex items-center justify-between p-2 bg-blue-50 rounded">
                  <span className="text-sm text-gray-900 font-medium truncate" title={company.fullName}>
                    {company.name}
                  </span>
                  <span className="text-sm text-blue-700 font-bold ml-2">{company.value}</span>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500 italic">No destination data</p>
            )}
          </div>
        </div>
      </div>

      {/* Combined Bar Chart */}
      {(inboundData.length > 0 || outboundData.length > 0) && (
        <div className="h-64 mt-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Top Talent Flows</h4>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart 
              data={[...inboundData, ...outboundData]}
              layout="horizontal"
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                type="number"
                tick={{ fill: '#6b7280', fontSize: 12 }}
              />
              <YAxis 
                type="category"
                dataKey="name"
                tick={{ fill: '#6b7280', fontSize: 11 }}
                width={100}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  padding: '8px 12px'
                }}
                formatter={(value: any, name: any, props: any) => {
                  const label = props.payload.type === 'inbound' ? 'Joined from' : 'Left to';
                  return [`${value} people ${label} ${props.payload.fullName}`, ''];
                }}
              />
              <Bar 
                dataKey="value" 
                fill="#10b981"
                radius={[0, 4, 4, 0]}
                maxBarSize={30}
              >
                {(inboundData.concat(outboundData)).map((entry: any, index: number) => (
                  <rect key={`cell-${index}`} fill={entry.type === 'inbound' ? '#10b981' : '#3b82f6'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Empty State */}
      {feederCompanies.length === 0 && destinationCompanies.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <Building2 className="w-12 h-12 text-gray-300 mx-auto mb-2" />
          <p>No talent flow data available</p>
          <p className="text-sm mt-1">This may indicate limited employment transition data</p>
        </div>
      )}
    </div>
  );
}

