import { useState, useEffect } from 'react';
import { X, Github, Users, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Button from '../common/Button';
import axios from 'axios';

interface GitHubIngestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (result: any) => void;
}

type IngestionType = 'user' | 'organization';
type JobStatus = 'idle' | 'pending' | 'running' | 'completed' | 'failed';

interface IngestionJob {
  job_id: string;
  status: JobStatus;
  progress?: string;
  result?: any;
  error?: string;
}

export default function GitHubIngestionModal({
  isOpen,
  onClose,
  onSuccess,
}: GitHubIngestionModalProps) {
  const navigate = useNavigate();
  const [type, setType] = useState<IngestionType>('user');
  const [input, setInput] = useState('');
  const [job, setJob] = useState<IngestionJob | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Poll job status
  useEffect(() => {
    if (!job || job.status === 'completed' || job.status === 'failed') {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const response = await axios.get(
          `http://localhost:8000/api/github/ingest/status/${job.job_id}`
        );
        const updatedJob = response.data;
        setJob(updatedJob);

        if (updatedJob.status === 'completed') {
          if (onSuccess) {
            onSuccess(updatedJob.result);
          }
        }
      } catch (err: any) {
        console.error('Error polling job status:', err);
        setError(err.response?.data?.detail || 'Failed to check job status');
        clearInterval(interval);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [job, onSuccess]);

  const extractUsername = (inputStr: string): string => {
    // Extract username from GitHub URL or return as-is
    const patterns = [
      /github\.com\/([^\/\?]+)/,  // https://github.com/username
      /^@?([a-zA-Z0-9-]+)$/,      // @username or username
    ];

    for (const pattern of patterns) {
      const match = inputStr.match(pattern);
      if (match) {
        return match[1];
      }
    }

    return inputStr.trim();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!input.trim()) {
      setError('Please enter a GitHub username or URL');
      return;
    }

    const username = extractUsername(input);

    try {
      const endpoint =
        type === 'user'
          ? `http://localhost:8000/api/github/ingest/user/${username}`
          : `http://localhost:8000/api/github/ingest/org/${username}`;

      const response = await axios.post(endpoint);
      setJob(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start ingestion');
    }
  };

  const handleClose = () => {
    setInput('');
    setJob(null);
    setError(null);
    onClose();
  };

  const renderStatusIcon = () => {
    if (!job) return null;

    switch (job.status) {
      case 'pending':
      case 'running':
        return <Loader2 className="w-5 h-5 animate-spin text-blue-500" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return null;
    }
  };

  const renderProgress = () => {
    if (!job) return null;

    const { status, progress, result, error: jobError } = job;

    return (
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-start space-x-3">
          {renderStatusIcon()}
          <div className="flex-1">
            <h4 className="font-medium text-gray-900 capitalize">{status}</h4>
            
            {progress && (
              <p className="text-sm text-gray-600 mt-1">{progress}</p>
            )}

            {result && status === 'completed' && (
              <div className="mt-3 space-y-2">
                <p className="text-sm text-green-700 font-medium">
                  ✓ Ingestion completed successfully!
                </p>
                <div className="text-sm text-gray-700 space-y-1">
                  {result.person_id && (
                    <div>Person ID: <code className="bg-gray-200 px-1 rounded">{result.person_id}</code></div>
                  )}
                  {result.company_id && (
                    <div>Company ID: <code className="bg-gray-200 px-1 rounded">{result.company_id}</code></div>
                  )}
                  {result.stats && (
                    <div className="mt-2">
                      <div>Users processed: {result.stats.users_processed || result.members_processed || 0}</div>
                      <div>Profiles matched: {result.stats.profiles_matched || 0}</div>
                      <div>Profiles created: {result.stats.profiles_created || 0}</div>
                      <div>Repos added: {result.stats.repos_added || result.repos_processed || 0}</div>
                      <div>Contributions added: {result.stats.contributions_added || 0}</div>
                    </div>
                  )}
                </div>
                <div className="mt-3 flex gap-2">
                  {result.person_id && (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => {
                        navigate(`/profile/${result.person_id}`);
                        handleClose();
                      }}
                    >
                      View Profile
                    </Button>
                  )}
                  {result.company_id && type === 'organization' && (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => {
                        navigate(`/company/${result.company_id}`);
                        handleClose();
                      }}
                    >
                      View Company
                    </Button>
                  )}
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={handleClose}
                  >
                    Close
                  </Button>
                </div>
              </div>
            )}

            {jobError && status === 'failed' && (
              <div className="mt-3">
                <p className="text-sm text-red-700">Error: {jobError}</p>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setJob(null)}
                  className="mt-3"
                >
                  Try Again
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Github className="w-6 h-6 text-gray-700" />
            <h2 className="text-xl font-semibold text-gray-900">
              Add GitHub Data
            </h2>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Description */}
        <p className="text-sm text-gray-600 mb-6">
          Import data from a GitHub user or organization. We'll automatically
          match profiles with existing people in your database.
        </p>

        {!job && (
          <form onSubmit={handleSubmit}>
            {/* Type selector */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Type
              </label>
              <div className="flex space-x-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="user"
                    checked={type === 'user'}
                    onChange={(e) => setType(e.target.value as IngestionType)}
                    className="mr-2"
                  />
                  <Users className="w-4 h-4 mr-1" />
                  Individual User
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="organization"
                    checked={type === 'organization'}
                    onChange={(e) => setType(e.target.value as IngestionType)}
                    className="mr-2"
                  />
                  <Github className="w-4 h-4 mr-1" />
                  Organization
                </label>
              </div>
            </div>

            {/* Input field */}
            <div className="mb-4">
              <label
                htmlFor="github-input"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                GitHub URL or Username
              </label>
              <input
                id="github-input"
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={
                  type === 'user'
                    ? 'https://github.com/uni-guillaume or uni-guillaume'
                    : 'https://github.com/uniswap or uniswap'
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Error message */}
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {/* Actions */}
            <div className="flex space-x-3">
              <Button type="submit" variant="primary" className="flex-1">
                Start Ingestion
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={handleClose}
              >
                Cancel
              </Button>
            </div>
          </form>
        )}

        {/* Progress display */}
        {renderProgress()}

        {/* Info */}
        {!job && (
          <div className="mt-6 p-3 bg-blue-50 border border-blue-200 rounded-md">
            <p className="text-xs text-blue-800">
              <strong>Note:</strong>{' '}
              {type === 'organization'
                ? 'Large organizations may take several minutes to process. You can close this dialog and check progress later.'
                : 'This will fetch the user\'s repositories and contributions. The process typically takes 10-30 seconds.'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

