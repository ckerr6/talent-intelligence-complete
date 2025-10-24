import React, { useState, useEffect } from 'react';
import Card from '../common/Card';
import LoadingSpinner from '../common/LoadingSpinner';
import EmptyState from '../common/EmptyState';
import EnhancedNoteForm from './EnhancedNoteForm';

interface Note {
  note_id: string;
  person_id: string;
  user_id: string;
  note_text: string;
  note_type: string;
  note_category?: string;
  priority: string;
  is_pinned: boolean;
  tags: string[];
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

interface NotesSectionProps {
  personId: string;
}

export const NotesSection: React.FC<NotesSectionProps> = ({ personId }) => {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  useEffect(() => {
    fetchNotes();
  }, [personId]);
  
  const fetchNotes = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`/api/workflow/notes/${personId}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch notes');
      }
      
      const data = await response.json();
      setNotes(data.notes || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  const handleNoteAdded = () => {
    fetchNotes();
    setShowForm(false);
  };
  
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'normal':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'low':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };
  
  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return '🔴';
      case 'high':
        return '🟠';
      case 'normal':
        return '🔵';
      case 'low':
        return '⚪';
      default:
        return '🔵';
    }
  };
  
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'call':
        return '📞';
      case 'screen':
        return '🎯';
      case 'meeting':
        return '👥';
      case 'email':
        return '✉️';
      case 'timing':
        return '⏰';
      case 'reference':
        return '📋';
      default:
        return '📝';
    }
  };
  
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };
  
  const filteredNotes = notes.filter(note => 
    !searchQuery || 
    note.note_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
    note.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  );
  
  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner />
        </div>
      </Card>
    );
  }
  
  return (
    <div className="space-y-4">
      {/* Header */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Notes & Context ({notes.length})
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Recruiter notes, screens, and candidate information
            </p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            {showForm ? 'Cancel' : '+ Add Note'}
          </button>
        </div>
        
        {/* Search */}
        {notes.length > 0 && (
          <div className="mt-4">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search notes and tags..."
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}
      </Card>
      
      {/* Note Form */}
      {showForm && (
        <EnhancedNoteForm
          personId={personId}
          onSuccess={handleNoteAdded}
          onCancel={() => setShowForm(false)}
        />
      )}
      
      {/* Notes List */}
      {error ? (
        <Card className="p-6">
          <div className="text-center py-8 text-red-600">
            <p>Error loading notes: {error}</p>
            <button 
              onClick={fetchNotes}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Retry
            </button>
          </div>
        </Card>
      ) : filteredNotes.length === 0 ? (
        <Card className="p-6">
          <EmptyState
            icon={
              <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            }
            title={searchQuery ? 'No matching notes found' : 'No notes yet'}
            description={searchQuery ? 'Try a different search term' : 'Add your first note about this candidate'}
          />
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredNotes.map((note) => (
            <Card key={note.note_id} className={`p-6 border-l-4 ${getPriorityColor(note.priority)}`}>
              {/* Note Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{getTypeIcon(note.note_type)}</span>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900 capitalize">
                        {note.note_type}
                      </span>
                      {note.note_category && note.note_category !== 'general' && (
                        <span className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
                          {note.note_category}
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-gray-500">{formatDate(note.created_at)}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-lg" title={note.priority}>
                    {getPriorityIcon(note.priority)}
                  </span>
                  {note.is_pinned && (
                    <span className="text-lg" title="Pinned">
                      📌
                    </span>
                  )}
                </div>
              </div>
              
              {/* Note Text */}
              <div className="mb-3 text-gray-700 whitespace-pre-wrap">
                {note.note_text}
              </div>
              
              {/* Tags */}
              {note.tags && note.tags.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-3">
                  {note.tags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-block px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
              
              {/* Metadata */}
              {note.metadata && Object.keys(note.metadata).length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <div className="text-xs text-gray-600 space-y-1">
                    {Object.entries(note.metadata).map(([key, value]) => (
                      <div key={key} className="flex gap-2">
                        <span className="font-medium capitalize">{key.replace(/_/g, ' ')}:</span>
                        <span>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default NotesSection;

