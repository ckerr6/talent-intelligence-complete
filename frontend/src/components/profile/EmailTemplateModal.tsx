import { useState } from 'react';
import { X, Sparkles, Copy, Check, Mail, Wand2 } from 'lucide-react';
import Button from '../common/Button';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { tokens } from '../../styles/tokens';
import type { Person, Email, GitHubContribution } from '../../types';

interface EmailTemplateModalProps {
  person: Person;
  emails: Email[];
  githubContributions?: GitHubContribution[];
  mutualConnection?: string;
  onClose: () => void;
}

interface TemplateOption {
  id: string;
  name: string;
  tone: 'professional' | 'casual' | 'warm';
  useCase: string;
  icon: string;
}

const TEMPLATE_OPTIONS: TemplateOption[] = [
  {
    id: 'direct',
    name: 'Direct Outreach',
    tone: 'professional',
    useCase: 'Cold outreach with email',
    icon: '📧'
  },
  {
    id: 'github',
    name: 'GitHub-First',
    tone: 'casual',
    useCase: 'Lead with their code contributions',
    icon: '💻'
  },
  {
    id: 'mutual',
    name: 'Mutual Connection',
    tone: 'warm',
    useCase: 'Reference shared connection',
    icon: '🤝'
  },
  {
    id: 'opportunity',
    name: 'Opportunity Focus',
    tone: 'professional',
    useCase: 'Emphasize the role and impact',
    icon: '🚀'
  }
];

export default function EmailTemplateModal({
  person,
  emails,
  githubContributions = [],
  mutualConnection,
  onClose
}: EmailTemplateModalProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<string>('direct');
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [generatedEmail, setGeneratedEmail] = useState<string>('');
  const [subject, setSubject] = useState<string>('');
  const [tone, setTone] = useState<'professional' | 'casual' | 'warm'>('professional');

  const primaryEmail = emails.find(e => e.is_primary)?.email || emails[0]?.email || '';
  const topRepo = githubContributions[0];

  const handleGenerateEmail = async () => {
    setGenerating(true);
    
    // Simulate AI email generation
    setTimeout(() => {
      const templates = {
        direct: {
          subject: `Exciting opportunity for a ${person.headline?.split('at')[0]?.trim() || 'talented engineer'}`,
          body: `Hi ${person.full_name.split(' ')[0]},\n\nI came across your profile and was impressed by your background${person.headline ? ` as ${person.headline}` : ''}${topRepo ? `, particularly your work on ${topRepo.repo_name}` : ''}.\n\nI'm reaching out about an exciting opportunity that might be a great fit for your skills and experience. We're looking for someone with your expertise to join our team and make a significant impact.\n\nWould you be open to a brief conversation to learn more?\n\nBest regards,\n[Your Name]`
        },
        github: {
          subject: `Loved your work on ${topRepo?.repo_name || 'your GitHub projects'}`,
          body: `Hey ${person.full_name.split(' ')[0]},\n\nI've been following your work on GitHub${topRepo ? `, especially your contributions to ${topRepo.repo_name}` : ''}. Your code quality and approach to problem-solving really stand out.\n\n${topRepo && topRepo.merged_pr_count ? `I saw you've had ${topRepo.merged_pr_count} PRs merged - that's impressive!` : ''}\n\nI'm working with a team that's tackling some interesting technical challenges, and I think you'd be a great fit. Would you be interested in chatting about it?\n\nCheers,\n[Your Name]`
        },
        mutual: {
          subject: `${mutualConnection || 'A mutual connection'} thought we should connect`,
          body: `Hi ${person.full_name.split(' ')[0]},\n\n${mutualConnection ? `${mutualConnection} suggested I reach out to you` : 'A mutual connection suggested we should connect'}. They spoke highly of your work${person.headline ? ` as ${person.headline}` : ''}.\n\nI'm exploring opportunities for talented engineers and thought you might be interested in learning more about what we're building.\n\nWould you have 15 minutes for a quick call this week?\n\nBest,\n[Your Name]`
        },
        opportunity: {
          subject: `High-impact role for exceptional ${person.headline?.split('at')[0]?.trim() || 'engineers'}`,
          body: `Hi ${person.full_name.split(' ')[0]},\n\nI'm reaching out about a unique opportunity to join a fast-growing team where you'd have significant impact and ownership.\n\nGiven your background${person.headline ? ` as ${person.headline}` : ''}${topRepo ? ` and your contributions to projects like ${topRepo.repo_name}` : ''}, I believe you'd thrive in this role.\n\nWhat we're offering:\n• Competitive compensation with significant equity\n• Work with cutting-edge technology\n• Small, high-caliber team\n• Real impact on product direction\n\nInterested in learning more?\n\nBest regards,\n[Your Name]`
        }
      };

      const template = templates[selectedTemplate as keyof typeof templates];
      setSubject(template.subject);
      setGeneratedEmail(template.body);
      setGenerating(false);
    }, 1500);
  };

  const handleCopy = () => {
    const fullEmail = `Subject: ${subject}\n\n${generatedEmail}`;
    navigator.clipboard.writeText(fullEmail);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSendEmail = () => {
    const mailtoLink = `mailto:${primaryEmail}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(generatedEmail)}`;
    window.location.href = mailtoLink;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto bg-white rounded-xl shadow-2xl m-4">
        {/* Header */}
        <div className="sticky top-0 z-10 bg-gradient-to-r from-indigo-600 to-cyan-600 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
              <Mail className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">AI-Powered Email</h2>
              <p className="text-sm text-indigo-100">To: {person.full_name}</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            icon={<X className="w-5 h-5" />}
            className="text-white hover:bg-white/20"
          />
        </div>

        <div className="p-6 space-y-6">
          {/* Email Address */}
          <Card hierarchy="secondary">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700">Email Address</label>
                <div className="flex items-center gap-2 mt-1">
                  <Mail className="w-4 h-4 text-gray-400" />
                  <span className="font-mono text-sm text-gray-900">{primaryEmail || 'No email available'}</span>
                  {emails.length > 1 && (
                    <Badge variant="secondary" size="xs">+{emails.length - 1} more</Badge>
                  )}
                </div>
              </div>
              {primaryEmail && (
                <Badge variant="success">✓ Verified</Badge>
              )}
            </div>
          </Card>

          {/* Template Selection */}
          <div>
            <label className="block text-sm font-semibold text-gray-900 mb-3">
              Choose Email Strategy
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {TEMPLATE_OPTIONS.map((template) => (
                <button
                  key={template.id}
                  onClick={() => {
                    setSelectedTemplate(template.id);
                    setTone(template.tone);
                    setGeneratedEmail('');
                  }}
                  className={`
                    p-4 rounded-lg border-2 text-left transition-all
                    ${selectedTemplate === template.id
                      ? 'border-indigo-600 bg-indigo-50 shadow-md scale-105'
                      : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
                    }
                  `}
                >
                  <div className="text-2xl mb-2">{template.icon}</div>
                  <div className="font-semibold text-sm text-gray-900">{template.name}</div>
                  <div className="text-xs text-gray-600 mt-1">{template.useCase}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Tone Selector */}
          <div>
            <label className="block text-sm font-semibold text-gray-900 mb-3">
              Tone & Style
            </label>
            <div className="flex gap-2">
              {(['professional', 'casual', 'warm'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setTone(t)}
                  className={`
                    px-4 py-2 rounded-lg border-2 text-sm font-medium transition-all capitalize
                    ${tone === t
                      ? 'border-cyan-600 bg-cyan-50 text-cyan-900'
                      : 'border-gray-300 text-gray-700 hover:border-gray-400'
                    }
                  `}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Generate Button */}
          {!generatedEmail && (
            <Button
              onClick={handleGenerateEmail}
              icon={<Wand2 className="w-4 h-4" />}
              className="w-full"
              loading={generating}
            >
              {generating ? 'Generating AI Email...' : 'Generate Personalized Email'}
            </Button>
          )}

          {/* Generated Email */}
          {generatedEmail && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-amber-500" />
                  <span className="font-semibold text-gray-900">AI-Generated Email</span>
                  <Badge variant="info" size="xs">
                    {tone}
                  </Badge>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleGenerateEmail}
                  icon={<Wand2 className="w-4 h-4" />}
                >
                  Regenerate
                </Button>
              </div>

              <Card>
                {/* Subject Line */}
                <div className="mb-4 pb-4 border-b border-gray-200">
                  <label className="block text-xs font-medium text-gray-600 mb-1">SUBJECT</label>
                  <input
                    type="text"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    className="w-full text-sm font-semibold text-gray-900 bg-transparent border-0 p-0 focus:ring-0"
                  />
                </div>

                {/* Email Body */}
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-2">MESSAGE</label>
                  <textarea
                    value={generatedEmail}
                    onChange={(e) => setGeneratedEmail(e.target.value)}
                    rows={12}
                    className="w-full text-sm text-gray-900 bg-transparent border-0 p-0 focus:ring-0 resize-none font-mono"
                  />
                </div>
              </Card>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <Button
                  onClick={handleSendEmail}
                  icon={<Mail className="w-4 h-4" />}
                  className="flex-1"
                  disabled={!primaryEmail}
                >
                  Open in Email Client
                </Button>
                <Button
                  variant="outline"
                  onClick={handleCopy}
                  icon={copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                >
                  {copied ? 'Copied!' : 'Copy'}
                </Button>
              </div>

              {/* Tips */}
              <Card hierarchy="secondary">
                <div className="flex gap-3">
                  <Sparkles className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-sm text-gray-900 mb-1">✨ Pro Tips</h4>
                    <ul className="text-xs text-gray-600 space-y-1">
                      <li>• Personalize the opening based on recent activity</li>
                      <li>• Keep it under 150 words for best response rates</li>
                      <li>• Include a specific call-to-action</li>
                      <li>• Follow up 3-4 days later if no response</li>
                    </ul>
                  </div>
                </div>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

