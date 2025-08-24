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
  ArrowTrendingUpIcon,
  FilmIcon,
  EyeIcon,
  PlusIcon,
  DocumentArrowDownIcon,
  ChartBarSquareIcon,
  ClipboardDocumentListIcon,
  CalendarIcon,
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
  ChartBarSquareIcon as ChartBarSquareIconSolid,
  ArrowTrendingUpIcon as ArrowTrendingUpIconSolid,
  CalendarIcon as CalendarIconSolid,
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
import SchedulingManagement from './components/SchedulingManagement';
import UserInteractionAnalytics from './components/UserInteractionAnalytics';
import TrendingAnalytics from './components/TrendingAnalytics';
import RealTimeCharts from './components/RealTimeCharts';
import AutoProcessingStatus from './components/AutoProcessingStatus';
import MovieEnrichmentPanel from './components/MovieEnrichmentPanel';
import AdminSidebar from './components/AdminSidebar';
import AdminHeader from './components/AdminHeader';
import ContentModerationDashboard from '../Moderator/components/ContentModerationDashboard';
import ReportsList from '../Moderator/components/ReportsList';
// import AdminStatsCards from './components/AdminStatsCards';
import {
  AdminDataProvider,
  useAdminData,
  useAdminRealTimeMetrics,
} from '../../contexts/AdminDataContext';

const AdminDashboardContent = () => {
  const dispatch = useDispatch();
  const [activeView, setActiveView] = useState('overview');
  const [selectedItems, setSelectedItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [viewMode, setViewMode] = useState('dashboard'); // dashboard, kanban, queue
  const [kanbanViewMode, setKanbanViewMode] = useState('kanban'); // Add for moderation view toggle

  const { dashboardData, setActiveTab, activeTab } = useAdminData();
  const { data: realTimeMetrics, isStale } = useAdminRealTimeMetrics();
  const user = useSelector(state => state.auth.user);
  const navigate = useNavigate();

  // Check if user is admin
  useEffect(() => {
    if (!user || !user.groups?.some(g => g.name === 'Administrators')) {
      navigate('/');
    }
  }, [user, navigate]);

  // Update active tab in context when view changes
  useEffect(() => {
    // Only update if tab actually changed
    if (activeTab !== activeView) {
      setActiveTab(activeView);
      console.log('🔄 [AdminDashboard] Active tab changed to:', activeView);
    }
  }, [activeView, setActiveTab, activeTab]);

  // Navigation configuration with improved grouping
  const getNavigationItems = () => {
    return [
      {
        id: 'overview',
        label: 'Tổng quan',
        icon: ChartBarIcon,
        iconSolid: ChartBarIconSolid,
        color: 'blue',
        group: 'main',
        priority: 'high',
        description: 'Dashboard tổng quan với metrics thời gian thực',
      },
      {
        id: 'realtime_analytics',
        label: 'Analytics Real-time',
        icon: ChartBarSquareIcon,
        iconSolid: ChartBarSquareIconSolid,
        color: 'indigo',
        group: 'main',
        priority: 'high',
        description: 'Biểu đồ và thống kê thời gian thực',
      },
      {
        id: 'auto_processing',
        label: 'Auto-Processing',
        icon: Cog6ToothIcon,
        iconSolid: Cog6ToothIconSolid,
        color: 'emerald',
        group: 'main',
        priority: 'high',
        description: 'Trạng thái tự động xử lý dữ liệu và metrics',
      },
      {
        id: 'movies',
        label: 'Quản lý phim',
        icon: FilmIcon,
        iconSolid: FilmIconSolid,
        color: 'purple',
        group: 'content',
        priority: 'high',
        description: 'Quản lý nội dung và production metrics',
      },
      {
        id: 'movie_enrichment',
        label: 'Enrichment',
        icon: CpuChipIcon,
        iconSolid: CpuChipIcon,
        color: 'emerald',
        group: 'content',
        priority: 'high',
        description: 'Enrichment dữ liệu phim từ TMDB/IMDB',
      },
      {
        id: 'scheduling',
        label: 'Lịch trình',
        icon: CalendarIcon,
        iconSolid: CalendarIconSolid,
        color: 'indigo',
        group: 'content',
        priority: 'high',
        description: 'Quản lý lịch trình xuất bản và featured content',
      },
      {
        id: 'visibility',
        label: 'Hiển thị',
        icon: EyeIcon,
        iconSolid: EyeIconSolid,
        color: 'indigo',
        group: 'content',
        priority: 'high',
        description: 'Điều khiển hiển thị và featured content',
      },
      {
        id: 'moderation',
        label: 'Queue kiểm duyệt',
        icon: ShieldCheckIcon,
        iconSolid: ShieldCheckIconSolid,
        color: 'orange',
        group: 'moderation',
        priority: 'high',
        description: 'Hệ thống kiểm duyệt và workflow',
      },
      {
        id: 'content_moderation',
        label: 'Kiểm duyệt nội dung',
        icon: ShieldCheckIcon,
        iconSolid: ShieldCheckIconSolid,
        color: 'orange',
        group: 'moderation',
        priority: 'high',
        description: 'Hệ thống kiểm duyệt nội dung',
      },
      {
        id: 'reports',
        label: 'Báo cáo vi phạm',
        icon: ChartPieIcon,
        iconSolid: ChartPieIconSolid,
        color: 'red',
        group: 'moderation',
        priority: 'high',
        description: 'Báo cáo vi phạm từ người dùng',
      },
      {
        id: 'users',
        label: 'Người dùng',
        icon: UsersIcon,
        iconSolid: UsersIconSolid,
        color: 'green',
        group: 'management',
        priority: 'high',
        description: 'Quản lý người dùng và phân quyền',
      },
      {
        id: 'user_interactions',
        label: 'Tương tác',
        icon: UsersIcon,
        iconSolid: UsersIconSolid,
        color: 'teal',
        group: 'analytics',
        priority: 'medium',
        description: 'Phân tích tương tác người dùng',
      },
      {
        id: 'trending_analytics',
        label: 'Xu hướng',
        icon: ArrowTrendingUpIcon,
        iconSolid: ArrowTrendingUpIconSolid,
        color: 'rose',
        group: 'analytics',
        priority: 'medium',
        description: 'Phân tích xu hướng và trending',
      },
      {
        id: 'content',
        label: 'Nội dung',
        icon: DocumentTextIcon,
        iconSolid: DocumentTextIconSolid,
        color: 'purple',
        group: 'analytics',
        priority: 'medium',
        description: 'Thống kê nội dung và chất lượng',
      },
      {
        id: 'analytics',
        label: 'Phân tích & Báo cáo',
        icon: ChartPieIcon,
        iconSolid: ChartPieIconSolid,
        color: 'indigo',
        group: 'analytics',
        priority: 'medium',
        description: 'Báo cáo tổng hợp và insights',
      },
      {
        id: 'settings',
        label: 'Cài đặt hệ thống',
        icon: Cog6ToothIcon,
        iconSolid: Cog6ToothIconSolid,
        color: 'gray',
        group: 'system',
        priority: 'low',
        description: 'Cấu hình hệ thống và tùy chỉnh',
      },
    ];
  };

  // Enhanced quick actions with production metrics focus
  const getQuickActions = () => {
    return [
      {
        id: 'refresh_metrics',
        label: 'Làm mới Metrics',
        icon: ArrowTrendingUpIcon,
        color: 'blue',
        description: 'Cập nhật production metrics',
      },
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
        description: 'Xuất báo cáo và dữ liệu metrics',
      },
    ];
  };

  // Get breadcrumbs with more context
  const getBreadcrumbs = () => {
    const navigationItems = getNavigationItems();
    const currentItem = navigationItems.find(item => item.id === activeView);
    return [
      { name: 'Admin', href: '#' },
      { name: currentItem?.label || 'Dashboard', href: '#' },
      ...(isStale ? [{ name: '⚠️ Dữ liệu cũ', href: '#' }] : []),
    ];
  };

  // Handle bulk selection
  const handleSelectItem = useCallback(itemId => {
    setSelectedItems(prev =>
      prev.includes(itemId) ? prev.filter(id => id !== itemId) : [...prev, itemId]
    );
  }, []);

  // Handle select all
  const handleSelectAll = useCallback(() => {
    // This would be implemented based on the current view
    console.log('Select all items');
  }, []);

  // Handle clear selection
  const handleClearSelection = useCallback(() => {
    setSelectedItems([]);
  }, []);

  // Enhanced bulk actions with production metrics
  const handleBulkAction = useCallback(async (action, items) => {
    try {
      setLoading(true);
      console.log(`Performing bulk action: ${action} on items:`, items);

      // Special handling for metrics refresh
      if (action === 'refresh_metrics') {
        // Trigger metrics refresh
        window.location.reload(); // Temporary solution
        return;
      }

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Clear selection after action
      setSelectedItems([]);

      // Show success message
      alert(`Đã thực hiện hành động: ${action}`);
    } catch (error) {
      console.error('Bulk action error:', error);
      alert('Có lỗi xảy ra khi thực hiện hành động');
    } finally {
      setLoading(false);
    }
  }, []);

  // Enhanced render main content with new real-time analytics
  const renderMainContent = () => {
    switch (activeView) {
      case 'overview':
        return <AdminDashboardOverview />;
      case 'realtime_analytics':
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Real-time Analytics Dashboard</h2>
                <p className="mt-1 text-gray-600">
                  Biểu đồ và thống kê thời gian thực cho user tracking và production metrics
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <div className="size-2 animate-pulse rounded-full bg-green-400"></div>
                <span className="text-sm text-gray-500">Live Data</span>
                {isStale && (
                  <span className="rounded bg-yellow-100 px-2 py-1 text-xs text-yellow-600">
                    Dữ liệu cũ
                  </span>
                )}
              </div>
            </div>
            <RealTimeCharts />
          </div>
        );
      case 'auto_processing':
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Auto-Processing Status</h2>
                <p className="mt-1 text-gray-600">
                  Trạng thái và điều khiển hệ thống tự động xử lý dữ liệu
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <div className="size-2 animate-pulse rounded-full bg-emerald-400"></div>
                <span className="text-sm text-gray-500">Automation Active</span>
              </div>
            </div>
            <AutoProcessingStatus />
          </div>
        );
      case 'users':
        return <UserManagement />;
      case 'movies':
        return <MovieManagement />;
      case 'movie_enrichment':
        return <MovieEnrichmentPanel />;
      case 'scheduling':
        return <SchedulingManagement />;
      case 'analytics':
        return <UserAnalytics />;
      case 'content':
        return <ContentAnalytics />;
      case 'visibility':
        return <VisibilityControl />;
      case 'content_moderation':
        return <ContentModerationDashboard />;
      case 'moderation':
        return (
          <div>
            {/* Toggle Kanban/Queue like Moderator dashboard */}
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
            </div>
            {kanbanViewMode === 'kanban' ? (
              <KanbanBoard
                selectedItems={selectedItems}
                onSelectItem={handleSelectItem}
                onBulkAction={handleBulkAction}
                isAdmin={true}
              />
            ) : (
              <QueueList
                selectedItems={selectedItems}
                onSelectItem={handleSelectItem}
                onSelectAll={handleSelectAll}
                onClearSelection={handleClearSelection}
                isAdmin={true}
              />
            )}
          </div>
        );
      case 'reports':
        // Use ReportsList for violation reports, like Moderator dashboard
        return (
          <ReportsList
            selectedItems={selectedItems}
            onSelectItem={handleSelectItem}
            onSelectAll={handleSelectAll}
            onClearSelection={handleClearSelection}
            isAdmin={true}
          />
        );
      case 'user_interactions':
        return <UserInteractionAnalytics />;
      case 'trending_analytics':
        return <TrendingAnalytics />;
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
  const breadcrumbs = getBreadcrumbs();

  // Group navigation items
  const groupedNavigation = navigationItems.reduce((acc, item) => {
    if (!acc[item.group]) {
      acc[item.group] = [];
    }
    acc[item.group].push(item);
    return acc;
  }, {});

  const groupLabels = {
    main: 'Tổng quan & Analytics',
    content: 'Quản lý nội dung',
    moderation: 'Kiểm duyệt & Báo cáo vi phạm',
    analytics: 'Phân tích & Thống kê',
    management: 'Quản lý người dùng & phân quyền',
    system: 'Cài đặt hệ thống',
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <AdminSidebar
        sidebarCollapsed={sidebarCollapsed}
        setSidebarCollapsed={setSidebarCollapsed}
        activeView={activeView}
        setActiveView={setActiveView}
        navigationItems={navigationItems}
        groupedNavigation={groupedNavigation}
        groupLabels={groupLabels}
      />

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Header */}
        <AdminHeader
          breadcrumbs={breadcrumbs}
          quickActions={quickActions}
          handleBulkAction={handleBulkAction}
          selectedItems={selectedItems}
        />

        {/* Content Area */}
        <main className="flex-1 overflow-y-auto p-6">
          {/* Enhanced System Stats Cards with Real-time Data */}
          {/* <AdminStatsCards realTimeMetrics={realTimeMetrics} /> */}

          {/* Main Content */}
          <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
            {loading ? (
              <div className="flex h-64 items-center justify-center">
                <div className="text-center">
                  <div className="mx-auto mb-4 size-12 animate-spin rounded-full border-b-2 border-blue-600"></div>
                  <p className="text-gray-600">Đang xử lý...</p>
                </div>
              </div>
            ) : (
              <div className="p-6">{renderMainContent()}</div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

// Main wrapper component with AdminDataProvider
const AdminDashboard = () => {
  return (
    <AdminDataProvider>
      <AdminDashboardContent />
    </AdminDataProvider>
  );
};

export default AdminDashboard;
