import type { GitHubProfile, GitHubContribution } from '../../types';
import { Search, ExternalLink, GitPullRequest, GitCommit } from 'lucide-react';
import Card from '../common/Card';
import Badge from '../common/Badge';

interface GitHubActivityProps {
  githubProfile?: GitHubProfile;
  contributions: GitHubContribution[];
}

export default function GitHubActivity({ githubProfile, contributions }: GitHubActivityProps) {
  if (!githubProfile) {
    return (
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">GitHub Activity</h2>
        <p className="text-gray-500">No GitHub profile linked</p>
      </Card>
    );
  }

  // Organize contributions by quality
  const officialRepos = contributions.filter(c => !c.is_fork && c.stars > 50);
  const standardContribs = contributions.filter(c => !c.is_fork && c.stars <= 50);
  const forkContribs = contributions.filter(c => c.is_fork);

  return (
    <div className="space-y-6">
      {/* Expert Sourcer's Verification Checklist */}
      <Card className="bg-gradient-to-br from-blue-50 to-purple-50 border-2 border-blue-200">
        <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
          <Search className="w-5 h-5 mr-2 text-blue-600" />
          Expert Sourcer's Verification Checklist
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-700">
          <div className="flex items-start">
            <span className="text-blue-600 mr-2 font-bold">✓</span>
            <span>Click commit links to verify merged status</span>
          </div>
          <div className="flex items-start">
            <span className="text-blue-600 mr-2 font-bold">✓</span>
            <span>Review actual code changes, not just docs</span>
          </div>
          <div className="flex items-start">
            <span className="text-blue-600 mr-2 font-bold">✓</span>
            <span>For forks, verify if merged to upstream</span>
          </div>
          <div className="flex items-start">
            <span className="text-blue-600 mr-2 font-bold">✓</span>
            <span>Check for community feedback on PRs</span>
          </div>
        </div>
      </Card>

      {/* Main GitHub Card */}
      <Card>
        <div className="flex items-start justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">GitHub Activity</h2>
          <a
            href={`https://github.com/${githubProfile.github_username}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-primary-600 hover:text-primary-700 hover:underline flex items-center"
          >
            View on GitHub <ExternalLink className="w-4 h-4 ml-1" />
          </a>
        </div>

      {/* GitHub Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-2xl font-bold text-gray-900">{githubProfile.followers}</p>
          <p className="text-sm text-gray-600">Followers</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-2xl font-bold text-gray-900">{githubProfile.following}</p>
          <p className="text-sm text-gray-600">Following</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-2xl font-bold text-gray-900">{githubProfile.public_repos}</p>
          <p className="text-sm text-gray-600">Public Repos</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-2xl font-bold text-gray-900">{contributions.length}</p>
          <p className="text-sm text-gray-600">Contributions</p>
        </div>
      </div>

      {/* Enhanced Stats (Phase 2 Data) */}
      {githubProfile.total_merged_prs !== undefined && githubProfile.total_merged_prs > 0 && (
        <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-green-50 to-green-100 border border-green-200 rounded-lg p-4">
            <p className="text-2xl font-bold text-green-900">{githubProfile.total_merged_prs}</p>
            <p className="text-sm text-green-700 font-medium">✓ Merged Pull Requests</p>
            <p className="text-xs text-green-600 mt-1">Confirmed code contributions</p>
          </div>
          
          {githubProfile.total_lines_contributed !== undefined && githubProfile.total_lines_contributed > 0 && (
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 rounded-lg p-4">
              <p className="text-2xl font-bold text-blue-900">{githubProfile.total_lines_contributed.toLocaleString()}</p>
              <p className="text-sm text-blue-700 font-medium">Lines of Code</p>
              <p className="text-xs text-blue-600 mt-1">Career total contributed</p>
            </div>
          )}
          
          {githubProfile.is_pro_account && (
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200 rounded-lg p-4">
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <p className="text-lg font-bold text-purple-900">✓ GitHub Pro</p>
                  <p className="text-xs text-purple-600 mt-1">Has private repositories</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Bio */}
      {githubProfile.bio && (
        <div className="mb-6">
          <p className="text-gray-700">{githubProfile.bio}</p>
        </div>
      )}

        {/* High-Quality Contributions (Official Repos) */}
        {officialRepos.length > 0 && (
          <div className="mb-8">
            <div className="flex items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <span className="text-2xl mr-2">🌟</span>
                High-Quality Contributions ({officialRepos.length})
              </h3>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Contributions to official repositories with significant community engagement (50+ stars)
            </p>
            <div className="space-y-3">
              {officialRepos.map((contrib) => renderContribution(contrib, githubProfile.github_username, 'success'))}
            </div>
          </div>
        )}

        {/* Standard Contributions */}
        {standardContribs.length > 0 && (
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <span className="text-2xl mr-2">💼</span>
              Other Contributions ({standardContribs.length})
            </h3>
            <div className="space-y-3">
              {standardContribs.slice(0, 5).map((contrib) => renderContribution(contrib, githubProfile.github_username, 'default'))}
            </div>
          </div>
        )}

        {/* Fork Contributions - Needs Verification */}
        {forkContribs.length > 0 && (
          <div>
            <div className="flex items-center mb-3">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <span className="text-2xl mr-2">🔱</span>
                Fork Contributions ({forkContribs.length})
              </h3>
            </div>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-yellow-800 flex items-start">
                <span className="mr-2">ℹ️</span>
                <span>
                  <strong>Verification Needed:</strong> These are forks. Click "View Commits" or "View PRs" to verify if changes were merged to the upstream/official repository.
                </span>
              </p>
            </div>
            <div className="space-y-3">
              {forkContribs.slice(0, 5).map((contrib) => renderContribution(contrib, githubProfile.github_username, 'warning'))}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

// Helper function to render a single contribution
function renderContribution(contrib: any, githubUsername: string, quality: 'success' | 'default' | 'warning') {
  const repoUrl = `https://github.com/${contrib.repo_full_name}`;
  const commitsUrl = `https://github.com/${contrib.repo_full_name}/commits?author=${githubUsername}`;
  const prsUrl = `https://github.com/${contrib.repo_full_name}/pulls?q=author:${githubUsername}`;
  
  return (
    <Card
      key={contrib.contribution_id}
      hover
      padding="md"
      className="border-l-4"
      style={{
        borderLeftColor: quality === 'success' ? '#10b981' : quality === 'warning' ? '#f59e0b' : '#6b7280'
      }}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Repository Name with Link */}
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <a
              href={repoUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-gray-900 hover:text-primary-600 hover:underline text-lg"
            >
              {contrib.repo_name}
            </a>
            {contrib.is_fork && (
              <Badge variant="warning" size="sm">
                Fork - Verify Merge
              </Badge>
            )}
            {quality === 'success' && (
              <Badge variant="success" size="sm">
                High Quality
              </Badge>
            )}
            {/* Phase 2: Show merged PR count if available */}
            {contrib.merged_pr_count !== undefined && contrib.merged_pr_count > 0 && (
              <Badge variant="success" size="sm">
                ✓ {contrib.merged_pr_count} Merged PR{contrib.merged_pr_count > 1 ? 's' : ''}
              </Badge>
            )}
            {/* Phase 2: Show quality score if available */}
            {contrib.contribution_quality_score !== undefined && contrib.contribution_quality_score !== null && (
              <Badge 
                variant={contrib.contribution_quality_score >= 70 ? 'success' : contrib.contribution_quality_score >= 40 ? 'info' : 'default'}
                size="sm"
              >
                Score: {contrib.contribution_quality_score.toFixed(0)}/100
              </Badge>
            )}
          </div>

          {/* Owner Organization/Company */}
          {contrib.owner_company_name && (
            <div className="mb-2">
              <Badge variant="info" size="sm">
                {contrib.owner_company_name}
              </Badge>
            </div>
          )}

          {/* Description */}
          {contrib.description && (
            <p className="mt-2 text-sm text-gray-600 line-clamp-2">
              {contrib.description}
            </p>
          )}

          {/* Stats Row */}
          <div className="mt-3 flex items-center flex-wrap gap-4 text-sm text-gray-500">
            {contrib.language && (
              <span className="flex items-center">
                <span className="w-3 h-3 rounded-full bg-primary-500 mr-1"></span>
                {contrib.language}
              </span>
            )}
            <span>⭐ {contrib.stars.toLocaleString()}</span>
            <span>🔱 {contrib.forks.toLocaleString()}</span>
            <span className="font-medium text-gray-700">
              {contrib.contribution_count} commit{contrib.contribution_count !== 1 ? 's' : ''}
            </span>
            {/* Phase 2: Show lines of code if available */}
            {contrib.lines_added !== undefined && contrib.lines_added > 0 && (
              <span className="font-medium text-green-700">
                +{contrib.lines_added.toLocaleString()} lines
              </span>
            )}
          </div>

          {/* Action Links */}
          <div className="mt-3 flex items-center gap-4">
            <a
              href={commitsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary-600 hover:text-primary-700 hover:underline font-medium flex items-center"
            >
              <GitCommit className="w-4 h-4 mr-1" />
              View All Commits
            </a>
            <a
              href={prsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary-600 hover:text-primary-700 hover:underline font-medium flex items-center"
            >
              <GitPullRequest className="w-4 h-4 mr-1" />
              View Pull Requests
            </a>
          </div>
        </div>
      </div>
    </Card>
  );
}

