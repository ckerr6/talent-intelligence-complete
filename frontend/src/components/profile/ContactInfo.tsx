import type { Email, GitHubProfile } from '../../types';

interface ContactInfoProps {
  emails: Email[];
  githubProfile?: GitHubProfile;
  linkedinUrl?: string;
}

export default function ContactInfo({ emails, githubProfile, linkedinUrl }: ContactInfoProps) {
  const hasAnyContact = emails.length > 0 || githubProfile || linkedinUrl;

  if (!hasAnyContact) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Contact Information</h2>
        <p className="text-gray-500">No contact information available</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Contact Information</h2>
      
      <div className="space-y-4">
        {/* Emails */}
        {emails.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Email Addresses</h3>
            <div className="space-y-2">
              {emails.map((email, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <a
                    href={`mailto:${email.email}`}
                    className="text-primary-600 hover:text-primary-700 hover:underline"
                  >
                    {email.email}
                  </a>
                  {email.is_primary && (
                    <span className="px-2 py-0.5 bg-primary-100 text-primary-700 text-xs font-medium rounded">
                      Primary
                    </span>
                  )}
                  {email.email_type && (
                    <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                      {email.email_type}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Social Links */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">Social Profiles</h3>
          <div className="flex flex-col space-y-2">
            {linkedinUrl && (
              <a
                href={linkedinUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center space-x-2 text-blue-600 hover:text-blue-700 hover:underline"
              >
                <span className="text-lg">in</span>
                <span>LinkedIn Profile</span>
              </a>
            )}
            
            {githubProfile && (
              <a
                href={`https://github.com/${githubProfile.github_username}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center space-x-2 text-gray-900 hover:text-gray-700 hover:underline"
              >
                <span className="text-lg">⚡</span>
                <span>GitHub: @{githubProfile.github_username}</span>
              </a>
            )}

            {githubProfile?.twitter_username && (
              <a
                href={`https://twitter.com/${githubProfile.twitter_username}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center space-x-2 text-blue-400 hover:text-blue-500 hover:underline"
              >
                <span className="text-lg">🐦</span>
                <span>Twitter: @{githubProfile.twitter_username}</span>
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

