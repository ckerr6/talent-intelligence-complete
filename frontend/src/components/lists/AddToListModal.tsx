import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';

interface List {
  list_id: string;
  name: string;
  description?: string;
  member_count: number;
}

interface AddToListModalProps {
  personId: string;
  personName: string;
  onClose: () => void;
  onSuccess?: () => void;
}

const AddToListModal: React.FC<AddToListModalProps> = ({ personId, personName, onClose, onSuccess }) => {
  const [lists, setLists] = useState<List[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedListId, setSelectedListId] = useState<string>('');
  const [status, setStatus] = useState<string>('identified');
  const [notes, setNotes] = useState<string>('');
  const [showNewListForm, setShowNewListForm] = useState(false);
  const [newListName, setNewListName] = useState('');
  const [newListDescription, setNewListDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLists();
  }, []);

  const fetchLists = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/workflow/lists');
      const data = await response.json();
      if (data.success) {
        setLists(data.lists || []);
      }
    } catch (err) {
      console.error('Error fetching lists:', err);
      setError('Failed to load lists');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateList = async () => {
    if (!newListName.trim()) {
      setError('List name is required');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/workflow/lists', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newListName,
          description: newListDescription || null
        })
      });

      const data = await response.json();
      if (data.success && data.list) {
        setLists([...lists, data.list]);
        setSelectedListId(data.list.list_id);
        setShowNewListForm(false);
        setNewListName('');
        setNewListDescription('');
      } else {
        setError('Failed to create list');
      }
    } catch (err) {
      console.error('Error creating list:', err);
      setError('Failed to create list');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddToList = async () => {
    if (!selectedListId) {
      setError('Please select a list');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch(
        `http://localhost:8000/api/workflow/lists/${selectedListId}/members`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            person_id: personId,
            status: status,
            notes: notes || null
          })
        }
      );

      const data = await response.json();
      if (data.success) {
        onSuccess?.();
        onClose();
      } else {
        setError(data.message || 'Failed to add to list');
      }
    } catch (err) {
      console.error('Error adding to list:', err);
      setError('Failed to add to list');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            Add {personName} to List
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* New List Form */}
          {showNewListForm ? (
            <div className="space-y-3 p-4 bg-gray-50 rounded-lg">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  List Name *
                </label>
                <input
                  type="text"
                  value={newListName}
                  onChange={(e) => setNewListName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Senior Engineers Q1 2025"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={newListDescription}
                  onChange={(e) => setNewListDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={2}
                  placeholder="Optional description"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleCreateList}
                  disabled={submitting || !newListName.trim()}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submitting ? 'Creating...' : 'Create List'}
                </button>
                <button
                  onClick={() => {
                    setShowNewListForm(false);
                    setNewListName('');
                    setNewListDescription('');
                    setError(null);
                  }}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* Select List */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select List *
                </label>
                {loading ? (
                  <div className="text-gray-500">Loading lists...</div>
                ) : lists.length === 0 ? (
                  <div className="text-gray-500 text-sm">No lists yet.</div>
                ) : (
                  <select
                    value={selectedListId}
                    onChange={(e) => setSelectedListId(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">-- Select a list --</option>
                    {lists.map((list) => (
                      <option key={list.list_id} value={list.list_id}>
                        {list.name} ({list.member_count} members)
                      </option>
                    ))}
                  </select>
                )}
                <button
                  onClick={() => setShowNewListForm(true)}
                  className="mt-2 text-sm text-blue-600 hover:text-blue-700"
                >
                  + Create New List
                </button>
              </div>

              {/* Status */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Status *
                </label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="identified">🔍 Identified</option>
                  <option value="contacted">📧 Contacted</option>
                  <option value="responded">💬 Responded</option>
                  <option value="interviewing">🎤 Interviewing</option>
                  <option value="offer">🎁 Offer</option>
                  <option value="hired">✅ Hired</option>
                  <option value="rejected">❌ Rejected</option>
                  <option value="withdrawn">🚪 Withdrawn</option>
                </select>
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Notes (Optional)
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Add any relevant notes about this candidate..."
                />
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        {!showNewListForm && (
          <div className="flex gap-3 p-6 border-t">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
            >
              Cancel
            </button>
            <button
              onClick={handleAddToList}
              disabled={submitting || !selectedListId}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Adding...' : 'Add to List'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default AddToListModal;

