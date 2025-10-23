import { useState } from 'react';

interface QuickActionsProps {
  personId: string;
  personName: string;
}

export default function QuickActions({ personId, personName }: QuickActionsProps) {
  const [showAddToList, setShowAddToList] = useState(false);
  const [showAddNote, setShowAddNote] = useState(false);
  const [showAddTag, setShowAddTag] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Add to List */}
        <button
          onClick={() => setShowAddToList(!showAddToList)}
          className="flex items-center justify-center space-x-2 px-4 py-3 bg-primary-50 text-primary-700 rounded-lg hover:bg-primary-100 transition-colors border border-primary-200"
        >
          <span className="text-lg">📋</span>
          <span className="font-medium">Add to List</span>
        </button>

        {/* Add Note */}
        <button
          onClick={() => setShowAddNote(!showAddNote)}
          className="flex items-center justify-center space-x-2 px-4 py-3 bg-yellow-50 text-yellow-700 rounded-lg hover:bg-yellow-100 transition-colors border border-yellow-200"
        >
          <span className="text-lg">📝</span>
          <span className="font-medium">Add Note</span>
        </button>

        {/* Add Tag */}
        <button
          onClick={() => setShowAddTag(!showAddTag)}
          className="flex items-center justify-center space-x-2 px-4 py-3 bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 transition-colors border border-purple-200"
        >
          <span className="text-lg">🏷️</span>
          <span className="font-medium">Add Tag</span>
        </button>
      </div>

      {/* Add to List Modal */}
      {showAddToList && (
        <div className="mt-4 p-4 bg-primary-50 rounded-lg border border-primary-200">
          <p className="text-sm text-primary-800 mb-2">Add {personName} to a list:</p>
          <select className="w-full px-3 py-2 border border-primary-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent mb-2">
            <option>Select a list...</option>
            <option>Engineering Candidates</option>
            <option>Executive Pipeline</option>
            <option>High Priority</option>
          </select>
          <div className="flex space-x-2">
            <button className="flex-1 px-3 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium">
              Add
            </button>
            <button 
              onClick={() => setShowAddToList(false)}
              className="px-3 py-2 bg-white text-primary-700 border border-primary-300 rounded-lg hover:bg-primary-50 text-sm font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Add Note Modal */}
      {showAddNote && (
        <div className="mt-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
          <p className="text-sm text-yellow-800 mb-2">Add a note about {personName}:</p>
          <textarea
            className="w-full px-3 py-2 border border-yellow-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent mb-2"
            rows={3}
            placeholder="Enter your note here..."
          />
          <div className="flex space-x-2">
            <button className="flex-1 px-3 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 text-sm font-medium">
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

      {/* Add Tag Modal */}
      {showAddTag && (
        <div className="mt-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
          <p className="text-sm text-purple-800 mb-2">Add tags to {personName}:</p>
          <input
            type="text"
            className="w-full px-3 py-2 border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent mb-2"
            placeholder="e.g. senior-engineer, crypto, rust"
          />
          <div className="flex space-x-2">
            <button className="flex-1 px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm font-medium">
              Add Tags
            </button>
            <button 
              onClick={() => setShowAddTag(false)}
              className="px-3 py-2 bg-white text-purple-700 border border-purple-300 rounded-lg hover:bg-purple-50 text-sm font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Additional Actions */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <button className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg transition-colors">
          📤 Export Profile
        </button>
        <button className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg transition-colors">
          🔗 Share Profile
        </button>
        <button className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg transition-colors">
          ⭐ Add to Favorites
        </button>
      </div>
    </div>
  );
}

