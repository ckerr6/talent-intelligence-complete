import { useRef, KeyboardEvent } from 'react';
import { Home, Briefcase, Github, Users, Sparkles } from 'lucide-react';

export interface Tab {
  id: string;
  label: string;
  badge?: string | number;
  icon?: React.ReactNode;
  color?: 'emerald' | 'cyan' | 'blue' | 'gray';
}

interface TabNavigationProps {
  activeTab: string;
  onTabChange: (tabId: string) => void;
  tabs: Tab[];
  className?: string;
}

export default function TabNavigation({
  activeTab,
  onTabChange,
  tabs,
  className = '',
}: TabNavigationProps) {
  const tabListRef = useRef<HTMLDivElement>(null);

  const handleKeyDown = (e: KeyboardEvent, currentIndex: number) => {
    let newIndex = currentIndex;

    if (e.key === 'ArrowLeft') {
      newIndex = Math.max(0, currentIndex - 1);
    } else if (e.key === 'ArrowRight') {
      newIndex = Math.min(tabs.length - 1, currentIndex + 1);
    } else if (e.key === 'Home') {
      newIndex = 0;
    } else if (e.key === 'End') {
      newIndex = tabs.length - 1;
    } else {
      return;
    }

    e.preventDefault();
    onTabChange(tabs[newIndex].id);
  };

  return (
    <div
      ref={tabListRef}
      role="tablist"
      aria-label="Profile sections"
      className={`
        sticky top-16 z-40 bg-white border-b-2 border-gray-200 shadow-sm
        ${className}
      `}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex space-x-1 overflow-x-auto scrollbar-hide">
          {tabs.map((tab, index) => {
            const isActive = tab.id === activeTab;
            const isAITab = tab.id === 'ai-insights';

            return (
              <button
                key={tab.id}
                role="tab"
                aria-selected={isActive}
                aria-controls={`${tab.id}-panel`}
                id={`${tab.id}-tab`}
                tabIndex={isActive ? 0 : -1}
                onClick={() => onTabChange(tab.id)}
                onKeyDown={(e) => handleKeyDown(e, index)}
                className={`
                  flex items-center gap-2 px-4 sm:px-6 py-4
                  font-semibold text-sm sm:text-base
                  border-b-2 transition-all duration-200
                  whitespace-nowrap
                  ${
                    isActive
                      ? 'text-indigo-600 border-indigo-600'
                      : 'text-gray-600 border-transparent hover:text-gray-900 hover:bg-gray-50'
                  }
                  ${isAITab && !isActive ? 'hover:bg-gradient-to-r hover:from-purple-50 hover:to-pink-50' : ''}
                  focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
                `}
              >
                {/* Icon */}
                {tab.icon && (
                  <span
                    className={`
                      inline-flex items-center
                      ${isAITab ? 'animate-pulse' : ''}
                    `}
                  >
                    {tab.icon}
                  </span>
                )}

                {/* Label */}
                <span>{tab.label}</span>

                {/* Badge */}
                {tab.badge !== undefined && tab.badge !== null && (
                  <TabBadge
                    value={tab.badge}
                    isActive={isActive}
                    color={tab.color}
                  />
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// Tab Badge Component
interface TabBadgeProps {
  value: string | number;
  isActive: boolean;
  color?: 'emerald' | 'cyan' | 'blue' | 'gray';
}

function TabBadge({ value, isActive, color }: TabBadgeProps) {
  const getColorClasses = () => {
    if (isActive) {
      switch (color) {
        case 'emerald':
          return 'bg-emerald-100 text-emerald-700 border-emerald-200';
        case 'cyan':
          return 'bg-cyan-100 text-cyan-700 border-cyan-200';
        case 'blue':
          return 'bg-blue-100 text-blue-700 border-blue-200';
        default:
          return 'bg-indigo-100 text-indigo-700 border-indigo-200';
      }
    }

    switch (color) {
      case 'emerald':
        return 'bg-emerald-50 text-emerald-600 border-emerald-100';
      case 'cyan':
        return 'bg-cyan-50 text-cyan-600 border-cyan-100';
      case 'blue':
        return 'bg-blue-50 text-blue-600 border-blue-100';
      default:
        return 'bg-gray-200 text-gray-700 border-gray-300';
    }
  };

  return (
    <span
      className={`
        inline-flex items-center justify-center
        min-w-[24px] h-5 px-2 rounded-full
        text-xs font-bold border
        transition-all duration-200
        ${getColorClasses()}
      `}
    >
      {value}
    </span>
  );
}

// Helper function to create default tabs for a profile
export function createProfileTabs(profile: {
  employment?: any[];
  github_profile?: { public_repos?: number };
  network_stats?: { total_connections?: number; shortest_path_length?: number };
  ai_insights_viewed?: boolean;
}): Tab[] {
  return [
    {
      id: 'overview',
      label: 'Overview',
      icon: <Home className="w-4 h-4" />,
    },
    {
      id: 'experience',
      label: 'Experience',
      icon: <Briefcase className="w-4 h-4" />,
      badge: profile.employment?.length || 0,
    },
    {
      id: 'code',
      label: 'Code',
      icon: <Github className="w-4 h-4" />,
      badge: profile.github_profile?.public_repos || 0,
      color: (profile.github_profile?.public_repos || 0) >= 50 ? 'emerald' : 
             (profile.github_profile?.public_repos || 0) >= 10 ? 'cyan' : 'gray',
    },
    {
      id: 'network',
      label: 'Network',
      icon: <Users className="w-4 h-4" />,
      badge: profile.network_stats?.shortest_path_length 
        ? `${profile.network_stats.shortest_path_length}°`
        : profile.network_stats?.total_connections || '',
    },
    {
      id: 'ai-insights',
      label: 'AI Insights',
      icon: <Sparkles className="w-4 h-4" />,
      badge: !profile.ai_insights_viewed ? 'New' : undefined,
    },
  ];
}

// Add scrollbar-hide utility to global CSS
const style = document.createElement('style');
style.textContent = `
  .scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }

  .scrollbar-hide::-webkit-scrollbar {
    display: none;
  }

  @media (max-width: 640px) {
    .scrollbar-hide {
      scroll-snap-type: x mandatory;
    }

    .scrollbar-hide > button {
      scroll-snap-align: start;
    }
  }
`;

if (typeof document !== 'undefined') {
  document.head.appendChild(style);
}

