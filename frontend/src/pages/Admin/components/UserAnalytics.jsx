import { useState, useEffect } from 'react';
import { getCommunityStats } from '../../../api/movieService';

const UserAnalytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchUserAnalytics();
  }, []);

  const fetchUserAnalytics = async () => {
    try {
      setLoading(true);
      // For now, using community stats as placeholder
      // TODO: Create proper admin API endpoint for user analytics
      const response = await getCommunityStats();
      setAnalytics(response);
    } catch (err) {
      setError('Không thể tải dữ liệu phân tích người dùng');
      console.error('Error fetching user analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="mb-6 h-4 w-1/4 rounded bg-gray-200"></div>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="h-64 rounded-lg bg-gray-200"></div>
            <div className="h-64 rounded-lg bg-gray-200"></div>
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

  if (!analytics) {
    return (
      <div className="p-6">
        <p className="text-gray-500">Không có dữ liệu</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <h2 className="mb-2 text-2xl font-bold text-gray-900">Phân tích người dùng</h2>
        <p className="text-gray-600">Thống kê chi tiết về người dùng và hoạt động</p>
      </div>

      {/* Key Metrics */}
      <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-3">
        <div className="overflow-hidden rounded-lg bg-white shadow">
          <div className="p-5">
            <div className="flex items-center">
              <div className="shrink-0">
                <div className="flex size-8 items-center justify-center rounded-md bg-blue-500">
                  <span className="text-lg text-white">👥</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="truncate text-sm font-medium text-gray-500">
                    Người dùng hoạt động (30 ngày)
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {analytics.active_users_30d?.toLocaleString() || '0'}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="overflow-hidden rounded-lg bg-white shadow">
          <div className="p-5">
            <div className="flex items-center">
              <div className="shrink-0">
                <div className="flex size-8 items-center justify-center rounded-md bg-green-500">
                  <span className="text-lg text-white">📈</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="truncate text-sm font-medium text-gray-500">
                    Tổng đăng ký (30 ngày)
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {analytics.daily_signups?.reduce((sum, day) => sum + day.count, 0) || '0'}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="overflow-hidden rounded-lg bg-white shadow">
          <div className="p-5">
            <div className="flex items-center">
              <div className="shrink-0">
                <div className="flex size-8 items-center justify-center rounded-md bg-purple-500">
                  <span className="text-lg text-white">🏆</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="truncate text-sm font-medium text-gray-500">Nhóm quản trị</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {analytics.group_stats?.length || '0'}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Daily Signups Chart */}
      <div className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="overflow-hidden rounded-lg bg-white shadow">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="mb-4 text-lg font-medium leading-6 text-gray-900">
              Đăng ký hàng ngày (30 ngày gần đây)
            </h3>
            <div className="space-y-3">
              {analytics.daily_signups?.slice(-7).map((day, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-500">
                    {new Date(day.date).toLocaleDateString('vi-VN')}
                  </span>
                  <div className="flex items-center">
                    <div className="mr-3 h-2 w-20 rounded-full bg-gray-200">
                      <div
                        className="h-2 rounded-full bg-blue-600"
                        style={{ width: `${Math.min((day.count / 10) * 100, 100)}%` }}
                      ></div>
                    </div>
                    <span className="w-8 text-right text-sm font-semibold text-gray-900">
                      {day.count}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Group Distribution */}
        <div className="overflow-hidden rounded-lg bg-white shadow">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="mb-4 text-lg font-medium leading-6 text-gray-900">
              Phân bố nhóm người dùng
            </h3>
            <div className="space-y-3">
              {analytics.group_stats?.map((group, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-500">
                    {group.groups__name || 'Không có nhóm'}
                  </span>
                  <div className="flex items-center">
                    <div className="mr-3 h-2 w-20 rounded-full bg-gray-200">
                      <div
                        className="h-2 rounded-full bg-purple-600"
                        style={{ width: `${Math.min((group.count / 100) * 100, 100)}%` }}
                      ></div>
                    </div>
                    <span className="w-8 text-right text-sm font-semibold text-gray-900">
                      {group.count}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Top Active Users */}
      <div className="overflow-hidden rounded-lg bg-white shadow">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="mb-4 text-lg font-medium leading-6 text-gray-900">
            Top 10 người dùng hoạt động nhiều nhất (30 ngày)
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Thứ hạng
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Tên người dùng
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Số hoạt động
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {analytics.top_active_users?.map((user, index) => (
                  <tr key={index}>
                    <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                      #{index + 1}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">
                      {user.user__username || 'Unknown'}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      {user.activity_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {(!analytics.top_active_users || analytics.top_active_users.length === 0) && (
            <div className="py-8 text-center">
              <p className="text-gray-500">Không có dữ liệu hoạt động</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserAnalytics;
