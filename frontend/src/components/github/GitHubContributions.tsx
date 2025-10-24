import React, { useState } from 'react';
import Card from '../common/Card';

interface Contribution {
  repo_name: string;
  repo_full_name: string;
  stars?: number;
  language?: string;
  description?: string;
  contribution_count: number;
  first_contributed?: string;
  // PR enrichment fields
  merged_pr_count?: number;
  pr_count?: number;
  open_pr_count?: number;
  lines_added?: number;
  lines_deleted?: number;
  contribution_quality_score?: number;
  last_merged_pr_date?: string;
}

interface GitHubContributionsProps {
  contributions: Contribution[];
  githubUsername?: string;
  maxDisplay?: number;
}

export const GitHubContributions: React.FC<GitHubContributionsProps> = ({
  contributions,
  githubUsername,
  maxDisplay = 10,
}) => {
  const [showAll, setShowAll] = useState(false);
  const [sortBy, setSortBy] = useState<'contributions' | 'stars' | 'quality'>('quality');

  if (!contributions || contributions.length === 0) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Repository Contributions</h3>
        <div className="text-center py-8 text-gray-500">
          <svg className="w-12 h-12 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
          </svg>
          <p>No contribution data available</p>
        </div>
      </Card>
    );
  }

  // Sort contributions
  const sortedContributions = [...contributions].sort((a, b) => {
    if (sortBy === 'contributions') {
      return b.contribution_count - a.contribution_count;
    } else if (sortBy === 'stars') {
      return (b.stars || 0) - (a.stars || 0);
    } else { // quality
      // Sort by merged PRs first, then quality score, then contributions
      const aQuality = (a.merged_pr_count || 0) * 100 + (a.contribution_quality_score || 0);
      const bQuality = (b.merged_pr_count || 0) * 100 + (b.contribution_quality_score || 0);
      return bQuality - aQuality;
    }
  });

  const displayedContributions = showAll 
    ? sortedContributions 
    : sortedContributions.slice(0, maxDisplay);

  const totalCommits = contributions.reduce((sum, c) => sum + c.contribution_count, 0);
  const totalStars = contributions.reduce((sum, c) => sum + (c.stars || 0), 0);

  const formatNumber = (num: number) => {
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}k`;
    }
    return num.toString();
  };

  const getLanguageColor = (language?: string) => {
    const colors: Record<string, string> = {
      'JavaScript': 'bg-yellow-400',
      'TypeScript': 'bg-blue-600',
      'Python': 'bg-blue-500',
      'Rust': 'bg-orange-600',
      'Go': 'bg-cyan-500',
      'Java': 'bg-red-600',
      'C++': 'bg-pink-500',
      'Ruby': 'bg-red-500',
      'PHP': 'bg-purple-500',
      'Solidity': 'bg-gray-700',
    };
    return colors[language || ''] || 'bg-gray-400';
  };

  return (
    <Card className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Repository Contributions</h3>
          <p className="text-sm text-gray-600 mt-1">
            {contributions.length} repositories • {formatNumber(totalCommits)} total commits • {formatNumber(totalStars)} ⭐ across repos
          </p>
        </div>
        
        {/* Sort Controls */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Sort by:</span>
          <button
            onClick={() => setSortBy('quality')}
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              sortBy === 'quality'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Quality
          </button>
          <button
            onClick={() => setSortBy('contributions')}
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              sortBy === 'contributions'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Commits
          </button>
          <button
            onClick={() => setSortBy('stars')}
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              sortBy === 'stars'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Stars
          </button>
        </div>
      </div>

      {/* Contributions List */}
      <div className="space-y-3">
        {displayedContributions.map((contribution, index) => (
          <div
            key={contribution.repo_name}
            className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            {/* Rank */}
            <div className="flex-shrink-0 w-8 text-center">
              <span className={`text-lg font-bold ${
                index === 0 ? 'text-yellow-600' :
                index === 1 ? 'text-gray-500' :
                index === 2 ? 'text-orange-600' :
                'text-gray-400'
              }`}>
                #{index + 1}
              </span>
            </div>

            {/* Repo Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <a
                  href={
                    githubUsername 
                      ? `https://github.com/${contribution.repo_full_name || contribution.repo_name}/commits?author=${githubUsername}`
                      : `https://github.com/${contribution.repo_full_name || contribution.repo_name}`
                  }
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 font-medium truncate"
                >
                  {contribution.repo_full_name || contribution.repo_name}
                </a>
                {contribution.language && (
                  <span className="flex items-center gap-1 text-xs text-gray-600">
                    <span className={`w-3 h-3 rounded-full ${getLanguageColor(contribution.language)}`} />
                    {contribution.language}
                  </span>
                )}
              </div>
              
              {contribution.description && (
                <p className="text-sm text-gray-600 line-clamp-2 mb-2">
                  {contribution.description}
                </p>
              )}
              
              <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500">
                <span className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                  </svg>
                  {formatNumber(contribution.contribution_count)} commits
                </span>
                {contribution.merged_pr_count && contribution.merged_pr_count > 0 && (
                  <span className="flex items-center gap-1 text-green-600 font-medium">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {contribution.merged_pr_count} merged PR{contribution.merged_pr_count !== 1 ? 's' : ''}
                  </span>
                )}
                {contribution.stars && contribution.stars > 0 && (
                  <span className="flex items-center gap-1">
                    ⭐ {formatNumber(contribution.stars)}
                  </span>
                )}
                {contribution.lines_added && contribution.lines_added > 0 && (
                  <span className="text-xs text-emerald-600">
                    +{formatNumber(contribution.lines_added)} lines
                  </span>
                )}
                {contribution.contribution_quality_score && contribution.contribution_quality_score > 0 && (
                  <span className="flex items-center gap-1 text-xs font-medium text-purple-600">
                    Quality: {contribution.contribution_quality_score.toFixed(0)}/100
                  </span>
                )}
                {contribution.first_contributed && (
                  <span className="flex items-center gap-1 text-xs">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Since {new Date(contribution.first_contributed).toLocaleDateString()}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Show More/Less Button */}
      {contributions.length > maxDisplay && (
        <div className="mt-6 text-center">
          <button
            onClick={() => setShowAll(!showAll)}
            className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors"
          >
            {showAll ? (
              <>
                <span>Show less</span>
                <svg className="w-4 h-4 inline ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
              </>
            ) : (
              <>
                <span>Show all {contributions.length} repositories</span>
                <svg className="w-4 h-4 inline ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </>
            )}
          </button>
        </div>
      )}
    </Card>
  );
};

export default GitHubContributions;

