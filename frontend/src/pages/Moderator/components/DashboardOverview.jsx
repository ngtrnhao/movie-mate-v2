import { useState, useEffect, useCallback } from 'react';
import {
  CheckCircleIcon,
  XCircleIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
} from '@heroicons/react/24/outline';
import {
  getDashboardOverview,
  getRecentModerationActivities,
  getModerationPerformanceMetrics,
} from '../../../api/moderatorService';
import moderationCacheService from '../../../services/moderationCacheService';

const DashboardOverview = ({ isAdmin: _isAdmin, isModerator: _isModerator }) => {
  // State for real data
  const [stats, setStats] = useState([]);
  const [recentActivities, setRecentActivities] = useState([]);
  const [performanceMetrics, setPerformanceMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Optimized fetch function with caching
  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Use cache service for all three APIs
      const [overviewResponse, activitiesResponse, metricsResponse] = await Promise.all([
        moderationCacheService.cachedApiCall(
          'dashboard_overview',
          async () => await getDashboardOverview(),
          {}
        ),
        moderationCacheService.cachedApiCall(
          'recent_activities',
          async () => await getRecentModerationActivities(5),
          { limit: 5 }
        ),
        moderationCacheService.cachedApiCall(
          'performance_metrics',
          async () => await getModerationPerformanceMetrics(),
          {}
        ),
      ]);

      // Set real data from APIs
      setStats(overviewResponse.data?.stats || []);
      setRecentActivities(activitiesResponse.data || []);
      setPerformanceMetrics(metricsResponse.data || null);

      console.log('✅ Dashboard overview data loaded:', {
        stats: overviewResponse.data?.stats?.length || 0,
        activities: activitiesResponse.data?.length || 0,
        metrics: !!metricsResponse.data,
        fromCache: {
          overview: overviewResponse.__fromCache || false,
          activities: activitiesResponse.__fromCache || false,
          metrics: metricsResponse.__fromCache || false,
        },
      });
    } catch (err) {
      console.error('Error fetching dashboard overview:', err);
      setError('Không thể tải dữ liệu dashboard');

      // Fallback to hardcoded data if API fails
      setStats([
        {
          title: 'Nội dung chờ duyệt',
          value: '23',
          change: '+5',
          change_type: 'increase',
          color: 'yellow',
        },
        {
          title: 'Báo cáo vi phạm',
          value: '12',
          change: '+3',
          change_type: 'increase',
          color: 'red',
        },
        {
          title: 'Đã duyệt hôm nay',
          value: '156',
          change: '+23',
          change_type: 'increase',
          color: 'green',
        },
        {
          title: 'Thời gian xử lý TB',
          value: '2.5h',
          change: '-0.3h',
          change_type: 'decrease',
          color: 'blue',
        },
      ]);

      setRecentActivities([
        {
          id: 1,
          content: 'Đã duyệt review "Avengers: Endgame"',
          user: 'Moderator A',
          time: '2 phút trước',
        },
        {
          id: 2,
          content: 'Từ chối comment vi phạm',
          user: 'Moderator B',
          time: '5 phút trước',
        },
        {
          id: 3,
          content: 'Xử lý báo cáo spam',
          user: 'Moderator C',
          time: '10 phút trước',
        },
      ]);

      setPerformanceMetrics({
        accuracy_rate: { value: 95, unit: '%' },
        avg_processing_time: { value: 2.3, unit: 'phút' },
        daily_processed: { value: 156, unit: 'nội dung/ngày' },
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const getStatusColor = status => {
    const colors = {
      yellow: 'bg-pink-50 border-pink-200 text-pink-700',
      red: 'bg-amber-50 border-amber-200 text-amber-700',
      green: 'bg-purple-50 border-purple-200 text-purple-700',
      blue: 'bg-gray-50 border-gray-200 text-gray-700',
    };
    return colors[status] || colors.blue;
  };

  // Loading state
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map(index => (
            <div key={index} className="rounded-lg border bg-gray-50 p-4">
              <div className="animate-pulse">
                <div className="mb-2 h-4 w-3/4 rounded bg-gray-200"></div>
                <div className="h-8 w-1/2 rounded bg-gray-200"></div>
                <div className="mt-2 h-3 w-1/3 rounded bg-gray-200"></div>
              </div>
            </div>
          ))}
        </div>
        <div className="rounded-lg bg-white p-6 shadow">
          <div className="animate-pulse">
            <div className="mb-4 h-6 w-1/4 rounded bg-gray-200"></div>
            <div className="space-y-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-16 rounded bg-gray-200"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-6">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <div className="flex items-center">
            <XCircleIcon className="mr-3 size-5 text-red-600" />
            <div>
              <h3 className="text-sm font-medium text-red-800">Lỗi tải dữ liệu</h3>
              <p className="text-sm text-red-700">{error}</p>
            </div>
            <button
              onClick={fetchDashboardData}
              className="ml-auto rounded bg-red-100 px-3 py-1 text-xs text-red-700 hover:bg-red-200"
            >
              Thử lại
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Grid - Now using real API data */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => (
          <div key={index} className={`rounded-lg border p-4 ${getStatusColor(stat.color)}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-700 opacity-75">{stat.title}</p>
                <p className="mt-2 text-3xl font-bold text-purple-900">{stat.value}</p>
                <p className="mt-1 text-xs text-gray-600 opacity-75">{stat.description}</p>
              </div>
              <div className="flex items-center">
                {stat.change_type === 'increase' ? (
                  <ArrowTrendingUpIcon className="mr-1 size-4 text-green-600" />
                ) : (
                  <ArrowTrendingDownIcon className="mr-1 size-4 text-red-600" />
                )}
                <span
                  className={`text-xs font-medium ${
                    stat.change_type === 'increase' ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {stat.change}
                </span>
                <span className="ml-1 text-xs text-gray-500 opacity-75">so với hôm qua</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity - Now using real API data */}
      <div className="rounded-lg bg-white p-6 shadow">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-purple-900">Hoạt động gần đây</h3>
          <button
            onClick={fetchDashboardData}
            className="rounded bg-gray-100 px-3 py-1 text-xs text-gray-600 hover:bg-gray-200"
          >
            Làm mới
          </button>
        </div>
        <div className="space-y-4">
          {recentActivities.length > 0 ? (
            recentActivities.map((activity, index) => (
              <div
                key={activity.id || index}
                className="flex items-start space-x-3 rounded-lg border border-pink-200 bg-gradient-to-r from-pink-50 to-amber-50 p-3"
              >
                <div className="mt-1 size-5 rounded-full bg-pink-600"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-purple-900">{activity.content}</p>
                  <p className="text-xs text-pink-700">
                    {activity.time} • {activity.user}
                  </p>
                </div>
              </div>
            ))
          ) : (
            <p className="text-center text-sm text-gray-500">Chưa có hoạt động gần đây</p>
          )}
        </div>
        <button className="mt-4 w-full text-sm font-medium text-pink-600 hover:text-pink-700">
          Xem tất cả hoạt động
        </button>
      </div>

      {/* Quick Actions */}
      <div className="rounded-lg bg-white p-6 shadow">
        <h3 className="mb-4 text-lg font-semibold text-purple-900">Hành động nhanh</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <button className="flex w-full items-center rounded-lg bg-green-50 p-3 text-left transition-colors hover:bg-pink-50">
            <CheckCircleIcon className="mr-3 size-5 text-pink-600" />
            <div>
              <p className="font-medium text-purple-900">Duyệt tất cả</p>
              <p className="text-xs text-pink-700">Duyệt nội dung chờ</p>
            </div>
          </button>
          <button className="flex w-full items-center rounded-lg bg-red-50 p-3 text-left transition-colors hover:bg-pink-50">
            <XCircleIcon className="mr-3 size-5 text-pink-600" />
            <div>
              <p className="font-medium text-purple-900">Từ chối vi phạm</p>
              <p className="text-xs text-pink-700">Loại bỏ nội dung xấu</p>
            </div>
          </button>
          <button className="flex w-full items-center rounded-lg bg-blue-50 p-3 text-left transition-colors hover:bg-pink-50">
            <ChartBarIcon className="mr-3 size-5 text-purple-600" />
            <div>
              <p className="font-medium text-purple-900">Xem báo cáo</p>
              <p className="text-xs text-pink-700">Thống kê chi tiết</p>
            </div>
          </button>
          <button className="flex w-full items-center rounded-lg bg-purple-50 p-3 text-left transition-colors hover:bg-pink-50">
            <Cog6ToothIcon className="mr-3 size-5 text-purple-600" />
            <div>
              <p className="font-medium text-purple-900">Cài đặt</p>
              <p className="text-xs text-pink-700">Cấu hình hệ thống</p>
            </div>
          </button>
        </div>
      </div>

      {/* Performance Metrics - Now using real API data */}
      <div className="rounded-lg bg-white p-6 shadow">
        <h3 className="mb-4 text-lg font-semibold text-purple-900">Hiệu suất kiểm duyệt</h3>
        {performanceMetrics ? (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">
                {performanceMetrics.accuracy_rate?.value || 0}
                {performanceMetrics.accuracy_rate?.unit || '%'}
              </div>
              <p className="mt-1 text-sm text-gray-600">Tỷ lệ chính xác</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">
                {performanceMetrics.avg_processing_time?.value || 0}{' '}
                {performanceMetrics.avg_processing_time?.unit || 'phút'}
              </div>
              <p className="mt-1 text-sm text-gray-600">Thời gian xử lý TB</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">
                {performanceMetrics.daily_processed?.value || 0}
              </div>
              <p className="mt-1 text-sm text-gray-600">
                {performanceMetrics.daily_processed?.unit || 'Nội dung/ngày'}
              </p>
            </div>
          </div>
        ) : (
          <div className="animate-pulse">
            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="text-center">
                  <div className="mx-auto h-8 w-16 rounded bg-gray-200"></div>
                  <div className="mx-auto mt-2 h-4 w-24 rounded bg-gray-200"></div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardOverview;
