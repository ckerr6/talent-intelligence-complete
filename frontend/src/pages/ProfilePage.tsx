import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, AlertCircle } from 'lucide-react';
import api from '../services/api';
import ProfileHero from '../components/profile/ProfileHero';
import TabNavigation from '../components/profile/TabNavigation';
import StickyActionBar from '../components/profile/StickyActionBar';
import EmploymentTimeline from '../components/profile/EmploymentTimeline';
import ContactInfo from '../components/profile/ContactInfo';
import GitHubActivity from '../components/profile/GitHubActivity';
import HowToReachEnhanced from '../components/profile/HowToReachEnhanced';
import QuickActions from '../components/profile/QuickActions';
import AISummaryCard from '../components/ai/AISummaryCard';
import CodeAnalysisCard from '../components/ai/CodeAnalysisCard';
import FloatingAIAssistant from '../components/ai/FloatingAIAssistant';
import GitHubProfileSection from '../components/github/GitHubProfileSection';
import GitHubContributions from '../components/github/GitHubContributions';
import NetworkStatsCard from '../components/network/NetworkStatsCard';
import CollaboratorsSection from '../components/network/CollaboratorsSection';
import NotesSection from '../components/notes/NotesSection';
import AddToListModal from '../components/lists/AddToListModal';
import { SkeletonProfile } from '../components/common/Skeleton';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import EmptyState from '../components/common/EmptyState';

export default function ProfilePage() {
  const { personId } = useParams<{ personId: string }>();
  const navigate = useNavigate();
  
  // Tab State
  const [activeTab, setActiveTab] = useState('overview');
  
  // Modal State
  const [showAddToListModal, setShowAddToListModal] = useState(false);
  
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


  if (isLoading) {
    return (
      <div className="space-y-4">
        <Button
          variant="ghost"
          onClick={() => navigate(-1)}
          icon={<ArrowLeft className="w-4 h-4" />}
        >
          Back
        </Button>
        <SkeletonProfile />
      </div>
    );
  }

  if (error || !profile || !profile.person) {
    return (
      <div className="space-y-4">
        <Button
          variant="ghost"
          onClick={() => navigate(-1)}
          icon={<ArrowLeft className="w-4 h-4" />}
        >
          Back
        </Button>
        <Card>
          <EmptyState
            icon={<AlertCircle className="w-8 h-8" />}
            title="Profile Not Found"
            description={error instanceof Error ? error.message : 'Unable to load profile. Please try again.'}
            action={
              <Button onClick={() => navigate('/search')}>
                Back to Search
              </Button>
            }
          />
        </Card>
      </div>
    );
  }

  // Calculate badge counts for tabs  
  const githubCount = profile.github_contributions?.length || 0;
  const networkCount = profile.network_stats?.total_connections || 0;

  return (
    <div className="space-y-6 pb-12">
      {/* Back button */}
      <Button
        variant="ghost"
        onClick={() => navigate(-1)}
        icon={<ArrowLeft className="w-4 h-4" />}
      >
        Back
      </Button>

      {/* NEW: Profile Hero Section */}
      <ProfileHero
        person={{
          person_id: profile.person.person_id,
          full_name: profile.person.full_name,
          headline: profile.person.headline,
          location: profile.person.location,
          linkedin_url: profile.person.linkedin_url,
          refreshed_at: profile.person.refreshed_at,
          has_email: profile.emails && profile.emails.length > 0,
          has_github: !!profile.github_profile,
          github_username: profile.github_profile?.github_username
        }}
        matchScore={85} // TODO: Calculate real match score
      />

      {/* NEW: Sticky Action Bar (appears on scroll) */}
      <StickyActionBar
        person={{
          person_id: profile.person.person_id,
          full_name: profile.person.full_name,
          headline: profile.person.headline,
          location: profile.person.location,
          linkedin_url: profile.person.linkedin_url,
          refreshed_at: profile.person.refreshed_at,
          has_email: profile.emails && profile.emails.length > 0,
          has_github: !!profile.github_profile,
          github_username: profile.github_profile?.github_username
        } as any}
      />

      {/* NEW: Tab Navigation */}
      <TabNavigation
        activeTab={activeTab}
        onTabChange={setActiveTab}
        tabs={[
          { id: 'overview', label: 'Overview' },
          { id: 'experience', label: 'Experience', badge: profile.employment?.length },
          { id: 'code', label: 'Code', badge: githubCount },
          { id: 'network', label: 'Network', badge: networkCount },
          { id: 'ai-insights', label: 'AI Insights', badge: aiSummary ? 1 : undefined }
        ]}
      />

      {/* Tab Content */}
      <div className="min-h-[600px]">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              {/* AI Summary - Prominent on Overview */}
              <AISummaryCard
                personId={profile.person.person_id}
                summary={aiSummary}
                onGenerate={handleGenerateSummary}
                loading={summaryLoading}
                error={summaryError}
              />

              {/* How to Reach */}
              <HowToReachEnhanced profile={profile} />

              {/* Quick Stats */}
              <Card hierarchy="secondary">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Stats</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-2xl font-bold text-indigo-600">
                      {profile.employment?.length || 0}
                    </div>
                    <div className="text-sm text-gray-600">Positions</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-cyan-600">
                      {githubCount}
                    </div>
                    <div className="text-sm text-gray-600">Contributions</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-emerald-600">
                      {profile.emails?.length || 0}
                    </div>
                    <div className="text-sm text-gray-600">Email{profile.emails?.length !== 1 ? 's' : ''}</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-amber-600">
                      {networkCount}
                    </div>
                    <div className="text-sm text-gray-600">Connections</div>
                  </div>
                </div>
              </Card>

              {/* Notes & Context */}
              <NotesSection personId={profile.person.person_id} />
            </div>

            <div className="space-y-6">
              {/* Contact Info */}
              <ContactInfo
                emails={profile.emails}
                githubProfile={profile.github_profile}
                linkedinUrl={profile.person.linkedin_url}
              />

              {/* Add to List Card */}
              <Card className="p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Manage Candidate</h3>
                <button
                  onClick={() => setShowAddToListModal(true)}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                  Add to List
                </button>
              </Card>

              {/* Quick Actions */}
              <QuickActions
                personId={profile.person.person_id}
                personName={profile.person.full_name}
              />
            </div>
          </div>
        )}

        {/* Experience Tab */}
        {activeTab === 'experience' && (
          <div className="max-w-4xl">
            <EmploymentTimeline employment={profile.employment} />
          </div>
        )}

        {/* Code Tab */}
        {activeTab === 'code' && (
          <div className="space-y-6">
            {profile.github_profile ? (
              <>
                {/* GitHub Profile Section */}
                <GitHubProfileSection github={profile.github_profile} />
                
                {/* AI Code Analysis */}
                <CodeAnalysisCard
                  personId={profile.person.person_id}
                  analysis={codeAnalysis}
                  onGenerate={handleAnalyzeCode}
                  loading={analysisLoading}
                  error={analysisError}
                  hasGitHub={true}
                />
                
                {/* GitHub Contributions */}
                {profile.github_contributions && profile.github_contributions.length > 0 && (
                  <GitHubContributions 
                    contributions={profile.github_contributions}
                    githubUsername={profile.github_profile.github_username}
                  />
                )}
              </>
            ) : (
              <Card>
                <EmptyState
                  icon={
                    <svg className="w-12 h-12" fill="currentColor" viewBox="0 0 24 24">
                      <path fillRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.167 22 16.418 22 12c0-5.523-4.477-10-10-10z" clipRule="evenodd" />
                    </svg>
                  }
                  title="No GitHub Profile"
                  description="This person doesn't have a GitHub profile linked yet."
                />
              </Card>
            )}
          </div>
        )}

        {/* Network Tab */}
        {activeTab === 'network' && (
          <div className="space-y-6">
            {/* Network Stats Card */}
            <NetworkStatsCard personId={profile.person.person_id} />
            
            {/* Collaborators Section */}
            <CollaboratorsSection personId={profile.person.person_id} />
            
            {/* Optional: Link to full network graph */}
            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Interactive Network Graph</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Explore visual network connections and find connection paths
                  </p>
                </div>
                <Button
                  onClick={() => navigate(`/network/${profile.person.person_id}`)}
                  className="whitespace-nowrap"
                >
                  Open Graph →
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* AI Insights Tab */}
        {activeTab === 'ai-insights' && (
          <div className="max-w-4xl space-y-6">
            <AISummaryCard
              personId={profile.person.person_id}
              summary={aiSummary}
              onGenerate={handleGenerateSummary}
              loading={summaryLoading}
              error={summaryError}
            />

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

            <Card hierarchy="secondary">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">💡 AI Features</h3>
              <p className="text-gray-600 mb-4">
                Use the floating AI assistant in the bottom-right corner to ask questions about this candidate!
              </p>
              <div className="text-sm text-gray-500">
                Example questions:
                <ul className="list-disc list-inside mt-2 space-y-1">
                  <li>What are their strongest technical skills?</li>
                  <li>How would they fit our team culture?</li>
                  <li>What's the best way to reach out to them?</li>
                </ul>
              </div>
            </Card>
          </div>
        )}
      </div>

      {/* Floating AI Assistant */}
      <FloatingAIAssistant
        context="profile"
        contextData={{
          personName: profile.person.full_name,
          personId: profile.person.person_id,
          currentPage: 'profile'
        }}
      />

      {/* Add to List Modal */}
      {showAddToListModal && (
        <AddToListModal
          personId={profile.person.person_id}
          personName={profile.person.full_name}
          onClose={() => setShowAddToListModal(false)}
          onSuccess={() => {
            setShowAddToListModal(false);
            // Optionally show success toast/message
          }}
        />
      )}
    </div>
  );
}

