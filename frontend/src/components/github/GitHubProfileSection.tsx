import React from 'react';
import Card from '../common/Card';
import { EcosystemBadges } from './EcosystemBadges';

interface GitHubProfile {
  github_username: string;
  github_name?: string;
  bio?: string;
  github_location?: string;
  github_company?: string;
  github_email?: string;
  blog?: string;
  twitter_username?: string;
  followers: number;
  following: number;
  public_repos: number;
  avatar_url?: string;
  ecosystem_tags?: string[];
  importance_score?: number;
  discovered_at?: string;
  // PR enrichment fields
  is_pro_account?: boolean;
  total_merged_prs?: number;
  total_stars_earned?: number;
  total_lines_contributed?: number;
  enriched_at?: string;
}

interface GitHubProfileSectionProps {
  github: GitHubProfile;
}

export const GitHubProfileSection: React.FC<GitHubProfileSectionProps> = ({ github }) => {
  const formatNumber = (num: number) => {
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}k`;
    }
    return num.toString();
  };

  return (
    <Card className="p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start gap-6">
        {/* Avatar */}
        {github.avatar_url && (
          <div className="flex-shrink-0">
            <img
              src={github.avatar_url}
              alt={github.github_username}
              className="w-20 h-20 rounded-full border-2 border-gray-200"
            />
          </div>
        )}

        {/* Main Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="flex items-center gap-3">
                <h3 className="text-2xl font-bold text-gray-900">
                  {github.github_name || github.github_username}
                </h3>
                <a
                  href={`https://github.com/${github.github_username}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path fillRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.167 22 16.418 22 12c0-5.523-4.477-10-10-10z" clipRule="evenodd" />
                  </svg>
                  @{github.github_username}
                </a>
                {github.is_pro_account && (
                  <span className="ml-2 px-2 py-1 bg-purple-100 text-purple-700 text-xs font-medium rounded-full">
                    PRO
                  </span>
                )}
              </div>
              {github.bio && (
                <p className="text-gray-700 mt-2 max-w-2xl">{github.bio}</p>
              )}
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">{formatNumber(github.followers)}</div>
              <div className="text-sm text-gray-600">Followers</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">{formatNumber(github.following)}</div>
              <div className="text-sm text-gray-600">Following</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">{formatNumber(github.public_repos)}</div>
              <div className="text-sm text-gray-600">Repositories</div>
            </div>
          </div>

          {/* Career Highlights - PR Enrichment Data */}
          {(github.total_merged_prs || github.total_stars_earned || github.total_lines_contributed) && (
            <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Career Highlights</h4>
              <div className="grid grid-cols-3 gap-3">
                {github.total_merged_prs && github.total_merged_prs > 0 && (
                  <div className="text-center">
                    <div className="text-xl font-bold text-green-600">
                      {formatNumber(github.total_merged_prs)}
                    </div>
                    <div className="text-xs text-gray-600">Merged PRs</div>
                  </div>
                )}
                {github.total_stars_earned && github.total_stars_earned > 0 && (
                  <div className="text-center">
                    <div className="text-xl font-bold text-yellow-600">
                      ⭐ {formatNumber(github.total_stars_earned)}
                    </div>
                    <div className="text-xs text-gray-600">Stars Earned</div>
                  </div>
                )}
                {github.total_lines_contributed && github.total_lines_contributed > 0 && (
                  <div className="text-center">
                    <div className="text-xl font-bold text-blue-600">
                      {formatNumber(github.total_lines_contributed)}
                    </div>
                    <div className="text-xs text-gray-600">Lines of Code</div>
                  </div>
                )}
              </div>
              {github.enriched_at && (
                <div className="mt-2 text-xs text-gray-500 text-center">
                  Updated {new Date(github.enriched_at).toLocaleDateString()}
                </div>
              )}
            </div>
          )}

          {/* Additional Info */}
          <div className="space-y-2 text-sm">
            {github.github_company && (
              <div className="flex items-center gap-2 text-gray-700">
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <span>{github.github_company}</span>
              </div>
            )}
            {github.github_location && (
              <div className="flex items-center gap-2 text-gray-700">
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span>{github.github_location}</span>
              </div>
            )}
            {github.blog && (
              <div className="flex items-center gap-2 text-gray-700">
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
                <a href={github.blog.startsWith('http') ? github.blog : `https://${github.blog}`} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                  {github.blog}
                </a>
              </div>
            )}
            {github.twitter_username && (
              <div className="flex items-center gap-2 text-gray-700">
                <svg className="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z" />
                </svg>
                <a href={`https://twitter.com/${github.twitter_username}`} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                  @{github.twitter_username}
                </a>
              </div>
            )}
          </div>

          {/* Ecosystem Tags */}
          {github.ecosystem_tags && github.ecosystem_tags.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm font-semibold text-gray-700">Ecosystems:</span>
              </div>
              <EcosystemBadges ecosystems={github.ecosystem_tags} />
            </div>
          )}

          {/* Importance Score */}
          {github.importance_score && github.importance_score > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-gray-700">Importance Score:</span>
                <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-xs">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all"
                    style={{ width: `${Math.min(github.importance_score * 10, 100)}%` }}
                  />
                </div>
                <span className="text-sm text-gray-600">{github.importance_score.toFixed(2)}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};

export default GitHubProfileSection;

