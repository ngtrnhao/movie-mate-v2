import { useState, useEffect, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  ChartBarIcon,
  ClipboardDocumentListIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon,
  UsersIcon,
  ChartPieIcon,
  Cog6ToothIcon,
  WrenchScrewdriverIcon,
  CheckCircleIcon,
  XCircleIcon,
  FlagIcon,
  UserGroupIcon,
  ArrowUpTrayIcon,
  NoSymbolIcon,
  ServerIcon,
  ClockIcon,
  CheckIcon,
  FlagIcon as FlagIconSolid,
  UserGroupIcon as UserGroupIconSolid,
  ArrowUpTrayIcon as ArrowUpTrayIconSolid,
  NoSymbolIcon as NoSymbolIconSolid,
  ServerIcon as ServerIconSolid,
  BellIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  EyeIcon,
  EyeSlashIcon,
  ChatBubbleLeftRightIcon,
  DocumentArrowDownIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  UserIcon,
  ShieldCheckIcon,
  CogIcon,
  InformationCircleIcon,
  BoltIcon,
  Bars3Icon,
  HomeIcon,
} from '@heroicons/react/24/outline';
import {
  ChartBarIcon as ChartBarIconSolid,
  ClipboardDocumentListIcon as ClipboardDocumentListIconSolid,
  ExclamationTriangleIcon as ExclamationTriangleIconSolid,
  DocumentTextIcon as DocumentTextIconSolid,
  UsersIcon as UsersIconSolid,
  ChartPieIcon as ChartPieIconSolid,
  Cog6ToothIcon as Cog6ToothIconSolid,
  WrenchScrewdriverIcon as WrenchScrewdriverIconSolid,
} from '@heroicons/react/24/solid';
import DashboardOverview from './components/DashboardOverview';
import KanbanBoard from './components/KanbanBoard';
import QueueList from './components/QueueList';
import BulkActions from './components/BulkActions';
import SpoilerDetectionPanel from './components/SpoilerDetectionPanel';
import UserManagement from './components/UserManagement';
import SystemSettings from './components/SystemSettings';
import Analytics from './components/Analytics';
import ContentManagement from './components/ContentManagement';

const ModeratorDashboard = () => {
  const [activeView, setActiveView] = useState('overview');
  const [selectedItems, setSelectedItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sidebarMobileOpen, setSidebarMobileOpen] = useState(false);
  const [viewMode, setViewMode] = useState('dashboard'); // dashboard, kanban, queue
  const [kanbanViewMode, setKanbanViewMode] = useState('kanban'); // kanban, queue
  const [notifications, setNotifications] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const user = useSelector(state => state.auth.user);
  const navigate = useNavigate();
  const location = useLocation();

  // Check if user is moderator or admin
  useEffect(() => {
    if (!user || !user.groups?.some(g => g.name === 'Moderators' || g.name === 'Administrators')) {
      navigate('/');
    }
  }, [user, navigate]);

  const isAdmin = user?.groups?.some(g => g.name === 'Administrators');
  const isModerator = user?.groups?.some(g => g.name === 'Moderators');

  // Handle navigation click
  const handleNavigationClick = viewId => {
    setActiveView(viewId);
    // Reset selection when changing views
    setSelectedItems([]);
  };

  // Enhanced Navigation items based on role - Professional design with best practices
  const getNavigationItems = () => {
    const baseItems = [
      {
        id: 'overview',
        label: 'Tổng quan',
        icon: ChartBarIcon,
        iconSolid: ChartBarIconSolid,
        color: 'blue',
        viewMode: 'dashboard',
        description: 'Thống kê tổng quan công việc kiểm duyệt',
        priority: 'high',
        badge: '23',
        badgeColor: 'yellow',
      },
      {
        id: 'moderation-queue',
        label: 'Queue kiểm duyệt',
        icon: ClipboardDocumentListIcon,
        iconSolid: ClipboardDocumentListIconSolid,
        color: 'orange',
        viewMode: 'queue',
        description: 'Danh sách nội dung chờ kiểm duyệt',
        priority: 'critical',
        badge: '15',
        badgeColor: 'red',
      },
      {
        id: 'reports',
        label: 'Báo cáo vi phạm',
        icon: ExclamationTriangleIcon,
        iconSolid: ExclamationTriangleIconSolid,
        color: 'red',
        viewMode: 'queue',
        description: 'Xử lý báo cáo vi phạm từ người dùng',
        priority: 'high',
        badge: '8',
        badgeColor: 'red',
      },
      {
        id: 'content-review',
        label: 'Review nội dung',
        icon: DocumentTextIcon,
        iconSolid: DocumentTextIconSolid,
        color: 'green',
        viewMode: 'dashboard',
        description: 'Kiểm duyệt review và comment',
        priority: 'medium',
        badge: '12',
        badgeColor: 'blue',
      },
      {
        id: 'user-management',
        label: 'Quản lý người dùng',
        icon: UsersIcon,
        iconSolid: UsersIconSolid,
        color: 'purple',
        viewMode: 'dashboard',
        description: 'Cảnh báo và tạm khóa người dùng',
        priority: 'medium',
        badge: '5',
        badgeColor: 'orange',
      },
      {
        id: 'analytics',
        label: 'Phân tích',
        icon: ChartPieIcon,
        iconSolid: ChartPieIconSolid,
        color: 'indigo',
        viewMode: 'dashboard',
        description: 'Báo cáo hiệu suất kiểm duyệt',
        priority: 'low',
        badge: '',
        badgeColor: 'gray',
      },
      {
        id: 'settings',
        label: 'Cài đặt',
        icon: Cog6ToothIcon,
        iconSolid: Cog6ToothIconSolid,
        color: 'gray',
        viewMode: 'dashboard',
        description: 'Cấu hình kiểm duyệt',
        priority: 'low',
        badge: '',
        badgeColor: 'gray',
      },
    ];

    // Admin-only items
    if (isAdmin) {
      baseItems.push({
        id: 'system-users',
        label: 'Quản lý hệ thống',
        icon: WrenchScrewdriverIcon,
        iconSolid: WrenchScrewdriverIconSolid,
        color: 'yellow',
        viewMode: 'dashboard',
        description: 'Quản lý người dùng hệ thống',
        priority: 'high',
        badge: '3',
        badgeColor: 'purple',
      });
    }

    return baseItems;
  };

  // Enhanced Quick actions based on role - Professional design with best practices
  const getQuickActions = () => {
    const baseActions = [
      {
        id: 'approve_bulk',
        label: 'Duyệt hàng loạt',
        icon: CheckCircleIcon,
        color: 'green',
        description: 'Duyệt tất cả nội dung đã chọn',
        priority: 'high',
        shortcut: 'Ctrl+A',
      },
      {
        id: 'reject_bulk',
        label: 'Từ chối hàng loạt',
        icon: XCircleIcon,
        color: 'red',
        description: 'Từ chối tất cả nội dung vi phạm',
        priority: 'high',
        shortcut: 'Ctrl+R',
      },
      {
        id: 'flag_users',
        label: 'Đánh dấu người dùng',
        icon: FlagIcon,
        color: 'orange',
        description: 'Đánh dấu người dùng vi phạm',
        priority: 'medium',
        shortcut: 'Ctrl+F',
      },
      {
        id: 'assign_tasks',
        label: 'Phân công',
        icon: UserGroupIcon,
        color: 'blue',
        description: 'Phân công công việc cho moderator khác',
        priority: 'medium',
        shortcut: 'Ctrl+T',
      },
      {
        id: 'export_data',
        label: 'Xuất dữ liệu',
        icon: ArrowUpTrayIcon,
        color: 'gray',
        description: 'Xuất báo cáo kiểm duyệt',
        priority: 'low',
        shortcut: 'Ctrl+E',
      },
    ];

    // Admin-only actions
    if (isAdmin) {
      baseActions.push(
        {
          id: 'ban_users',
          label: 'Ban người dùng',
          icon: NoSymbolIcon,
          color: 'red',
          description: 'Cấm người dùng vi phạm nghiêm trọng',
          priority: 'high',
          shortcut: 'Ctrl+B',
        },
        {
          id: 'system_backup',
          label: 'Backup hệ thống',
          icon: ServerIcon,
          color: 'purple',
          description: 'Tạo bản sao lưu hệ thống kiểm duyệt',
          priority: 'low',
          shortcut: 'Ctrl+S',
        }
      );
    }

    return baseActions;
  };

  // Enhanced stats data
  const getDashboardStats = () => [
    {
      title: 'Nội dung chờ duyệt',
      value: '23',
      change: '+5',
      changeType: 'increase',
      icon: ClockIcon,
      color: 'yellow',
      description: 'Cần xử lý trong ngày',
      trend: 'up',
    },
    {
      title: 'Báo cáo vi phạm',
      value: '12',
      change: '+3',
      changeType: 'increase',
      icon: ExclamationTriangleIcon,
      color: 'red',
      description: 'Cần ưu tiên xử lý',
      trend: 'up',
    },
    {
      title: 'Đã duyệt hôm nay',
      value: '156',
      change: '+23',
      changeType: 'increase',
      icon: CheckCircleIcon,
      color: 'green',
      description: 'Tăng 17% so với hôm qua',
      trend: 'up',
    },
    {
      title: 'Thời gian xử lý TB',
      value: '2.5h',
      change: '-0.3h',
      changeType: 'decrease',
      icon: ClockIcon,
      color: 'blue',
      description: 'Cải thiện hiệu suất',
      trend: 'down',
    },
  ];

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

  // Handle bulk actions
  const handleBulkAction = useCallback(
    async (actionType, itemIds) => {
      setLoading(true);
      try {
        console.log('Bulk action:', actionType, 'Items:', itemIds);

        // Role-based action validation
        if (actionType === 'ban_users' && !isAdmin) {
          throw new Error('Chỉ Admin mới có quyền ban người dùng');
        }

        // API calls would go here
        // await moderationAPI.bulkAction(actionType, itemIds);

        // Clear selection after action
        setSelectedItems([]);
      } catch (error) {
        console.error('Bulk action failed:', error);
        // Show error notification
      } finally {
        setLoading(false);
      }
    },
    [isAdmin]
  );

  // Sidebar toggle handler
  const handleSidebarToggle = () => {
    if (window.innerWidth < 768) {
      setSidebarMobileOpen(open => !open);
    } else {
      setSidebarCollapsed(prev => !prev);
    }
  };

  // Close sidebar on mobile when clicking outside
  useEffect(() => {
    if (!sidebarMobileOpen) return;
    const handleClick = e => {
      if (e.target.closest('#moderator-sidebar')) return;
      setSidebarMobileOpen(false);
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [sidebarMobileOpen]);

  const renderMainContent = () => {
    switch (activeView) {
      case 'overview':
        return <DashboardOverview isAdmin={isAdmin} isModerator={isModerator} />;
      case 'moderation-queue':
        return (
          <div>
            {/* Enhanced Toggle Button */}
            <div className="mb-6">
              <div className="flex justify-center mb-4">
                <div className="bg-white rounded-xl shadow-lg p-1 flex border border-gray-200">
                  <button
                    onClick={() => setKanbanViewMode('kanban')}
                    className={`px-6 py-3 rounded-lg text-sm font-medium transition-all duration-200 flex items-center ${
                      kanbanViewMode === 'kanban'
                        ? 'bg-green-100 text-green-700 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                  >
                    <ClipboardDocumentListIcon className="w-5 h-5 mr-2" />
                    <div className="text-left">
                      <div className="font-semibold">Kanban Board</div>
                      <div className="text-xs opacity-75">Quản lý theo cột</div>
                    </div>
                  </button>
                  <button
                    onClick={() => setKanbanViewMode('queue')}
                    className={`px-6 py-3 rounded-lg text-sm font-medium transition-all duration-200 flex items-center ${
                      kanbanViewMode === 'queue'
                        ? 'bg-green-100 text-green-700 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                  >
                    <DocumentTextIcon className="w-5 h-5 mr-2" />
                    <div className="text-left">
                      <div className="font-semibold">Queue List</div>
                      <div className="text-xs opacity-75">Danh sách đơn giản</div>
                    </div>
                  </button>
                </div>
              </div>

              {/* View-specific stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-white rounded-lg shadow p-4 border-l-4 border-yellow-500">
                  <div className="flex items-center">
                    <ClockIcon className="w-6 h-6 text-yellow-600 mr-3" />
                    <div>
                      <p className="text-sm font-medium text-gray-600">Chờ duyệt</p>
                      <p className="text-2xl font-bold text-gray-900">23</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
                  <div className="flex items-center">
                    <ChartBarIcon className="w-6 h-6 text-blue-600 mr-3" />
                    <div>
                      <p className="text-sm font-medium text-gray-600">Đang xử lý</p>
                      <p className="text-2xl font-bold text-gray-900">8</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
                  <div className="flex items-center">
                    <CheckIcon className="w-6 h-6 text-green-600 mr-3" />
                    <div>
                      <p className="text-sm font-medium text-gray-600">Hoàn thành</p>
                      <p className="text-2xl font-bold text-gray-900">156</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Content based on view mode */}
            {kanbanViewMode === 'kanban' ? (
              <KanbanBoard
                selectedItems={selectedItems}
                onSelectItem={handleSelectItem}
                onBulkAction={handleBulkAction}
                isAdmin={isAdmin}
              />
            ) : (
              <QueueList
                selectedItems={selectedItems}
                onSelectItem={handleSelectItem}
                onSelectAll={handleSelectAll}
                onClearSelection={handleClearSelection}
                isAdmin={isAdmin}
              />
            )}
          </div>
        );
      case 'reports':
        return (
          <QueueList
            selectedItems={selectedItems}
            onSelectItem={handleSelectItem}
            onSelectAll={handleSelectAll}
            onClearSelection={handleClearSelection}
            isAdmin={isAdmin}
            filterType="reports"
          />
        );
      case 'content-review':
        return <ContentManagement />;
      case 'user-management':
        return <UserManagement />;
      case 'analytics':
        return <Analytics />;
      case 'settings':
        return <SystemSettings />;
      case 'system-users':
        return isAdmin ? <UserManagement /> : null;
      default:
        return <DashboardOverview isAdmin={isAdmin} isModerator={isModerator} />;
    }
  };

  if (!user || !user.groups?.some(g => g.name === 'Moderators' || g.name === 'Administrators')) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Không có quyền truy cập</h1>
          <p className="text-gray-600">Bạn cần quyền Moderator hoặc Admin để truy cập trang này.</p>
        </div>
      </div>
    );
  }

  const navigationItems = getNavigationItems();
  const quickActions = getQuickActions();
  const dashboardStats = getDashboardStats();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex flex-col">
      {/* Responsive Header */}
      <header className="bg-gradient-to-r from-pink-100 via-purple-100 to-amber-100 shadow-md border-b border-pink-200 h-auto flex flex-col md:flex-row md:items-center md:justify-between px-2 sm:px-4 md:px-8 z-20 w-full gap-2 md:gap-0">
        <div className="flex items-center space-x-2 min-w-0 flex-shrink-0">
          <div className="flex items-center bg-gradient-to-r from-purple-400 to-pink-300 rounded-xl shadow-md px-2 py-1">
            <ShieldCheckIcon className="w-6 h-6 text-white" />
            {!sidebarCollapsed && (
              <span className="ml-2 text-base font-bold text-white tracking-wide sm:inline truncate">
                Moderator
              </span>
            )}
          </div>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center min-w-0">
          <h1 className="text-base md:text-lg font-bold text-gray-900 leading-tight truncate">
            Moderator Dashboard
          </h1>
          <p className="text-xs text-gray-500 items-center mt-0.5 hidden md:flex truncate">
            <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
            Hệ thống kiểm duyệt nội dung Movie Recommendation
          </p>
        </div>
        <div className="flex items-center space-x-1 sm:space-x-2 md:space-x-4 min-w-0 flex-shrink-0 mt-2 md:mt-0">
          <div className="relative hidden sm:block w-28 md:w-48 lg:w-64">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Tìm kiếm..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-200 rounded-full bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-transparent w-full text-sm"
            />
          </div>
          <div className="relative">
            <button className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-colors">
              <BellIcon className="w-5 h-5" />
              {notifications.length > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {notifications.length}
                </span>
              )}
            </button>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            <span className="text-xs text-gray-600">Online</span>
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                isAdmin
                  ? 'bg-purple-100 text-purple-800 border border-purple-200'
                  : 'bg-blue-100 text-blue-800 border border-blue-200'
              }`}
            >
              {isAdmin ? 'Admin' : 'Moderator'}
            </span>
          </div>
          <button
            onClick={() => navigate('/')}
            className="inline-flex items-center px-2 py-2 border border-transparent text-xs font-medium rounded-full text-white bg-gradient-to-r from-amber-400 to-pink-400 hover:from-amber-500 hover:to-pink-500 transition-all duration-200 shadow-md hover:shadow-lg ml-1"
          >
            <HomeIcon className="w-5 h-5" />
            <span className="hidden md:inline">Trang chủ</span>
          </button>
        </div>
      </header>

      {/* Responsive Layout: Sidebar + Main */}
      <div className="flex-1 flex w-full min-w-0">
        {/* Sidebar: responsive, overlays on mobile, collapses on md+ */}
        <div
          id="moderator-sidebar"
          className={`
            fixed top-0 left-0 z-30 h-full bg-gradient-to-b from-pink-50 via-amber-50 to-purple-50 shadow-lg border-r border-pink-200 transition-all duration-300
            ${sidebarMobileOpen ? 'block' : 'hidden'}
            md:static md:block
            ${sidebarCollapsed ? 'w-16' : 'w-64'}
          `}
        >
          <div className="p-4 flex flex-col h-full gap-2 min-w-0">
            {/* Sidebar Toggle (sticky on mobile) */}
            <button
              onClick={handleSidebarToggle}
              className="mb-4 p-2 rounded-lg hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-400 self-center md:self-start"
              aria-label={sidebarCollapsed ? 'Mở sidebar' : 'Ẩn sidebar'}
            >
              <Bars3Icon className="w-6 h-6 text-blue-600" />
            </button>
            {/* Stats */}
            <div className="mb-6 flex flex-col gap-2">
              <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center justify-center md:justify-start">
                <ChartBarIcon className="w-4 h-4 mr-0 md:mr-2" />
                {!sidebarCollapsed && <span className="truncate">Thống kê hôm nay</span>}
              </h3>
              <div className="space-y-2">
                {dashboardStats.slice(0, 3).map((stat, index) => {
                  const StatIcon = stat.icon;
                  return (
                    <div
                      key={index}
                      className={`flex items-center ${sidebarCollapsed ? 'justify-center' : 'justify-between'} p-2 rounded-lg ${
                        stat.color === 'yellow'
                          ? 'bg-yellow-50 border border-yellow-200'
                          : stat.color === 'green'
                            ? 'bg-green-50 border border-green-200'
                            : stat.color === 'red'
                              ? 'bg-red-50 border border-red-200'
                              : 'bg-blue-50 border border-blue-200'
                      }`}
                    >
                      <StatIcon
                        className={`w-5 h-5 ${
                          stat.color === 'yellow'
                            ? 'text-yellow-600'
                            : stat.color === 'green'
                              ? 'text-green-600'
                              : stat.color === 'red'
                                ? 'text-red-600'
                                : 'text-blue-600'
                        }`}
                      />
                      {!sidebarCollapsed && (
                        <span className="ml-2 text-sm font-medium text-gray-700 truncate">
                          {stat.title}
                        </span>
                      )}
                      {!sidebarCollapsed && (
                        <span
                          className={`ml-auto text-lg font-bold ${
                            stat.color === 'yellow'
                              ? 'text-yellow-600'
                              : stat.color === 'green'
                                ? 'text-green-600'
                                : stat.color === 'red'
                                  ? 'text-red-600'
                                  : 'text-blue-600'
                          }`}
                        >
                          {stat.value}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
            {/* Navigation */}
            <div className="mb-6 flex flex-col gap-2">
              {navigationItems.map(item => {
                const IconComponent = activeView === item.id ? item.iconSolid : item.icon;
                return (
                  <button
                    key={item.id}
                    onClick={() => handleNavigationClick(item.id)}
                    className={`flex items-center ${sidebarCollapsed ? 'justify-center' : 'justify-between'} p-3 rounded-lg transition-all duration-200 group
                      ${
                        activeView === item.id
                          ? 'bg-gradient-to-r from-amber-100 to-pink-100 text-pink-700 border border-amber-200'
                          : 'text-purple-900 hover:bg-pink-50 hover:text-pink-700'
                      }`}
                  >
                    <IconComponent className="w-5 h-5 text-pink-400" />
                    {/* Ẩn label, badge khi thu nỏ */}
                    {!sidebarCollapsed && (
                      <div className="ml-2 flex-1 min-w-0">
                        <div className="font-medium text-sm truncate">{item.label}</div>
                        <div className="text-xs opacity-75 mt-0.5 truncate">{item.description}</div>
                      </div>
                    )}
                    {!sidebarCollapsed && item.badge && (
                      <span className="ml-2 px-2 py-1 text-xs rounded-full font-medium bg-pink-100 text-pink-700 truncate">
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
            {/* Quick Actions */}
            <div className="mb-6 flex flex-col gap-2">
              {quickActions.map(action => {
                const ActionIcon = action.icon;
                return (
                  <button
                    key={action.id}
                    onClick={() => handleBulkAction(action.id, selectedItems)}
                    className={`flex items-center ${sidebarCollapsed ? 'justify-center' : 'justify-start'} p-3 rounded-lg text-left hover:bg-gray-50 transition-colors group`}
                  >
                    <ActionIcon className="w-5 h-5" />
                    {/* Ẩn label khi thu nỏ */}
                    {!sidebarCollapsed && (
                      <span className="ml-2 font-medium text-sm truncate">{action.label}</span>
                    )}
                  </button>
                );
              })}
            </div>
            {/* Moderator Info */}
            {!sidebarCollapsed && (
              <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200 mt-auto">
                <h4 className="text-sm font-semibold text-blue-800 mb-2 flex items-center">
                  <InformationCircleIcon className="w-4 h-4 mr-1" />
                  Quyền Moderator
                </h4>
                <div className="text-xs text-blue-700 space-y-1">
                  <div>• Kiểm duyệt nội dung</div>
                  <div>• Xử lý báo cáo vi phạm</div>
                  <div>• Cảnh báo người dùng</div>
                  <div>• Tạm khóa tài khoản</div>
                  <div>• Quản lý cộng đồng</div>
                </div>
              </div>
            )}
          </div>
        </div>
        {/* Main Content Area: responsive padding, min-w-0, overflow-x-auto */}
        <main className="flex-1 p-2 sm:p-4 md:p-6 min-w-0 overflow-x-auto">
          {/* Enhanced Content Header: responsive */}
          <div className="mb-4 sm:mb-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-0">
              <div>
                <h2 className="text-base md:text-xl font-bold text-gray-900 flex items-center truncate">
                  {activeView === 'overview' && (
                    <>
                      <ChartBarIcon className="w-5 h-5 mr-2 text-blue-600" />
                      Tổng quan kiểm duyệt
                    </>
                  )}
                  {activeView === 'moderation-queue' && (
                    <>
                      <ClipboardDocumentListIcon className="w-5 h-5 mr-2 text-orange-600" />
                      Queue kiểm duyệt -{' '}
                      {kanbanViewMode === 'kanban' ? 'Kanban Board' : 'Queue List'}
                    </>
                  )}
                  {activeView === 'reports' && (
                    <>
                      <ExclamationTriangleIcon className="w-5 h-5 mr-2 text-red-600" />
                      Báo cáo vi phạm
                    </>
                  )}
                  {activeView === 'content-review' && (
                    <>
                      <DocumentTextIcon className="w-5 h-5 mr-2 text-green-600" />
                      Review nội dung
                    </>
                  )}
                  {activeView === 'user-management' && (
                    <>
                      <UsersIcon className="w-5 h-5 mr-2 text-purple-600" />
                      Quản lý người dùng
                    </>
                  )}
                  {activeView === 'analytics' && (
                    <>
                      <ChartPieIcon className="w-5 h-5 mr-2 text-indigo-600" />
                      Phân tích
                    </>
                  )}
                  {activeView === 'settings' && (
                    <>
                      <Cog6ToothIcon className="w-5 h-5 mr-2 text-gray-600" />
                      Cài đặt
                    </>
                  )}
                  {activeView === 'system-users' && (
                    <>
                      <WrenchScrewdriverIcon className="w-5 h-5 mr-2 text-yellow-600" />
                      Quản lý hệ thống
                    </>
                  )}
                </h2>
                <p className="text-xs text-gray-600 mt-1 truncate">
                  {activeView === 'moderation-queue'
                    ? kanbanViewMode === 'kanban'
                      ? 'Quản lý công việc kiểm duyệt theo kanban'
                      : 'Danh sách nội dung chờ kiểm duyệt'
                    : navigationItems.find(item => item.id === activeView)?.description}
                </p>
              </div>
              {/* Enhanced Bulk Actions Bar: responsive */}
              {selectedItems.length > 0 && (
                <div className="flex flex-wrap items-center gap-2 p-2 sm:p-3 bg-gradient-to-r from-amber-50 to-pink-50 rounded-lg border border-amber-200 shadow-sm">
                  <div className="flex items-center space-x-2">
                    <CheckIcon className="w-5 h-5 text-yellow-600" />
                    <span className="text-xs sm:text-sm font-medium text-yellow-800">
                      Đã chọn {selectedItems.length} mục
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button className="px-2 sm:px-3 py-1 bg-green-600 text-white text-xs rounded-md hover:bg-green-700 transition-colors">
                      Duyệt tất cả
                    </button>
                    <button className="px-2 sm:px-3 py-1 bg-red-600 text-white text-xs rounded-md hover:bg-red-700 transition-colors">
                      Từ chối tất cả
                    </button>
                    <button
                      onClick={handleClearSelection}
                      className="px-2 sm:px-3 py-1 bg-gray-600 text-white text-xs rounded-md hover:bg-gray-700 transition-colors"
                    >
                      Bỏ chọn
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
          {/* Enhanced Content Container: responsive */}
          <div className="bg-white rounded-xl shadow-lg border border-pink-200 overflow-x-auto">
            <div className="p-2 sm:p-6">
              {loading ? (
                <div className="flex flex-col items-center justify-center h-40 sm:h-64">
                  <div className="animate-spin rounded-full h-10 w-10 sm:h-12 sm:w-12 border-b-2 border-blue-600"></div>
                  <p className="text-gray-600 mt-2 text-xs sm:text-base">Đang xử lý...</p>
                </div>
              ) : (
                renderMainContent()
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default ModeratorDashboard;
