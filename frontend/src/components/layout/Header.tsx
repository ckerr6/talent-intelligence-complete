import { Link } from 'react-router-dom';

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and Title */}
          <Link to="/" className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">TI</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                Talent Intelligence
              </h1>
              <p className="text-xs text-gray-500">MVP Platform</p>
            </div>
          </Link>

          {/* Quick Actions */}
          <div className="flex items-center space-x-4">
            <button
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              title="Quick search (Cmd+K)"
            >
              <span className="hidden sm:inline">Search</span>
              <span className="sm:hidden">🔍</span>
              <span className="hidden sm:inline ml-2 text-xs text-gray-400">⌘K</span>
            </button>

            <div className="relative">
              <button className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center hover:bg-gray-300 transition-colors">
                <span className="text-gray-600 font-medium">U</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

