import { useState } from 'react';
import { Code2, RefreshCw, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';

interface CodeAnalysis {
  code_quality_assessment: string;
  technical_depth: string;
  engineering_style: string;
  standout_contributions: string[];
  languages_and_tools: string[];
  work_complexity: string;
  collaboration_indicators: string;
  relevance_to_role?: string;
  concerns: string[];
  analyzed_at: string;
  model: string;
}

interface CodeAnalysisCardProps {
  personId: string;
  analysis?: CodeAnalysis | null;
  onGenerate: () => void;
  loading?: boolean;
  error?: string | null;
  hasGitHub?: boolean;
}

export default function CodeAnalysisCard({
  personId,
  analysis,
  onGenerate,
  loading = false,
  error = null,
  hasGitHub = true,
}: CodeAnalysisCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  if (!hasGitHub) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <div className="flex items-center space-x-2 text-gray-500">
          <Code2 className="w-5 h-5" />
          <span className="text-sm">No GitHub profile available for code analysis</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-blue-50 to-cyan-50 border-2 border-blue-200 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-2">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
            <Code2 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">AI Code Analysis</h3>
            <p className="text-sm text-gray-600">Technical work explained</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {analysis && (
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
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Analyzing...' : analysis ? 'Re-analyze' : 'Analyze Code'}</span>
          </button>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-3" />
            <p className="text-gray-600">AI is analyzing GitHub contributions...</p>
            <p className="text-sm text-gray-500 mt-1">This takes about 5-8 seconds</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 font-medium">Error analyzing code</p>
          <p className="text-red-600 text-sm mt-1">{error}</p>
        </div>
      )}

      {/* Analysis Content */}
      {analysis && isExpanded && !loading && (
        <div className="space-y-4">
          {/* Technical Depth Badge */}
          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm text-gray-600 block mb-1">Technical Level</span>
              <span className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg font-semibold text-lg">
                {analysis.technical_depth}
              </span>
            </div>
            <div className="text-right">
              <span className="text-sm text-gray-600 block mb-1">Engineering Style</span>
              <span className="text-gray-800 font-medium">{analysis.engineering_style}</span>
            </div>
          </div>

          {/* Code Quality Assessment */}
          <div>
            <h4 className="text-sm font-semibold text-blue-900 uppercase tracking-wide mb-2">
              Quality Assessment
            </h4>
            <p className="text-gray-700 leading-relaxed text-sm">{analysis.code_quality_assessment}</p>
          </div>

          {/* Languages & Tools */}
          <div>
            <h4 className="text-sm font-semibold text-blue-900 uppercase tracking-wide mb-2">
              Languages & Tools
            </h4>
            <div className="flex flex-wrap gap-2">
              {analysis.languages_and_tools.map((tool, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-cyan-100 text-cyan-800 rounded-full text-sm font-medium"
                >
                  {tool}
                </span>
              ))}
            </div>
          </div>

          {/* Work Complexity */}
          <div>
            <h4 className="text-sm font-semibold text-blue-900 uppercase tracking-wide mb-2">
              Work Complexity
            </h4>
            <p className="text-gray-700 text-sm leading-relaxed">{analysis.work_complexity}</p>
          </div>

          {/* Standout Contributions */}
          {analysis.standout_contributions && analysis.standout_contributions.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-blue-900 uppercase tracking-wide mb-2">
                Standout Contributions
              </h4>
              <ul className="space-y-2">
                {analysis.standout_contributions.map((contribution, idx) => (
                  <li key={idx} className="flex items-start space-x-2">
                    <span className="text-blue-500 font-bold mt-0.5">•</span>
                    <span className="text-gray-700 text-sm">{contribution}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Collaboration */}
          <div>
            <h4 className="text-sm font-semibold text-blue-900 uppercase tracking-wide mb-2">
              Collaboration & Teamwork
            </h4>
            <p className="text-gray-700 text-sm leading-relaxed">{analysis.collaboration_indicators}</p>
          </div>

          {/* Role Relevance (if provided) */}
          {analysis.relevance_to_role && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-green-900 uppercase tracking-wide mb-2">
                ✓ Role Fit Assessment
              </h4>
              <p className="text-gray-700 text-sm leading-relaxed">{analysis.relevance_to_role}</p>
            </div>
          )}

          {/* Concerns */}
          {analysis.concerns && analysis.concerns.length > 0 && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-orange-900 uppercase tracking-wide mb-2 flex items-center space-x-2">
                <AlertCircle className="w-4 h-4" />
                <span>Areas to Explore</span>
              </h4>
              <ul className="space-y-1">
                {analysis.concerns.map((concern, idx) => (
                  <li key={idx} className="flex items-start space-x-2">
                    <span className="text-orange-500 mt-0.5">⚠</span>
                    <span className="text-gray-700 text-sm">{concern}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Metadata */}
          <div className="pt-3 border-t border-blue-200">
            <p className="text-xs text-gray-500">
              Analyzed {new Date(analysis.analyzed_at).toLocaleString()} • Model: {analysis.model}
            </p>
          </div>
        </div>
      )}

      {/* Collapsed State */}
      {analysis && !isExpanded && !loading && (
        <div className="py-2">
          <p className="text-gray-600 text-sm italic">
            Code analysis available - Click to expand
          </p>
        </div>
      )}

      {/* No Analysis State */}
      {!analysis && !loading && !error && (
        <div className="text-center py-6">
          <Code2 className="w-12 h-12 text-blue-300 mx-auto mb-3" />
          <p className="text-gray-600 font-medium">No code analysis yet</p>
          <p className="text-sm text-gray-500 mt-1">
            Click "Analyze Code" to get AI insights about their technical work
          </p>
        </div>
      )}
    </div>
  );
}

