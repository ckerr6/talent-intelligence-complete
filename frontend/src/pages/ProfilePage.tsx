import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ProfileHeader from '../components/profile/ProfileHeader';
import EmploymentTimeline from '../components/profile/EmploymentTimeline';
import ContactInfo from '../components/profile/ContactInfo';
import GitHubActivity from '../components/profile/GitHubActivity';
import HowToReach from '../components/profile/HowToReach';
import QuickActions from '../components/profile/QuickActions';

export default function ProfilePage() {
  const { personId } = useParams<{ personId: string }>();
  const navigate = useNavigate();

  const { data: profile, isLoading, error } = useQuery({
    queryKey: ['profile', personId],
    queryFn: () => api.getPersonProfile(personId!),
    enabled: !!personId,
  });

  if (isLoading) {
    return <LoadingSpinner message="Loading profile..." />;
  }

  if (error || !profile || !profile.person) {
    return (
      <div className="space-y-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-red-900 mb-2">Error Loading Profile</h2>
          <p className="text-red-700">
            {error instanceof Error ? error.message : 'Unable to load profile. Please try again.'}
          </p>
          <button
            onClick={() => navigate('/search')}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            ← Back to Search
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="text-primary-600 hover:text-primary-700 flex items-center space-x-1"
      >
        <span>←</span>
        <span>Back</span>
      </button>

      {/* Profile Header */}
      <ProfileHeader person={profile.person} />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* How to Reach - THE WOW MOMENT */}
          <HowToReach targetPersonId={profile.person.person_id} />

          {/* Employment Timeline */}
          <EmploymentTimeline employment={profile.employment} />

          {/* GitHub Activity */}
          <GitHubActivity
            githubProfile={profile.github_profile}
            contributions={profile.github_contributions}
          />
        </div>

        {/* Right Column - Sidebar */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <QuickActions
            personId={profile.person.person_id}
            personName={profile.person.full_name}
          />

          {/* Contact Info */}
          <ContactInfo
            emails={profile.emails}
            githubProfile={profile.github_profile}
            linkedinUrl={profile.person.linkedin_url}
          />

          {/* Network Stats */}
          {profile.network_stats && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Network</h2>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Total Connections</span>
                  <span className="font-semibold text-gray-900">
                    {profile.network_stats.total_connections}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Co-workers</span>
                  <span className="font-semibold text-gray-900">
                    {profile.network_stats.coworker_connections}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">GitHub Collaborators</span>
                  <span className="font-semibold text-gray-900">
                    {profile.network_stats.github_connections}
                  </span>
                </div>
              </div>

              {profile.network_stats.top_companies.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-sm font-medium text-gray-700 mb-2">Top Companies</p>
                  <div className="space-y-1">
                    {profile.network_stats.top_companies.slice(0, 5).map((company, index) => (
                      <div key={index} className="text-sm text-gray-600">
                        {company.company_name} ({company.connection_count})
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <button
                onClick={() => navigate(`/network/${profile.person.person_id}`)}
                className="mt-4 w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
              >
                Explore Network Graph →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

