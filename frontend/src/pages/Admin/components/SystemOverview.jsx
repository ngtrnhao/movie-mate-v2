import { useState, useEffect } from 'react';
import { getCommunityStats } from '../../../api/movieService';

const SystemOverview = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchSystemStats();
  }, []);

  const fetchSystemStats = async () => {
    try {
      setLoading(true);
      // For now, using community stats as placeholder
      // TODO: Create proper admin API endpoint for system overview
      const response = await getCommunityStats();
      setStats(response);
    } catch (err) {
      setError('Không thể tải dữ liệu hệ thống');
      console.error('Error fetching system stats:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="mb-6 h-4 w-1/4 rounded bg-gray-200"></div>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-32 rounded-lg bg-gray-200"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="rounded-md border border-red-200 bg-red-50 p-4">
          <div className="flex">
            <div className="shrink-0">
              <svg className="size-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Lỗi</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="p-6">
        <p className="text-gray-500">Không có dữ liệu</p>
      </div>
    );
  }

  const StatCard = ({ title, value, change, icon, color }) => (
    <div className="overflow-hidden rounded-lg bg-white shadow">
      <div className="p-5">
        <div className="flex items-center">
          <div className="shrink-0">
            <div className={`flex size-8 items-center justify-center rounded-md ${color}`}>
              <span className="text-lg text-white">{icon}</span>
            </div>
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="truncate text-sm font-medium text-gray-500">{title}</dt>
              <dd className="text-lg font-medium text-gray-900">{value}</dd>
            </dl>
          </div>
        </div>
        {change && (
          <div className="mt-4">
            <div className="text-sm">
              <span className={`font-medium ${change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {change > 0 ? '+' : ''}
                {change}%
              </span>
              <span className="ml-1 text-gray-500">so với tháng trước</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="p-6">
      <div className="mb-8">
        <h2 className="mb-2 text-2xl font-bold text-gray-900">Tổng quan hệ thống</h2>
        <p className="text-gray-600">Thống kê tổng quan về hệ thống Movie Recommendation</p>
      </div>

      {/* Key Metrics */}
      <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Tổng người dùng"
          value={stats.users?.total?.toLocaleString() || '0'}
          change={
            stats.users?.new_30d > 0
              ? Math.round((stats.users.new_30d / stats.users.total) * 100)
              : 0
          }
          icon="👥"
          color="bg-blue-500"
        />
        <StatCard
          title="Người dùng mới (30 ngày)"
          value={stats.users?.new_30d?.toLocaleString() || '0'}
          icon="🆕"
          color="bg-green-500"
        />
        <StatCard
          title="Tổng review"
          value={stats.content?.total_reviews?.toLocaleString() || '0'}
          change={
            stats.content?.new_reviews_30d > 0
              ? Math.round((stats.content.new_reviews_30d / stats.content.total_reviews) * 100)
              : 0
          }
          icon="📝"
          color="bg-yellow-500"
        />
        <StatCard
          title="Tổng phim"
          value={stats.content?.total_movies?.toLocaleString() || '0'}
          icon="🎬"
          color="bg-purple-500"
        />
      </div>

      {/* User Type Distribution */}
      <div className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="overflow-hidden rounded-lg bg-white shadow">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="mb-4 text-lg font-medium leading-6 text-gray-900">
              Phân bố loại người dùng
            </h3>
            <div className="space-y-3">
              {stats.users?.types?.map((type, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm font-medium capitalize text-gray-500">
                    {type.user_type?.replace('_', ' ') || 'Unknown'}
                  </span>
                  <span className="text-sm font-semibold text-gray-900">
                    {type.count?.toLocaleString() || '0'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="overflow-hidden rounded-lg bg-white shadow">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="mb-4 text-lg font-medium leading-6 text-gray-900">Thống kê quản trị</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-500">Administrators</span>
                <span className="text-sm font-semibold text-gray-900">
                  {stats.users?.admins || '0'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-500">Moderators</span>
                <span className="text-sm font-semibold text-gray-900">
                  {stats.users?.moderators || '0'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="overflow-hidden rounded-lg bg-white shadow">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="mb-4 text-lg font-medium leading-6 text-gray-900">Hoạt động gần đây</h3>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{stats.users?.new_7d || '0'}</div>
              <div className="text-sm text-gray-500">Người dùng mới (7 ngày)</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {stats.content?.new_reviews_7d || '0'}
              </div>
              <div className="text-sm text-gray-500">Review mới (7 ngày)</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {stats.content?.total_movies || '0'}
              </div>
              <div className="text-sm text-gray-500">Tổng số phim</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemOverview;
