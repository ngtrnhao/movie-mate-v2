import { useState, useEffect, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate, useLocation } from 'react-router-dom';
import moderationCacheService from '../../services/moderationCacheService';
import { getUnifiedModerationQueue } from '../../api/movieService';
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
  BellIcon,
  MagnifyingGlassIcon,
  ShieldCheckIcon,
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
import ReportsList from './components/ReportsList';
import UserManagement from './components/UserManagement';
import SystemSettings from './components/SystemSettings';
import AdminSettings from './components/AdminSettings';
import Analytics from './components/Analytics';
import ContentManagement from './components/ContentManagement';
import ContentModerationDashboard from './components/ContentModerationDashboard';
import AutoMarkedReviews from './components/AutoMarkedReviews';
import ModerationDebugPanel from './components/ModerationDebugPanel';

const ModeratorDashboard = () => {
  const [activeView, setActiveView] = useState('overview');
  const [selectedItems, setSelectedItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sidebarHidden, setSidebarHidden] = useState(false);
  const [sidebarMobileOpen, setSidebarMobileOpen] = useState(false);
  const [viewMode, setViewMode] = useState('dashboard'); // dashboard, kanban, queue
  const [kanbanViewMode, setKanbanViewMode] = useState('kanban'); // kanban, queue
  const [notifications, setNotifications] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showDebugPanel, setShowDebugPanel] = useState(false);

  // Shared data for both KanbanBoard and QueueList
  const [unifiedModerationData, setUnifiedModerationData] = useState(null);
  const [unifiedDataLoading, setUnifiedDataLoading] = useState(false);

  // Shared cache for moderation data to prevent duplicate API calls
  const [moderationCache, setModerationCache] = useState({
    queueData: null,
    kanbanData: null,
    lastFetch: 0,
    isStale: true,
  });

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

  // Fetch unified moderation data for both KanbanBoard and QueueList
  const fetchUnifiedModerationData = useCallback(async () => {
    try {
      setUnifiedDataLoading(true);
      console.log('🔄 Fetching unified moderation data for both KanbanBoard and QueueList...');

      // Use cache service for unified moderation queue API
      const data = await moderationCacheService.cachedApiCall(
        'unified_moderation_queue',
        async () => await getUnifiedModerationQueue(1, 100),
        { page: 1, pageSize: 100 }
      );

      setUnifiedModerationData(data);

      // Process data for both components
      const now = Date.now();

      // Process for QueueList
      const queueData = {
        items: data.tasks || [],
        totalPages: data.total_pages || 1,
        stats: data.stats?.priority_stats || {},
        timestamp: now,
      };

      // Process for KanbanBoard
      const kanbanData = data.kanban_data || {};
      const usedItemIds = new Set();

      const columnsData = {
        backlog: {
          id: 'backlog',
          title: 'Hàng đợi',
          items: (kanbanData.backlog || []).filter(item => {
            if (usedItemIds.has(item.id)) return false;
            usedItemIds.add(item.id);
            return true;
          }),
        },
        inProgress: {
          id: 'inProgress',
          title: 'Đang xử lý',
          items: (kanbanData.in_progress || []).filter(item => {
            if (usedItemIds.has(item.id)) return false;
            usedItemIds.add(item.id);
            return true;
          }),
        },
        review: {
          id: 'review',
          title: 'Đang xem xét',
          items: (kanbanData.review || []).filter(item => {
            if (usedItemIds.has(item.id)) return false;
            usedItemIds.add(item.id);
            return true;
          }),
        },
        completed: {
          id: 'completed',
          title: 'Hoàn thành',
          items: (kanbanData.completed || []).filter(item => {
            if (usedItemIds.has(item.id)) return false;
            usedItemIds.add(item.id);
            return true;
          }),
        },
      };

      const kanbanProcessedData = {
        columns: columnsData,
        timestamp: now,
      };

      // Update cache
      setModerationCache(prev => ({
        ...prev,
        queueData,
        kanbanData: kanbanProcessedData,
        lastFetch: now,
        isStale: false,
      }));

      console.log('✅ Unified moderation data loaded:', {
        totalTasks: data.tasks?.length || 0,
        totalKanbanItems: Object.values(columnsData).reduce(
          (sum, col) => sum + col.items.length,
          0
        ),
        fromCache: data.__fromCache || false,
      });
    } catch (error) {
      console.error('Error fetching unified moderation data:', error);
    } finally {
      setUnifiedDataLoading(false);
    }
  }, []);

  // Fetch data when moderation queue view is active
  useEffect(() => {
    if (activeView === 'moderation-queue' || activeView === 'reports') {
      fetchUnifiedModerationData();
    }
  }, [activeView, fetchUnifiedModerationData]);

  // Cache invalidation - mark data as stale after 60 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setModerationCache(prev => {
        const now = Date.now();
        if (now - prev.lastFetch > 60000) {
          // 60 seconds
          return { ...prev, isStale: true };
        }
        return prev;
      });
    }, 10000); // Check every 10 seconds

    return () => clearInterval(interval);
  }, []);

  // Handle data fetch from child components (legacy - now handled by unified fetch)
  const handleQueueDataFetch = useCallback(data => {
    // This is now handled by unified fetch
    console.log('💾 Queue data updated via unified fetch');
  }, []);

  const handleKanbanDataFetch = useCallback(data => {
    // This is now handled by unified fetch
    console.log('💾 Kanban data updated via unified fetch');
  }, []);

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
        id: 'content-moderation',
        label: 'Kiểm duyệt nội dung',
        icon: ShieldCheckIcon,
        iconSolid: ShieldCheckIcon,
        color: 'purple',
        viewMode: 'dashboard',
        description: 'Kiểm duyệt với spoiler detection',
        priority: 'high',
        badge: '25',
        badgeColor: 'red',
      },
      {
        id: 'auto-marked',
        label: 'Auto-marked Reviews',
        icon: BoltIcon,
        iconSolid: BoltIcon,
        color: 'yellow',
        viewMode: 'dashboard',
        description: 'Reviews được đánh dấu tự động bởi AI',
        priority: 'high',
        badge: '18',
        badgeColor: 'yellow',
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
    if (sidebarHidden) {
      setSidebarHidden(false);
      setSidebarCollapsed(false);
    } else if (sidebarCollapsed) {
      setSidebarHidden(true);
    } else {
      setSidebarCollapsed(true);
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
              <div className="mb-4 flex justify-center">
                <div className="flex rounded-xl border border-gray-200 bg-white p-1 shadow-lg">
                  <button
                    onClick={() => setKanbanViewMode('kanban')}
                    className={`flex items-center rounded-lg px-6 py-3 text-sm font-medium transition-all duration-200 ${
                      kanbanViewMode === 'kanban'
                        ? 'bg-green-100 text-green-700 shadow-sm'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <ClipboardDocumentListIcon className="mr-2 size-5" />
                    <div className="text-left">
                      <div className="font-semibold">Kanban Board</div>
                      <div className="text-xs opacity-75">Quản lý theo cột</div>
                    </div>
                  </button>
                  <button
                    onClick={() => setKanbanViewMode('queue')}
                    className={`flex items-center rounded-lg px-6 py-3 text-sm font-medium transition-all duration-200 ${
                      kanbanViewMode === 'queue'
                        ? 'bg-green-100 text-green-700 shadow-sm'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <DocumentTextIcon className="mr-2 size-5" />
                    <div className="text-left">
                      <div className="font-semibold">Queue List</div>
                      <div className="text-xs opacity-75">Danh sách đơn giản</div>
                    </div>
                  </button>
                </div>
              </div>

              {/* View-specific stats */}
              <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
                <div className="rounded-lg border-l-4 border-yellow-500 bg-white p-4 shadow">
                  <div className="flex items-center">
                    <ClockIcon className="mr-3 size-6 text-yellow-600" />
                    <div>
                      <p className="text-sm font-medium text-gray-600">Chờ duyệt</p>
                      <p className="text-2xl font-bold text-gray-900">23</p>
                    </div>
                  </div>
                </div>
                <div className="rounded-lg border-l-4 border-blue-500 bg-white p-4 shadow">
                  <div className="flex items-center">
                    <ChartBarIcon className="mr-3 size-6 text-blue-600" />
                    <div>
                      <p className="text-sm font-medium text-gray-600">Đang xử lý</p>
                      <p className="text-2xl font-bold text-gray-900">8</p>
                    </div>
                  </div>
                </div>
                <div className="rounded-lg border-l-4 border-green-500 bg-white p-4 shadow">
                  <div className="flex items-center">
                    <CheckIcon className="mr-3 size-6 text-green-600" />
                    <div>
                      <p className="text-sm font-medium text-gray-600">Hoàn thành</p>
                      <p className="text-2xl font-bold text-gray-900">156</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Loading state for unified data */}
            {unifiedDataLoading && (
              <div className="flex items-center justify-center py-8">
                <div className="size-8 animate-spin rounded-full border-b-2 border-blue-600"></div>
                <span className="ml-3 text-gray-600">Đang tải dữ liệu kiểm duyệt...</span>
              </div>
            )}

            {/* Content based on view mode */}
            {!unifiedDataLoading && (
              <>
                {kanbanViewMode === 'kanban' ? (
                  <KanbanBoard
                    selectedItems={selectedItems}
                    onSelectItem={handleSelectItem}
                    onBulkAction={handleBulkAction}
                    isAdmin={isAdmin}
                    // Pass processed data directly instead of letting component fetch
                    columns={
                      moderationCache.kanbanData?.columns || {
                        backlog: { id: 'backlog', title: 'Hàng đợi', items: [] },
                        inProgress: { id: 'inProgress', title: 'Đang xử lý', items: [] },
                        review: { id: 'review', title: 'Đang xem xét', items: [] },
                        completed: { id: 'completed', title: 'Hoàn thành', items: [] },
                      }
                    }
                    // Disable internal fetching since data is passed via props
                    disableInternalFetch={true}
                    onDataFetch={handleKanbanDataFetch}
                  />
                ) : (
                  <QueueList
                    selectedItems={selectedItems}
                    onSelectItem={handleSelectItem}
                    onSelectAll={handleSelectAll}
                    onClearSelection={handleClearSelection}
                    isAdmin={isAdmin}
                    // Pass processed data directly instead of letting component fetch
                    items={moderationCache.queueData?.items || []}
                    totalPages={moderationCache.queueData?.totalPages || 1}
                    stats={moderationCache.queueData?.stats || {}}
                    // Disable internal fetching since data is passed via props
                    disableInternalFetch={true}
                    onDataFetch={handleQueueDataFetch}
                  />
                )}
              </>
            )}
          </div>
        );
      case 'reports':
        return (
          <ReportsList
            selectedItems={selectedItems}
            onSelectItem={handleSelectItem}
            onSelectAll={handleSelectAll}
            onClearSelection={handleClearSelection}
            isAdmin={isAdmin}
          />
        );
      case 'content-review':
        return <ContentManagement />;
      case 'content-moderation':
        return <ContentModerationDashboard />;
      case 'auto-marked':
        return <AutoMarkedReviews />;
      case 'user-management':
        return <UserManagement />;
      case 'analytics':
        return <Analytics />;
      case 'settings':
        return isAdmin ? <AdminSettings /> : <SystemSettings />;
      case 'system-users':
        return isAdmin ? <UserManagement /> : null;
      default:
        return <DashboardOverview isAdmin={isAdmin} isModerator={isModerator} />;
    }
  };

  if (!user || !user.groups?.some(g => g.name === 'Moderators' || g.name === 'Administrators')) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="mb-4 text-2xl font-bold text-gray-900">Không có quyền truy cập</h1>
          <p className="text-gray-600">Bạn cần quyền Moderator hoặc Admin để truy cập trang này.</p>
        </div>
      </div>
    );
  }

  const navigationItems = getNavigationItems();
  const quickActions = getQuickActions();
  const dashboardStats = getDashboardStats();

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Responsive Header */}
      <header className=" flex h-auto w-full flex-col gap-2 border-b border-pink-200 bg-gradient-to-r from-pink-100 via-purple-100 to-amber-100 px-2 shadow-md sm:px-4 md:flex-row md:items-center md:justify-between md:gap-0 md:px-8">
        <div className="flex min-w-0 shrink-0 items-center space-x-2">
          <div className="flex items-center rounded-xl bg-gradient-to-r from-purple-400 to-pink-300 px-2 py-1 shadow-md">
            <ShieldCheckIcon className="size-6 text-white" />
            {!sidebarCollapsed && (
              <span className="ml-2 truncate text-base font-bold tracking-wide text-white sm:inline">
                Moderator
              </span>
            )}
          </div>
        </div>
        <div className="flex min-w-0 flex-1 flex-col items-center justify-center">
          <h1 className="truncate text-base font-bold leading-tight text-gray-900 md:text-lg">
            Moderator Dashboard
          </h1>
          <p className="mt-0.5 hidden items-center truncate text-xs text-gray-500 md:flex">
            <span className="mr-2 size-2 animate-pulse rounded-full bg-green-500"></span>
            Hệ thống kiểm duyệt nội dung Movie Recommendation
          </p>
        </div>
        <div className="mt-2 flex min-w-0 shrink-0 items-center space-x-1 sm:space-x-2 md:mt-0 md:space-x-4">
          <div className="relative hidden w-28 sm:block md:w-48 lg:w-64">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Tìm kiếm..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="w-full rounded-full border border-gray-200 bg-gray-50 py-2 pl-10 pr-4 text-sm focus:border-transparent focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="relative">
            <button className="rounded-full p-2 text-gray-600 transition-colors hover:bg-blue-50 hover:text-blue-600">
              <BellIcon className="size-5" />
              {notifications.length > 0 && (
                <span className="absolute -right-1 -top-1 flex size-5 items-center justify-center rounded-full bg-red-500 text-xs text-white">
                  {notifications.length}
                </span>
              )}
            </button>
          </div>
          <div className="flex items-center space-x-2">
            <span className="size-2 animate-pulse rounded-full bg-green-500"></span>
            <span className="text-xs text-gray-600">Online</span>
            <span
              className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                isAdmin
                  ? 'border border-purple-200 bg-purple-100 text-purple-800'
                  : 'border border-blue-200 bg-blue-100 text-blue-800'
              }`}
            >
              {isAdmin ? 'Admin' : 'Moderator'}
            </span>
          </div>
          <button
            onClick={() => navigate('/')}
            className="ml-1 inline-flex items-center rounded-full border border-transparent bg-gradient-to-r from-amber-400 to-pink-400 p-2 text-xs font-medium text-white shadow-md transition-all duration-200 hover:from-amber-500 hover:to-pink-500 hover:shadow-lg"
          >
            <HomeIcon className="size-5" />
            <span className="hidden md:inline">Trang chủ</span>
          </button>
        </div>
      </header>

      {/* Responsive Layout: Sidebar + Main */}
      <div className="flex w-full min-w-0 flex-1">
        {/* Sidebar: responsive, overlays on mobile, collapses on md+ */}
        <div
          id="moderator-sidebar"
          className={`
            fixed left-0 top-0 z-30 h-full border-r border-pink-200 bg-gradient-to-b from-pink-50 via-amber-50 to-purple-50 shadow-lg transition-all duration-300
            ${sidebarMobileOpen ? 'block' : 'hidden'}
            md:static md:block
            ${sidebarCollapsed ? 'w-16' : 'w-64'}
          `}
        >
          <div className="flex h-full min-w-0 flex-col gap-2 p-4">
            {/* Sidebar Toggle (sticky on mobile) */}
            <button
              onClick={handleSidebarToggle}
              className="mb-4 self-center rounded-lg p-2 hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-400 md:self-start"
              aria-label={sidebarCollapsed ? 'Mở sidebar' : 'Ẩn sidebar'}
            >
              <Bars3Icon className="size-6 text-blue-600" />
            </button>
            {/* Stats - Compact */}
            <div className="mb-4 flex flex-col gap-1">
              <h3 className="mb-2 flex items-center justify-center text-sm font-semibold text-gray-900 md:justify-start">
                <ChartBarIcon className="mr-0 size-4 md:mr-2" />
                {!sidebarCollapsed && <span className="truncate">Thống kê hôm nay</span>}
              </h3>
              <div className="space-y-1">
                {dashboardStats.slice(0, 3).map((stat, index) => {
                  const StatIcon = stat.icon;
                  return (
                    <div
                      key={index}
                      className={`flex items-center ${sidebarCollapsed ? 'justify-center' : 'justify-between'} ${sidebarCollapsed ? 'p-3' : 'p-2'} rounded-lg ${
                        stat.color === 'yellow'
                          ? 'border border-yellow-200 bg-yellow-50'
                          : stat.color === 'green'
                            ? 'border border-green-200 bg-green-50'
                            : stat.color === 'red'
                              ? 'border border-red-200 bg-red-50'
                              : 'border border-blue-200 bg-blue-50'
                      }`}
                    >
                      <StatIcon
                        className={`${sidebarCollapsed ? 'size-6' : 'size-4'} ${
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
                        <div className="ml-2 min-w-0 flex-1">
                          <div className="truncate text-xs font-medium text-gray-700">
                            {stat.title}
                          </div>
                          <div
                            className={`text-sm font-bold ${
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
                          </div>
                        </div>
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
                    className={`flex items-center ${sidebarCollapsed ? 'justify-center' : 'justify-between'} ${sidebarCollapsed ? 'p-4' : 'p-3'} group rounded-lg transition-all duration-200 ${sidebarCollapsed ? 'border-2 border-red-200' : ''}
                      ${
                        activeView === item.id
                          ? 'border border-amber-200 bg-gradient-to-r from-amber-100 to-pink-100 text-pink-700'
                          : 'text-purple-900 hover:bg-pink-50 hover:text-pink-700'
                      }`}
                  >
                    <IconComponent
                      className={`${sidebarCollapsed ? 'size-8 text-blue-600' : 'size-5 text-pink-400'} shrink-0`}
                      style={sidebarCollapsed ? { color: '#2563eb !important' } : {}}
                    />
                    {/* Ẩn label, badge khi thu nhỏ */}
                    {!sidebarCollapsed && (
                      <div className="ml-2 min-w-0 flex-1">
                        <div className="truncate text-sm font-medium">{item.label}</div>
                        <div className="mt-0.5 truncate text-xs opacity-75">{item.description}</div>
                      </div>
                    )}
                    {!sidebarCollapsed && item.badge && (
                      <span className="ml-2 truncate rounded-full bg-pink-100 px-2 py-1 text-xs font-medium text-pink-700">
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
            {/* Quick Actions - Compact Layout */}
            <div className="mb-4 flex flex-col gap-1">
              <h3 className="mb-2 flex items-center justify-center text-sm font-semibold text-gray-900 md:justify-start">
                <BoltIcon className="mr-0 size-4 md:mr-2" />
                {!sidebarCollapsed && <span className="truncate">Hành động nhanh</span>}
              </h3>
              <div className="space-y-1">
                {quickActions.map(action => {
                  const ActionIcon = action.icon;
                  return (
                    <button
                      key={action.id}
                      onClick={() => handleBulkAction(action.id, selectedItems)}
                      className={`flex items-center ${sidebarCollapsed ? 'justify-center' : 'justify-start'} ${sidebarCollapsed ? 'p-3' : 'p-2'} group rounded-lg text-left transition-all duration-200 ${sidebarCollapsed ? 'border border-gray-200' : ''}
                        hover:from- hover:bg-gradient-to-r${action.color}-50 hover:to-${action.color}-100 hover:border-${action.color}-200`}
                    >
                      <ActionIcon
                        className={`${sidebarCollapsed ? 'size-6' : 'size-4'} shrink-0 ${
                          action.color === 'green'
                            ? 'text-green-600'
                            : action.color === 'red'
                              ? 'text-red-600'
                              : action.color === 'orange'
                                ? 'text-orange-600'
                                : action.color === 'blue'
                                  ? 'text-blue-600'
                                  : 'text-gray-600'
                        }`}
                      />
                      {!sidebarCollapsed && (
                        <div className="ml-2 min-w-0 flex-1">
                          <div
                            className={`truncate text-xs font-medium ${
                              action.color === 'green'
                                ? 'text-green-700'
                                : action.color === 'red'
                                  ? 'text-red-700'
                                  : action.color === 'orange'
                                    ? 'text-orange-700'
                                    : action.color === 'blue'
                                      ? 'text-blue-700'
                                      : 'text-gray-700'
                            }`}
                          >
                            {action.label}
                          </div>
                          <div className="mt-0.5 truncate text-xs text-gray-500">
                            {action.shortcut}
                          </div>
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
            {/* Moderator Info - Compact */}
            {!sidebarCollapsed && (
              <div className="mt-auto rounded-lg border border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 p-3">
                <h4 className="mb-1 flex items-center text-xs font-semibold text-blue-800">
                  <InformationCircleIcon className="mr-1 size-3" />
                  Quyền Moderator
                </h4>
                <div className="space-y-0.5 text-xs text-blue-700">
                  <div>• Kiểm duyệt nội dung</div>
                  <div>• Xử lý báo cáo vi phạm</div>
                  <div>• Cảnh báo người dùng</div>
                </div>
              </div>
            )}
          </div>
        </div>
        {/* Main Content Area: responsive padding, min-w-0, overflow-x-auto */}
        <main className="min-w-0 flex-1 overflow-x-auto p-2 sm:p-4 md:p-6">
          {/* Enhanced Content Header: responsive */}
          <div className="mb-4 sm:mb-6">
            <div className="flex flex-col items-start justify-between gap-2 sm:flex-row sm:items-center sm:gap-0">
              <div>
                <h2 className="flex items-center truncate text-base font-bold text-gray-900 md:text-xl">
                  {activeView === 'overview' && (
                    <>
                      <ChartBarIcon
                        className={`${sidebarCollapsed ? 'size-8' : 'size-5'} mr-2 text-blue-600`}
                      />
                      Tổng quan kiểm duyệt
                    </>
                  )}
                  {activeView === 'moderation-queue' && (
                    <>
                      <ClipboardDocumentListIcon
                        className={`${sidebarCollapsed ? 'size-8' : 'size-5'} mr-2 text-orange-600`}
                      />
                      Queue kiểm duyệt -{' '}
                      {kanbanViewMode === 'kanban' ? 'Kanban Board' : 'Queue List'}
                    </>
                  )}
                  {activeView === 'reports' && (
                    <>
                      <ExclamationTriangleIcon
                        className={`${sidebarCollapsed ? 'size-8' : 'size-5'} mr-2 text-red-600`}
                      />
                      Báo cáo vi phạm
                    </>
                  )}
                  {activeView === 'content-review' && (
                    <>
                      <DocumentTextIcon
                        className={`${sidebarCollapsed ? 'size-8' : 'size-5'} mr-2 text-green-600`}
                      />
                      Review nội dung
                    </>
                  )}
                  {activeView === 'user-management' && (
                    <>
                      <UsersIcon
                        className={`${sidebarCollapsed ? 'size-8' : 'size-5'} mr-2 text-purple-600`}
                      />
                      Quản lý người dùng
                    </>
                  )}
                  {activeView === 'analytics' && (
                    <>
                      <ChartPieIcon
                        className={`${sidebarCollapsed ? 'size-8' : 'size-5'} mr-2 text-indigo-600`}
                      />
                      Phân tích
                    </>
                  )}
                  {activeView === 'settings' && (
                    <>
                      <Cog6ToothIcon
                        className={`${sidebarCollapsed ? 'size-8' : 'size-5'} mr-2 text-gray-600`}
                      />
                      Cài đặt
                    </>
                  )}
                  {activeView === 'system-users' && (
                    <>
                      <WrenchScrewdriverIcon
                        className={`${sidebarCollapsed ? 'size-8' : 'size-5'} mr-2 text-yellow-600`}
                      />
                      Quản lý hệ thống
                    </>
                  )}
                </h2>
                <p className="mt-1 truncate text-xs text-gray-600">
                  {activeView === 'moderation-queue'
                    ? kanbanViewMode === 'kanban'
                      ? 'Quản lý công việc kiểm duyệt theo kanban'
                      : 'Danh sách nội dung chờ kiểm duyệt'
                    : navigationItems.find(item => item.id === activeView)?.description}
                </p>
              </div>
              {/* Enhanced Bulk Actions Bar: responsive */}
              {selectedItems.length > 0 && (
                <div className="flex flex-wrap items-center gap-2 rounded-lg border border-amber-200 bg-gradient-to-r from-amber-50 to-pink-50 p-2 shadow-sm sm:p-3">
                  <div className="flex items-center space-x-2">
                    <CheckIcon className="size-5 text-yellow-600" />
                    <span className="text-xs font-medium text-yellow-800 sm:text-sm">
                      Đã chọn {selectedItems.length} mục
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button className="rounded-md bg-green-600 px-2 py-1 text-xs text-white transition-colors hover:bg-green-700 sm:px-3">
                      Duyệt tất cả
                    </button>
                    <button className="rounded-md bg-red-600 px-2 py-1 text-xs text-white transition-colors hover:bg-red-700 sm:px-3">
                      Từ chối tất cả
                    </button>
                    <button
                      onClick={handleClearSelection}
                      className="rounded-md bg-gray-600 px-2 py-1 text-xs text-white transition-colors hover:bg-gray-700 sm:px-3"
                    >
                      Bỏ chọn
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
          {/* Enhanced Content Container: responsive */}
          <div className="overflow-x-auto rounded-xl border border-pink-200 bg-white shadow-lg">
            <div className="p-2 sm:p-6">
              {loading ? (
                <div className="flex h-40 flex-col items-center justify-center sm:h-64">
                  <div className="size-10 animate-spin rounded-full border-b-2 border-blue-600 sm:size-12"></div>
                  <p className="mt-2 text-xs text-gray-600 sm:text-base">Đang xử lý...</p>
                </div>
              ) : (
                renderMainContent()
              )}
            </div>
          </div>
        </main>
      </div>

      {/* Debug Panel for monitoring API calls */}
      <ModerationDebugPanel
        moderationCache={moderationCache}
        showDebug={showDebugPanel}
        onToggleDebug={setShowDebugPanel}
      />
    </div>
  );
};

export default ModeratorDashboard;
