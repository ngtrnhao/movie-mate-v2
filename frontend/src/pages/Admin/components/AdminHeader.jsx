import { ChevronRightIcon } from '@heroicons/react/24/outline';

const AdminHeader = ({ breadcrumbs, quickActions, handleBulkAction, selectedItems }) => {
  return (
    <header className="border-b border-gray-200 bg-white shadow-sm">
      <div className="flex h-16 items-center justify-between px-6">
        {/* Breadcrumbs */}
        <nav className="flex" aria-label="Breadcrumb">
          <ol className="flex items-center space-x-4">
            {breadcrumbs.map((item, index) => (
              <li key={item.name}>
                <div className="flex items-center">
                  {index > 0 && <ChevronRightIcon className="mr-4 size-5 text-gray-400" />}
                  <span
                    className={`text-sm font-medium ${
                      index === breadcrumbs.length - 1 ? 'text-gray-900' : 'text-gray-500'
                    }`}
                  >
                    {item.name}
                  </span>
                </div>
              </li>
            ))}
          </ol>
        </nav>

        {/* Quick Actions */}
        <div className="flex items-center space-x-3">
          {quickActions.map(action => {
            const ActionIcon = action.icon;
            return (
              <button
                key={action.id}
                onClick={() => handleBulkAction(action.id, selectedItems)}
                className="flex items-center space-x-2 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                title={action.label}
              >
                <ActionIcon className="size-4" />
                <span className="hidden sm:inline">{action.label}</span>
              </button>
            );
          })}

          {/* User Info */}
          <div className="flex items-center space-x-2">
            <div className="size-2 rounded-full bg-green-400"></div>
            <span className="text-sm text-gray-600">Administrator</span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default AdminHeader;
