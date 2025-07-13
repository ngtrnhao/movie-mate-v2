import React from 'react';
import { useUserInteractionStats } from '../../../hooks/useUserInteractionStats';
import {
  EyeIcon,
  UsersIcon,
  DevicePhoneMobileIcon,
  ComputerDesktopIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ClockIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';

const UserInteractionAnalytics = () => {
  const { data, loading, error, refetch } = useUserInteractionStats();

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={refetch}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Thử lại
          </button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <p className="text-gray-500 text-center">Không có dữ liệu</p>
      </div>
    );
  }

  const { overview, action_breakdown, top_movies, session_stats, trends } = data;

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Tổng quan tương tác người dùng</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="flex items-center justify-center w-10 h-10 bg-blue-100 rounded-full mx-auto mb-2">
              <ChartBarIcon className="w-5 h-5 text-blue-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {overview.total_interactions?.toLocaleString() || 0}
            </p>
            <p className="text-sm text-gray-500">Tổng tương tác</p>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center w-10 h-10 bg-green-100 rounded-full mx-auto mb-2">
              <UsersIcon className="w-5 h-5 text-green-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {overview.total_users?.toLocaleString() || 0}
            </p>
            <p className="text-sm text-gray-500">Người dùng</p>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center w-10 h-10 bg-purple-100 rounded-full mx-auto mb-2">
              <EyeIcon className="w-5 h-5 text-purple-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {overview.total_sessions?.toLocaleString() || 0}
            </p>
            <p className="text-sm text-gray-500">Phiên làm việc</p>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center w-10 h-10 bg-orange-100 rounded-full mx-auto mb-2">
              <ClockIcon className="w-5 h-5 text-orange-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {overview.avg_interactions_per_user || 0}
            </p>
            <p className="text-sm text-gray-500">Tương tác/người dùng</p>
          </div>
        </div>
      </div>

      {/* Time-based Stats */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Thống kê theo thời gian</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              {overview.today_interactions?.toLocaleString() || 0}
            </p>
            <p className="text-sm text-gray-500">Hôm nay</p>
            <div className="flex items-center justify-center mt-1">
              {trends.daily_growth > 0 ? (
                <ArrowTrendingUpIcon className="w-4 h-4 text-green-500 mr-1" />
              ) : (
                <ArrowTrendingDownIcon className="w-4 h-4 text-red-500 mr-1" />
              )}
              <span
                className={`text-sm ${trends.daily_growth > 0 ? 'text-green-600' : 'text-red-600'}`}
              >
                {trends.daily_growth > 0 ? '+' : ''}
                {trends.daily_growth}%
              </span>
            </div>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              {overview.week_interactions?.toLocaleString() || 0}
            </p>
            <p className="text-sm text-gray-500">Tuần này</p>
            <div className="flex items-center justify-center mt-1">
              {trends.weekly_growth > 0 ? (
                <ArrowTrendingUpIcon className="w-4 h-4 text-green-500 mr-1" />
              ) : (
                <ArrowTrendingDownIcon className="w-4 h-4 text-red-500 mr-1" />
              )}
              <span
                className={`text-sm ${trends.weekly_growth > 0 ? 'text-green-600' : 'text-red-600'}`}
              >
                {trends.weekly_growth > 0 ? '+' : ''}
                {trends.weekly_growth}%
              </span>
            </div>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              {overview.month_interactions?.toLocaleString() || 0}
            </p>
            <p className="text-sm text-gray-500">Tháng này</p>
          </div>
        </div>
      </div>

      {/* Action Breakdown */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Phân tích hành động</h3>
        <div className="space-y-3">
          {action_breakdown?.slice(0, 5).map((action, index) => (
            <div key={action.action} className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-blue-500 rounded-full mr-3"></div>
                <span className="text-sm font-medium text-gray-900 capitalize">
                  {action.action}
                </span>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">
                  {action.count?.toLocaleString() || 0}
                </p>
                <p className="text-xs text-gray-500">{action.unique_users || 0} người dùng</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Top Movies */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Phim có nhiều tương tác nhất</h3>
        <div className="space-y-3">
          {top_movies?.slice(0, 5).map((movie, index) => (
            <div key={movie.movie__id} className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-6 h-6 bg-yellow-100 rounded-full flex items-center justify-center mr-3">
                  <span className="text-xs font-medium text-yellow-600">#{index + 1}</span>
                </div>
                <span className="text-sm font-medium text-gray-900">{movie.movie__title}</span>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">
                  {movie.total_interactions?.toLocaleString() || 0}
                </p>
                <p className="text-xs text-gray-500">{movie.unique_users || 0} người dùng</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Session Stats */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Thống kê phiên làm việc</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              {Math.round(session_stats.avg_duration_seconds / 60) || 0}m
            </p>
            <p className="text-sm text-gray-500">Thời gian trung bình</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              {Math.round(session_stats.max_duration_seconds / 60) || 0}m
            </p>
            <p className="text-sm text-gray-500">Thời gian tối đa</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              {Math.round(session_stats.min_duration_seconds / 60) || 0}m
            </p>
            <p className="text-sm text-gray-500">Thời gian tối thiểu</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserInteractionAnalytics;
