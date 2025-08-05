import { useState, useEffect, useCallback } from 'react';
import { debounce } from 'lodash';
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Eye,
  Shield,
  RefreshCw,
  Star,
  MessageSquare,
  User,
  TrendingDown,
} from 'lucide-react';
import {
  getModerationQueue,
  moderateReview,
  bulkModerateReviews,
  detectSpoilers,
  analyzeReviewSpoiler,
  getModerationQueueOptimized,
  getUltraOptimizedModerationQueue,
} from '../../../api/movieService';
import moderationCacheService from '../../../services/moderationCacheService';
import SpoilerDetectionPanel from './SpoilerDetectionPanel';

const ContentModerationDashboard = () => {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedReviews, setSelectedReviews] = useState([]);
  const [selectedReview, setSelectedReview] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [spoilerResult, setSpoilerResult] = useState(null);
  const [analyzingSpoiler, setAnalyzingSpoiler] = useState(false);
  const [filters, setFilters] = useState({
    priority: 'all',
    language: '',
    date_from: '',
    date_to: '',
  });

  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [notification, setNotification] = useState(null);
  // Add state for API stats
  const [apiStats, setApiStats] = useState({
    count: 0,
    priority_stats: { high: 0, medium: 0, low: 0 },
    type_stats: { reported: 0, spoiler: 0, total: 0 },
  });
  // Removed viewMode state - only list view is supported

  // Optimized fetch function with caching
  const fetchModerationQueue = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Use cache service for ultra-optimized API (handles 400k+ reviews)
      const response = await moderationCacheService.cachedApiCall(
        'ultra_optimized_moderation_queue',
        async () => await getUltraOptimizedModerationQueue(currentPage, 20, filters),
        { page: currentPage, pageSize: 20, ...filters }
      );

      // API returns { results: [...], count: ..., page_info: {...} }
      setReviews(response.results || []);
      setTotalPages(response.page_info?.total_pages || 1);

      // Update API stats from response
      setApiStats({
        count: response.count || 0,
        priority_stats: response.priority_stats || { high: 0, medium: 0, low: 0 },
        type_stats: response.type_stats || { reported: 0, spoiler: 0, total: 0 },
      });

      console.log('✅ Optimized moderation queue loaded:', {
        count: response.results?.length || 0,
        performance: response.performance_info,
        fromCache: response.__fromCache || false,
      });
    } catch (err) {
      console.error('Error fetching moderation queue:', err);
      setError('Không thể tải hàng đợi kiểm duyệt');

      // Fallback to original API if optimized fails
      try {
        console.log('⚠️ Falling back to original API...');
        const fallbackResponse = await getModerationQueue(currentPage, 20, filters);
        setReviews(fallbackResponse.results || fallbackResponse.data || []);
        setTotalPages(fallbackResponse.page_info?.total_pages || fallbackResponse.total_pages || 1);

        // For fallback, calculate stats from current page data (not ideal but better than nothing)
        const fallbackData = fallbackResponse.results || fallbackResponse.data || [];
        const priorityCounts = {
          high:
            fallbackData.filter(r => r.moderation_analysis?.priority_level === 'high').length || 0,
          medium:
            fallbackData.filter(r => r.moderation_analysis?.priority_level === 'medium').length ||
            0,
          low:
            fallbackData.filter(r => r.moderation_analysis?.priority_level === 'low').length || 0,
        };
        setApiStats({
          count: fallbackData.length || 0,
          priority_stats: priorityCounts,
          type_stats: { reported: 0, spoiler: 0, total: fallbackData.length || 0 },
        });
      } catch (fallbackErr) {
        console.error('Fallback also failed:', fallbackErr);
      }
    } finally {
      setLoading(false);
    }
  }, [currentPage, filters]);

  // Debounced fetch to prevent rapid API calls
  const debouncedFetch = useCallback(
    debounce(() => {
      fetchModerationQueue();
    }, 300), // 300ms debounce
    [fetchModerationQueue]
  );

  // Separate useEffects to prevent unnecessary calls
  useEffect(() => {
    debouncedFetch();
    return () => debouncedFetch.cancel(); // Cleanup on unmount
  }, [debouncedFetch]);

  const handleModerationAction = async (reviewId, action, reason = '') => {
    try {
      console.log(`Moderating review ${reviewId} with action: ${action}`);
      const result = await moderateReview(reviewId, action, reason);
      console.log('Moderation result:', result);

      // Update local state
      setReviews(prevReviews => prevReviews.filter(review => review.id !== reviewId));
      setSelectedReview(null);
      setShowModal(false);

      // Invalidate cache and refresh moderation queue
      moderationCacheService.invalidateCache('ultra_optimized_moderation_queue');
      await fetchModerationQueue();

      // Show success notification
      setNotification({
        type: 'success',
        message: `Đã ${action === 'approve' ? 'phê duyệt' : 'từ chối'} review thành công!`,
      });

      // Clear notification after 3 seconds
      setTimeout(() => setNotification(null), 3000);

      return {
        success: true,
        message: `Đã ${action === 'approve' ? 'phê duyệt' : 'từ chối'} review thành công!`,
      };
    } catch (err) {
      console.error('Error performing moderation action:', err);
      setNotification({
        type: 'error',
        message: 'Có lỗi xảy ra khi thực hiện hành động kiểm duyệt',
      });
      setTimeout(() => setNotification(null), 3000);
      return { success: false, message: 'Có lỗi xảy ra khi thực hiện hành động kiểm duyệt' };
    }
  };

  const handleBulkModeration = async (action, reason = '') => {
    if (selectedReviews.length === 0) {
      alert('Vui lòng chọn ít nhất một review để thực hiện hành động');
      return;
    }

    try {
      await bulkModerateReviews(selectedReviews, action, reason);

      // Clear selection, invalidate cache and refresh
      setSelectedReviews([]);
      moderationCacheService.invalidateCache('moderation_queue_optimized');
      await fetchModerationQueue();

      alert(
        `Đã ${action === 'approve' ? 'phê duyệt' : 'từ chối'} ${selectedReviews.length} reviews thành công!`
      );
    } catch (err) {
      console.error('Error performing bulk moderation:', err);
      alert('Có lỗi xảy ra khi thực hiện hành động kiểm duyệt hàng loạt');
    }
  };

  const handleAnalyzeSpoiler = async review => {
    setAnalyzingSpoiler(true);
    setSelectedReview(review);

    try {
      // First try to analyze existing review
      const result = await analyzeReviewSpoiler(review.id);
      setSpoilerResult(result.detection_result);
    } catch (err) {
      console.error('Error analyzing spoiler:', err);
      // Fallback to direct spoiler detection
      try {
        const result = await detectSpoilers(
          review.content,
          review.language || 'en',
          review.movie?.title || ''
        );
        setSpoilerResult(result);
      } catch (detectionErr) {
        console.error('Error in spoiler detection:', detectionErr);
        setSpoilerResult({
          is_spoiler: false,
          confidence: 0,
          explanation: 'Không thể phân tích spoiler',
        });
      }
    } finally {
      setAnalyzingSpoiler(false);
      setShowModal(true);
    }
  };

  const getConfidenceColor = confidence => {
    if (confidence > 0.8) return 'text-red-600 bg-red-50';
    if (confidence > 0.6) return 'text-orange-600 bg-orange-50';
    if (confidence > 0.4) return 'text-yellow-600 bg-yellow-50';
    return 'text-green-600 bg-green-50';
  };

  const getConfidenceIcon = confidence => {
    if (confidence > 0.8) return <AlertTriangle className="size-4" />;
    if (confidence > 0.6) return <AlertTriangle className="size-4" />;
    if (confidence > 0.4) return <AlertTriangle className="size-4" />;
    return <CheckCircle className="size-4" />;
  };

  const handleSelectReview = reviewId => {
    setSelectedReviews(prev =>
      prev.includes(reviewId) ? prev.filter(id => id !== reviewId) : [...prev, reviewId]
    );
  };

  const handleSelectAll = () => {
    if (selectedReviews.length === reviews.length) {
      setSelectedReviews([]);
    } else {
      setSelectedReviews(reviews.map(review => review.id));
    }
  };

  // Remove the local priority calculation since we now use apiStats
  // const priorityCounts = {
  //   high: reviews.filter(r => r.moderation_analysis?.priority_level === 'high').length,
  //   medium: reviews.filter(r => r.moderation_analysis?.priority_level === 'medium').length,
  //   low: reviews.filter(r => r.moderation_analysis?.priority_level === 'low').length,
  // };

  if (loading && reviews.length === 0) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="mb-6 h-4 w-1/4 rounded bg-gray-200"></div>
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-32 rounded-lg bg-gray-200"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Notification */}
      {notification && (
        <div
          className={`fixed right-4 top-4 z-50 rounded-md p-4 shadow-lg ${
            notification.type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
          }`}
        >
          <div className="flex items-center">
            {notification.type === 'success' ? (
              <CheckCircle className="mr-2 size-5" />
            ) : (
              <XCircle className="mr-2 size-5" />
            )}
            <span>{notification.message}</span>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="mb-2 text-2xl font-bold text-gray-900">Kiểm duyệt nội dung</h2>
            <p className="text-gray-600">Quản lý và kiểm duyệt reviews với spoiler detection</p>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => {
                moderationCacheService.invalidateCache('moderation_queue_optimized');
                fetchModerationQueue();
              }}
              className="flex items-center space-x-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              <RefreshCw className="size-4" />
              <span>Làm mới</span>
            </button>
          </div>
        </div>
      </div>

      {/* Priority Statistics */}
      <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
        <div className="rounded-lg bg-white p-4 shadow">
          <div className="flex items-center">
            <div className="rounded-full bg-blue-100 p-3">
              <Shield className="size-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Tổng cần kiểm duyệt</p>
              <p className="text-2xl font-bold text-gray-900">{apiStats.count}</p>
            </div>
          </div>
        </div>

        <div className="rounded-lg bg-white p-4 shadow">
          <div className="flex items-center">
            <div className="rounded-full bg-red-100 p-3">
              <AlertTriangle className="size-6 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-red-600">Ưu tiên cao</p>
              <p className="text-2xl font-bold text-red-900">{apiStats.priority_stats.high}</p>
            </div>
          </div>
        </div>

        <div className="rounded-lg bg-white p-4 shadow">
          <div className="flex items-center">
            <div className="rounded-full bg-orange-100 p-3">
              <TrendingDown className="size-6 text-orange-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-orange-600">Ưu tiên trung bình</p>
              <p className="text-2xl font-bold text-orange-900">{apiStats.priority_stats.medium}</p>
            </div>
          </div>
        </div>

        <div className="rounded-lg bg-white p-4 shadow">
          <div className="flex items-center">
            <div className="rounded-full bg-green-100 p-3">
              <CheckCircle className="size-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-green-600">Ưu tiên thấp</p>
              <p className="text-2xl font-bold text-green-900">{apiStats.priority_stats.low}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Spoiler Detection Statistics - Using dedicated component */}
      <div className="mb-6">
        <SpoilerDetectionPanel />
      </div>

      {/* Filters */}
      <div className="mb-6 rounded-lg bg-white shadow">
        <div className="border-b border-gray-200 p-4">
          <h3 className="text-lg font-medium text-blue-900">Bộ lọc</h3>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-blue-700">Mức độ ưu tiên</label>
              <select
                value={filters.priority}
                onChange={e => setFilters(prev => ({ ...prev, priority: e.target.value }))}
                className="block w-full rounded-md border-gray-300 bg-white text-gray-900 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="all" className="text-gray-900">
                  Tất cả ưu tiên
                </option>
                <option value="high" className="text-red-700">
                  Ưu tiên cao (Spoiler đã đánh dấu)
                </option>
                <option value="medium" className="text-orange-700">
                  Ưu tiên trung bình (Cần kiểm tra)
                </option>
                <option value="low" className="text-green-700">
                  Ưu tiên thấp (Từ khóa nghi ngờ)
                </option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-blue-700">Ngôn ngữ</label>
              <select
                value={filters.language}
                onChange={e => setFilters(prev => ({ ...prev, language: e.target.value }))}
                className="block w-full rounded-md border-gray-300 bg-white text-gray-900 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="" className="text-gray-900">
                  Tất cả ngôn ngữ
                </option>
                <option value="vi" className="text-blue-700">
                  Tiếng Việt
                </option>
                <option value="en" className="text-purple-700">
                  Tiếng Anh
                </option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-blue-700">Từ ngày</label>
              <input
                type="date"
                value={filters.date_from}
                onChange={e => setFilters(prev => ({ ...prev, date_from: e.target.value }))}
                className="block w-full rounded-md border-gray-300 bg-white text-gray-900 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                placeholder="Từ ngày"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-blue-700">Đến ngày</label>
              <input
                type="date"
                value={filters.date_to}
                onChange={e => setFilters(prev => ({ ...prev, date_to: e.target.value }))}
                className="block w-full rounded-md border-gray-300 bg-white text-gray-900 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                placeholder="Đến ngày"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedReviews.length > 0 && (
        <div className="mb-6 rounded-lg border border-blue-200 bg-blue-50 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-blue-900">
                Đã chọn {selectedReviews.length} reviews
              </span>
              <button
                onClick={handleSelectAll}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                {selectedReviews.length === reviews.length ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}
              </button>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => handleBulkModeration('approve')}
                className="flex items-center space-x-1 rounded-md bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700"
              >
                <CheckCircle className="size-4" />
                <span>Phê duyệt ({selectedReviews.length})</span>
              </button>
              <button
                onClick={() => handleBulkModeration('reject')}
                className="flex items-center space-x-1 rounded-md bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-700"
              >
                <XCircle className="size-4" />
                <span>Từ chối ({selectedReviews.length})</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 p-4">
          <div className="flex">
            <div className="shrink-0">
              <XCircle className="size-5 text-red-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Lỗi</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      ) : reviews.length === 0 ? (
        <div className="py-12 text-center">
          <div className="mx-auto size-12 text-gray-400">
            <Shield className="size-12" />
          </div>
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            Không có review nào chờ kiểm duyệt
          </h3>
          <p className="mt-1 text-sm text-gray-500">Tất cả review đã được xử lý.</p>
        </div>
      ) : (
        // List View
        <div className="space-y-4">
          {reviews.map(review => (
            <div key={review.id} className="rounded-lg border border-gray-200 bg-white p-6">
              <div className="flex items-start space-x-4">
                {/* Checkbox */}
                <input
                  type="checkbox"
                  checked={selectedReviews.includes(review.id)}
                  onChange={() => handleSelectReview(review.id)}
                  className="mt-1 size-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />

                {/* Review Content */}
                <div className="flex-1">
                  <div className="mb-4 flex items-center space-x-3">
                    <img
                      className="size-10 rounded-full"
                      src={review.user?.avatar_url || '/images/avatar_default.jpg'}
                      alt=""
                    />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {review.user?.username || 'Unknown User'}
                      </p>
                      <p className="text-sm text-gray-500">
                        {new Date(review.created_at).toLocaleDateString('vi-VN')}
                      </p>
                    </div>
                    {review.rating && (
                      <div className="flex items-center">
                        <span className="mr-1 text-sm text-gray-500">Rating:</span>
                        <div className="flex items-center">
                          {[...Array(5)].map((_, i) => (
                            <Star
                              key={i}
                              className={`size-4 ${
                                i < review.rating ? 'fill-current text-yellow-400' : 'text-gray-300'
                              }`}
                            />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="mb-4">
                    <h3 className="mb-2 text-lg font-medium text-gray-900">
                      {review.title || `Review cho ${review.movie?.title}`}
                    </h3>
                    <p className="whitespace-pre-wrap text-gray-700">
                      {review.content.length > 300
                        ? `${review.content.substring(0, 300)}...`
                        : review.content}
                    </p>
                  </div>

                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <span className="flex items-center">
                      <MessageSquare className="mr-1 size-4" />
                      Phim: {review.movie?.title}
                    </span>
                    <span className="flex items-center">
                      <User className="mr-1 size-4" />
                      Ngôn ngữ: {review.language}
                    </span>
                    {review.moderation_analysis && (
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          review.moderation_analysis.priority_level === 'high'
                            ? 'bg-red-100 text-red-800'
                            : review.moderation_analysis.priority_level === 'medium'
                              ? 'bg-orange-100 text-orange-800'
                              : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        <AlertTriangle className="mr-1 size-3" />
                        {review.moderation_analysis.priority_level === 'high'
                          ? 'Ưu tiên cao'
                          : review.moderation_analysis.priority_level === 'medium'
                            ? 'Ưu tiên TB'
                            : 'Ưu tiên thấp'}
                        (
                        {review.moderation_analysis.spoiler_analysis
                          ? Math.round(review.moderation_analysis.spoiler_analysis.confidence * 100)
                          : review.moderation_analysis.priority_level === 'high'
                            ? 'Cao'
                            : review.moderation_analysis.priority_level === 'medium'
                              ? 'TB'
                              : 'Thấp'}
                        %)
                      </span>
                    )}
                    {review.is_spoiler && (
                      <span className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800">
                        <AlertTriangle className="mr-1 size-3" />
                        Đã đánh dấu Spoiler
                      </span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex flex-col space-y-2">
                  <button
                    onClick={() => handleAnalyzeSpoiler(review)}
                    className="inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium leading-4 text-gray-700 hover:bg-gray-50"
                  >
                    {analyzingSpoiler && selectedReview?.id === review.id ? (
                      <RefreshCw className="mr-1 size-4 animate-spin" />
                    ) : (
                      <Eye className="mr-1 size-4" />
                    )}
                    Phân tích Spoiler
                  </button>
                  <button
                    onClick={() => handleModerationAction(review.id, 'approve')}
                    className="inline-flex items-center rounded-md border border-transparent bg-green-600 px-3 py-2 text-sm font-medium leading-4 text-white hover:bg-green-700"
                  >
                    <CheckCircle className="mr-1 size-4" />
                    Phê duyệt
                  </button>
                  <button
                    onClick={() => handleModerationAction(review.id, 'reject')}
                    className="inline-flex items-center rounded-md border border-transparent bg-red-600 px-3 py-2 text-sm font-medium leading-4 text-white hover:bg-red-700"
                  >
                    <XCircle className="mr-1 size-4" />
                    Từ chối
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
            >
              Trước
            </button>
            <span className="text-sm text-gray-700">
              Trang {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
            >
              Sau
            </button>
          </div>
        </div>
      )}

      {/* Spoiler Analysis Modal */}
      {showModal && selectedReview && (
        <div className="fixed inset-0 z-50 size-full overflow-y-auto bg-gray-600 bg-opacity-50">
          <div className="relative top-20 mx-auto w-11/12 rounded-md border bg-white p-5 shadow-lg md:w-3/4 lg:w-1/2">
            <div className="mt-3">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">
                  Phân tích Spoiler - {selectedReview.movie?.title}
                </h3>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="size-6" />
                </button>
              </div>

              {(spoilerResult || selectedReview?.moderation_analysis?.spoiler_analysis) && (
                <div className="space-y-4">
                  {/* Spoiler Detection Result */}
                  <div
                    className={`rounded-lg border p-4 ${
                      spoilerResult?.is_spoiler ||
                      selectedReview?.moderation_analysis?.spoiler_analysis?.is_spoiler
                        ? 'border-red-200 bg-red-50'
                        : 'border-green-200 bg-green-50'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      {getConfidenceIcon(
                        spoilerResult?.confidence ||
                          selectedReview?.moderation_analysis?.spoiler_analysis?.confidence
                      )}
                      <span
                        className={`font-medium ${
                          spoilerResult?.is_spoiler ||
                          selectedReview?.moderation_analysis?.spoiler_analysis?.is_spoiler
                            ? 'text-red-800'
                            : 'text-green-800'
                        }`}
                      >
                        {spoilerResult?.is_spoiler ||
                        selectedReview?.moderation_analysis?.spoiler_analysis?.is_spoiler
                          ? 'Có phát hiện spoiler'
                          : 'Không có spoiler'}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-gray-600">
                      Độ tin cậy:{' '}
                      {(
                        (spoilerResult?.confidence ||
                          selectedReview?.moderation_analysis?.spoiler_analysis?.confidence) * 100
                      ).toFixed(1)}
                      %
                    </p>
                  </div>

                  {/* Explanation */}
                  {spoilerResult.explanation && (
                    <div className="rounded-lg bg-gray-50 p-4">
                      <h4 className="mb-2 text-sm font-medium text-gray-900">Giải thích</h4>
                      <p className="text-sm text-gray-700">{spoilerResult.explanation}</p>
                    </div>
                  )}

                  {/* Detected Patterns */}
                  {spoilerResult.detected_patterns &&
                    spoilerResult.detected_patterns.length > 0 && (
                      <div className="rounded-lg bg-yellow-50 p-4">
                        <h4 className="mb-2 text-sm font-medium text-yellow-900">Mẫu phát hiện</h4>
                        <div className="space-y-1">
                          {spoilerResult.detected_patterns.map((pattern, index) => (
                            <div key={index} className="text-sm text-yellow-800">
                              • {pattern}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                  {/* Spoiler Indicators */}
                  {spoilerResult.spoiler_indicators &&
                    spoilerResult.spoiler_indicators.length > 0 && (
                      <div className="rounded-lg bg-orange-50 p-4">
                        <h4 className="mb-2 text-sm font-medium text-orange-900">
                          Chỉ báo spoiler
                        </h4>
                        <div className="space-y-1">
                          {spoilerResult.spoiler_indicators.map((indicator, index) => (
                            <div key={index} className="text-sm text-orange-800">
                              • {indicator}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                  {/* Suggested Action */}
                  {spoilerResult.suggested_action && (
                    <div className="rounded-lg bg-blue-50 p-4">
                      <h4 className="mb-2 text-sm font-medium text-blue-900">Hành động đề xuất</h4>
                      <p className="text-sm text-blue-800">{spoilerResult.suggested_action}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Action Buttons */}
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setShowModal(false)}
                  className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Đóng
                </button>
                <button
                  onClick={() => {
                    handleModerationAction(selectedReview.id, 'approve');
                    setShowModal(false);
                  }}
                  className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
                >
                  Phê duyệt
                </button>
                <button
                  onClick={() => {
                    handleModerationAction(selectedReview.id, 'reject');
                    setShowModal(false);
                  }}
                  className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
                >
                  Từ chối
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ContentModerationDashboard;
