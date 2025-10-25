import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  Github, Mail, Twitter, Globe, MapPin, Building, Star,
  TrendingUp, Users, Code, Clock, Target
} from 'lucide-react';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import { SkeletonList } from '../../components/common/Skeleton';

interface GitHubIntelligence {
  username: string;
  seniority: string;
  seniority_confidence: number;
  primary_languages: Record<string, any>;
  frameworks: string[];
  domains: string[];
  influence_score: number;
  reachability_score: number;
  activity_trend: string;
  organizations: string[];
}

export default function GitHubDeveloperProfile() {
  const { username } = useParams<{ username: string }>();
  const [analyzing, setAnalyzing] = useState(false);

  const { data: profile, isLoading, error, refetch } = useQuery({
    queryKey: ['github-profile', username],
    queryFn: async () => {
      const response = await fetch(`/api/github-intelligence/profile/${username}`);
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Profile not found');
        }
        throw new Error('Failed to fetch profile');
      }
      return response.json() as Promise<GitHubIntelligence>;
    },
    enabled: !!username,
    retry: false
  });

  const handleAnalyze = async () => {
    if (!username) return;
    
    setAnalyzing(true);
    try {
      const response = await fetch(`/api/github-intelligence/analyze/${username}`, {
        method: 'POST'
      });
      if (response.ok) {
        // Refetch after analysis
        setTimeout(() => refetch(), 2000);
      }
    } catch (error) {
      console.error('Failed to analyze profile:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <SkeletonList count={3} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="p-8 text-center">
          <Github className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h2 className="text-2xl font-bold mb-2">Profile Not Found</h2>
          <p className="text-gray-600 mb-6">
            @{username} hasn't been analyzed yet or doesn't exist on GitHub.
          </p>
          <Button onClick={handleAnalyze} disabled={analyzing}>
            {analyzing ? 'Analyzing...' : 'Analyze This Profile'}
          </Button>
        </Card>
      </div>
    );
  }

  if (!profile) return null;

  // Get top languages sorted by size
  const languages = profile.primary_languages 
    ? Object.entries(profile.primary_languages)
        .sort((a: any, b: any) => (b[1]?.bytes || 0) - (a[1]?.bytes || 0))
        .slice(0, 5)
    : [];

  return (
    <div className="container mx-auto px-4 py-8 space-y-6">
      {/* Header Card */}
      <Card className="p-8">
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center space-x-4">
            <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <Github className="w-10 h-10 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold mb-1">@{profile.username}</h1>
              <div className="flex items-center space-x-4 text-gray-600">
                <span className="flex items-center">
                  <Target className="w-4 h-4 mr-1" />
                  {profile.seniority}
                </span>
                <span className="flex items-center">
                  <Star className="w-4 h-4 mr-1" />
                  {profile.influence_score}/100 Influence
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex space-x-2">
            <Button variant="outline" size="sm" onClick={handleAnalyze}>
              Refresh Analysis
            </Button>
            <Button size="sm">
              <Mail className="w-4 h-4 mr-2" />
              Contact
            </Button>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">Seniority</div>
            <div className="text-2xl font-bold text-blue-600">{profile.seniority}</div>
            <div className="text-xs text-gray-500">{(profile.seniority_confidence * 100).toFixed(0)}% confidence</div>
          </div>
          
          <div className="bg-green-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">Influence</div>
            <div className="text-2xl font-bold text-green-600">{profile.influence_score}/100</div>
            <div className="text-xs text-gray-500">Community impact</div>
          </div>
          
          <div className="bg-purple-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">Reachability</div>
            <div className="text-2xl font-bold text-purple-600">{profile.reachability_score}/100</div>
            <div className="text-xs text-gray-500">Contact likelihood</div>
          </div>
          
          <div className="bg-orange-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">Activity</div>
            <div className="text-2xl font-bold text-orange-600">{profile.activity_trend}</div>
            <div className="text-xs text-gray-500">Recent trend</div>
          </div>
        </div>
      </Card>

      {/* Skills & Tech Stack */}
      <div className="grid grid-cols-2 gap-6">
        {/* Languages */}
        <Card className="p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center">
            <Code className="w-5 h-5 mr-2" />
            Primary Languages
          </h2>
          <div className="space-y-3">
            {languages.map(([lang, data]: [string, any]) => {
              const percentage = data?.percentage || 0;
              return (
                <div key={lang}>
                  <div className="flex justify-between mb-1">
                    <span className="font-medium">{lang}</span>
                    <span className="text-sm text-gray-600">{percentage.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Frameworks & Tools */}
        <Card className="p-6">
          <h2 className="text-xl font-bold mb-4">Frameworks & Tools</h2>
          <div className="space-y-4">
            <div>
              <div className="text-sm font-medium text-gray-600 mb-2">Frameworks</div>
              <div className="flex flex-wrap gap-2">
                {profile.frameworks.slice(0, 8).map((framework: string) => (
                  <span 
                    key={framework}
                    className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium"
                  >
                    {framework}
                  </span>
                ))}
              </div>
            </div>
            
            <div>
              <div className="text-sm font-medium text-gray-600 mb-2">Domains</div>
              <div className="flex flex-wrap gap-2">
                {profile.domains.map((domain: string) => (
                  <span 
                    key={domain}
                    className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium"
                  >
                    {domain}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Network & Organizations */}
      {profile.organizations.length > 0 && (
        <Card className="p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center">
            <Users className="w-5 h-5 mr-2" />
            Organizations
          </h2>
          <div className="flex flex-wrap gap-2">
            {profile.organizations.map((org: string) => (
              <div 
                key={org}
                className="flex items-center px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors cursor-pointer"
              >
                <Building className="w-4 h-4 mr-2 text-gray-600" />
                <span className="font-medium">{org}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Outreach Section */}
      <Card className="p-6 bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
        <h2 className="text-xl font-bold mb-4">Outreach Tips</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm font-medium text-gray-600 mb-2">Reachability Score</div>
            <div className="flex items-center">
              <div className="text-3xl font-bold text-blue-600">{profile.reachability_score}</div>
              <div className="text-sm text-gray-600 ml-2">/ 100</div>
            </div>
            <p className="text-sm text-gray-600 mt-1">
              {profile.reachability_score >= 80 ? 'Very High' : 
               profile.reachability_score >= 60 ? 'High' :
               profile.reachability_score >= 40 ? 'Medium' : 'Low'} likelihood of response
            </p>
          </div>
          
          <div>
            <div className="text-sm font-medium text-gray-600 mb-2">Best Approach</div>
            <ul className="space-y-2 text-sm">
              <li className="flex items-start">
                <Mail className="w-4 h-4 mr-2 mt-0.5 text-blue-600" />
                <span>Direct email (professional)</span>
              </li>
              <li className="flex items-start">
                <Github className="w-4 h-4 mr-2 mt-0.5 text-gray-600" />
                <span>GitHub issue/discussion</span>
              </li>
              <li className="flex items-start">
                <Users className="w-4 h-4 mr-2 mt-0.5 text-purple-600" />
                <span>Warm intro via {profile.organizations[0] || 'network'}</span>
              </li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
}

