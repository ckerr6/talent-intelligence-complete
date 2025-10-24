import { Mail, Plus, Sparkles, Download, Briefcase, MapPin } from 'lucide-react';
import Button from '../common/Button';

export interface Person {
  person_id: string;
  full_name: string;
  headline?: string;
  location?: string;
  linkedin_url?: string;
  refreshed_at?: string;
  has_email?: boolean;
  has_github?: boolean;
  github_username?: string;
}

interface ProfileHeroProps {
  person: Person;
  matchScore?: number;
  onEmailClick?: () => void;
  onAddToListClick?: () => void;
  onAIChatClick?: () => void;
  onExportClick?: () => void;
}

export default function ProfileHero({
  person,
  matchScore,
  onEmailClick,
  onAddToListClick,
  onAIChatClick,
  onExportClick,
}: ProfileHeroProps) {
  // Generate initials
  const initials = person.full_name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  // Get consistent gradient for this person
  const gradientClass = getAvatarGradient(person.full_name);

  // Calculate match score color
  const scoreConfig = getMatchScoreConfig(matchScore);

  // Format relative time
  const formatRelativeTime = (dateString?: string) => {
    if (!dateString) return null;
    
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) return 'just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <header className="bg-white rounded-xl shadow-lg p-8 lg:p-12 mb-6 relative overflow-hidden animate-fadeInUp">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-r from-gray-50 to-white opacity-50" />
      
      {/* Content */}
      <div className="relative">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 flex-1 min-w-0">
            {/* Avatar */}
            <div
              className={`
                w-20 h-20 lg:w-24 lg:h-24 rounded-full
                ${gradientClass}
                flex items-center justify-center
                text-white text-2xl lg:text-3xl font-bold
                shadow-lg
                hover:scale-105 transition-transform duration-200
                cursor-pointer flex-shrink-0
              `}
              title={person.full_name}
            >
              {initials}
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-2 break-words">
                {person.full_name}
              </h1>

              {person.headline && (
                <h2 className="text-lg sm:text-xl lg:text-2xl font-semibold text-gray-700 flex items-center gap-2 mb-2 flex-wrap">
                  <Briefcase className="w-5 h-5 text-gray-500 flex-shrink-0" />
                  <span className="break-words">{person.headline}</span>
                </h2>
              )}

              <div className="flex flex-wrap items-center gap-3 text-sm sm:text-base text-gray-600 mt-2">
                {person.location && (
                  <>
                    <div className="flex items-center gap-1">
                      <MapPin className="w-4 h-4 text-gray-400" />
                      <span>{person.location}</span>
                    </div>
                  </>
                )}
                {person.refreshed_at && (
                  <>
                    {person.location && <span className="text-gray-400">•</span>}
                    <span className="text-gray-500">
                      Updated {formatRelativeTime(person.refreshed_at)}
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Match Score Badge */}
          {matchScore !== undefined && (
            <MatchScoreBadge score={matchScore} config={scoreConfig} />
          )}
        </div>

        {/* Action Bar */}
        <div className="mt-8 flex flex-wrap items-center gap-3">
          {person.has_email && onEmailClick && (
            <Button
              onClick={onEmailClick}
              icon={<Mail className="w-4 h-4" />}
              variant="primary"
              size="md"
            >
              Email
            </Button>
          )}

          {onAddToListClick && (
            <Button
              onClick={onAddToListClick}
              icon={<Plus className="w-4 h-4" />}
              variant="secondary"
              size="md"
            >
              Add to List
            </Button>
          )}

          {onAIChatClick && (
            <Button
              onClick={onAIChatClick}
              icon={<Sparkles className="w-4 h-4 animate-pulse" />}
              className="bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700 border-none focus:ring-purple-500"
              size="md"
            >
              AI Chat
            </Button>
          )}

          {onExportClick && (
            <Button
              onClick={onExportClick}
              icon={<Download className="w-4 h-4" />}
              variant="outline"
              size="md"
            >
              Export
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}

// Match Score Badge Component
interface MatchScoreBadgeProps {
  score: number;
  config: ReturnType<typeof getMatchScoreConfig>;
}

function MatchScoreBadge({ score, config }: MatchScoreBadgeProps) {
  return (
    <div
      className={`
        ${config.bgColor} ${config.borderColor}
        border-2 rounded-xl shadow-md p-4
        min-w-[140px] text-center
        hover:scale-105 hover:shadow-lg
        transition-all duration-200
        flex-shrink-0
        animate-pulse-slow
      `}
      title={`Match score: ${score}%`}
    >
      <div className="text-sm font-semibold text-white/90 mb-1">Match</div>
      <div className="text-3xl font-bold text-white mb-2">{score}%</div>
      <div className="flex justify-center gap-0.5">
        {[...Array(5)].map((_, i) => (
          <span
            key={i}
            className={`text-lg ${i < config.stars ? 'text-white' : 'text-white/30'}`}
          >
            ⭐
          </span>
        ))}
      </div>
    </div>
  );
}

// Helper function to get avatar gradient
function getAvatarGradient(name: string): string {
  const gradients = [
    'bg-gradient-to-br from-indigo-400 to-indigo-600',
    'bg-gradient-to-br from-cyan-400 to-cyan-600',
    'bg-gradient-to-br from-purple-400 to-purple-600',
    'bg-gradient-to-br from-emerald-400 to-emerald-600',
    'bg-gradient-to-br from-pink-400 to-pink-600',
    'bg-gradient-to-br from-amber-400 to-amber-600',
  ];

  const hash = name.split('').reduce((acc, char) => {
    return char.charCodeAt(0) + ((acc << 5) - acc);
  }, 0);

  return gradients[Math.abs(hash) % gradients.length];
}

// Helper function to get match score configuration
function getMatchScoreConfig(score?: number) {
  if (!score || score < 40) {
    return {
      bgColor: 'bg-gray-500',
      borderColor: 'border-gray-600',
      stars: 2,
    };
  }
  if (score < 60) {
    return {
      bgColor: 'bg-blue-500',
      borderColor: 'border-blue-600',
      stars: 3,
    };
  }
  if (score < 80) {
    return {
      bgColor: 'bg-cyan-500',
      borderColor: 'border-cyan-600',
      stars: 4,
    };
  }
  return {
    bgColor: 'bg-emerald-500',
    borderColor: 'border-emerald-600',
    stars: 5,
  };
}

// Add animation to global CSS
const style = document.createElement('style');
style.textContent = `
  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes pulse-slow {
    0%, 100% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.02);
    }
  }

  .animate-fadeInUp {
    animation: fadeInUp 0.4s ease-out;
  }

  .animate-pulse-slow {
    animation: pulse-slow 3s ease-in-out infinite;
  }
`;

if (typeof document !== 'undefined') {
  document.head.appendChild(style);
}

