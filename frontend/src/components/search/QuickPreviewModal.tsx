import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  X, Mail, Plus, Sparkles, ExternalLink, Github, Linkedin,
  Briefcase, MapPin, TrendingUp, Code, Calendar
} from 'lucide-react';
import Button from '../common/Button';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { calculateMatchScore, formatMatchScore, getMatchScoreColor } from '../../utils/matchScoring';
import api from '../../services/api';
import type { Person } from '../../types';

interface QuickPreviewModalProps {
  person: Person;
  onClose: () => void;
  onViewFull: (personId: string) => void;
}

export default function QuickPreviewModal({
  person,
  onClose,
  onViewFull
}: QuickPreviewModalProps) {
  const [generateAI, setGenerateAI] = useState(false);

  // Fetch full profile data
  const { data: profile, isLoading } = useQuery({
    queryKey: ['quickPreview', person.person_id],
    queryFn: () => api.getPersonProfile(person.person_id),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Calculate match score
  const matchScore = profile ? calculateMatchScore(
    profile.person,
    profile.emails,
    profile.github_profile,
    profile.github_contributions
  ) : null;

  // Get initials for avatar
  const initials = person.full_name
    .split(' ')
    .map(n => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  // Gradient based on name
  const nameHash = person.full_name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const gradientIndex = nameHash % 6;
  const gradients = [
    'from-indigo-400 to-indigo-600',
    'from-cyan-400 to-cyan-600',
    'from-emerald-400 to-emerald-600',
    'from-amber-400 to-amber-600',
    'from-rose-400 to-rose-600',
    'from-purple-400 to-purple-600',
  ];
  const gradient = gradients[gradientIndex];

  // Close on Escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-white rounded-xl shadow-2xl m-4 animate-in slide-in-from-bottom duration-300"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 bg-gradient-to-r from-indigo-600 to-cyan-600 px-6 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-white">Quick Preview</h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              icon={<X className="w-5 h-5" />}
              className="text-white hover:bg-white/20"
            />
          </div>
        </div>

        {isLoading ? (
          <div className="p-8 flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-indigo-600" />
            <span className="ml-4 text-gray-600">Loading profile...</span>
          </div>
        ) : profile ? (
          <div className="p-6 space-y-6">
            {/* Profile Hero */}
            <div className="flex items-start gap-6">
              <div className={`flex-shrink-0 w-24 h-24 bg-gradient-to-br ${gradient} rounded-xl flex items-center justify-center text-white font-bold text-3xl shadow-lg`}>
                {initials}
              </div>
              <div className="flex-1">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900">{profile.person.full_name}</h3>
                    {profile.person.headline && (
                      <p className="text-gray-700 mt-1 flex items-center">
                        <Briefcase className="w-4 h-4 mr-2 text-gray-400" />
                        {profile.person.headline}
                      </p>
                    )}
                    {profile.person.location && (
                      <p className="text-gray-600 mt-1 flex items-center">
                        <MapPin className="w-4 h-4 mr-2 text-gray-400" />
                        {profile.person.location}
                      </p>
                    )}
                  </div>
                  {matchScore && (
                    <div className={`
                      px-4 py-2 rounded-lg font-bold text-lg border-2 flex items-center gap-2
                      ${getMatchScoreColor(matchScore.totalScore)}
                    `}>
                      <TrendingUp className="w-5 h-5" />
                      {formatMatchScore(matchScore.totalScore)}
                    </div>
                  )}
                </div>

                {/* Badges */}
                <div className="flex flex-wrap gap-2 mt-3">
                  {profile.emails && profile.emails.length > 0 && (
                    <Badge variant="success" icon={<Mail className="w-3 h-3" />}>
                      {profile.emails.length} Email{profile.emails.length > 1 ? 's' : ''}
                    </Badge>
                  )}
                  {profile.github_profile && (
                    <Badge variant="info" icon={<Github className="w-3 h-3" />}>
                      GitHub
                    </Badge>
                  )}
                  {profile.person.linkedin_url && (
                    <Badge variant="info" icon={<Linkedin className="w-3 h-3" />}>
                      LinkedIn
                    </Badge>
                  )}
                </div>
              </div>
            </div>

            {/* Quick Stats Grid */}
            <div className="grid grid-cols-4 gap-4">
              <Card hierarchy="secondary" className="text-center p-4">
                <div className="text-2xl font-bold text-indigo-600">
                  {profile.employment?.length || 0}
                </div>
                <div className="text-xs text-gray-600 mt-1">Positions</div>
              </Card>
              <Card hierarchy="secondary" className="text-center p-4">
                <div className="text-2xl font-bold text-cyan-600">
                  {profile.github_contributions?.length || 0}
                </div>
                <div className="text-xs text-gray-600 mt-1">Repos</div>
              </Card>
              <Card hierarchy="secondary" className="text-center p-4">
                <div className="text-2xl font-bold text-emerald-600">
                  {profile.github_profile?.total_merged_prs || 0}
                </div>
                <div className="text-xs text-gray-600 mt-1">PRs</div>
              </Card>
              <Card hierarchy="secondary" className="text-center p-4">
                <div className="text-2xl font-bold text-amber-600">
                  {profile.network_stats?.total_connections || 0}
                </div>
                <div className="text-xs text-gray-600 mt-1">Connections</div>
              </Card>
            </div>

            {/* Top GitHub Repos */}
            {profile.github_contributions && profile.github_contributions.length > 0 && (
              <Card>
                <div className="flex items-center gap-2 mb-4">
                  <Code className="w-5 h-5 text-indigo-600" />
                  <h4 className="font-semibold text-gray-900">Top Repositories</h4>
                </div>
                <div className="space-y-3">
                  {profile.github_contributions.slice(0, 3).map((contrib) => (
                    <div key={contrib.contribution_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900 truncate">{contrib.repo_name}</div>
                        {contrib.description && (
                          <div className="text-sm text-gray-600 truncate">{contrib.description}</div>
                        )}
                        <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                          {contrib.language && (
                            <span className="flex items-center gap-1">
                              <span className="w-2 h-2 rounded-full bg-blue-500" />
                              {contrib.language}
                            </span>
                          )}
                          <span>⭐ {contrib.stars}</span>
                          {contrib.merged_pr_count && contrib.merged_pr_count > 0 && (
                            <Badge variant="success" size="xs">
                              {contrib.merged_pr_count} PRs
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Recent Employment */}
            {profile.employment && profile.employment.length > 0 && (
              <Card>
                <div className="flex items-center gap-2 mb-4">
                  <Briefcase className="w-5 h-5 text-indigo-600" />
                  <h4 className="font-semibold text-gray-900">Recent Experience</h4>
                </div>
                <div className="space-y-3">
                  {profile.employment.slice(0, 3).map((emp) => (
                    <div key={emp.employment_id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <Calendar className="w-4 h-4 text-gray-400 mt-1 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900">{emp.title || 'Engineer'}</div>
                        <div className="text-sm text-gray-600">{emp.company_name}</div>
                        <div className="text-xs text-gray-500 mt-1">
                          {emp.start_date} - {emp.end_date || 'Present'}
                          {emp.duration && ` • ${emp.duration}`}
                        </div>
                      </div>
                      {emp.is_current && (
                        <Badge variant="success" size="xs">Current</Badge>
                      )}
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Contact Info */}
            {profile.emails && profile.emails.length > 0 && (
              <Card hierarchy="secondary">
                <div className="flex items-center gap-2 mb-3">
                  <Mail className="w-5 h-5 text-emerald-600" />
                  <h4 className="font-semibold text-gray-900">Contact</h4>
                </div>
                <div className="space-y-2">
                  {profile.emails.map((email, idx) => (
                    <div key={idx} className="flex items-center justify-between">
                      <span className="text-sm font-mono text-gray-700">{email.email}</span>
                      <Badge variant={email.is_primary ? 'success' : 'secondary'} size="xs">
                        {email.email_type}
                      </Badge>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* AI Summary (if available or generate) */}
            {!generateAI && (
              <Button
                variant="outline"
                icon={<Sparkles className="w-4 h-4" />}
                onClick={() => setGenerateAI(true)}
                className="w-full"
              >
                Generate AI Summary
              </Button>
            )}

            {generateAI && (
              <Card className="bg-gradient-to-r from-amber-50 to-orange-50 border-amber-200">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-5 h-5 text-amber-600" />
                  <h4 className="font-semibold text-gray-900">AI Summary</h4>
                </div>
                <div className="text-sm text-gray-700 space-y-2">
                  <p>
                    <strong>{profile.person.full_name}</strong> is a talented engineer with{' '}
                    {profile.employment?.length || 0} positions of experience
                    {profile.github_profile && ` and ${profile.github_profile.total_merged_prs || 0} merged PRs on GitHub`}.
                  </p>
                  {profile.github_contributions && profile.github_contributions.length > 0 && (
                    <p>
                      They've contributed to notable projects including{' '}
                      <strong>{profile.github_contributions[0].repo_name}</strong>
                      {profile.github_contributions.length > 1 && (
                        <span> and {profile.github_contributions.length - 1} other repositories</span>
                      )}.
                    </p>
                  )}
                  {matchScore && matchScore.totalScore >= 70 && (
                    <p className="text-emerald-700 font-medium">
                      ✓ Strong match for this search ({matchScore.totalScore}% match score)
                    </p>
                  )}
                </div>
              </Card>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4 border-t border-gray-200">
              <Button
                onClick={() => onViewFull(person.person_id)}
                icon={<ExternalLink className="w-4 h-4" />}
                className="flex-1"
              >
                View Full Profile
              </Button>
              <Button
                variant="outline"
                icon={<Plus className="w-4 h-4" />}
                onClick={() => {
                  // TODO: Add to list
                }}
              >
                Add to List
              </Button>
              <Button
                variant="ghost"
                onClick={onClose}
              >
                Close
              </Button>
            </div>
          </div>
        ) : (
          <div className="p-8 text-center">
            <p className="text-gray-600">Failed to load profile data.</p>
            <Button variant="outline" onClick={onClose} className="mt-4">
              Close
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

