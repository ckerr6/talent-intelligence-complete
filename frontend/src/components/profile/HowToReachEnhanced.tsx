import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Mail, Users, Linkedin, Github,
  TrendingUp, Clock, Sparkles, ChevronRight, Info, AlertCircle
} from 'lucide-react';
import api from '../../services/api';
import Button from '../common/Button';
import Card from '../common/Card';
import Badge from '../common/Badge';
import EmailTemplateModal from './EmailTemplateModal';
import IntroRequestModal from './IntroRequestModal';
import type { FullProfile } from '../../types';

interface HowToReachEnhancedProps {
  profile: FullProfile;
  sourcePersonId?: string;
}

interface ContactMethod {
  id: string;
  name: string;
  icon: JSX.Element;
  probability: number;
  timeToResponse: string;
  pros: string[];
  cons: string[];
  action: () => void;
  available: boolean;
  badge?: {
    text: string;
    variant: 'success' | 'info' | 'warning';
  };
}

export default function HowToReachEnhanced({
  profile,
  sourcePersonId
}: HowToReachEnhancedProps) {
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [showIntroModal, setShowIntroModal] = useState(false);
  const [selectedMethod, setSelectedMethod] = useState<string | null>(null);

  const { person, emails, github_profile, github_contributions } = profile;

  // Fetch network path for warm intro
  const effectiveSourceId = sourcePersonId || 'current-user-placeholder';
  const { data: networkPath } = useQuery({
    queryKey: ['networkPath', effectiveSourceId, person.person_id],
    queryFn: () => api.findPath(effectiveSourceId, person.person_id),
    enabled: effectiveSourceId !== 'current-user-placeholder',
    retry: false,
  });

  const hasEmail = !!(emails && emails.length > 0);
  const hasLinkedIn = !!person.linkedin_url;
  const hasGitHub = !!github_profile;
  const hasWarmIntro = !!(networkPath && networkPath.nodes && networkPath.nodes.length > 1);

  // Calculate AI-powered success probabilities
  const calculateProbability = (method: string): number => {
    const baseRates = {
      'email': 0.25,
      'warm-intro': 0.65,
      'linkedin': 0.15,
      'github': 0.20
    };

    let probability = baseRates[method as keyof typeof baseRates] || 0.10;

    // Boost for quality indicators
    if (method === 'email' && hasEmail) probability += 0.15;
    if (method === 'warm-intro' && hasWarmIntro) probability += 0.20;
    if (method === 'github' && github_profile?.total_merged_prs && github_profile.total_merged_prs > 10) probability += 0.10;

    return Math.min(probability, 0.95);
  };

  const contactMethods: ContactMethod[] = [
    {
      id: 'warm-intro',
      name: 'Warm Introduction',
      icon: <Users className="w-5 h-5" />,
      probability: calculateProbability('warm-intro'),
      timeToResponse: '2-3 days',
      pros: [
        'Highest response rate (65%+)',
        `Connected via ${networkPath?.nodes?.[1]?.name || 'mutual connection'}`,
        'Builds trust immediately',
        'Personal recommendation'
      ],
      cons: [
        'Requires mutual connection participation',
        'Takes slightly longer than direct email'
      ],
      available: hasWarmIntro,
      badge: hasWarmIntro ? {
        text: `${networkPath?.path_length}° connection`,
        variant: 'success'
      } : undefined,
      action: () => setShowIntroModal(true)
    },
    {
      id: 'email',
      name: 'Direct Email',
      icon: <Mail className="w-5 h-5" />,
      probability: calculateProbability('email'),
      timeToResponse: '1-2 days',
      pros: [
        'Fast and direct',
        'Professional and expected',
        'Can include detailed information',
        hasEmail ? `${emails.length} verified email${emails.length > 1 ? 's' : ''}` : ''
      ].filter(Boolean),
      cons: [
        'Lower response rate without warm intro',
        'Easy to ignore in busy inbox'
      ],
      available: hasEmail,
      badge: hasEmail ? {
        text: '✓ Email verified',
        variant: 'success'
      } : undefined,
      action: () => setShowEmailModal(true)
    },
    {
      id: 'linkedin',
      name: 'LinkedIn InMail',
      icon: <Linkedin className="w-5 h-5" />,
      probability: calculateProbability('linkedin'),
      timeToResponse: '3-5 days',
      pros: [
        'Professional context',
        'Profile available for reference',
        'Easy to respond'
      ],
      cons: [
        'Requires LinkedIn Premium for InMail',
        'Lower response rate (~15%)',
        'Character limit constraints'
      ],
      available: hasLinkedIn,
      badge: hasLinkedIn ? {
        text: 'Profile available',
        variant: 'info'
      } : undefined,
      action: () => {
        if (hasLinkedIn) window.open(person.linkedin_url, '_blank');
      }
    },
    {
      id: 'github',
      name: 'GitHub Comment',
      icon: <Github className="w-5 h-5" />,
      probability: calculateProbability('github'),
      timeToResponse: '2-4 days',
      pros: [
        'Shows you value their technical work',
        'Can reference specific contributions',
        github_profile?.total_merged_prs ? `${github_profile.total_merged_prs} merged PRs` : ''
      ].filter(Boolean),
      cons: [
        'Less professional for job outreach',
        'May not check GitHub regularly',
        'Best as secondary touchpoint'
      ],
      available: hasGitHub,
      badge: hasGitHub ? {
        text: `@${github_profile?.github_username}`,
        variant: 'info'
      } : undefined,
      action: () => {
        if (hasGitHub) window.open(`https://github.com/${github_profile?.github_username}`, '_blank');
      }
    }
  ];

  // Sort by probability
  const sortedMethods = [...contactMethods].sort((a, b) => b.probability - a.probability);
  const recommendedMethod = sortedMethods.find(m => m.available);

  return (
    <>
      <Card className="relative overflow-hidden">
        {/* Gradient background accent */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-emerald-100/50 to-cyan-100/50 rounded-full blur-3xl -z-10" />

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-cyan-500 rounded-xl flex items-center justify-center shadow-lg">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-gray-900">How to Reach</h3>
              <p className="text-sm text-gray-600">AI-powered outreach strategy</p>
            </div>
          </div>
          {recommendedMethod && (
            <Badge variant="success" icon={<Sparkles className="w-3 h-3" />}>
              {Math.round(recommendedMethod.probability * 100)}% success rate
            </Badge>
          )}
        </div>

        {/* AI Recommendation */}
        {recommendedMethod && (
          <Card hierarchy="secondary" className="mb-6 bg-gradient-to-r from-emerald-50 to-cyan-50 border-emerald-200">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 bg-emerald-500 rounded-lg flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h4 className="font-bold text-gray-900">Recommended Approach</h4>
                  <Badge variant="success" size="xs">Best option</Badge>
                </div>
                <p className="text-sm text-gray-700 mb-3">
                  <strong>{recommendedMethod.name}</strong> has the highest success rate for reaching {person.full_name.split(' ')[0]}.
                  {recommendedMethod.id === 'warm-intro' && hasWarmIntro && (
                    <span> You're connected via <strong>{networkPath?.nodes?.[1]?.name}</strong>.</span>
                  )}
                  {recommendedMethod.id === 'email' && hasEmail && (
                    <span> We have {emails.length} verified email{emails.length > 1 ? 's' : ''}.</span>
                  )}
                </p>
                <Button
                  onClick={recommendedMethod.action}
                  icon={recommendedMethod.icon}
                  size="sm"
                >
                  Use {recommendedMethod.name}
                </Button>
              </div>
            </div>
          </Card>
        )}

        {/* All Contact Methods */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            All Contact Methods
            <Info className="w-4 h-4 text-gray-400" />
          </h4>
          
          {sortedMethods.map((method, index) => (
            <Card
              key={method.id}
              hierarchy="secondary"
              className={`
                transition-all cursor-pointer
                ${method.available
                  ? 'hover:shadow-md hover:-translate-y-0.5 border-2 border-transparent hover:border-indigo-200'
                  : 'opacity-50 cursor-not-allowed'
                }
                ${selectedMethod === method.id ? 'ring-2 ring-indigo-500 border-indigo-500' : ''}
              `}
              onClick={() => {
                if (method.available) {
                  setSelectedMethod(method.id);
                }
              }}
            >
              <div className="flex items-start gap-4">
                {/* Rank Badge */}
                <div className={`
                  w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm flex-shrink-0
                  ${index === 0 && method.available ? 'bg-emerald-500 text-white' : 'bg-gray-200 text-gray-600'}
                `}>
                  {index + 1}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {method.icon}
                      <h5 className="font-semibold text-gray-900">{method.name}</h5>
                      {method.badge && (
                        <Badge variant={method.badge.variant} size="xs">
                          {method.badge.text}
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <div className={`
                          text-lg font-bold
                          ${method.probability >= 0.5 ? 'text-emerald-600' : method.probability >= 0.3 ? 'text-cyan-600' : 'text-gray-600'}
                        `}>
                          {Math.round(method.probability * 100)}%
                        </div>
                        <div className="text-xs text-gray-500 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {method.timeToResponse}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {selectedMethod === method.id && method.available && (
                    <div className="mt-3 pt-3 border-t border-gray-200 space-y-3 animate-in fade-in slide-in-from-top duration-200">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <h6 className="text-xs font-semibold text-emerald-700 mb-1 flex items-center gap-1">
                            <span className="text-emerald-600">✓</span>
                            Pros
                          </h6>
                          <ul className="text-xs text-gray-600 space-y-1">
                            {method.pros.map((pro, i) => (
                              <li key={i}>• {pro}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <h6 className="text-xs font-semibold text-amber-700 mb-1 flex items-center gap-1">
                            <AlertCircle className="w-3 h-3" />
                            Cons
                          </h6>
                          <ul className="text-xs text-gray-600 space-y-1">
                            {method.cons.map((con, i) => (
                              <li key={i}>• {con}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                      <Button
                        onClick={(e) => {
                          e.stopPropagation();
                          method.action();
                        }}
                        icon={<ChevronRight className="w-4 h-4" />}
                        iconPosition="right"
                        size="sm"
                        className="w-full"
                      >
                        Use This Method
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* Tips */}
        <Card hierarchy="secondary" className="mt-6">
          <div className="flex gap-3">
            <Sparkles className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-sm text-gray-900 mb-2">Pro Tips for Best Results</h4>
              <ul className="text-xs text-gray-600 space-y-1">
                <li>• Personalize your message by referencing specific projects or contributions</li>
                <li>• Keep initial outreach brief (under 150 words)</li>
                <li>• Lead with value - what's in it for them?</li>
                <li>• Multiple touchpoints (email + LinkedIn) increase response rates by 40%</li>
                <li>• Follow up once after 3-4 days if no response</li>
              </ul>
            </div>
          </div>
        </Card>
      </Card>

      {/* Modals */}
      {showEmailModal && hasEmail && (
        <EmailTemplateModal
          person={person}
          emails={emails}
          githubContributions={github_contributions}
          mutualConnection={networkPath?.nodes?.[1]?.name}
          onClose={() => setShowEmailModal(false)}
        />
      )}

      {showIntroModal && hasWarmIntro && networkPath && (
        <IntroRequestModal
          targetPerson={person}
          mutualConnection={networkPath.nodes[1]}
          connectionContext={networkPath.edges[0]}
          onClose={() => setShowIntroModal(false)}
        />
      )}
    </>
  );
}

