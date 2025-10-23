import { useState } from 'react';
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
import AISummaryCard from '../components/ai/AISummaryCard';
import CodeAnalysisCard from '../components/ai/CodeAnalysisCard';
import AskAIChat from '../components/ai/AskAIChat';

export default function ProfilePage() {
  const { personId } = useParams<{ personId: string }>();
  const navigate = useNavigate();
  
  // AI State
  const [aiSummary, setAiSummary] = useState<any>(null);
  const [codeAnalysis, setCodeAnalysis] = useState<any>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const { data: profile, isLoading, error } = useQuery({
    queryKey: ['profile', personId],
    queryFn: () => api.getPersonProfile(personId!),
    enabled: !!personId,
  });

  // AI Handlers
  const handleGenerateSummary = async () => {
    if (!personId) return;
    
    setSummaryLoading(true);
    setSummaryError(null);
    
    try {
      const result = await api.generateProfileSummary(personId);
      setAiSummary(result.summary);
    } catch (err) {
      setSummaryError(err instanceof Error ? err.message : 'Failed to generate summary');
    } finally {
      setSummaryLoading(false);
    }
  };

  const handleAnalyzeCode = async () => {
    if (!personId) return;
    
    setAnalysisLoading(true);
    setAnalysisError(null);
    
    try {
      const result = await api.analyzeCodeQuality(personId);
      setCodeAnalysis(result.analysis);
    } catch (err) {
      setAnalysisError(err instanceof Error ? err.message : 'Failed to analyze code');
    } finally {
      setAnalysisLoading(false);
    }
  };

  const handleAskAI = async (
    question: string,
    history: Array<{ role: string; content: string }>
  ): Promise<string> => {
    if (!personId) throw new Error('No person ID');
    
    try {
      const result = await api.askAI(personId, question, history);
      return result.answer;
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Failed to get answer');
    }
  };

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
          {/* AI Career Intelligence - NEW WOW MOMENT */}
          <AISummaryCard
            personId={profile.person.person_id}
            summary={aiSummary}
            onGenerate={handleGenerateSummary}
            loading={summaryLoading}
            error={summaryError}
          />

          {/* How to Reach */}
          <HowToReach targetPersonId={profile.person.person_id} />

          {/* Employment Timeline */}
          <EmploymentTimeline employment={profile.employment} />

          {/* AI Code Analysis - Next to GitHub */}
          {profile.github_profile && (
            <CodeAnalysisCard
              personId={profile.person.person_id}
              analysis={codeAnalysis}
              onGenerate={handleAnalyzeCode}
              loading={analysisLoading}
              error={analysisError}
              hasGitHub={!!profile.github_profile}
            />
          )}

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

      {/* Floating Ask AI Chat */}
      <AskAIChat
        personId={profile.person.person_id}
        personName={profile.person.full_name}
        onAsk={handleAskAI}
      />
    </div>
  );
}

