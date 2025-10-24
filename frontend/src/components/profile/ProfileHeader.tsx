import { useState, useEffect } from 'react';
import { RefreshCw, Github, Sparkles } from 'lucide-react';
import axios from 'axios';
import type { Person } from '../../types';
import Button from '../common/Button';

interface ProfileHeaderProps {
  person: Person & {
    github_username?: string;
    has_email?: boolean;
    has_github?: boolean;
  };
}

export default function ProfileHeader({ person }: ProfileHeaderProps) {
  const [refreshing, setRefreshing] = useState(false);
  const [refreshStatus, setRefreshStatus] = useState<string | null>(null);
  const [enriching, setEnriching] = useState(false);
  const [enrichStatus, setEnrichStatus] = useState<string | null>(null);

  // Auto-trigger enrichment if profile has GitHub but no enhanced stats
  useEffect(() => {
    const checkAndEnrich = async () => {
      if (!person.person_id || !person.github_username) return;

      try {
        // Check if already enriched
        const statusResponse = await axios.get(
          `http://localhost:8000/api/profile/${person.person_id}/enrichment-status`
        );

        if (statusResponse.data.has_github && !statusResponse.data.is_enriched) {
          // Trigger enrichment in background
          setEnriching(true);
          setEnrichStatus('Calculating enhanced stats...');

          await axios.post(
            `http://localhost:8000/api/profile/${person.person_id}/enrich-github`
          );

          // Update status after a delay
          setTimeout(() => {
            setEnriching(false);
            setEnrichStatus('✓ Stats updated! Refresh to see.');
            setTimeout(() => setEnrichStatus(null), 5000);
          }, 15000); // Wait 15 seconds for enrichment to complete
        }
      } catch (error) {
        console.error('Auto-enrichment error:', error);
      }
    };

    checkAndEnrich();
  }, [person.person_id, person.github_username]);

  const handleRefreshGitHub = async () => {
    // Extract GitHub username from the person's GitHub data
    const githubUsername = person.github_username;
    
    if (!githubUsername) {
      setRefreshStatus('No GitHub profile found');
      setTimeout(() => setRefreshStatus(null), 3000);
      return;
    }

    setRefreshing(true);
    setRefreshStatus('Starting refresh...');

    try {
      // Call the ingestion API to refresh this user's data
      const response = await axios.post(
        `http://localhost:8000/api/github/ingest/user/${githubUsername}`
      );

      setRefreshStatus('Refreshing GitHub data...');
      
      // Poll for job status
      const jobId = response.data.job_id;
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await axios.get(
            `http://localhost:8000/api/github/ingest/status/${jobId}`
          );
          
          if (statusResponse.data.status === 'completed') {
            clearInterval(pollInterval);
            setRefreshStatus('✓ Refresh complete! Reload page to see updates.');
            setRefreshing(false);
            setTimeout(() => setRefreshStatus(null), 5000);
          } else if (statusResponse.data.status === 'failed') {
            clearInterval(pollInterval);
            setRefreshStatus(`Failed: ${statusResponse.data.error}`);
            setRefreshing(false);
            setTimeout(() => setRefreshStatus(null), 5000);
          }
        } catch (err) {
          clearInterval(pollInterval);
          setRefreshing(false);
          setRefreshStatus('Error checking status');
          setTimeout(() => setRefreshStatus(null), 3000);
        }
      }, 2000);
    } catch (error: any) {
      setRefreshing(false);
      setRefreshStatus(`Error: ${error.response?.data?.detail || 'Unknown error'}`);
      setTimeout(() => setRefreshStatus(null), 3000);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-4">
          {/* Avatar */}
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary-400 to-secondary-400 flex items-center justify-center text-white text-2xl font-bold">
            {person.full_name
              .split(' ')
              .map((n) => n[0])
              .join('')
              .toUpperCase()
              .slice(0, 2)}
          </div>

          {/* Name and headline */}
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{person.full_name}</h1>
            {person.headline && (
              <p className="mt-1 text-lg text-gray-600">{person.headline}</p>
            )}
            {person.location && (
              <p className="mt-2 text-sm text-gray-500 flex items-center">
                <span className="mr-1">📍</span>
                {person.location}
              </p>
            )}
            {person.refreshed_at && (
              <p className="mt-1 text-xs text-gray-400">
                Last updated: {new Date(person.refreshed_at).toLocaleDateString()}
              </p>
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center space-x-3">
          {/* Enrichment Status Indicator */}
          {enriching && (
            <div className="flex items-center gap-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg">
              <Sparkles className="w-4 h-4 text-blue-600 animate-pulse" />
              <span className="text-xs text-blue-700">{enrichStatus}</span>
            </div>
          )}
          {!enriching && enrichStatus && (
            <div className="flex items-center gap-2 px-3 py-2 bg-green-50 border border-green-200 rounded-lg">
              <span className="text-xs text-green-700">{enrichStatus}</span>
            </div>
          )}

          {/* Refresh GitHub button */}
          {person.github_username && (
            <div className="flex flex-col items-end">
              <Button
                variant="secondary"
                size="sm"
                onClick={handleRefreshGitHub}
                disabled={refreshing || enriching}
                icon={refreshing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Github className="w-4 h-4" />}
              >
                {refreshing ? 'Refreshing...' : 'Refresh GitHub'}
              </Button>
              {refreshStatus && (
                <p className="mt-1 text-xs text-gray-600">{refreshStatus}</p>
              )}
            </div>
          )}

          {/* LinkedIn Link */}
          {person.linkedin_url && (
            <a
              href={person.linkedin_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
            >
              <span>in</span>
              <span>LinkedIn</span>
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

