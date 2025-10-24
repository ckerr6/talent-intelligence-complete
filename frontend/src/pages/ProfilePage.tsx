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
import { SkeletonProfile } from '../components/common/Skeleton';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import EmptyState from '../components/common/EmptyState';

export default function ProfilePage() {
  const { personId } = useParams<{ personId: string }>();
  const navigate = useNavigate();
  
  // Tab State
  const [activeTab, setActiveTab] = useState('overview');
  
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
            </div>

            <div className="space-y-6">
              {/* Contact Info */}
              <ContactInfo
                emails={profile.emails}
                githubProfile={profile.github_profile}
                linkedinUrl={profile.person.linkedin_url}
              />

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
            
            <GitHubActivity
              githubProfile={profile.github_profile}
              contributions={profile.github_contributions}
            />
          </div>
        )}

        {/* Network Tab */}
        {activeTab === 'network' && (
          <div className="max-w-4xl">
            {profile.network_stats && (
              <Card>
                <h2 className="text-2xl font-bold text-gray-900 mb-6">Network Connections</h2>
                
                <div className="grid grid-cols-3 gap-6 mb-8">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-indigo-600">
                      {profile.network_stats.total_connections}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">Total Connections</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-cyan-600">
                      {profile.network_stats.coworker_connections}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">Co-workers</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-emerald-600">
                      {profile.network_stats.github_connections}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">GitHub Collaborators</div>
                  </div>
                </div>

                {profile.network_stats.top_companies.length > 0 && (
                  <div className="border-t border-gray-200 pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Companies</h3>
                    <div className="space-y-3">
                      {profile.network_stats.top_companies.slice(0, 10).map((company, index) => (
                        <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                          <span className="font-medium text-gray-900">{company.company_name}</span>
                          <span className="text-sm text-gray-600">{company.connection_count} connections</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <Button
                  onClick={() => navigate(`/network/${profile.person.person_id}`)}
                  className="mt-6 w-full"
                >
                  Explore Full Network Graph →
                </Button>
              </Card>
            )}
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
    </div>
  );
}

