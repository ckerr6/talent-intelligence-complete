/**
 * ProfilePage with New Design System Components
 * 
 * This is an example implementation showing how to use:
 * - ProfileHero (large hero section with match score)
 * - TabNavigation (organized content sections)
 * - StickyActionBar (persistent actions on scroll)
 * - Enhanced base components (Button, Badge, Card, Toast)
 * 
 * To use this:
 * 1. Rename this file to ProfilePage.tsx (backup the old one first)
 * 2. Update imports as needed
 * 3. Customize tab content based on your needs
 */

import { useState, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, AlertCircle } from 'lucide-react';
import api from '../services/api';

// New Components
import ProfileHero from '../components/profile/ProfileHero';
import TabNavigation, { createProfileTabs } from '../components/profile/TabNavigation';
import StickyActionBar from '../components/profile/StickyActionBar';
import { ToastContainer, useToast } from '../components/common/Toast';

// Existing Components
import EmploymentTimeline from '../components/profile/EmploymentTimeline';
import ContactInfo from '../components/profile/ContactInfo';
import GitHubActivity from '../components/profile/GitHubActivity';
import HowToReach from '../components/profile/HowToReach';
import QuickActions from '../components/profile/QuickActions';
import AISummaryCard from '../components/ai/AISummaryCard';
import CodeAnalysisCard from '../components/ai/CodeAnalysisCard';
import AskAIChat from '../components/ai/AskAIChat';
import { SkeletonProfile } from '../components/common/Skeleton';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import EmptyState from '../components/common/EmptyState';

export default function ProfilePage() {
  const { personId } = useParams<{ personId: string }>();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const heroRef = useRef<HTMLElement>(null);
  const toast = useToast();
  
  // Get active tab from URL, default to 'overview'
  const activeTab = searchParams.get('tab') || 'overview';
  
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

  // Calculate match score (example algorithm)
  const calculateMatchScore = () => {
    if (!profile) return 50;
    
    let score = 0;
    
    // Has email: +30
    if (profile.emails?.length > 0) score += 30;
    
    // Has GitHub: +20
    if (profile.github_profile) score += 20;
    
    // Merged PRs: +2 per PR (capped at 20)
    if (profile.github_profile?.total_merged_prs) {
      score += Math.min(20, profile.github_profile.total_merged_prs * 2);
    }
    
    // Years of experience: +5 per year (capped at 20)
    if (profile.employment?.length) {
      const years = profile.employment.length * 2; // Rough estimate
      score += Math.min(20, years * 5);
    }
    
    return Math.min(100, score);
  };

  const matchScore = profile ? calculateMatchScore() : undefined;

  // Tab change handler
  const handleTabChange = (tabId: string) => {
    setSearchParams({ tab: tabId });
    
    // Smooth scroll to top of content
    window.scrollTo({ top: 200, behavior: 'smooth' });
  };

  // Create tabs based on profile data
  const tabs = profile ? createProfileTabs({
    employment: profile.employment,
    github_profile: profile.github_profile,
    network_stats: profile.network_stats,
    ai_insights_viewed: !!aiSummary, // Mark as viewed if we have summary
  }) : [];

  // Action handlers
  const handleEmailClick = () => {
    if (profile?.emails?.[0]?.email) {
      window.location.href = `mailto:${profile.emails[0].email}`;
      toast.success('Opening email client...');
    } else {
      toast.warning('No email available for this candidate');
    }
  };

  const handleAddToListClick = () => {
    // TODO: Implement list selector modal
    toast.info('Add to list feature coming soon!');
  };

  const handleAIChatClick = () => {
    // TODO: Open AI chat panel
    toast.info('AI Chat panel opening...');
  };

  const handleExportClick = () => {
    toast.info('Generating PDF...', {
      duration: 2000,
      action: {
        label: 'Cancel',
        onClick: () => toast.info('Export cancelled'),
      },
    });
    
    // TODO: Implement PDF export
    setTimeout(() => {
      toast.success('Profile exported successfully!');
    }, 2000);
  };

  // AI Handlers
  const handleGenerateSummary = async () => {
    if (!personId) return;
    
    setSummaryLoading(true);
    setSummaryError(null);
    toast.info('AI is analyzing profile...');
    
    try {
      const result = await api.generateProfileSummary(personId);
      setAiSummary(result.summary);
      toast.success('AI summary generated!');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate summary';
      setSummaryError(message);
      toast.error(message);
    } finally {
      setSummaryLoading(false);
    }
  };

  const handleAnalyzeCode = async () => {
    if (!personId) return;
    
    setAnalysisLoading(true);
    setAnalysisError(null);
    toast.info('AI is analyzing code quality...');
    
    try {
      const result = await api.analyzeCodeQuality(personId);
      setCodeAnalysis(result.analysis);
      toast.success('Code analysis complete!');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to analyze code';
      setAnalysisError(message);
      toast.error(message);
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

  // Loading state
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

  // Error state
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

  return (
    <div className="space-y-6">
      {/* Toast Container */}
      <ToastContainer toasts={toast.toasts} position="top-right" />

      {/* Back button */}
      <Button
        variant="ghost"
        onClick={() => navigate(-1)}
        icon={<ArrowLeft className="w-4 h-4" />}
      >
        Back
      </Button>

      {/* Profile Hero */}
      <div ref={heroRef}>
        <ProfileHero
          person={profile.person}
          matchScore={matchScore}
          onEmailClick={handleEmailClick}
          onAddToListClick={handleAddToListClick}
          onAIChatClick={handleAIChatClick}
          onExportClick={handleExportClick}
        />
      </div>

      {/* Sticky Action Bar (appears on scroll) */}
      <StickyActionBar
        person={profile.person}
        matchScore={matchScore}
        onEmailClick={handleEmailClick}
        onAddToListClick={handleAddToListClick}
        onAIChatClick={handleAIChatClick}
        onExportClick={handleExportClick}
        heroRef={heroRef}
      />

      {/* Tab Navigation */}
      <TabNavigation
        activeTab={activeTab}
        onTabChange={handleTabChange}
        tabs={tabs}
      />

      {/* Tab Content */}
      <div className="max-w-7xl mx-auto">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              {/* AI Summary */}
              <AISummaryCard
                personId={profile.person.person_id}
                summary={aiSummary}
                onGenerate={handleGenerateSummary}
                loading={summaryLoading}
                error={summaryError}
              />

              {/* How to Reach */}
              <HowToReach targetPersonId={profile.person.person_id} />

              {/* Quick Employment Summary */}
              <Card>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Recent Experience</h3>
                {profile.employment?.slice(0, 3).map((job, index) => (
                  <div key={index} className="mb-4 pb-4 border-b border-gray-200 last:border-0">
                    <h4 className="font-semibold text-gray-900">{job.title}</h4>
                    <p className="text-gray-600">{job.company_name}</p>
                    <p className="text-sm text-gray-500">{job.duration}</p>
                  </div>
                ))}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleTabChange('experience')}
                  className="mt-2"
                >
                  View Full History →
                </Button>
              </Card>
            </div>

            <div className="space-y-6">
              <QuickActions
                personId={profile.person.person_id}
                personName={profile.person.full_name}
              />
              <ContactInfo
                emails={profile.emails}
                githubProfile={profile.github_profile}
                linkedinUrl={profile.person.linkedin_url}
              />
            </div>
          </div>
        )}

        {/* Experience Tab */}
        {activeTab === 'experience' && (
          <div className="max-w-4xl mx-auto">
            <EmploymentTimeline employment={profile.employment} />
          </div>
        )}

        {/* Code Tab */}
        {activeTab === 'code' && (
          <div className="space-y-6">
            {profile.github_profile ? (
              <>
                <CodeAnalysisCard
                  personId={profile.person.person_id}
                  analysis={codeAnalysis}
                  onGenerate={handleAnalyzeCode}
                  loading={analysisLoading}
                  error={analysisError}
                  hasGitHub={!!profile.github_profile}
                />
                <GitHubActivity
                  githubProfile={profile.github_profile}
                  contributions={profile.github_contributions}
                />
              </>
            ) : (
              <Card>
                <EmptyState
                  icon={<AlertCircle className="w-8 h-8" />}
                  title="No GitHub Profile"
                  description="This candidate hasn't linked a GitHub profile yet."
                />
              </Card>
            )}
          </div>
        )}

        {/* Network Tab */}
        {activeTab === 'network' && (
          <div className="max-w-4xl mx-auto">
            {profile.network_stats ? (
              <Card>
                <h2 className="text-2xl font-semibold text-gray-900 mb-6">Network Connections</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                  <div className="bg-indigo-50 p-4 rounded-lg">
                    <p className="text-sm text-indigo-600 font-medium">Total Connections</p>
                    <p className="text-3xl font-bold text-indigo-900">{profile.network_stats.total_connections}</p>
                  </div>
                  <div className="bg-cyan-50 p-4 rounded-lg">
                    <p className="text-sm text-cyan-600 font-medium">Co-workers</p>
                    <p className="text-3xl font-bold text-cyan-900">{profile.network_stats.coworker_connections}</p>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <p className="text-sm text-purple-600 font-medium">GitHub Collaborators</p>
                    <p className="text-3xl font-bold text-purple-900">{profile.network_stats.github_connections}</p>
                  </div>
                </div>
                
                <Button
                  onClick={() => navigate(`/network/${profile.person.person_id}`)}
                  variant="primary"
                  fullWidth
                >
                  Explore Network Graph →
                </Button>
              </Card>
            ) : (
              <Card>
                <EmptyState
                  icon={<AlertCircle className="w-8 h-8" />}
                  title="Building Network Graph"
                  description="Network connections are being calculated..."
                />
              </Card>
            )}
          </div>
        )}

        {/* AI Insights Tab */}
        {activeTab === 'ai-insights' && (
          <div className="max-w-4xl mx-auto space-y-6">
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

            <Card>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Ask AI About This Candidate</h3>
              <p className="text-gray-600 mb-4">
                Have questions about this candidate? Our AI can help analyze their background, skills, and fit for your role.
              </p>
              <Button onClick={handleAIChatClick} icon={<Sparkles className="w-4 h-4" />}>
                Start AI Conversation
              </Button>
            </Card>
          </div>
        )}
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

