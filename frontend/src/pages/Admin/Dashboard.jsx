import { useState, useEffect, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {
  ChartBarIcon,
  UsersIcon,
  Cog6ToothIcon,
  ShieldCheckIcon,
  DocumentTextIcon,
  ChartPieIcon,
  CircleStackIcon,
  CpuChipIcon,
  ClockIcon,
  ExclamationCircleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  FilmIcon,
  FlagIcon,
  EyeIcon,
  PlusIcon,
  DocumentArrowDownIcon,
} from '@heroicons/react/24/outline';
import {
  ChartBarIcon as ChartBarIconSolid,
  UsersIcon as UsersIconSolid,
  ShieldCheckIcon as ShieldCheckIconSolid,
  DocumentTextIcon as DocumentTextIconSolid,
  ChartPieIcon as ChartPieIconSolid,
  Cog6ToothIcon as Cog6ToothIconSolid,
  FilmIcon as FilmIconSolid,
  EyeIcon as EyeIconSolid,
} from '@heroicons/react/24/solid';

import UserAnalytics from './components/UserAnalytics';
import ContentAnalytics from './components/ContentAnalytics';
import UserManagement from './components/UserManagement';
import SystemSettings from './components/SystemSettings';
import KanbanBoard from '../Moderator/components/KanbanBoard';
import QueueList from '../Moderator/components/QueueList';
import AdminDashboardOverview from './components/AdminDashboardOverview';
import VisibilityControl from './components/VisibilityControl';
import MovieManagement from './components/MovieManagement';
import { useDashboardData } from '../../hooks/useDashboardData';

const AdminDashboard = () => {
  const dispatch = useDispatch();
  const [activeView, setActiveView] = useState('overview');
  const [selectedItems, setSelectedItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [viewMode, setViewMode] = useState('dashboard'); // dashboard, kanban, queue

  const { data: dashboardData } = useDashboardData();
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
        iconSolid: FilmIconSolid,
        color: 'blue',
        description: 'Quản lý nội dung phim và production control',
        priority: 'high',
      },
      {
        id: 'visibility',
        label: 'Quản lý hiện thị',
        icon: EyeIcon,
        iconSolid: EyeIconSolid,
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
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="mb-4 text-2xl font-bold text-gray-900">Không có quyền truy cập</h1>
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
      <div className="mb-8 rounded-xl bg-gradient-to-r from-blue-600 to-blue-800 p-6 shadow-lg">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>
            <p className="mt-1 text-blue-100">Quản lý hệ thống Movie Recommendation</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="size-2 animate-pulse rounded-full bg-green-400"></div>
              <span className="text-sm text-blue-100">Hệ thống hoạt động</span>
            </div>
            <span className="inline-flex items-center rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-800">
              Administrator
            </span>
            <button
              onClick={() => navigate('/')}
              className="inline-flex items-center rounded-md border border-transparent bg-white px-4 py-2 text-sm font-medium text-blue-600 transition-colors hover:bg-blue-50"
            >
              Về trang chủ
            </button>
          </div>
        </div>
      </div>

      {/* System Stats */}
      <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Tổng người dùng</p>
              <p className="text-3xl font-bold text-gray-900">1,234</p>
              <p className="mt-1 flex items-center text-sm text-green-600">
                <ArrowTrendingUpIcon className="mr-1 size-4" />
                +12% so với tháng trước
              </p>
            </div>
            <div className="rounded-lg bg-blue-100 p-3">
              <UsersIcon className="size-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Tổng phim</p>
              <p className="text-3xl font-bold text-gray-900">8,934</p>
              <p className="mt-1 flex items-center text-sm text-green-600">
                <ArrowTrendingUpIcon className="mr-1 size-4" />
                +5% so với tháng trước
              </p>
            </div>
            <div className="rounded-lg bg-green-100 p-3">
              <FilmIcon className="size-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Nội dung chờ duyệt</p>
              <p className="text-3xl font-bold text-gray-900">47</p>
              <p className="mt-1 flex items-center text-sm text-red-600">
                <ArrowTrendingDownIcon className="mr-1 size-4" />
                -8% so với tuần trước
              </p>
            </div>
            <div className="rounded-lg bg-yellow-100 p-3">
              <ClockIcon className="size-6 text-yellow-600" />
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Báo cáo vi phạm</p>
              <p className="text-3xl font-bold text-gray-900">23</p>
              <p className="mt-1 flex items-center text-sm text-orange-600">
                <ExclamationCircleIcon className="mr-1 size-4" />
                Cần xử lý
              </p>
            </div>
            <div className="rounded-lg bg-red-100 p-3">
              <FlagIcon className="size-6 text-red-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Admin Main Content - Grid Layout */}
      <div className="mx-auto max-w-7xl px-6 py-8">
        {/* Navigation Cards */}
        <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {navigationItems.map(item => {
            const IconComponent = activeView === item.id ? item.iconSolid : item.icon;
            return (
              <button
                key={item.id}
                onClick={() => setActiveView(item.id)}
                className={`rounded-xl border p-6 text-left transition-all duration-200 hover:shadow-lg ${
                  activeView === item.id
                    ? 'border-blue-200 bg-blue-50 shadow-md'
                    : 'border-gray-200 bg-white hover:border-blue-300'
                }`}
              >
                <div className="mb-4 flex items-center justify-between">
                  <div
                    className={`rounded-lg p-3 ${
                      activeView === item.id ? 'bg-blue-100' : 'bg-gray-100'
                    }`}
                  >
                    <IconComponent
                      className={`size-6 ${
                        activeView === item.id ? 'text-blue-600' : 'text-gray-600'
                      }`}
                    />
                  </div>
                  {/* Priority indicator */}
                  <div
                    className={`rounded-full px-2 py-1 text-xs ${
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
                  className={`mb-2 text-lg font-semibold ${
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
        <div className="mb-8 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">Hành động nhanh</h3>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            {quickActions.map(action => {
              const ActionIcon = action.icon;
              return (
                <button
                  key={action.id}
                  onClick={() => handleBulkAction(action.id, selectedItems)}
                  className="flex items-center rounded-lg border border-gray-200 p-4 transition-all duration-200 hover:border-blue-300 hover:bg-blue-50"
                >
                  <ActionIcon className="mr-3 size-5 text-gray-600" />
                  <div className="text-left">
                    <div className="text-sm font-medium text-gray-900">{action.label}</div>
                    <div className="text-xs text-gray-500">{action.description}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Main Content Area */}
        <div className="mt-8 rounded-xl bg-white p-6 shadow-lg">
          {loading ? (
            <div className="flex h-64 items-center justify-center">
              <div className="size-12 animate-spin rounded-full border-b-2 border-blue-600"></div>
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
