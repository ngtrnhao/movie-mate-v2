import { useUserInteractionStats } from '../../../hooks/useUserInteractionStats';
import {
  EyeIcon,
  UsersIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ClockIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';

const UserInteractionAnalytics = () => {
  const { data, loading, error, refetch } = useUserInteractionStats();

  if (loading) {
    return (
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <div className="animate-pulse">
          <div className="mb-4 h-4 w-1/4 rounded bg-gray-200"></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-20 rounded bg-gray-200"></div>
            <div className="h-20 rounded bg-gray-200"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <div className="text-center">
          <p className="mb-4 text-red-600">{error}</p>
          <button
            onClick={refetch}
            className="rounded bg-blue-500 px-4 py-2 text-white hover:bg-blue-600"
          >
            Thử lại
          </button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <p className="text-center text-gray-500">Không có dữ liệu</p>
      </div>
    );
  }

  const { overview, action_breakdown, top_movies, session_stats, trends } = data;

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-medium text-gray-900">Tổng quan tương tác người dùng</h3>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <div className="text-center">
            <div className="mx-auto mb-2 flex size-10 items-center justify-center rounded-full bg-blue-100">
              <ChartBarIcon className="size-5 text-blue-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {overview.total_interactions?.toLocaleString() || 0}
            </p>
            <p className="text-sm text-gray-500">Tổng tương tác</p>
          </div>
          <div className="text-center">
            <div className="mx-auto mb-2 flex size-10 items-center justify-center rounded-full bg-green-100">
              <UsersIcon className="size-5 text-green-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {overview.total_users?.toLocaleString() || 0}
            </p>
            <p className="text-sm text-gray-500">Người dùng</p>
          </div>
          <div className="text-center">
            <div className="mx-auto mb-2 flex size-10 items-center justify-center rounded-full bg-purple-100">
              <EyeIcon className="size-5 text-purple-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {overview.total_sessions?.toLocaleString() || 0}
            </p>
            <p className="text-sm text-gray-500">Phiên làm việc</p>
          </div>
          <div className="text-center">
            <div className="mx-auto mb-2 flex size-10 items-center justify-center rounded-full bg-orange-100">
              <ClockIcon className="size-5 text-orange-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {overview.avg_interactions_per_user || 0}
            </p>
            <p className="text-sm text-gray-500">Tương tác/người dùng</p>
          </div>
        </div>
      </div>

      {/* Time-based Stats */}
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-medium text-gray-900">Thống kê theo thời gian</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              {overview.today_interactions?.toLocaleString() || 0}
            </p>
            <p className="text-sm text-gray-500">Hôm nay</p>
            <div className="mt-1 flex items-center justify-center">
              {trends.daily_growth > 0 ? (
                <ArrowTrendingUpIcon className="mr-1 size-4 text-green-500" />
              ) : (
                <ArrowTrendingDownIcon className="mr-1 size-4 text-red-500" />
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
            <div className="mt-1 flex items-center justify-center">
              {trends.weekly_growth > 0 ? (
                <ArrowTrendingUpIcon className="mr-1 size-4 text-green-500" />
              ) : (
                <ArrowTrendingDownIcon className="mr-1 size-4 text-red-500" />
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
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-medium text-gray-900">Phân tích hành động</h3>
        <div className="space-y-3">
          {action_breakdown?.slice(0, 5).map((action, index) => (
            <div key={action.action} className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="mr-3 size-3 rounded-full bg-blue-500"></div>
                <span className="text-sm font-medium capitalize text-gray-900">
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
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-medium text-gray-900">Phim có nhiều tương tác nhất</h3>
        <div className="space-y-3">
          {top_movies?.slice(0, 5).map((movie, index) => (
            <div key={movie.movie__id} className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="mr-3 flex size-6 items-center justify-center rounded-full bg-yellow-100">
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
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-medium text-gray-900">Thống kê phiên làm việc</h3>
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
