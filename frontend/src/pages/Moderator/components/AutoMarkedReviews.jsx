import { useState, useEffect, useCallback } from 'react';
import {
  getAutoMarkedReviews,
  submitModerationFeedback,
  getModerationAnalytics,
} from '../../../api/movieService';
import {
  BoltIcon,
  FunnelIcon,
  ChartBarIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  EyeIcon,
  UserIcon,
  CalendarDaysIcon,
  AdjustmentsHorizontalIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

const AutoMarkedReviews = () => {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [analytics, setAnalytics] = useState(null);
  const [selectedReview, setSelectedReview] = useState(null);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [filters, setFilters] = useState({
    reviewedStatus: 'pending',
    confidenceMin: 0.8,
    confidenceMax: 1.0,
    dateFrom: '',
    dateTo: '',
  });
  const [pagination, setPagination] = useState({
    currentPage: 1,
    totalPages: 1,
    totalCount: 0,
    pageSize: 20,
  });
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');

  // Fetch auto-marked reviews
  const fetchAutoMarkedReviews = useCallback(
    async (page = 1) => {
      setLoading(true);
      try {
        const response = await getAutoMarkedReviews(page, pagination.pageSize, filters);
        // Debug log
        console.log('AutoMarkedReviews API response:', response);
        const reviewList = Array.isArray(response)
          ? response
          : Array.isArray(response?.data)
            ? response.data
            : [];
        setReviews(reviewList);
        setPagination({
          currentPage: response.current_page || 1,
          totalPages: response.total_pages || 1,
          totalCount: response.count || reviewList.length,
          pageSize: response.page_size || 20,
        });
      } catch (error) {
        console.error('Error fetching auto-marked reviews:', error);
      } finally {
        setLoading(false);
      }
    },
    [filters, pagination.pageSize]
  );

  // Fetch analytics
  const fetchAnalytics = useCallback(async () => {
    try {
      const response = await getModerationAnalytics(30);
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchAutoMarkedReviews();
    fetchAnalytics();
  }, [fetchAutoMarkedReviews, fetchAnalytics]);

  // Handle filter changes
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  // Apply filters
  const applyFilters = () => {
    fetchAutoMarkedReviews(1);
  };

  // Reset filters
  const resetFilters = () => {
    setFilters({
      reviewedStatus: 'pending',
      confidenceMin: 0.8,
      confidenceMax: 1.0,
      dateFrom: '',
      dateTo: '',
    });
  };

  // Handle pagination
  const handlePageChange = page => {
    fetchAutoMarkedReviews(page);
  };

  // Submit feedback
  const handleSubmitFeedback = async (reviewId, feedbackData) => {
    try {
      await submitModerationFeedback(reviewId, feedbackData);
      // Refresh the reviews list
      fetchAutoMarkedReviews(pagination.currentPage);
      setShowFeedbackModal(false);
      setSelectedReview(null);
    } catch (error) {
      console.error('Error submitting feedback:', error);
    }
  };

  // Get confidence color
  const getConfidenceColor = confidence => {
    if (confidence >= 0.9) return 'text-red-600 bg-red-100';
    if (confidence >= 0.8) return 'text-orange-600 bg-orange-100';
    return 'text-yellow-600 bg-yellow-100';
  };

  // Get status color
  const getStatusColor = hasReviewed => {
    return hasReviewed ? 'text-green-600 bg-green-100' : 'text-gray-600 bg-gray-100';
  };

  // Format date
  const formatDate = dateString => {
    return new Date(dateString).toLocaleDateString('vi-VN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <BoltIcon className="h-6 w-6 text-yellow-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Auto-marked Reviews</h1>
              <p className="text-gray-600">
                Quản lý và đánh giá các reviews được đánh dấu tự động bởi AI
              </p>
            </div>
          </div>
          <button
            onClick={() => fetchAutoMarkedReviews(pagination.currentPage)}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <ArrowPathIcon className="h-4 w-4" />
            <span>Làm mới</span>
          </button>
        </div>
      </div>

      {/* Analytics Summary */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <ChartBarIcon className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Độ chính xác tổng</p>
                <p className="text-lg font-semibold">
                  {(analytics.summary?.overall_accuracy * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircleIcon className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Tổng feedback</p>
                <p className="text-lg font-semibold">{analytics.summary?.total_feedback}</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <BoltIcon className="h-5 w-5 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Auto-marked (30d)</p>
                <p className="text-lg font-semibold">
                  {analytics.volume_metrics?.auto_marked_reviews}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <ClockIcon className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Chờ xử lý</p>
                <p className="text-lg font-semibold">{pagination.totalCount}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <div className="flex items-center space-x-3 mb-4">
          <FunnelIcon className="h-5 w-5 text-gray-600" />
          <h3 className="text-lg text-black font-medium">Bộ lọc</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-1">Trạng thái</label>
            <select
              value={filters.reviewedStatus}
              onChange={e => handleFilterChange('reviewedStatus', e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-black focus:ring-blue-500 focus:border-blue-500"
            >
              <option className="text-black" value="pending">
                Chờ xử lý
              </option>
              <option className="text-black" value="reviewed">
                Đã xử lý
              </option>
              <option className="text-black" value="all">
                Tất cả
              </option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium  text-gray-700 mb-1">
              Confidence tối thiểu
            </label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={filters.confidenceMin}
              onChange={e => handleFilterChange('confidenceMin', parseFloat(e.target.value))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-blue-500 focus:border-blue-500 text-black"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Confidence tối đa
            </label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={filters.confidenceMax}
              onChange={e => handleFilterChange('confidenceMax', parseFloat(e.target.value))}
              className="w-full border border-gray-300 rounded-lg text-black px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Từ ngày</label>
            <input
              type="date"
              value={filters.dateFrom}
              onChange={e => handleFilterChange('dateFrom', e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 text-black py-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Đến ngày</label>
            <input
              type="date"
              value={filters.dateTo}
              onChange={e => handleFilterChange('dateTo', e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-black  focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        <div className="flex space-x-3 mt-4">
          <button
            onClick={applyFilters}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Áp dụng bộ lọc
          </button>
          <button
            onClick={resetFilters}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            Đặt lại
          </button>
        </div>
      </div>

      {/* Reviews List */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6 border-b">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-black">
              {`Danh sách Reviews (${
                typeof pagination.totalCount === 'number'
                  ? pagination.totalCount
                  : Array.isArray(reviews)
                    ? reviews.length
                    : 0
              })`}
            </h3>
            <div className="text-sm text-gray-600">
              Trang {pagination.currentPage} / {pagination.totalPages}
            </div>
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Đang tải...</p>
          </div>
        ) : Array.isArray(reviews) && reviews.length === 0 ? (
          <div className="p-12 text-center">
            <BoltIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Không có reviews nào được tìm thấy</p>
          </div>
        ) : (
          <div className="divide-y">
            {Array.isArray(reviews) &&
              reviews.map(review => {
                const moderationFeedback = Array.isArray(review.moderation_feedback)
                  ? review.moderation_feedback
                  : [];
                return (
                  <div key={review.id} className="p-6 hover:bg-gray-50 transition-colors">
                    <div className="flex items-start space-x-4">
                      {/* Review Content */}
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <div className="flex items-center space-x-2">
                            <UserIcon className="h-4 w-4 text-gray-500" />
                            <span className="font-medium text-gray-900">
                              {review.user?.username || 'Anonymous'}
                            </span>
                          </div>

                          <span
                            className={`px-2 py-1 text-xs font-medium rounded-full ${getConfidenceColor(
                              review.spoiler_confidence
                            )}`}
                          >
                            Confidence: {(review.spoiler_confidence * 100).toFixed(1)}%
                          </span>

                          <span
                            className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
                              moderationFeedback.length > 0
                            )}`}
                          >
                            {moderationFeedback.length > 0 ? 'Đã xử lý' : 'Chờ xử lý'}
                          </span>

                          <div className="flex items-center space-x-1 text-sm text-gray-500">
                            <CalendarDaysIcon className="h-4 w-4" />
                            <span>{formatDate(review.created_at)}</span>
                          </div>
                        </div>

                        <div className="mb-3">
                          <p className="text-sm text-gray-600 mb-1">
                            <strong>Phim:</strong> {review.movie?.title || 'N/A'}
                          </p>
                          <div className="bg-gray-50 p-3 rounded-lg">
                            <p className="text-gray-800">{review.content}</p>
                          </div>
                        </div>

                        {Array.isArray(review.spoiler_detected_patterns) &&
                          review.spoiler_detected_patterns.length > 0 && (
                            <div className="mb-3">
                              <p className="text-sm font-medium text-gray-700 mb-1">
                                Patterns phát hiện:
                              </p>
                              <div className="flex flex-wrap gap-1">
                                {review.spoiler_detected_patterns.map((pattern, index) => (
                                  <span
                                    key={index}
                                    className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded"
                                  >
                                    {pattern}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                      </div>

                      {/* Actions */}
                      <div className="flex flex-col space-y-2">
                        <button
                          onClick={() => {
                            setSelectedReview(review);
                            setShowFeedbackModal(true);
                          }}
                          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                        >
                          <EyeIcon className="h-4 w-4 inline mr-1" />
                          Xử lý
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>
        )}

        {/* Pagination */}
        {pagination.totalPages > 1 && (
          <div className="p-6 border-t">
            <div className="flex items-center justify-between">
              <button
                onClick={() => handlePageChange(pagination.currentPage - 1)}
                disabled={pagination.currentPage === 1}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Trang trước
              </button>

              <span className="text-sm text-gray-700">
                Trang {pagination.currentPage} / {pagination.totalPages}
              </span>

              <button
                onClick={() => handlePageChange(pagination.currentPage + 1)}
                disabled={pagination.currentPage === pagination.totalPages}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Trang sau
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Feedback Modal */}
      {showFeedbackModal && selectedReview && (
        <FeedbackModal
          review={selectedReview}
          onSubmit={handleSubmitFeedback}
          onClose={() => {
            setShowFeedbackModal(false);
            setSelectedReview(null);
          }}
        />
      )}
    </div>
  );
};

// Feedback Modal Component
const FeedbackModal = ({ review, onSubmit, onClose }) => {
  const [feedbackData, setFeedbackData] = useState({
    feedbackType: '',
    moderatorDecision: '',
    isSpoilerCorrect: false,
    difficultyLevel: 'medium',
    notes: '',
    timeSpentSeconds: 0,
  });
  const [startTime] = useState(Date.now());

  const handleSubmit = e => {
    e.preventDefault();

    // Calculate time spent
    const timeSpent = Math.floor((Date.now() - startTime) / 1000);

    const finalFeedbackData = {
      ...feedbackData,
      timeSpentSeconds: timeSpent,
    };

    onSubmit(review.id, finalFeedbackData);
  };

  return (
    <div className="fixed inset-0 min-h-screen bg-black bg-opacity-50 z-50 flex items-center justify-center p-2">
      <div className="bg-white rounded-lg max-w-xl w-full max-h-[90vh] overflow-y-auto shadow-lg">
        <div className="p-6 border-b">
          <h3 className="text-lg font-medium text-black">Feedback cho Review</h3>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Review Info */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="font-medium mb-2 text-black">Review Content:</p>
            <p className="text-gray-800">{review.content}</p>
            <p className="text-sm text-gray-600 mt-2  ">
              Confidence: {(review.spoiler_confidence * 100).toFixed(1)}%
            </p>
          </div>

          {/* Feedback Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Loại feedback *</label>
            <select
              value={feedbackData.feedbackType}
              onChange={e => setFeedbackData({ ...feedbackData, feedbackType: e.target.value })}
              required
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-blue-500 focus:border-blue-500 text-black"
            >
              <option className="text-black" value="">
                Chọn loại feedback
              </option>
              <option className="text-black" value="correct_spoiler">
                Spoiler chính xác
              </option>
              <option className="text-black" value="false_positive">
                False positive
              </option>
              <option className="text-black" value="missed_spoiler">
                Bỏ sót spoiler
              </option>
              <option className="text-black" value="correct_non_spoiler">
                Không phải spoiler chính xác
              </option>
            </select>
          </div>

          {/* Moderator Decision */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Quyết định moderator *
            </label>
            <select
              value={feedbackData.moderatorDecision}
              onChange={e =>
                setFeedbackData({ ...feedbackData, moderatorDecision: e.target.value })
              }
              required
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-blue-500 focus:border-blue-500 text-black"
            >
              <option className="text-black" value="">
                Chọn quyết định
              </option>
              <option className="text-black" value="approve_as_spoiler">
                Phê duyệt là spoiler
              </option>
              <option className="text-black" value="approve_as_non_spoiler">
                Phê duyệt không phải spoiler
              </option>
              <option className="text-black" value="reject_review">
                Từ chối review
              </option>
            </select>
          </div>

          {/* Is Spoiler Correct */}
          <div>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={feedbackData.isSpoilerCorrect}
                onChange={e =>
                  setFeedbackData({ ...feedbackData, isSpoilerCorrect: e.target.checked })
                }
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Phát hiện spoiler chính xác</span>
            </label>
          </div>

          {/* Difficulty Level */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Mức độ khó</label>
            <select
              value={feedbackData.difficultyLevel}
              onChange={e => setFeedbackData({ ...feedbackData, difficultyLevel: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-blue-500 focus:border-blue-500 text-black"
            >
              <option className="text-black" value="easy">
                Dễ
              </option>
              <option className="text-black" value="medium">
                Trung bình
              </option>
              <option className="text-black" value="hard">
                Khó
              </option>
            </select>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Ghi chú</label>
            <textarea
              value={feedbackData.notes}
              onChange={e => setFeedbackData({ ...feedbackData, notes: e.target.value })}
              rows={3}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Ghi chú thêm về quyết định..."
            />
          </div>

          {/* Actions */}
          <div className="flex space-x-3 pt-4">
            <button
              type="submit"
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Gửi Feedback
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 transition-colors"
            >
              Hủy
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AutoMarkedReviews;
