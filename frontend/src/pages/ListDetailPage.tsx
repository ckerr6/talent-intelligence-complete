import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, UserPlus, X, ExternalLink, MapPin, Briefcase, Mail, Linkedin, Github } from 'lucide-react';

interface ListMember {
  person_id: string;
  full_name: string;
  headline?: string;
  location?: string;
  linkedin_url?: string;
  added_at: string;
  notes?: string;
}

interface CandidateList {
  list_id: string;
  name: string;
  description?: string;
  member_count: number;
  members: ListMember[];
  created_at: string;
  updated_at: string;
}

export default function ListDetailPage() {
  const { listId } = useParams();
  const navigate = useNavigate();
  const [list, setList] = useState<CandidateList | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (listId) {
      loadListDetail();
    }
  }, [listId]);

  const loadListDetail = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/workflow/lists/${listId}`);
      const data = await response.json();
      if (data.success) {
        setList(data.list);
      }
    } catch (error) {
      console.error('Error loading list:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveMember = async (personId: string) => {
    if (!confirm('Remove this person from the list?')) return;

    try {
      const response = await fetch(`/api/workflow/lists/${listId}/members/${personId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        loadListDetail();
      }
    } catch (error) {
      console.error('Error removing member:', error);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading list...</p>
        </div>
      </div>
    );
  }

  if (!list) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <p className="text-gray-600">List not found</p>
          <button
            onClick={() => navigate('/lists')}
            className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            Back to Lists
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <button
          onClick={() => navigate('/lists')}
          className="flex items-center text-purple-600 hover:text-purple-700 mb-4 font-medium"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Lists
        </button>

        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{list.name}</h1>
            {list.description && (
              <p className="mt-2 text-gray-600">{list.description}</p>
            )}
            <div className="mt-3 flex items-center space-x-4 text-sm text-gray-500">
              <span>{list.member_count} {list.member_count === 1 ? 'person' : 'people'}</span>
              <span>•</span>
              <span>Updated {new Date(list.updated_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Empty State */}
      {list.members.length === 0 && (
        <div className="bg-gradient-to-br from-purple-50 to-blue-50 border-2 border-purple-200 rounded-lg p-12 text-center">
          <UserPlus className="w-16 h-16 text-purple-400 mx-auto mb-4" />
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            No candidates yet
          </h2>
          <p className="text-gray-600 mb-6">
            Add people to this list from search results or profile pages
          </p>
        </div>
      )}

      {/* Members List */}
      {list.members.length > 0 && (
        <div className="bg-white rounded-lg shadow-md divide-y divide-gray-200">
          {list.members.map((member) => (
            <div
              key={member.person_id}
              className="p-6 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {/* Name and Title */}
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <Link
                        to={`/profile/${member.person_id}`}
                        className="text-lg font-semibold text-purple-600 hover:text-purple-700 flex items-center"
                      >
                        {member.full_name}
                        <ExternalLink className="w-4 h-4 ml-2" />
                      </Link>
                      {member.headline && (
                        <p className="text-gray-600 mt-1">{member.headline}</p>
                      )}
                    </div>
                  </div>

                  {/* Location */}
                  {member.location && (
                    <div className="flex items-center text-sm text-gray-500 mb-2">
                      <MapPin className="w-4 h-4 mr-1" />
                      <span>{member.location}</span>
                    </div>
                  )}

                  {/* Added date */}
                  <div className="text-sm text-gray-500 mb-3">
                    Added {new Date(member.added_at).toLocaleDateString()}
                  </div>

                  {/* Notes */}
                  {member.notes && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-sm text-gray-700">
                      <span className="font-medium">Notes: </span>
                      {member.notes}
                    </div>
                  )}

                  {/* Links */}
                  <div className="flex items-center space-x-3 mt-3">
                    <Link
                      to={`/profile/${member.person_id}`}
                      className="text-sm px-3 py-1.5 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors font-medium"
                    >
                      View Full Profile
                    </Link>
                    {member.linkedin_url && (
                      <a
                        href={member.linkedin_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm px-3 py-1.5 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors font-medium inline-flex items-center"
                      >
                        <Linkedin className="w-3.5 h-3.5 mr-1" />
                        LinkedIn
                      </a>
                    )}
                  </div>
                </div>

                {/* Remove Button */}
                <button
                  onClick={() => handleRemoveMember(member.person_id)}
                  className="ml-4 p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  title="Remove from list"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

