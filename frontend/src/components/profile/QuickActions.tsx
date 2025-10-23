import { useState, useEffect } from 'react';
import { ListPlus, StickyNote, Tag, Check } from 'lucide-react';

interface QuickActionsProps {
  personId: string;
  personName: string;
}

interface CandidateList {
  list_id: string;
  name: string;
  member_count: number;
}

export default function QuickActions({ personId, personName }: QuickActionsProps) {
  const [showAddToList, setShowAddToList] = useState(false);
  const [showAddNote, setShowAddNote] = useState(false);
  const [showAddTag, setShowAddTag] = useState(false);
  
  const [lists, setLists] = useState<CandidateList[]>([]);
  const [selectedListId, setSelectedListId] = useState('');
  const [noteText, setNoteText] = useState('');
  const [tagInput, setTagInput] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    loadLists();
  }, []);

  const loadLists = async () => {
    try {
      const response = await fetch('/api/workflow/lists');
      const data = await response.json();
      if (data.success) {
        setLists(data.lists || []);
      }
    } catch (error) {
      console.error('Error loading lists:', error);
    }
  };

  const handleAddToList = async () => {
    if (!selectedListId) return;

    try {
      const response = await fetch(`/api/workflow/lists/${selectedListId}/members`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ person_id: personId }),
      });

      if (response.ok) {
        showSuccess('Added to list!');
        setShowAddToList(false);
        setSelectedListId('');
      }
    } catch (error) {
      console.error('Error adding to list:', error);
    }
  };

  const handleAddNote = async () => {
    if (!noteText.trim()) return;

    try {
      const response = await fetch('/api/workflow/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          person_id: personId,
          note_text: noteText,
        }),
      });

      if (response.ok) {
        showSuccess('Note added!');
        setShowAddNote(false);
        setNoteText('');
      }
    } catch (error) {
      console.error('Error adding note:', error);
    }
  };

  const handleAddTag = async () => {
    if (!tagInput.trim()) return;

    const tags = tagInput.split(',').map(t => t.trim()).filter(t => t);

    try {
      for (const tag of tags) {
        await fetch('/api/workflow/tags', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            person_id: personId,
            tag: tag,
            tag_type: 'manual',
          }),
        });
      }

      showSuccess('Tags added!');
      setShowAddTag(false);
      setTagInput('');
    } catch (error) {
      console.error('Error adding tags:', error);
    }
  };

  const showSuccess = (message: string) => {
    setSuccessMessage(message);
    setTimeout(() => setSuccessMessage(''), 3000);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
      
      {/* Success Message */}
      {successMessage && (
        <div className="mb-4 p-3 bg-green-100 text-green-800 rounded-lg flex items-center">
          <Check className="w-4 h-4 mr-2" />
          {successMessage}
        </div>
      )}
      
      <div className="grid grid-cols-1 gap-3">
        {/* Add to List */}
        <button
          onClick={() => setShowAddToList(!showAddToList)}
          className="flex items-center justify-center space-x-2 px-4 py-3 bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 transition-colors border border-purple-200"
        >
          <ListPlus className="w-5 h-5" />
          <span className="font-medium">Add to List</span>
        </button>

        {/* Add Note */}
        <button
          onClick={() => setShowAddNote(!showAddNote)}
          className="flex items-center justify-center space-x-2 px-4 py-3 bg-yellow-50 text-yellow-700 rounded-lg hover:bg-yellow-100 transition-colors border border-yellow-200"
        >
          <StickyNote className="w-5 h-5" />
          <span className="font-medium">Add Note</span>
        </button>

        {/* Add Tag */}
        <button
          onClick={() => setShowAddTag(!showAddTag)}
          className="flex items-center justify-center space-x-2 px-4 py-3 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors border border-blue-200"
        >
          <Tag className="w-5 h-5" />
          <span className="font-medium">Add Tag</span>
        </button>
      </div>

      {/* Add to List Form */}
      {showAddToList && (
        <div className="mt-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
          <p className="text-sm text-purple-800 mb-2 font-medium">Add {personName} to a list:</p>
          <select
            value={selectedListId}
            onChange={(e) => setSelectedListId(e.target.value)}
            className="w-full px-3 py-2 border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent mb-2"
          >
            <option value="">Select a list...</option>
            {lists.map((list) => (
              <option key={list.list_id} value={list.list_id}>
                {list.name} ({list.member_count} members)
              </option>
            ))}
          </select>
          <div className="flex space-x-2">
            <button
              onClick={handleAddToList}
              disabled={!selectedListId}
              className="flex-1 px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
            >
              Add
            </button>
            <button 
              onClick={() => setShowAddToList(false)}
              className="px-3 py-2 bg-white text-purple-700 border border-purple-300 rounded-lg hover:bg-purple-50 text-sm font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Add Note Form */}
      {showAddNote && (
        <div className="mt-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
          <p className="text-sm text-yellow-800 mb-2 font-medium">Add a note about {personName}:</p>
          <textarea
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            className="w-full px-3 py-2 border border-yellow-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent mb-2"
            rows={3}
            placeholder="Enter your note here..."
          />
          <div className="flex space-x-2">
            <button
              onClick={handleAddNote}
              disabled={!noteText.trim()}
              className="flex-1 px-3 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
            >
              Save Note
            </button>
            <button 
              onClick={() => setShowAddNote(false)}
              className="px-3 py-2 bg-white text-yellow-700 border border-yellow-300 rounded-lg hover:bg-yellow-50 text-sm font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Add Tag Form */}
      {showAddTag && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm text-blue-800 mb-2 font-medium">Add tags to {personName}:</p>
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            className="w-full px-3 py-2 border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent mb-2"
            placeholder="e.g. senior-engineer, crypto, rust (comma-separated)"
          />
          <div className="flex space-x-2">
            <button
              onClick={handleAddTag}
              disabled={!tagInput.trim()}
              className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
            >
              Add Tags
            </button>
            <button 
              onClick={() => setShowAddTag(false)}
              className="px-3 py-2 bg-white text-blue-700 border border-blue-300 rounded-lg hover:bg-blue-50 text-sm font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

