import React, { useState, useEffect } from 'react';
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
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="bg-gray-200 h-32 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
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
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className={`w-8 h-8 rounded-md flex items-center justify-center ${color}`}>
              <span className="text-white text-lg">{icon}</span>
            </div>
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
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
              <span className="text-gray-500 ml-1">so với tháng trước</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="p-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Tổng quan hệ thống</h2>
        <p className="text-gray-600">Thống kê tổng quan về hệ thống Movie Recommendation</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
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
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Phân bố loại người dùng
            </h3>
            <div className="space-y-3">
              {stats.users?.types?.map((type, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-500 capitalize">
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

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Thống kê quản trị</h3>
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
      <div className="bg-white overflow-hidden shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Hoạt động gần đây</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
