import type { Employment } from '../../types';

interface EmploymentTimelineProps {
  employment: Employment[];
}

function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return 'Present';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
}

function calculateDuration(startDate: string, endDate: string | null): string {
  const start = new Date(startDate);
  const end = endDate ? new Date(endDate) : new Date();
  
  const months = (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth());
  const years = Math.floor(months / 12);
  const remainingMonths = months % 12;
  
  if (years === 0) {
    return `${remainingMonths} mo`;
  } else if (remainingMonths === 0) {
    return `${years} yr`;
  } else {
    return `${years} yr ${remainingMonths} mo`;
  }
}

export default function EmploymentTimeline({ employment }: EmploymentTimelineProps) {
  // Sort by start date, most recent first
  const sortedEmployment = [...employment].sort((a, b) => {
    const dateA = a.start_date ? new Date(a.start_date).getTime() : 0;
    const dateB = b.start_date ? new Date(b.start_date).getTime() : 0;
    return dateB - dateA;
  });

  if (employment.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Employment History</h2>
        <p className="text-gray-500">No employment history available</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">Employment History</h2>
      
      <div className="space-y-4">
        {sortedEmployment.map((job) => (
          <div
            key={job.employment_id}
            className={`relative pl-8 pb-6 border-l-2 ${
              job.is_current ? 'border-green-500' : 'border-gray-300'
            } last:pb-0`}
          >
            {/* Timeline dot */}
            <div
              className={`absolute left-0 top-0 w-4 h-4 rounded-full -ml-2 ${
                job.is_current ? 'bg-green-500 ring-4 ring-green-100' : 'bg-gray-400'
              }`}
            />
            
            {/* Content */}
            <div>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {job.title || 'Position'}
                  </h3>
                  <p className="text-md font-medium text-gray-700">{job.company_name}</p>
                </div>
                
                {job.is_current && (
                  <span className="ml-4 px-3 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded-full">
                    Current
                  </span>
                )}
              </div>
              
              <div className="mt-2 flex items-center space-x-4 text-sm text-gray-500">
                <span>
                  {formatDate(job.start_date)} - {formatDate(job.end_date)}
                </span>
                {job.start_date && (
                  <>
                    <span>•</span>
                    <span>{calculateDuration(job.start_date, job.end_date)}</span>
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

