import { 
  Search, Users, Mail, Github, Sparkles, List, Network, 
  Database, Zap, BookOpen, Target
} from 'lucide-react';
import Button from './Button';
import Card from './Card';

interface EmptyStateProps {
  variant: 'no-results' | 'no-lists' | 'no-ai-summary' | 'no-github' | 'no-email' | 'no-network' | 'no-filters' | 'no-data' | 'first-search' | 'no-candidates';
  customTitle?: string;
  customDescription?: string;
  customAction?: React.ReactNode;
  onAction?: () => void;
}

export default function EmptyStates({
  variant,
  customTitle,
  customDescription,
  customAction,
  onAction
}: EmptyStateProps) {
  const configs = {
    'no-results': {
      icon: <Search className="w-16 h-16" />,
      title: 'No candidates found',
      description: 'Try adjusting your filters or use our AI-powered suggestions to find more matches.',
      illustration: (
        <div className="relative w-48 h-48 mx-auto mb-6">
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-100 to-cyan-100 rounded-full opacity-50 blur-2xl" />
          <div className="relative flex items-center justify-center h-full">
            <Search className="w-24 h-24 text-indigo-300" />
          </div>
        </div>
      ),
      actions: (
        <>
          <Button
            variant="primary"
            onClick={onAction}
          >
            Clear All Filters
          </Button>
          <Button
            variant="outline"
            onClick={onAction}
          >
            Try AI Suggestions
          </Button>
        </>
      ),
      tips: [
        'Try broader search terms',
        'Remove some filters to see more results',
        'Use our AI filter suggestions',
        'Try searching by company or location'
      ]
    },
    'first-search': {
      icon: <Target className="w-16 h-16" />,
      title: 'Start your talent search',
      description: 'Use our AI-powered filters to find the perfect candidates for your role.',
      illustration: (
        <div className="relative w-48 h-48 mx-auto mb-6">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-100 to-teal-100 rounded-full opacity-50 blur-2xl" />
          <div className="relative flex items-center justify-center h-full">
            <div className="relative">
              <Target className="w-24 h-24 text-emerald-400" />
              <Sparkles className="w-8 h-8 text-amber-400 absolute -top-2 -right-2 animate-pulse" />
            </div>
          </div>
        </div>
      ),
      actions: (
        <>
          <Button
            variant="primary"
            icon={<Sparkles className="w-4 h-4" />}
            onClick={onAction}
          >
            Try "Senior Blockchain Engineers"
          </Button>
          <Button
            variant="outline"
            onClick={onAction}
          >
            Browse All Candidates
          </Button>
        </>
      ),
      tips: [
        'Try our AI-powered natural language search',
        'Use filter presets for common searches',
        'Search by company, location, or skills',
        'Filter by GitHub activity or email availability'
      ]
    },
    'no-lists': {
      icon: <List className="w-16 h-16" />,
      title: 'No candidate lists yet',
      description: 'Create your first list to organize and track candidates for different roles.',
      illustration: (
        <div className="relative w-48 h-48 mx-auto mb-6">
          <div className="absolute inset-0 bg-gradient-to-br from-amber-100 to-orange-100 rounded-full opacity-50 blur-2xl" />
          <div className="relative flex items-center justify-center h-full">
            <List className="w-24 h-24 text-amber-300" />
          </div>
        </div>
      ),
      actions: (
        <Button
          variant="primary"
          icon={<List className="w-4 h-4" />}
          onClick={onAction}
        >
          Create Your First List
        </Button>
      ),
      tips: [
        'Organize candidates by role or project',
        'Track your recruiting pipeline',
        'Share lists with your team',
        'Export lists for reporting'
      ]
    },
    'no-ai-summary': {
      icon: <Sparkles className="w-16 h-16" />,
      title: 'No AI summary yet',
      description: 'Generate an AI-powered analysis of this candidate to get instant insights.',
      illustration: (
        <div className="relative w-48 h-48 mx-auto mb-6">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-100 to-pink-100 rounded-full opacity-50 blur-2xl" />
          <div className="relative flex items-center justify-center h-full">
            <Sparkles className="w-24 h-24 text-purple-300 animate-pulse" />
          </div>
        </div>
      ),
      actions: (
        <Button
          variant="primary"
          icon={<Sparkles className="w-4 h-4" />}
          onClick={onAction}
        >
          Generate AI Summary
        </Button>
      ),
      tips: [
        'Get instant career insights',
        'Understand technical strengths',
        'See recommended outreach strategy',
        'Ask AI questions about the candidate'
      ]
    },
    'no-github': {
      icon: <Github className="w-16 h-16" />,
      title: 'No GitHub profile linked',
      description: 'Add their GitHub username to unlock code quality insights and contribution analysis.',
      illustration: (
        <div className="relative w-48 h-48 mx-auto mb-6">
          <div className="absolute inset-0 bg-gradient-to-br from-gray-100 to-slate-100 rounded-full opacity-50 blur-2xl" />
          <div className="relative flex items-center justify-center h-full">
            <Github className="w-24 h-24 text-gray-300" />
          </div>
        </div>
      ),
      actions: (
        <Button
          variant="primary"
          icon={<Github className="w-4 h-4" />}
          onClick={onAction}
        >
          Link GitHub Profile
        </Button>
      ),
      tips: [
        'Verify code quality with merged PRs',
        'See contribution history',
        'Analyze technical expertise',
        'View collaboration patterns'
      ]
    },
    'no-email': {
      icon: <Mail className="w-16 h-16" />,
      title: 'No email address available',
      description: 'We\'re working on finding contact information for this candidate.',
      illustration: (
        <div className="relative w-48 h-48 mx-auto mb-6">
          <div className="absolute inset-0 bg-gradient-to-br from-red-100 to-rose-100 rounded-full opacity-50 blur-2xl" />
          <div className="relative flex items-center justify-center h-full">
            <Mail className="w-24 h-24 text-red-300" />
          </div>
        </div>
      ),
      actions: (
        <>
          <Button
            variant="primary"
            onClick={onAction}
          >
            Find via LinkedIn
          </Button>
          <Button
            variant="outline"
            onClick={onAction}
          >
            Request Introduction
          </Button>
        </>
      ),
      tips: [
        'Try reaching via mutual connections',
        'Check their LinkedIn profile',
        'Look for GitHub contact info',
        'Use intro request workflow'
      ]
    },
    'no-network': {
      icon: <Network className="w-16 h-16" />,
      title: 'No network connections found',
      description: 'This candidate isn\'t in your network yet. Grow your network to unlock warm introductions.',
      illustration: (
        <div className="relative w-48 h-48 mx-auto mb-6">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-full opacity-50 blur-2xl" />
          <div className="relative flex items-center justify-center h-full">
            <Network className="w-24 h-24 text-blue-300" />
          </div>
        </div>
      ),
      actions: (
        <Button
          variant="primary"
          icon={<Users className="w-4 h-4" />}
          onClick={onAction}
        >
          Explore Network
        </Button>
      ),
      tips: [
        'Add your team members',
        'Import LinkedIn connections',
        'Add GitHub collaborators',
        'Mutual connections boost response rates by 3-5x'
      ]
    },
    'no-filters': {
      icon: <Zap className="w-16 h-16" />,
      title: 'No active filters',
      description: 'Add filters to narrow down your search and find the perfect candidates.',
      illustration: (
        <div className="relative w-48 h-48 mx-auto mb-6">
          <div className="absolute inset-0 bg-gradient-to-br from-yellow-100 to-amber-100 rounded-full opacity-50 blur-2xl" />
          <div className="relative flex items-center justify-center h-full">
            <Zap className="w-24 h-24 text-yellow-300" />
          </div>
        </div>
      ),
      actions: (
        <>
          <Button
            variant="primary"
            icon={<Sparkles className="w-4 h-4" />}
            onClick={onAction}
          >
            Use AI Suggestions
          </Button>
          <Button
            variant="outline"
            onClick={onAction}
          >
            Add Filters
          </Button>
        </>
      ),
      tips: [
        'Filter by company, location, or skills',
        'Use AI-powered filter suggestions',
        'Save filter combinations as presets',
        'Try natural language search'
      ]
    },
    'no-data': {
      icon: <Database className="w-16 h-16" />,
      title: 'No data available',
      description: 'We\'re still gathering information for this section.',
      illustration: (
        <div className="relative w-48 h-48 mx-auto mb-6">
          <div className="absolute inset-0 bg-gradient-to-br from-gray-100 to-slate-100 rounded-full opacity-50 blur-2xl" />
          <div className="relative flex items-center justify-center h-full">
            <Database className="w-24 h-24 text-gray-300" />
          </div>
        </div>
      ),
      actions: (
        <Button
          variant="outline"
          onClick={onAction}
        >
          Refresh Data
        </Button>
      ),
      tips: []
    },
    'no-candidates': {
      icon: <Users className="w-16 h-16" />,
      title: 'No candidates yet',
      description: 'Start by searching for candidates or importing data from LinkedIn or GitHub.',
      illustration: (
        <div className="relative w-48 h-48 mx-auto mb-6">
          <div className="absolute inset-0 bg-gradient-to-br from-teal-100 to-cyan-100 rounded-full opacity-50 blur-2xl" />
          <div className="relative flex items-center justify-center h-full">
            <Users className="w-24 h-24 text-teal-300" />
          </div>
        </div>
      ),
      actions: (
        <>
          <Button
            variant="primary"
            icon={<Search className="w-4 h-4" />}
            onClick={onAction}
          >
            Start Searching
          </Button>
          <Button
            variant="outline"
            icon={<Github className="w-4 h-4" />}
            onClick={onAction}
          >
            Import from GitHub
          </Button>
        </>
      ),
      tips: [
        'Search by company or skills',
        'Import GitHub organizations',
        'Upload LinkedIn exports',
        'Use AI-powered discovery'
      ]
    }
  };

  const config = configs[variant];
  const title = customTitle || config.title;
  const description = customDescription || config.description;
  const actions = customAction || config.actions;

  return (
    <Card className="text-center py-12 px-6">
      {/* Illustration */}
      {config.illustration}

      {/* Content */}
      <div className="max-w-md mx-auto space-y-4">
        <h3 className="text-2xl font-bold text-gray-900">{title}</h3>
        <p className="text-gray-600">{description}</p>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-4">
          {actions}
        </div>

        {/* Tips */}
        {config.tips && config.tips.length > 0 && (
          <Card hierarchy="secondary" className="mt-8 text-left">
            <div className="flex items-start gap-3">
              <BookOpen className="w-5 h-5 text-indigo-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">💡 Helpful Tips</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  {config.tips.map((tip, idx) => (
                    <li key={idx}>• {tip}</li>
                  ))}
                </ul>
              </div>
            </div>
          </Card>
        )}
      </div>
    </Card>
  );
}

// Export individual empty state variants for convenience
export function NoResultsEmptyState(props: Omit<EmptyStateProps, 'variant'>) {
  return <EmptyStates variant="no-results" {...props} />;
}

export function FirstSearchEmptyState(props: Omit<EmptyStateProps, 'variant'>) {
  return <EmptyStates variant="first-search" {...props} />;
}

export function NoListsEmptyState(props: Omit<EmptyStateProps, 'variant'>) {
  return <EmptyStates variant="no-lists" {...props} />;
}

export function NoAISummaryEmptyState(props: Omit<EmptyStateProps, 'variant'>) {
  return <EmptyStates variant="no-ai-summary" {...props} />;
}

export function NoGitHubEmptyState(props: Omit<EmptyStateProps, 'variant'>) {
  return <EmptyStates variant="no-github" {...props} />;
}

export function NoEmailEmptyState(props: Omit<EmptyStateProps, 'variant'>) {
  return <EmptyStates variant="no-email" {...props} />;
}

export function NoNetworkEmptyState(props: Omit<EmptyStateProps, 'variant'>) {
  return <EmptyStates variant="no-network" {...props} />;
}

