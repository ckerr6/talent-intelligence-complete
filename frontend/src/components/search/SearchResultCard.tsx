import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Mail, Github, Linkedin, MapPin, Briefcase, Eye, Plus, Sparkles, TrendingUp
} from 'lucide-react';
import Button from '../common/Button';
import Badge from '../common/Badge';
import { calculateMatchScore, formatMatchScore, getMatchScoreColor } from '../../utils/matchScoring';
import type { Person } from '../../types';

interface SearchResultCardProps {
  person: Person & {
    has_email?: boolean;
    has_github?: boolean;
    github_username?: string;
    total_merged_prs?: number;
    total_stars_earned?: number;
    importance_score?: number;
  };
  onQuickPreview: (person: Person) => void;
  isSelected?: boolean;
  onSelect?: (personId: string, selected: boolean) => void;
  showCheckbox?: boolean;
}

export default function SearchResultCard({
  person,
  onQuickPreview,
  isSelected = false,
  onSelect,
  showCheckbox = false
}: SearchResultCardProps) {
  const navigate = useNavigate();
  const [isHovering, setIsHovering] = useState(false);

  // Calculate match score
  const emails = person.has_email ? [{ email: '', email_type: 'work', is_primary: true }] : [];
  const githubProfile = person.has_github ? {
    github_profile_id: '',
    github_username: person.github_username || '',
    total_merged_prs: person.total_merged_prs,
    total_stars_earned: person.total_stars_earned,
    followers: 0,
    following: 0,
    public_repos: 0
  } : undefined;

  const matchScore = calculateMatchScore(person, emails, githubProfile);

  // Get initials for avatar
  const initials = person.full_name
    .split(' ')
    .map(n => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  // Gradient based on name (consistent per person)
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

  const handleClick = (e: React.MouseEvent) => {
    // Don't navigate if clicking checkbox or buttons
    if ((e.target as HTMLElement).closest('button, input[type="checkbox"]')) {
      return;
    }
    navigate(`/profile/${person.person_id}`);
  };

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.stopPropagation();
    if (onSelect) {
      onSelect(person.person_id, e.target.checked);
    }
  };

  return (
    <div
      className={`
        relative p-6 border-2 transition-all duration-200 cursor-pointer
        ${isSelected
          ? 'border-indigo-500 bg-indigo-50'
          : 'border-transparent hover:border-indigo-200 hover:bg-gray-50'
        }
        ${isHovering ? 'shadow-lg -translate-y-1' : 'shadow-sm'}
      `}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
      onClick={handleClick}
    >
      {/* Selection Checkbox */}
      {showCheckbox && (
        <div className="absolute top-4 left-4">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={handleCheckboxChange}
            className="w-5 h-5 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}

      <div className="flex gap-6">
        {/* Avatar */}
        <div className={`flex-shrink-0 ${showCheckbox ? 'ml-7' : ''}`}>
          <div className={`w-20 h-20 bg-gradient-to-br ${gradient} rounded-xl flex items-center justify-center text-white font-bold text-2xl shadow-lg`}>
            {initials}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-start justify-between mb-3">
            <div className="flex-1 min-w-0 pr-4">
              <div className="flex items-center gap-3 mb-1">
                <h3 className="text-xl font-bold text-gray-900 hover:text-indigo-600 transition-colors truncate">
                  {person.full_name}
                </h3>
                {/* Match Score Badge */}
                <div
                  className={`
                    px-3 py-1 rounded-full font-bold text-sm border-2 flex items-center gap-1
                    ${getMatchScoreColor(matchScore.totalScore)}
                  `}
                >
                  <TrendingUp className="w-4 h-4" />
                  {formatMatchScore(matchScore.totalScore)}
                </div>
                {/* Importance Score Badge */}
                {person.importance_score && person.importance_score > 0 && (
                  <div
                    className={`
                      px-3 py-1 rounded-full font-bold text-sm border-2 flex items-center gap-1
                      ${person.importance_score >= 40 
                        ? 'border-yellow-400 bg-yellow-50 text-yellow-800' 
                        : person.importance_score >= 20
                        ? 'border-blue-400 bg-blue-50 text-blue-800'
                        : 'border-gray-400 bg-gray-50 text-gray-700'
                      }
                    `}
                    title={`Developer Importance Score: ${person.importance_score.toFixed(1)}/100`}
                  >
                    <Sparkles className="w-4 h-4" />
                    {person.importance_score.toFixed(0)}
                  </div>
                )}
              </div>
              
              {person.headline && (
                <p className="text-base text-gray-700 flex items-center mt-1">
                  <Briefcase className="w-4 h-4 mr-2 text-gray-400 flex-shrink-0" />
                  <span className="truncate">{person.headline}</span>
                </p>
              )}
              
              {person.location && (
                <p className="text-sm text-gray-500 flex items-center mt-1">
                  <MapPin className="w-4 h-4 mr-2 text-gray-400 flex-shrink-0" />
                  {person.location}
                </p>
              )}
            </div>

            {/* Quick Actions */}
            <div className="flex flex-col gap-2">
              <Button
                size="sm"
                variant="outline"
                icon={<Eye className="w-4 h-4" />}
                onClick={(e) => {
                  e.stopPropagation();
                  onQuickPreview(person);
                }}
              >
                Preview
              </Button>
              <Button
                size="sm"
                variant="ghost"
                icon={<Plus className="w-4 h-4" />}
                onClick={(e) => {
                  e.stopPropagation();
                  // TODO: Add to list functionality
                }}
              >
                Add to List
              </Button>
            </div>
          </div>

          {/* Badges */}
          <div className="flex flex-wrap gap-2 mb-3">
            {person.has_email && (
              <Badge variant="success" size="sm" icon={<Mail className="w-3 h-3" />}>
                Email
              </Badge>
            )}
            {person.has_github && (
              <Badge variant="info" size="sm" icon={<Github className="w-3 h-3" />}>
                GitHub
              </Badge>
            )}
            {person.github_username && (
              <Badge variant="secondary" size="sm">
                @{person.github_username}
              </Badge>
            )}
            {person.total_merged_prs && person.total_merged_prs > 0 && (
              <Badge variant="primary" size="sm">
                {person.total_merged_prs} PRs
              </Badge>
            )}
            {person.total_stars_earned && person.total_stars_earned > 0 && (
              <Badge variant="warning" size="sm">
                ⭐ {person.total_stars_earned}
              </Badge>
            )}
            {person.linkedin_url && (
              <Badge variant="info" size="sm" icon={<Linkedin className="w-3 h-3" />}>
                LinkedIn
              </Badge>
            )}
          </div>

          {/* Match Score Breakdown (subtle) */}
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <div className="flex items-center gap-1">
              <div className={`w-2 h-2 rounded-full ${matchScore.factors.email.score > 0 ? 'bg-emerald-500' : 'bg-gray-300'}`} />
              <span>{matchScore.factors.email.label}</span>
            </div>
            <div className="flex items-center gap-1">
              <div className={`w-2 h-2 rounded-full ${matchScore.factors.github.score > 0 ? 'bg-cyan-500' : 'bg-gray-300'}`} />
              <span>{matchScore.factors.github.label}</span>
            </div>
            {matchScore.factors.contributions.score > 0 && (
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-indigo-500" />
                <span>{matchScore.factors.contributions.label}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Hover Quick Actions Bar */}
      {isHovering && (
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-white via-white to-transparent pt-6 pb-4 px-6">
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              <Button
                size="xs"
                variant="ghost"
                icon={<Sparkles className="w-3 h-3" />}
                onClick={(e) => {
                  e.stopPropagation();
                  // TODO: Generate AI summary
                }}
              >
                AI Summary
              </Button>
              <Button
                size="xs"
                variant="ghost"
                icon={<Mail className="w-3 h-3" />}
                onClick={(e) => {
                  e.stopPropagation();
                  // TODO: Open email modal
                }}
              >
                Email
              </Button>
            </div>
            <Button
              size="xs"
              onClick={(e) => {
                e.stopPropagation();
                navigate(`/profile/${person.person_id}`);
              }}
            >
              View Full Profile →
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

