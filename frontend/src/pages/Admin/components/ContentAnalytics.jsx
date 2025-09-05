import { useState, useEffect } from 'react';
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
        <h2 className="mb-2 text-2xl font-bold text-gray-900">Phân tích nội dung</h2>
        <p className="text-gray-600">Thống kê chi tiết về review và nội dung phim</p>
      </div>

      {/* Key Metrics */}
      <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-4">
        <div className="overflow-hidden rounded-lg bg-white shadow">
          <div className="p-5">
            <div className="flex items-center">
              <div className="shrink-0">
                <div className="flex size-8 items-center justify-center rounded-md bg-blue-500">
                  <span className="text-lg text-white">⭐</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="truncate text-sm font-medium text-gray-500">Review 5 sao</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {analytics.reviews_by_rating?.find(r => r.rating === 5)?.count || '0'}
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
                  <span className="text-lg text-white">📝</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="truncate text-sm font-medium text-gray-500">
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

        <div className="overflow-hidden rounded-lg bg-white shadow">
          <div className="p-5">
            <div className="flex items-center">
              <div className="shrink-0">
                <div className="flex size-8 items-center justify-center rounded-md bg-yellow-500">
                  <span className="text-lg text-white">🌍</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="truncate text-sm font-medium text-gray-500">Ngôn ngữ</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {analytics.language_stats?.length || '0'}
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
                  <span className="text-lg text-white">🎬</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="truncate text-sm font-medium text-gray-500">
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
      <div className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="overflow-hidden rounded-lg bg-white shadow">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="mb-4 text-lg font-medium leading-6 text-gray-900">
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
                      <span className="w-8 text-sm font-medium text-gray-500">{rating} ⭐</span>
                      <div className="ml-3 flex-1">
                        <div className="h-2 w-full rounded-full bg-gray-200">
                          <div
                            className="h-2 rounded-full bg-yellow-400"
                            style={{ width: `${percentage}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                    <span className="w-12 text-right text-sm font-semibold text-gray-900">
                      {count}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Language Distribution */}
        <div className="overflow-hidden rounded-lg bg-white shadow">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="mb-4 text-lg font-medium leading-6 text-gray-900">
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
                    <div className="mr-3 h-2 w-20 rounded-full bg-gray-200">
                      <div
                        className="h-2 rounded-full bg-blue-600"
                        style={{ width: `${Math.min((lang.count / 100) * 100, 100)}%` }}
                      ></div>
                    </div>
                    <span className="w-8 text-right text-sm font-semibold text-gray-900">
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
      <div className="mb-8 overflow-hidden rounded-lg bg-white shadow">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="mb-4 text-lg font-medium leading-6 text-gray-900">
            Review hàng ngày (30 ngày gần đây)
          </h3>
          <div className="space-y-3">
            {analytics.daily_reviews?.slice(-7).map((day, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-500">
                  {new Date(day.date).toLocaleDateString('vi-VN')}
                </span>
                <div className="flex items-center">
                  <div className="mr-3 h-2 w-32 rounded-full bg-gray-200">
                    <div
                      className="h-2 rounded-full bg-green-600"
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

      {/* Top Reviewed Movies */}
      <div className="overflow-hidden rounded-lg bg-white shadow">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="mb-4 text-lg font-medium leading-6 text-gray-900">
            Top 10 phim được review nhiều nhất
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Thứ hạng
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Tên phim
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Số review
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {analytics.top_reviewed_movies?.map((movie, index) => (
                  <tr key={index}>
                    <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                      #{index + 1}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">
                      {movie.movie__title || 'Unknown'}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      {movie.review_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {(!analytics.top_reviewed_movies || analytics.top_reviewed_movies.length === 0) && (
            <div className="py-8 text-center">
              <p className="text-gray-500">Không có dữ liệu review</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ContentAnalytics;
