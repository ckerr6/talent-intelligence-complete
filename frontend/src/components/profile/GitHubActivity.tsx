import type { GitHubProfile, GitHubContribution } from '../../types';

interface GitHubActivityProps {
  githubProfile?: GitHubProfile;
  contributions: GitHubContribution[];
}

export default function GitHubActivity({ githubProfile, contributions }: GitHubActivityProps) {
  if (!githubProfile) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">GitHub Activity</h2>
        <p className="text-gray-500">No GitHub profile linked</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-start justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">GitHub Activity</h2>
        <a
          href={`https://github.com/${githubProfile.github_username}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-primary-600 hover:text-primary-700 hover:underline"
        >
          View on GitHub →
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

      {/* Bio */}
      {githubProfile.bio && (
        <div className="mb-6">
          <p className="text-gray-700">{githubProfile.bio}</p>
        </div>
      )}

      {/* Top Repositories */}
      {contributions.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Top Contributions
          </h3>
          <div className="space-y-3">
            {contributions.slice(0, 10).map((contrib) => {
              // Construct GitHub URLs
              const repoUrl = `https://github.com/${contrib.repo_full_name}`;
              const contributorUrl = `https://github.com/${contrib.repo_full_name}/commits?author=${githubProfile.github_username}`;
              
              return (
                <div
                  key={contrib.contribution_id}
                  className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* Repository Name with Link */}
                      <div className="flex items-center gap-2 mb-1">
                        <a
                          href={repoUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-medium text-gray-900 hover:text-primary-600 hover:underline"
                        >
                          {contrib.repo_name}
                        </a>
                        {contrib.is_fork && (
                          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                            Fork
                          </span>
                        )}
                      </div>

                      {/* Owner Organization/Company */}
                      {contrib.owner_company_name && (
                        <div className="mb-2">
                          <span className="text-sm text-gray-600">
                            {contrib.owner_company_name} repository
                          </span>
                        </div>
                      )}

                      {/* Description */}
                      {contrib.description && (
                        <p className="mt-1 text-sm text-gray-600 line-clamp-2">
                          {contrib.description}
                        </p>
                      )}

                      {/* Stats Row */}
                      <div className="mt-2 flex items-center space-x-4 text-sm text-gray-500">
                        {contrib.language && (
                          <span className="flex items-center">
                            <span className="w-3 h-3 rounded-full bg-primary-500 mr-1"></span>
                            {contrib.language}
                          </span>
                        )}
                        <span>⭐ {contrib.stars.toLocaleString()}</span>
                        <span>🔱 {contrib.forks.toLocaleString()}</span>
                        <a
                          href={contributorUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-medium text-primary-600 hover:text-primary-700 hover:underline"
                        >
                          {contrib.contribution_count} commit{contrib.contribution_count !== 1 ? 's' : ''} →
                        </a>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

