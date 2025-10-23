import { useState } from 'react';
import { Sparkles, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';

interface AISummary {
  executive_summary: string;
  key_strengths: string[];
  technical_domains: string[];
  ideal_roles: string[];
  career_trajectory: string;
  standout_projects: string[];
  recruiter_notes: string;
  generated_at: string;
  model: string;
}

interface AISummaryCardProps {
  personId: string;
  summary?: AISummary | null;
  onGenerate: () => void;
  loading?: boolean;
  error?: string | null;
}

export default function AISummaryCard({
  personId,
  summary,
  onGenerate,
  loading = false,
  error = null,
}: AISummaryCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="bg-gradient-to-br from-purple-50 to-blue-50 border-2 border-purple-200 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-2">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">AI Career Intelligence</h3>
            <p className="text-sm text-gray-600">Powered by GPT-4o-mini</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {summary && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
            >
              {isExpanded ? (
                <ChevronUp className="w-5 h-5" />
              ) : (
                <ChevronDown className="w-5 h-5" />
              )}
            </button>
          )}
          <button
            onClick={onGenerate}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Generating...' : summary ? 'Regenerate' : 'Generate Summary'}</span>
          </button>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <RefreshCw className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-3" />
            <p className="text-gray-600">AI is analyzing this candidate...</p>
            <p className="text-sm text-gray-500 mt-1">This takes about 5-8 seconds</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 font-medium">Error generating summary</p>
          <p className="text-red-600 text-sm mt-1">{error}</p>
        </div>
      )}

      {/* Summary Content */}
      {summary && isExpanded && !loading && (
        <div className="space-y-4">
          {/* Executive Summary */}
          <div>
            <h4 className="text-sm font-semibold text-purple-900 uppercase tracking-wide mb-2">
              Executive Summary
            </h4>
            <p className="text-gray-700 leading-relaxed">{summary.executive_summary}</p>
          </div>

          {/* Key Strengths */}
          <div>
            <h4 className="text-sm font-semibold text-purple-900 uppercase tracking-wide mb-2">
              Key Strengths
            </h4>
            <div className="flex flex-wrap gap-2">
              {summary.key_strengths.map((strength, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium"
                >
                  ✓ {strength}
                </span>
              ))}
            </div>
          </div>

          {/* Technical Domains & Ideal Roles - Side by Side */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Technical Domains */}
            <div>
              <h4 className="text-sm font-semibold text-purple-900 uppercase tracking-wide mb-2">
                Technical Domains
              </h4>
              <div className="space-y-1">
                {summary.technical_domains.map((domain, idx) => (
                  <div key={idx} className="flex items-center space-x-2">
                    <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                    <span className="text-gray-700 text-sm">{domain}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Ideal Roles */}
            <div>
              <h4 className="text-sm font-semibold text-purple-900 uppercase tracking-wide mb-2">
                Ideal Roles
              </h4>
              <div className="space-y-1">
                {summary.ideal_roles.map((role, idx) => (
                  <div key={idx} className="flex items-center space-x-2">
                    <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
                    <span className="text-gray-700 text-sm">{role}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Career Trajectory */}
          <div>
            <h4 className="text-sm font-semibold text-purple-900 uppercase tracking-wide mb-2">
              Career Assessment
            </h4>
            <p className="text-gray-700 text-sm leading-relaxed">{summary.career_trajectory}</p>
          </div>

          {/* Standout Projects */}
          {summary.standout_projects && summary.standout_projects.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-purple-900 uppercase tracking-wide mb-2">
                Standout Projects
              </h4>
              <ul className="space-y-2">
                {summary.standout_projects.map((project, idx) => (
                  <li key={idx} className="flex items-start space-x-2">
                    <span className="text-purple-500 font-bold mt-0.5">•</span>
                    <span className="text-gray-700 text-sm">{project}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recruiter Notes */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-yellow-900 uppercase tracking-wide mb-2">
              💡 Recruiter Notes
            </h4>
            <p className="text-gray-700 text-sm leading-relaxed">{summary.recruiter_notes}</p>
          </div>

          {/* Metadata */}
          <div className="pt-3 border-t border-purple-200">
            <p className="text-xs text-gray-500">
              Generated {new Date(summary.generated_at).toLocaleString()} • Model: {summary.model}
            </p>
          </div>
        </div>
      )}

      {/* Collapsed State */}
      {summary && !isExpanded && !loading && (
        <div className="py-2">
          <p className="text-gray-600 text-sm italic">
            AI summary available - Click to expand
          </p>
        </div>
      )}

      {/* No Summary State */}
      {!summary && !loading && !error && (
        <div className="text-center py-6">
          <Sparkles className="w-12 h-12 text-purple-300 mx-auto mb-3" />
          <p className="text-gray-600 font-medium">No AI summary generated yet</p>
          <p className="text-sm text-gray-500 mt-1">
            Click "Generate Summary" to get AI-powered insights about this candidate
          </p>
        </div>
      )}
    </div>
  );
}

