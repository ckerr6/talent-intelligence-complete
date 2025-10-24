import { useEffect, useState } from 'react';
import { Mail, Plus, Sparkles, Download } from 'lucide-react';
import Button from '../common/Button';

export interface Person {
  person_id: string;
  full_name: string;
  has_email?: boolean;
}

interface StickyActionBarProps {
  person: Person;
  matchScore?: number;
  onEmailClick?: () => void;
  onAddToListClick?: () => void;
  onAIChatClick?: () => void;
  onExportClick?: () => void;
  heroRef?: React.RefObject<HTMLElement>;
}

export default function StickyActionBar({
  person,
  matchScore,
  onEmailClick,
  onAddToListClick,
  onAIChatClick,
  onExportClick,
  heroRef,
}: StickyActionBarProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      if (heroRef?.current) {
        const heroBottom = heroRef.current.getBoundingClientRect().bottom;
        const shouldShow = heroBottom < 0;
        setIsVisible(shouldShow);
      }

      // Calculate scroll progress
      const windowHeight = window.innerHeight;
      const documentHeight = document.documentElement.scrollHeight;
      const scrollTop = window.scrollY;
      const progress = (scrollTop / (documentHeight - windowHeight)) * 100;
      setScrollProgress(Math.min(100, Math.max(0, progress)));
    };

    window.addEventListener('scroll', handleScroll);
    handleScroll(); // Check initial state

    return () => window.removeEventListener('scroll', handleScroll);
  }, [heroRef]);

  // Generate initials
  const initials = person.full_name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  // Get avatar gradient (same logic as ProfileHero)
  const getAvatarGradient = (name: string): string => {
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
  };

  const gradientClass = getAvatarGradient(person.full_name);

  return (
    <>
      {/* Sticky Action Bar */}
      <div
        className={`
          fixed top-0 left-0 right-0 z-50
          bg-white border-b border-gray-200 shadow-md
          transition-all duration-300 ease-in-out
          ${isVisible ? 'translate-y-0 opacity-100' : '-translate-y-full opacity-0'}
        `}
      >
        {/* Progress bar */}
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-100">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 to-cyan-500 transition-all duration-200"
            style={{ width: `${scrollProgress}%` }}
          />
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Left: Person info */}
            <div className="flex items-center gap-3 min-w-0 flex-1">
              {/* Small avatar */}
              <div
                className={`
                  w-10 h-10 rounded-full
                  ${gradientClass}
                  flex items-center justify-center
                  text-white text-sm font-bold
                  shadow-md flex-shrink-0
                `}
              >
                {initials}
              </div>

              {/* Name and match score */}
              <div className="min-w-0 flex-1">
                <h2 className="text-base font-semibold text-gray-900 truncate">
                  {person.full_name}
                </h2>
                {matchScore !== undefined && (
                  <p className="text-xs text-gray-600">
                    Match: <span className="font-semibold text-indigo-600">{matchScore}%</span>
                  </p>
                )}
              </div>
            </div>

            {/* Right: Actions */}
            <div className="flex items-center gap-2 flex-shrink-0">
              {person.has_email && onEmailClick && (
                <Button
                  onClick={onEmailClick}
                  icon={<Mail className="w-4 h-4" />}
                  variant="primary"
                  size="sm"
                  className="hidden sm:inline-flex"
                >
                  Email
                </Button>
              )}

              {onAddToListClick && (
                <Button
                  onClick={onAddToListClick}
                  icon={<Plus className="w-4 h-4" />}
                  variant="secondary"
                  size="sm"
                  className="hidden md:inline-flex"
                >
                  Add to List
                </Button>
              )}

              {onAIChatClick && (
                <Button
                  onClick={onAIChatClick}
                  icon={<Sparkles className="w-4 h-4" />}
                  className="bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700 border-none"
                  size="sm"
                >
                  <span className="hidden lg:inline">AI Chat</span>
                  <span className="lg:hidden">AI</span>
                </Button>
              )}

              {onExportClick && (
                <Button
                  onClick={onExportClick}
                  icon={<Download className="w-4 h-4" />}
                  variant="ghost"
                  size="sm"
                  className="hidden xl:inline-flex"
                />
              )}

              {/* Mobile: Show icons only */}
              {person.has_email && onEmailClick && (
                <Button
                  onClick={onEmailClick}
                  icon={<Mail className="w-4 h-4" />}
                  variant="primary"
                  size="sm"
                  className="sm:hidden"
                  aria-label="Send email"
                />
              )}

              {onAddToListClick && (
                <Button
                  onClick={onAddToListClick}
                  icon={<Plus className="w-4 h-4" />}
                  variant="secondary"
                  size="sm"
                  className="md:hidden"
                  aria-label="Add to list"
                />
              )}

              {onExportClick && (
                <Button
                  onClick={onExportClick}
                  icon={<Download className="w-4 h-4" />}
                  variant="ghost"
                  size="sm"
                  className="xl:hidden"
                  aria-label="Export profile"
                />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Spacer to prevent content jump when sticky bar appears */}
      {isVisible && <div className="h-16" />}
    </>
  );
}

