import React from 'react';

interface EcosystemBadgesProps {
  ecosystems: string[];
  size?: 'sm' | 'md' | 'lg';
  maxDisplay?: number;
}

const ecosystemColors: Record<string, string> = {
  'ethereum': 'bg-purple-100 text-purple-800 border-purple-300',
  'paradigm-ecosystem': 'bg-blue-100 text-blue-800 border-blue-300',
  'eip-author': 'bg-indigo-100 text-indigo-800 border-indigo-300',
  'defi': 'bg-green-100 text-green-800 border-green-300',
  'nft': 'bg-pink-100 text-pink-800 border-pink-300',
  'web3': 'bg-cyan-100 text-cyan-800 border-cyan-300',
  'l2': 'bg-orange-100 text-orange-800 border-orange-300',
};

const ecosystemIcons: Record<string, string> = {
  'ethereum': '⟠',
  'paradigm-ecosystem': '🏛️',
  'eip-author': '📝',
  'defi': '💰',
  'nft': '🎨',
  'web3': '🌐',
  'l2': '⚡',
};

export const EcosystemBadges: React.FC<EcosystemBadgesProps> = ({
  ecosystems,
  size = 'md',
  maxDisplay = 5,
}) => {
  if (!ecosystems || ecosystems.length === 0) {
    return null;
  }

  const displayEcosystems = ecosystems.slice(0, maxDisplay);
  const remainingCount = ecosystems.length - maxDisplay;

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'text-xs px-2 py-0.5';
      case 'lg':
        return 'text-base px-4 py-2';
      default:
        return 'text-sm px-3 py-1';
    }
  };

  return (
    <div className="flex flex-wrap gap-2 items-center">
      {displayEcosystems.map((ecosystem) => {
        const normalizedEcosystem = ecosystem.toLowerCase();
        const color = ecosystemColors[normalizedEcosystem] || 'bg-gray-100 text-gray-800 border-gray-300';
        const icon = ecosystemIcons[normalizedEcosystem] || '🔹';

        return (
          <span
            key={ecosystem}
            className={`inline-flex items-center gap-1.5 rounded-full border ${color} ${getSizeClasses()} font-medium transition-all hover:shadow-md`}
            title={`${ecosystem} ecosystem`}
          >
            <span className="text-base">{icon}</span>
            <span className="capitalize">{ecosystem.replace('-', ' ')}</span>
          </span>
        );
      })}
      {remainingCount > 0 && (
        <span
          className={`inline-flex items-center rounded-full border bg-gray-100 text-gray-600 border-gray-300 ${getSizeClasses()} font-medium`}
          title={`${remainingCount} more ecosystem${remainingCount > 1 ? 's' : ''}`}
        >
          +{remainingCount} more
        </span>
      )}
    </div>
  );
};

export default EcosystemBadges;

