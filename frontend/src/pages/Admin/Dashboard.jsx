import React, { useState, useEffect, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {
  ChartBarIcon,
  UsersIcon,
  Cog6ToothIcon,
  ShieldCheckIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  ChartPieIcon,
  ServerIcon,
  UserGroupIcon,
  CogIcon,
  BellIcon,
  KeyIcon,
  GlobeAltIcon,
  CircleStackIcon,
  CpuChipIcon,
  SignalIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ExclamationCircleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  UserIcon,
  FilmIcon,
  ChatBubbleLeftRightIcon,
  FlagIcon,
  EyeIcon,
  EyeSlashIcon,
  TrashIcon,
  PencilIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowPathIcon,
  DocumentArrowDownIcon,
  Cog6ToothIcon as Cog6ToothIconSolid,
  UsersIcon as UsersIconSolid,
  ChartBarIcon as ChartBarIconSolid,
  ShieldCheckIcon as ShieldCheckIconSolid,
  DocumentTextIcon as DocumentTextIconSolid,
  ExclamationTriangleIcon as ExclamationTriangleIconSolid,
  ChartPieIcon as ChartPieIconSolid,
  ServerIcon as ServerIconSolid,
  UserGroupIcon as UserGroupIconSolid,
  CogIcon as CogIconSolid,
} from '@heroicons/react/24/outline';
import SystemOverview from './components/SystemOverview';
import UserAnalytics from './components/UserAnalytics';
import ContentAnalytics from './components/ContentAnalytics';
import UserManagement from './components/UserManagement';
import SystemSettings from './components/SystemSettings';
import KanbanBoard from '../Moderator/components/KanbanBoard';
import QueueList from '../Moderator/components/QueueList';
import BulkActions from '../Moderator/components/BulkActions';
import AdminDashboardOverview from './components/AdminDashboardOverview';
import VisibilityControl from './components/VisibilityControl';
import MovieManagement from './components/MovieManagement';

const AdminDashboard = () => {
  const [activeView, setActiveView] = useState('overview');
  const [selectedItems, setSelectedItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [viewMode, setViewMode] = useState('dashboard'); // dashboard, kanban, queue
  const user = useSelector(state => state.auth.user);
  const navigate = useNavigate();

  // Check if user is admin
  useEffect(() => {
    if (!user || !user.groups?.some(g => g.name === 'Administrators')) {
      navigate('/');
    }
  }, [user, navigate]);

  // Admin-specific navigation items - Professional design
  const getNavigationItems = () => {
    return [
      {
        id: 'overview',
        label: 'Tổng quan hệ thống',
        icon: ChartBarIcon,
        iconSolid: ChartBarIconSolid,
        color: 'blue',
        description: 'Thống kê tổng quan và hiệu suất hệ thống',
        priority: 'high',
      },
      {
        id: 'users',
        label: 'Quản lý người dùng',
        icon: UsersIcon,
        iconSolid: UsersIconSolid,
        color: 'green',
        description: 'Quản lý tài khoản và phân quyền người dùng',
        priority: 'high',
      },
      {
        id: 'movies',
        label: 'Quản lý phim',
        icon: FilmIcon,
        iconSolid: FilmIcon,
        color: 'blue',
        description: 'Quản lý nội dung phim và production control',
        priority: 'high',
      },
      {
        id: 'visibility',
        label: 'Quản lý hiện thị',
        icon: EyeIcon,
        iconSolid: EyeIcon,
        color: 'blue',
        description: 'Quản lý hiện thị phim và production control',
      },
      {
        id: 'content',
        label: 'Phân tích nội dung',
        icon: DocumentTextIcon,
        iconSolid: DocumentTextIconSolid,
        color: 'purple',
        description: 'Thống kê và phân tích nội dung hệ thống',
        priority: 'medium',
      },
      {
        id: 'moderation',
        label: 'Công cụ kiểm duyệt',
        icon: ShieldCheckIcon,
        iconSolid: ShieldCheckIconSolid,
        color: 'orange',
        description: 'Quản lý và cấu hình hệ thống kiểm duyệt',
        priority: 'high',
      },
      {
        id: 'reports',
        label: 'Báo cáo & Thống kê',
        icon: ChartPieIcon,
        iconSolid: ChartPieIconSolid,
        color: 'indigo',
        description: 'Báo cáo chi tiết và thống kê hệ thống',
        priority: 'medium',
      },
      {
        id: 'system',
        label: 'Cài đặt hệ thống',
        icon: Cog6ToothIcon,
        iconSolid: Cog6ToothIconSolid,
        color: 'gray',
        description: 'Cấu hình và quản lý hệ thống',
        priority: 'low',
      },
    ];
  };

  // Admin-specific quick actions - Professional design
  const getQuickActions = () => {
    return [
      {
        id: 'add_user',
        label: 'Thêm người dùng',
        icon: PlusIcon,
        color: 'green',
        description: 'Tạo tài khoản người dùng mới',
      },
      {
        id: 'backup_system',
        label: 'Backup hệ thống',
        icon: CircleStackIcon,
        color: 'blue',
        description: 'Tạo bản sao lưu dữ liệu',
      },
      {
        id: 'system_health',
        label: 'Kiểm tra hệ thống',
        icon: CpuChipIcon,
        color: 'orange',
        description: 'Kiểm tra tình trạng hệ thống',
      },
      {
        id: 'export_data',
        label: 'Xuất dữ liệu',
        icon: DocumentArrowDownIcon,
        color: 'purple',
        description: 'Xuất báo cáo và dữ liệu',
      },
    ];
  };

  // Handle bulk selection
  const handleSelectItem = useCallback(itemId => {
    setSelectedItems(prev =>
      prev.includes(itemId) ? prev.filter(id => id !== itemId) : [...prev, itemId]
    );
  }, []);

  const handleSelectAll = useCallback(items => {
    setSelectedItems(items.map(item => item.id));
  }, []);

  const handleClearSelection = useCallback(() => {
    setSelectedItems([]);
  }, []);

  // Handle bulk actions with admin privileges
  const handleBulkAction = useCallback(async (actionType, itemIds) => {
    setLoading(true);
    try {
      console.log('Admin bulk action:', actionType, 'Items:', itemIds);

      // Admin-specific actions
      switch (actionType) {
        case 'ban_users':
          // Implement permanent ban logic
          console.log('Permanently banning users:', itemIds);
          break;
        case 'promote_moderators':
          // Implement promote to moderator logic
          console.log('Promoting users to moderators:', itemIds);
          break;
        case 'system_backup':
          // Implement system backup logic
          console.log('Creating system backup');
          break;
        default:
          // Standard moderation actions
          console.log('Standard moderation action:', actionType);
      }

      // API calls would go here
      // await adminAPI.bulkAction(actionType, itemIds);

      // Clear selection after action
      setSelectedItems([]);
    } catch (error) {
      console.error('Admin bulk action failed:', error);
      // Show error notification
    } finally {
      setLoading(false);
    }
  }, []);

  const renderMainContent = () => {
    switch (activeView) {
      case 'overview':
        return <AdminDashboardOverview />;
      case 'users':
        return <UserManagement />;
      case 'movies':
        return <MovieManagement />;
      case 'analytics':
        return <UserAnalytics />;
      case 'content':
        return <ContentAnalytics />;
      case 'visibility':
        return <VisibilityControl />;
      case 'moderation':
        return (
          <KanbanBoard
            selectedItems={selectedItems}
            onSelectItem={handleSelectItem}
            onBulkAction={handleBulkAction}
            isAdmin={true}
          />
        );
      case 'reports':
        return (
          <QueueList
            selectedItems={selectedItems}
            onSelectItem={handleSelectItem}
            onSelectAll={handleSelectAll}
            onClearSelection={handleClearSelection}
            isAdmin={true}
            filterType="reports"
          />
        );
      case 'settings':
        return <SystemSettings />;
      default:
        return <AdminDashboardOverview />;
    }
  };

  if (!user || !user.groups?.some(g => g.name === 'Administrators')) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Không có quyền truy cập</h1>
          <p className="text-gray-600">Bạn cần quyền Admin để truy cập trang này.</p>
        </div>
      </div>
    );
  }

  const navigationItems = getNavigationItems();
  const quickActions = getQuickActions();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Admin Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-xl shadow-lg p-6 mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>
            <p className="text-blue-100 mt-1">Quản lý hệ thống Movie Recommendation</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm text-blue-100">Hệ thống hoạt động</span>
            </div>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
              Administrator
            </span>
            <button
              onClick={() => navigate('/')}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-blue-600 bg-white hover:bg-blue-50 transition-colors"
            >
              Về trang chủ
            </button>
          </div>
        </div>
      </div>

      {/* System Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Tổng người dùng</p>
              <p className="text-3xl font-bold text-gray-900">1,234</p>
              <p className="text-sm text-green-600 flex items-center mt-1">
                <ArrowTrendingUpIcon className="w-4 h-4 mr-1" />
                +12% so với tháng trước
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <UsersIcon className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Tổng phim</p>
              <p className="text-3xl font-bold text-gray-900">8,934</p>
              <p className="text-sm text-green-600 flex items-center mt-1">
                <ArrowTrendingUpIcon className="w-4 h-4 mr-1" />
                +5% so với tháng trước
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <FilmIcon className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Nội dung chờ duyệt</p>
              <p className="text-3xl font-bold text-gray-900">47</p>
              <p className="text-sm text-red-600 flex items-center mt-1">
                <ArrowTrendingDownIcon className="w-4 h-4 mr-1" />
                -8% so với tuần trước
              </p>
            </div>
            <div className="p-3 bg-yellow-100 rounded-lg">
              <ClockIcon className="w-6 h-6 text-yellow-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Báo cáo vi phạm</p>
              <p className="text-3xl font-bold text-gray-900">23</p>
              <p className="text-sm text-orange-600 flex items-center mt-1">
                <ExclamationCircleIcon className="w-4 h-4 mr-1" />
                Cần xử lý
              </p>
            </div>
            <div className="p-3 bg-red-100 rounded-lg">
              <FlagIcon className="w-6 h-6 text-red-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Admin Main Content - Grid Layout */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Navigation Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {navigationItems.map(item => {
            const IconComponent = activeView === item.id ? item.iconSolid : item.icon;
            return (
              <button
                key={item.id}
                onClick={() => setActiveView(item.id)}
                className={`p-6 rounded-xl border transition-all duration-200 text-left hover:shadow-lg ${
                  activeView === item.id
                    ? 'bg-blue-50 border-blue-200 shadow-md'
                    : 'bg-white border-gray-200 hover:border-blue-300'
                }`}
              >
                <div className="flex items-center justify-between mb-4">
                  <div
                    className={`p-3 rounded-lg ${
                      activeView === item.id ? 'bg-blue-100' : 'bg-gray-100'
                    }`}
                  >
                    <IconComponent
                      className={`w-6 h-6 ${
                        activeView === item.id ? 'text-blue-600' : 'text-gray-600'
                      }`}
                    />
                  </div>
                  {/* Priority indicator */}
                  <div
                    className={`px-2 py-1 text-xs rounded-full ${
                      item.priority === 'high'
                        ? 'bg-orange-100 text-orange-700'
                        : item.priority === 'medium'
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {item.priority === 'high' ? '⚡' : item.priority === 'medium' ? '📌' : '📋'}
                  </div>
                </div>
                <h3
                  className={`text-lg font-semibold mb-2 ${
                    activeView === item.id ? 'text-blue-900' : 'text-gray-900'
                  }`}
                >
                  {item.label}
                </h3>
                <p
                  className={`text-sm ${
                    activeView === item.id ? 'text-blue-700' : 'text-gray-600'
                  }`}
                >
                  {item.description}
                </p>
              </button>
            );
          })}
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Hành động nhanh</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {quickActions.map(action => {
              const ActionIcon = action.icon;
              return (
                <button
                  key={action.id}
                  onClick={() => handleBulkAction(action.id, selectedItems)}
                  className="flex items-center p-4 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-all duration-200"
                >
                  <ActionIcon className="w-5 h-5 text-gray-600 mr-3" />
                  <div className="text-left">
                    <div className="font-medium text-sm text-gray-900">{action.label}</div>
                    <div className="text-xs text-gray-500">{action.description}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Main Content Area */}
        <div className="mt-8 bg-white rounded-xl shadow-lg p-6">
          {loading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            renderMainContent()
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
