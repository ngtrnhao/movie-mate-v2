import { useNavigate } from 'react-router-dom';
import { Bars3Icon, XMarkIcon, HomeIcon } from '@heroicons/react/24/outline';
import { ShieldCheckIcon as ShieldCheckIconSolid } from '@heroicons/react/24/solid';

const AdminSidebar = ({
  sidebarCollapsed,
  setSidebarCollapsed,
  activeView,
  setActiveView,
  navigationItems,
  groupedNavigation,
  groupLabels,
}) => {
  const navigate = useNavigate();

  return (
    <div
      className={`bg-white shadow-lg transition-all duration-300 ${
        sidebarCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      <div className="flex h-full flex-col">
        {/* Sidebar Header */}
        <div className="flex items-center justify-between border-b border-gray-200 p-4">
          {!sidebarCollapsed && (
            <div className="flex items-center space-x-3">
              <div className="rounded-lg bg-blue-600 p-2">
                <ShieldCheckIconSolid className="size-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">Admin Panel</h1>
                <p className="text-sm text-gray-500">Movie Recommendation</p>
              </div>
            </div>
          )}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
          >
            {sidebarCollapsed ? <Bars3Icon className="size-6" /> : <XMarkIcon className="size-6" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4">
          <div className="space-y-6">
            {Object.entries(groupedNavigation).map(([group, items]) => (
              <div key={group}>
                {!sidebarCollapsed && (
                  <div className="px-4 text-xs font-semibold uppercase tracking-wider text-gray-500">
                    {groupLabels[group]}
                  </div>
                )}
                <div className="mt-2 space-y-1">
                  {items.map(item => {
                    const IconComponent = activeView === item.id ? item.iconSolid : item.icon;
                    return (
                      <button
                        key={item.id}
                        onClick={() => setActiveView(item.id)}
                        className={`group flex w-full items-center px-4 py-3 text-sm font-medium transition-colors ${
                          activeView === item.id
                            ? 'border-r-2 border-blue-700 bg-blue-50 text-blue-700'
                            : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                        }`}
                      >
                        <IconComponent
                          className={`size-5 shrink-0 ${
                            activeView === item.id
                              ? 'text-blue-700'
                              : 'text-gray-400 group-hover:text-gray-500'
                          }`}
                        />
                        {!sidebarCollapsed && <span className="ml-3 truncate">{item.label}</span>}
                        {!sidebarCollapsed && item.priority === 'high' && (
                          <span className="ml-auto size-2 rounded-full bg-orange-400"></span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </nav>

        {/* Sidebar Footer */}
        <div className="border-t border-gray-200 p-4">
          <button
            onClick={() => navigate('/')}
            className="flex w-full items-center space-x-3 rounded-lg px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            <HomeIcon className="size-5 text-gray-400" />
            {!sidebarCollapsed && <span>Về trang chủ</span>}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminSidebar;
