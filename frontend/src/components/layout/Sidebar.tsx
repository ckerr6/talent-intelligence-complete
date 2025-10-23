import { NavLink } from 'react-router-dom';
import { useAppStore } from '../../store/store';

const navigation = [
  { name: 'Search', path: '/search', icon: '🔍', description: 'Find candidates' },
  { name: 'Lists', path: '/lists', icon: '📋', description: 'Manage lists' },
  { name: 'Network', path: '/network', icon: '🕸️', description: 'Network graph' },
  { name: 'Market Intel', path: '/market', icon: '📈', description: 'AI insights' },
  { name: 'Analytics', path: '/analytics', icon: '📊', description: 'Reports' },
];

export default function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useAppStore();

  return (
    <aside
      className={`fixed left-0 top-16 h-[calc(100vh-4rem)] bg-white border-r border-gray-200 transition-all duration-300 ${
        sidebarCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      <nav className="h-full flex flex-col">
        {/* Toggle button */}
        <button
          onClick={toggleSidebar}
          className="p-4 text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors border-b border-gray-200"
          title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <span className="text-xl">{sidebarCollapsed ? '→' : '←'}</span>
        </button>

        {/* Navigation items */}
        <div className="flex-1 overflow-y-auto py-4">
          {navigation.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center px-4 py-3 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary-50 text-primary-700 border-r-4 border-primary-700'
                    : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
            >
              <span className="text-xl">{item.icon}</span>
              {!sidebarCollapsed && (
                <div className="ml-3">
                  <div>{item.name}</div>
                  <div className="text-xs text-gray-500">{item.description}</div>
                </div>
              )}
            </NavLink>
          ))}
        </div>

        {/* Bottom section */}
        {!sidebarCollapsed && (
          <div className="p-4 border-t border-gray-200">
            <div className="text-xs text-gray-500">
              <p className="font-medium mb-1">Talent Intelligence</p>
              <p>Version 1.0.0</p>
            </div>
          </div>
        )}
      </nav>
    </aside>
  );
}

