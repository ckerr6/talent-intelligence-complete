import { useEffect, useState } from 'react';
import { X, Github, Star, GitBranch, TrendingUp, MapPin, Briefcase, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Button from '../common/Button';
import Badge from '../common/Badge';
import Card from '../common/Card';

interface TechnologistsModalProps {
  isOpen: boolean;
  onClose: () => void;
  technology: string;
}

interface Technologist {
  person_id: string;
  name: string;
  title?: string;
  location?: string;
  github_username: string;
  current_company?: string;
  current_title?: string;
  stats: {
    repo_count: number;
    total_stars: number;
    max_contributions: number;
    quality_score: number;
  };
  engineer_tier: '10x' | '5x' | 'standard';
  top_repos: string[];
  most_recent_contribution?: string;
}

interface TechnologistsData {
  technology: string;
  total_count: number;
  tier_distribution: {
    '10x': number;
    '5x': number;
    standard: number;
  };
  technologists: Technologist[];
}

export default function TechnologistsModal({
  isOpen,
  onClose,
  technology,
}: TechnologistsModalProps) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<TechnologistsData | null>(null);
  const [sortBy, setSortBy] = useState<'quality' | 'repos' | 'stars' | 'recent'>('quality');

  useEffect(() => {
    if (isOpen && technology) {
      fetchTechnologists();
    }
  }, [isOpen, technology, sortBy]);

  const fetchTechnologists = async () => {
    setLoading(true);
    try {
      const response = await axios.get(
        `http://localhost:8000/api/market/enhanced/technology/${encodeURIComponent(technology)}/technologists`,
        {
          params: {
            limit: 50,
            sort_by: sortBy,
          },
        }
      );
      setData(response.data);
    } catch (err) {
      console.error('Error fetching technologists:', err);
    } finally {
      setLoading(false);
    }
  };

  const getTierBadge = (tier: string) => {
    if (tier === '10x') {
      return <Badge variant="success" size="sm">⭐ 10x Engineer</Badge>;
    }
    if (tier === '5x') {
      return <Badge variant="info" size="sm">🌟 5x Engineer</Badge>;
    }
    return null;
  };

  const getTierColor = (tier: string) => {
    if (tier === '10x') return 'bg-green-50 border-green-200';
    if (tier === '5x') return 'bg-blue-50 border-blue-200';
    return 'bg-white border-gray-200';
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl max-w-6xl w-full mx-4 my-8 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <GitBranch className="w-6 h-6 text-primary-600" />
              {technology} Developers
            </h2>
            {data && (
              <p className="text-sm text-gray-600 mt-1">
                {data.total_count} technologists found •{' '}
                <span className="text-green-600 font-medium">{data.tier_distribution['10x']} 10x</span> •{' '}
                <span className="text-blue-600 font-medium">{data.tier_distribution['5x']} 5x</span>
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Sort Controls */}
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">Sort by:</span>
            <div className="flex gap-2">
              {[
                { value: 'quality', label: 'Quality Score', icon: <TrendingUp className="w-4 h-4" /> },
                { value: 'repos', label: 'Repositories', icon: <GitBranch className="w-4 h-4" /> },
                { value: 'stars', label: 'Stars', icon: <Star className="w-4 h-4" /> },
                { value: 'recent', label: 'Recent Activity', icon: <Github className="w-4 h-4" /> },
              ].map((option) => (
                <button
                  key={option.value}
                  onClick={() => setSortBy(option.value as any)}
                  className={`px-3 py-1.5 text-sm rounded-lg flex items-center gap-1.5 transition-colors ${
                    sortBy === option.value
                      ? 'bg-primary-600 text-white'
                      : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                  }`}
                >
                  {option.icon}
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading technologists...</p>
              </div>
            </div>
          ) : data && data.technologists.length > 0 ? (
            <div className="space-y-4">
              {data.technologists.map((tech, idx) => (
                <Card
                  key={tech.person_id}
                  padding="sm"
                  className={`hover:shadow-lg transition-shadow cursor-pointer border-2 ${getTierColor(tech.engineer_tier)}`}
                  onClick={() => {
                    navigate(`/profile/${tech.person_id}`);
                    onClose();
                  }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-lg font-medium text-gray-500">#{idx + 1}</span>
                          <h3 className="text-lg font-semibold text-gray-900">{tech.name}</h3>
                        </div>
                        {getTierBadge(tech.engineer_tier)}
                        <Badge variant="default" size="sm">
                          Score: {tech.stats.quality_score}/100
                        </Badge>
                      </div>

                      <div className="flex flex-wrap gap-4 text-sm text-gray-600 mb-3">
                        {tech.current_company && (
                          <div className="flex items-center gap-1">
                            <Briefcase className="w-4 h-4" />
                            {tech.current_title ? `${tech.current_title} at ${tech.current_company}` : tech.current_company}
                          </div>
                        )}
                        {tech.location && (
                          <div className="flex items-center gap-1">
                            <MapPin className="w-4 h-4" />
                            {tech.location}
                          </div>
                        )}
                        {tech.github_username && (
                          <a
                            href={`https://github.com/${tech.github_username}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="flex items-center gap-1 text-primary-600 hover:text-primary-700"
                          >
                            <Github className="w-4 h-4" />
                            {tech.github_username}
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>

                      {/* Stats */}
                      <div className="flex flex-wrap gap-4 mb-2">
                        <div className="flex items-center gap-1 text-sm">
                          <GitBranch className="w-4 h-4 text-gray-400" />
                          <span className="font-medium text-gray-900">{tech.stats.repo_count}</span>
                          <span className="text-gray-600">repos</span>
                        </div>
                        <div className="flex items-center gap-1 text-sm">
                          <Star className="w-4 h-4 text-yellow-500" />
                          <span className="font-medium text-gray-900">{tech.stats.total_stars.toLocaleString()}</span>
                          <span className="text-gray-600">stars</span>
                        </div>
                        {tech.stats.max_contributions > 0 && (
                          <div className="flex items-center gap-1 text-sm">
                            <TrendingUp className="w-4 h-4 text-green-500" />
                            <span className="font-medium text-gray-900">{tech.stats.max_contributions}</span>
                            <span className="text-gray-600">contributions</span>
                          </div>
                        )}
                      </div>

                      {/* Top Repos */}
                      {tech.top_repos && tech.top_repos.length > 0 && (
                        <div className="text-sm">
                          <span className="text-gray-600">Top repos: </span>
                          <span className="text-gray-900 font-mono text-xs">
                            {tech.top_repos.slice(0, 3).join(', ')}
                          </span>
                        </div>
                      )}
                    </div>

                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/profile/${tech.person_id}`);
                        onClose();
                      }}
                    >
                      View Profile
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-600">No technologists found for {technology}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div>
              <strong>10x Engineers:</strong> 10+ repos, 500+ stars, active in last 6 months
            </div>
            <div>
              <strong>5x Engineers:</strong> 5+ repos, 100+ stars, active in last 12 months
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

