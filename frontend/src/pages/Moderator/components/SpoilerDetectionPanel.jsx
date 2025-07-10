import { useState, useEffect, useCallback } from 'react';
import {
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  XCircle,
  RefreshCw,
} from 'lucide-react';
import {
  getSpoilerStatistics,
  getSpoilerStatisticsOptimized,
  analyzeReviewSpoiler,
} from '../../../api/movieService';
import moderationCacheService from '../../../services/moderationCacheService';

const SpoilerDetectionPanel = () => {
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [analyzingReview, setAnalyzingReview] = useState(null);

  // Optimized fetch function with caching
  const fetchStatistics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Use cache service for optimized spoiler statistics API
      const data = await moderationCacheService.cachedApiCall(
        'spoiler_statistics_optimized',
        async () => await getSpoilerStatisticsOptimized(),
        { days: 30 } // Default 30 days parameter
      );

      setStatistics(data);

      console.log('✅ Spoiler statistics loaded:', {
        total_reviews: data.statistics?.total_reviews || 0,
        fromCache: data.__fromCache || false,
      });
    } catch (err) {
      console.error('Error with optimized API, trying fallback:', err);
      try {
        // Fallback to original API
        const fallbackData = await getSpoilerStatistics();
        setStatistics(fallbackData);
      } catch (fallbackErr) {
        console.error('Error with both APIs:', fallbackErr);
        setError('Không thể tải thống kê spoiler detection');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatistics();
  }, [fetchStatistics]);

  const handleAnalyzeReview = async reviewId => {
    setAnalyzingReview(reviewId);
    try {
      const result = await analyzeReviewSpoiler(reviewId);
      // Invalidate cache and refresh statistics after analysis
      moderationCacheService.invalidateCache('spoiler_statistics_optimized');
      await fetchStatistics();
      return result;
    } catch (err) {
      console.error('Error analyzing review:', err);
      throw err;
    } finally {
      setAnalyzingReview(null);
    }
  };

  const getConfidenceColor = confidence => {
    if (confidence > 0.8) return 'text-red-600';
    if (confidence > 0.6) return 'text-orange-600';
    if (confidence > 0.4) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getConfidenceIcon = confidence => {
    if (confidence > 0.8) return <AlertTriangle className="size-4 text-red-600" />;
    if (confidence > 0.6) return <AlertTriangle className="size-4 text-orange-600" />;
    if (confidence > 0.4) return <AlertTriangle className="size-4 text-yellow-600" />;
    return <CheckCircle className="size-4 text-green-600" />;
  };

  if (loading) {
    return (
      <div className="rounded-lg bg-white p-6 shadow">
        <div className="flex items-center justify-center space-x-2">
          <RefreshCw className="size-5 animate-spin text-blue-600" />
          <span className="text-gray-600">Đang tải thống kê spoiler detection...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-white p-6 shadow">
        <div className="flex items-center space-x-2 text-red-600">
          <XCircle className="size-5" />
          <span>{error}</span>
        </div>
        <button
          onClick={() => {
            moderationCacheService.invalidateCache('spoiler_statistics_optimized');
            fetchStatistics();
          }}
          className="mt-2 text-sm text-blue-600 hover:text-blue-800"
        >
          Thử lại
        </button>
      </div>
    );
  }

  if (!statistics) {
    return (
      <div className="rounded-lg bg-white p-6 shadow">
        <p className="text-gray-600">Không có dữ liệu thống kê</p>
      </div>
    );
  }

  const { statistics: stats, total_reviews_analyzed } = statistics;

  return (
    <div className="rounded-lg bg-white shadow">
      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Spoiler Detection Analytics</h3>
            <p className="text-sm text-gray-500">Thống kê phát hiện spoiler trong reviews</p>
          </div>
          <button
            onClick={() => {
              moderationCacheService.invalidateCache('spoiler_statistics_optimized');
              fetchStatistics();
            }}
            className="flex items-center space-x-2 rounded-md bg-blue-50 px-3 py-2 text-sm font-medium text-blue-700 hover:bg-blue-100"
          >
            <RefreshCw className="size-4" />
            <span>Làm mới</span>
          </button>
        </div>
      </div>

      {/* Statistics Grid */}
      <div className="p-6">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
          {/* Total Reviews */}
          <div className="rounded-lg bg-gray-50 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Tổng Reviews</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats.total_reviews?.toLocaleString() || 0}
                </p>
              </div>
              <div className="rounded-full bg-blue-100 p-3">
                <TrendingUp className="size-6 text-blue-600" />
              </div>
            </div>
          </div>

          {/* Spoiler Count */}
          <div className="rounded-lg bg-red-50 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-red-600">Reviews có Spoiler</p>
                <p className="text-2xl font-bold text-red-900">
                  {stats.spoiler_count?.toLocaleString() || 0}
                </p>
              </div>
              <div className="rounded-full bg-red-100 p-3">
                <AlertTriangle className="size-6 text-red-600" />
              </div>
            </div>
          </div>

          {/* Spoiler Percentage */}
          <div className="rounded-lg bg-orange-50 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-600">Tỷ lệ Spoiler</p>
                <p className="text-2xl font-bold text-orange-900">
                  {stats.spoiler_percentage?.toFixed(1) || 0}%
                </p>
              </div>
              <div className="rounded-full bg-orange-100 p-3">
                <TrendingDown className="size-6 text-orange-600" />
              </div>
            </div>
          </div>

          {/* Average Confidence */}
          <div className="rounded-lg bg-green-50 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600">Độ tin cậy TB</p>
                <p className="text-2xl font-bold text-green-900">
                  {(stats.average_confidence * 100)?.toFixed(1) || 0}%
                </p>
              </div>
              <div className="rounded-full bg-green-100 p-3">
                <CheckCircle className="size-6 text-green-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Detection Patterns */}
        {stats.detection_patterns && Object.keys(stats.detection_patterns).length > 0 && (
          <div className="mt-6">
            <h4 className="text-md mb-3 font-medium text-gray-900">Mẫu phát hiện phổ biến</h4>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
              {Object.entries(stats.detection_patterns)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 6)
                .map(([pattern, count]) => (
                  <div key={pattern} className="rounded-lg bg-gray-50 p-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium capitalize text-gray-700">
                        {pattern.replace(/_/g, ' ')}
                      </span>
                      <span className="text-sm text-gray-500">{count} lần</span>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Recent Activity */}
        <div className="mt-6">
          <h4 className="text-md mb-3 font-medium text-gray-900">Hoạt động gần đây</h4>
          <div className="rounded-lg bg-gray-50 p-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Reviews đã phân tích:</span>
                <span className="font-medium text-gray-900">
                  {total_reviews_analyzed?.toLocaleString() || 0}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Tự động đánh dấu spoiler:</span>
                <span className="font-medium text-green-600">
                  {stats.spoiler_count || 0} reviews
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Cần kiểm tra thủ công:</span>
                <span className="font-medium text-orange-600">
                  {Math.round((stats.total_reviews - stats.spoiler_count) * 0.1) || 0} reviews
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-6">
          <h4 className="text-md mb-3 font-medium text-gray-900">Hành động nhanh</h4>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={fetchStatistics}
              className="flex items-center space-x-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              <RefreshCw className="size-4" />
              <span>Cập nhật thống kê</span>
            </button>
            <button className="flex items-center space-x-2 rounded-md bg-orange-600 px-4 py-2 text-sm font-medium text-white hover:bg-orange-700">
              <AlertTriangle className="size-4" />
              <span>Kiểm tra reviews mới</span>
            </button>
            <button className="flex items-center space-x-2 rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700">
              <CheckCircle className="size-4" />
              <span>Xem báo cáo chi tiết</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SpoilerDetectionPanel;
