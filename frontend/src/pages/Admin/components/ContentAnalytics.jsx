import React, { useState, useEffect } from 'react';
import { getCommunityStats } from '../../../api/movieService';

const ContentAnalytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchContentAnalytics();
  }, []);

  const fetchContentAnalytics = async () => {
    try {
      setLoading(true);
      // For now, using community stats as placeholder
      // TODO: Create proper admin API endpoint for content analytics
      const response = await getCommunityStats();
      setAnalytics(response);
    } catch (err) {
      setError('Không thể tải dữ liệu phân tích nội dung');
      console.error('Error fetching content analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-gray-200 h-64 rounded-lg"></div>
            <div className="bg-gray-200 h-64 rounded-lg"></div>
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
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Phân tích nội dung</h2>
        <p className="text-gray-600">Thống kê chi tiết về review và nội dung phim</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 rounded-md flex items-center justify-center bg-blue-500">
                  <span className="text-white text-lg">⭐</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Review 5 sao</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {analytics.reviews_by_rating?.find(r => r.rating === 5)?.count || '0'}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 rounded-md flex items-center justify-center bg-green-500">
                  <span className="text-white text-lg">📝</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Review mới (30 ngày)
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {analytics.daily_reviews?.reduce((sum, day) => sum + day.count, 0) || '0'}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 rounded-md flex items-center justify-center bg-yellow-500">
                  <span className="text-white text-lg">🌍</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Ngôn ngữ</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {analytics.language_stats?.length || '0'}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 rounded-md flex items-center justify-center bg-purple-500">
                  <span className="text-white text-lg">🎬</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Phim được review nhiều
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {analytics.top_reviewed_movies?.length || '0'}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Reviews by Rating */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Phân bố đánh giá sao
            </h3>
            <div className="space-y-3">
              {[5, 4, 3, 2, 1].map(rating => {
                const ratingData = analytics.reviews_by_rating?.find(r => r.rating === rating);
                const count = ratingData?.count || 0;
                const total =
                  analytics.reviews_by_rating?.reduce((sum, r) => sum + r.count, 0) || 1;
                const percentage = Math.round((count / total) * 100);

                return (
                  <div key={rating} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <span className="text-sm font-medium text-gray-500 w-8">{rating} ⭐</span>
                      <div className="ml-3 flex-1">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-yellow-400 h-2 rounded-full"
                            style={{ width: `${percentage}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                    <span className="text-sm font-semibold text-gray-900 w-12 text-right">
                      {count}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Language Distribution */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Phân bố ngôn ngữ review
            </h3>
            <div className="space-y-3">
              {analytics.language_stats?.slice(0, 5).map((lang, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-500">
                    {lang.language === 'en'
                      ? 'English'
                      : lang.language === 'vi'
                        ? 'Tiếng Việt'
                        : lang.language.toUpperCase()}
                  </span>
                  <div className="flex items-center">
                    <div className="w-20 bg-gray-200 rounded-full h-2 mr-3">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${Math.min((lang.count / 100) * 100, 100)}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-semibold text-gray-900 w-8 text-right">
                      {lang.count}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Daily Reviews Chart */}
      <div className="bg-white overflow-hidden shadow rounded-lg mb-8">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Review hàng ngày (30 ngày gần đây)
          </h3>
          <div className="space-y-3">
            {analytics.daily_reviews?.slice(-7).map((day, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-500">
                  {new Date(day.date).toLocaleDateString('vi-VN')}
                </span>
                <div className="flex items-center">
                  <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                    <div
                      className="bg-green-600 h-2 rounded-full"
                      style={{ width: `${Math.min((day.count / 10) * 100, 100)}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-semibold text-gray-900 w-8 text-right">
                    {day.count}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Reviewed Movies */}
      <div className="bg-white overflow-hidden shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Top 10 phim được review nhiều nhất
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Thứ hạng
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tên phim
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Số review
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {analytics.top_reviewed_movies?.map((movie, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      #{index + 1}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {movie.movie__title || 'Unknown'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {movie.review_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {(!analytics.top_reviewed_movies || analytics.top_reviewed_movies.length === 0) && (
            <div className="text-center py-8">
              <p className="text-gray-500">Không có dữ liệu review</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ContentAnalytics;
