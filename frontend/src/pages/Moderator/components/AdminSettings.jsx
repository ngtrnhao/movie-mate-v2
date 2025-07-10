import { useState } from 'react';
import {
  CogIcon,
  AdjustmentsHorizontalIcon,
  ShieldCheckIcon,
  ServerIcon,
  UsersIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import AdminThresholdConfig from './AdminThresholdConfig';
import SystemSettings from './SystemSettings';

const AdminSettings = () => {
  const [activeTab, setActiveTab] = useState('thresholds');

  const tabs = [
    {
      id: 'thresholds',
      label: 'Threshold Configuration',
      icon: AdjustmentsHorizontalIcon,
      description: 'Cấu hình ngưỡng phát hiện spoiler',
      color: 'blue',
    },
    {
      id: 'system',
      label: 'System Settings',
      icon: ServerIcon,
      description: 'Cài đặt hệ thống chung',
      color: 'gray',
    },
    {
      id: 'moderation',
      label: 'Moderation Settings',
      icon: ShieldCheckIcon,
      description: 'Cài đặt kiểm duyệt',
      color: 'green',
    },
    {
      id: 'users',
      label: 'User Management',
      icon: UsersIcon,
      description: 'Quản lý người dùng và quyền',
      color: 'purple',
    },
    {
      id: 'analytics',
      label: 'Analytics Settings',
      icon: ChartBarIcon,
      description: 'Cài đặt phân tích và báo cáo',
      color: 'indigo',
    },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'thresholds':
        return <AdminThresholdConfig />;
      case 'system':
      case 'moderation':
        return <SystemSettings />;
      case 'users':
        return (
          <div className="rounded-lg border bg-white p-8 text-center shadow-sm">
            <UsersIcon className="mx-auto mb-4 size-12 text-gray-400" />
            <h3 className="mb-2 text-lg font-medium text-gray-900">User Management</h3>
            <p className="text-gray-600">Tính năng quản lý người dùng đang được phát triển</p>
          </div>
        );
      case 'analytics':
        return (
          <div className="rounded-lg border bg-white p-8 text-center shadow-sm">
            <ChartBarIcon className="mx-auto mb-4 size-12 text-gray-400" />
            <h3 className="mb-2 text-lg font-medium text-gray-900">Analytics Settings</h3>
            <p className="text-gray-600">Cài đặt analytics đang được phát triển</p>
          </div>
        );
      default:
        return <AdminThresholdConfig />;
    }
  };

  const getTabColorClasses = (color, isActive) => {
    const colorMap = {
      blue: isActive
        ? 'bg-blue-100 text-blue-700 border-blue-200'
        : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50',
      gray: isActive
        ? 'bg-gray-100 text-gray-700 border-gray-200'
        : 'text-gray-600 hover:text-gray-700 hover:bg-gray-50',
      green: isActive
        ? 'bg-green-100 text-green-700 border-green-200'
        : 'text-gray-600 hover:text-green-600 hover:bg-green-50',
      purple: isActive
        ? 'bg-purple-100 text-purple-700 border-purple-200'
        : 'text-gray-600 hover:text-purple-600 hover:bg-purple-50',
      indigo: isActive
        ? 'bg-indigo-100 text-indigo-700 border-indigo-200'
        : 'text-gray-600 hover:text-indigo-600 hover:bg-indigo-50',
    };
    return colorMap[color] || colorMap.gray;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg border bg-white p-6 shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="rounded-lg bg-indigo-100 p-2">
            <CogIcon className="size-6 text-indigo-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Admin Settings</h1>
            <p className="text-gray-600">Cấu hình hệ thống và quản lý các thông số quan trọng</p>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="rounded-lg border bg-white shadow-sm">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6" aria-label="Tabs">
            {tabs.map(tab => {
              const isActive = activeTab === tab.id;
              const Icon = tab.icon;

              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`border-b-2 px-1 py-4 text-sm font-medium transition-colors ${
                    isActive
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <Icon className="size-5" />
                    <span className={isActive ? 'text-indigo-600' : 'text-gray-700'}>
                      {tab.label}
                    </span>
                  </div>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Description */}
        <div className="bg-gray-50 px-6 py-3">
          <p className="text-sm text-gray-600">
            {tabs.find(tab => tab.id === activeTab)?.description}
          </p>
        </div>
      </div>

      {/* Tab Content */}
      <div className="min-h-[500px] text-black">{renderTabContent()}</div>
    </div>
  );
};

export default AdminSettings;
