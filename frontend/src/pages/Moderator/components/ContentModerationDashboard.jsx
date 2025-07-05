import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Eye,
  Shield,
  RefreshCw,
  Filter,
  Search,
  Clock,
  Flag,
  Star,
  MessageSquare,
  User,
  Calendar,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import {
  getModerationQueue,
  moderateReview,
  bulkModerateReviews,
  getReviewsPendingSpoilerDetection,
  analyzeReviewSpoiler,
  detectSpoilers,
  getSpoilerStatistics,
} from '../../../api/movieService';

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
  const [stats, setStats] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    fetchModerationQueue();
    fetchSpoilerStats();
  }, [currentPage, filters]);

  const fetchModerationQueue = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getModerationQueue(currentPage, 20, filters);
      setReviews(response.data || []);
      setTotalPages(response.total_pages || 1);
    } catch (err) {
      console.error('Error fetching moderation queue:', err);
      setError('Không thể tải hàng đợi kiểm duyệt');
    } finally {
      setLoading(false);
    }
  };

  const fetchSpoilerStats = async () => {
    try {
      const response = await getSpoilerStatistics();
      setStats(response.statistics);
    } catch (err) {
      console.error('Error fetching spoiler stats:', err);
    }
  };

  const handleModerationAction = async (reviewId, action, reason = '') => {
    try {
      console.log(`Moderating review ${reviewId} with action: ${action}`);
      const result = await moderateReview(reviewId, action, reason);
      console.log('Moderation result:', result);

      // Update local state
      setReviews(prevReviews => prevReviews.filter(review => review.id !== reviewId));
      setSelectedReview(null);
      setShowModal(false);

      // Refresh data
      await fetchModerationQueue();
      await fetchSpoilerStats();

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

      // Clear selection and refresh
      setSelectedReviews([]);
      await fetchModerationQueue();
      await fetchSpoilerStats();

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
    if (confidence > 0.8) return <AlertTriangle className="h-4 w-4" />;
    if (confidence > 0.6) return <AlertTriangle className="h-4 w-4" />;
    if (confidence > 0.4) return <AlertTriangle className="h-4 w-4" />;
    return <CheckCircle className="h-4 w-4" />;
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

  if (loading && reviews.length === 0) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-gray-200 h-32 rounded-lg"></div>
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
          className={`fixed top-4 right-4 z-50 p-4 rounded-md shadow-lg ${
            notification.type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
          }`}
        >
          <div className="flex items-center">
            {notification.type === 'success' ? (
              <CheckCircle className="h-5 w-5 mr-2" />
            ) : (
              <XCircle className="h-5 w-5 mr-2" />
            )}
            <span>{notification.message}</span>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Kiểm duyệt nội dung</h2>
            <p className="text-gray-600">Quản lý và kiểm duyệt reviews với spoiler detection</p>
          </div>
          <button
            onClick={fetchModerationQueue}
            className="flex items-center space-x-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Làm mới</span>
          </button>
        </div>
      </div>

      {/* Priority Statistics */}
      <div className="grid grid-cols-1 gap-4 mb-6 md:grid-cols-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center">
            <div className="bg-blue-100 rounded-full p-3">
              <Shield className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Tổng cần kiểm duyệt</p>
              <p className="text-2xl font-bold text-gray-900">{reviews.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center">
            <div className="bg-red-100 rounded-full p-3">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-red-600">Ưu tiên cao</p>
              <p className="text-2xl font-bold text-red-900">
                {reviews.filter(r => r.spoiler_analysis?.priority_level === 'high').length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center">
            <div className="bg-orange-100 rounded-full p-3">
              <TrendingDown className="h-6 w-6 text-orange-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-orange-600">Ưu tiên trung bình</p>
              <p className="text-2xl font-bold text-orange-900">
                {reviews.filter(r => r.spoiler_analysis?.priority_level === 'medium').length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center">
            <div className="bg-green-100 rounded-full p-3">
              <CheckCircle className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-green-600">Ưu tiên thấp</p>
              <p className="text-2xl font-bold text-green-900">
                {reviews.filter(r => r.spoiler_analysis?.priority_level === 'low').length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Bộ lọc</h3>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            <select
              value={filters.priority}
              onChange={e => setFilters(prev => ({ ...prev, priority: e.target.value }))}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="all">Tất cả ưu tiên</option>
              <option value="high">Ưu tiên cao (Spoiler đã đánh dấu)</option>
              <option value="medium">Ưu tiên trung bình (Cần kiểm tra)</option>
              <option value="low">Ưu tiên thấp (Từ khóa nghi ngờ)</option>
            </select>

            <select
              value={filters.language}
              onChange={e => setFilters(prev => ({ ...prev, language: e.target.value }))}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="">Tất cả ngôn ngữ</option>
              <option value="vi">Tiếng Việt</option>
              <option value="en">Tiếng Anh</option>
            </select>

            <input
              type="date"
              value={filters.date_from}
              onChange={e => setFilters(prev => ({ ...prev, date_from: e.target.value }))}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              placeholder="Từ ngày"
            />

            <input
              type="date"
              value={filters.date_to}
              onChange={e => setFilters(prev => ({ ...prev, date_to: e.target.value }))}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              placeholder="Đến ngày"
            />
          </div>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedReviews.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
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
                <CheckCircle className="h-4 w-4" />
                <span>Phê duyệt ({selectedReviews.length})</span>
              </button>
              <button
                onClick={() => handleBulkModeration('reject')}
                className="flex items-center space-x-1 rounded-md bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-700"
              >
                <XCircle className="h-4 w-4" />
                <span>Từ chối ({selectedReviews.length})</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reviews List */}
      {error ? (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <XCircle className="h-5 w-5 text-red-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Lỗi</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      ) : reviews.length === 0 ? (
        <div className="text-center py-12">
          <div className="mx-auto h-12 w-12 text-gray-400">
            <Shield className="h-12 w-12" />
          </div>
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            Không có review nào chờ kiểm duyệt
          </h3>
          <p className="mt-1 text-sm text-gray-500">Tất cả review đã được xử lý.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {reviews.map(review => (
            <div key={review.id} className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-start space-x-4">
                {/* Checkbox */}
                <input
                  type="checkbox"
                  checked={selectedReviews.includes(review.id)}
                  onChange={() => handleSelectReview(review.id)}
                  className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />

                {/* Review Content */}
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-4">
                    <img
                      className="h-10 w-10 rounded-full"
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
                        <span className="text-sm text-gray-500 mr-1">Rating:</span>
                        <div className="flex items-center">
                          {[...Array(5)].map((_, i) => (
                            <Star
                              key={i}
                              className={`h-4 w-4 ${
                                i < review.rating ? 'text-yellow-400 fill-current' : 'text-gray-300'
                              }`}
                            />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="mb-4">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      {review.title || `Review cho ${review.movie?.title}`}
                    </h3>
                    <p className="text-gray-700 whitespace-pre-wrap">
                      {review.content.length > 300
                        ? `${review.content.substring(0, 300)}...`
                        : review.content}
                    </p>
                  </div>

                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <span className="flex items-center">
                      <MessageSquare className="h-4 w-4 mr-1" />
                      Phim: {review.movie?.title}
                    </span>
                    <span className="flex items-center">
                      <User className="h-4 w-4 mr-1" />
                      Ngôn ngữ: {review.language}
                    </span>
                    {review.spoiler_analysis && (
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          review.spoiler_analysis.priority_level === 'high'
                            ? 'bg-red-100 text-red-800'
                            : review.spoiler_analysis.priority_level === 'medium'
                              ? 'bg-orange-100 text-orange-800'
                              : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        <AlertTriangle className="h-3 w-3 mr-1" />
                        {review.spoiler_analysis.priority_level === 'high'
                          ? 'Ưu tiên cao'
                          : review.spoiler_analysis.priority_level === 'medium'
                            ? 'Ưu tiên TB'
                            : 'Ưu tiên thấp'}
                        ({Math.round(review.spoiler_analysis.confidence * 100)}%)
                      </span>
                    )}
                    {review.is_spoiler && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        <AlertTriangle className="h-3 w-3 mr-1" />
                        Đã đánh dấu Spoiler
                      </span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex flex-col space-y-2">
                  <button
                    onClick={() => handleAnalyzeSpoiler(review)}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    {analyzingSpoiler && selectedReview?.id === review.id ? (
                      <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
                    ) : (
                      <Eye className="h-4 w-4 mr-1" />
                    )}
                    Phân tích Spoiler
                  </button>
                  <button
                    onClick={() => handleModerationAction(review.id, 'approve')}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
                  >
                    <CheckCircle className="h-4 w-4 mr-1" />
                    Phê duyệt
                  </button>
                  <button
                    onClick={() => handleModerationAction(review.id, 'reject')}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
                  >
                    <XCircle className="h-4 w-4 mr-1" />
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
              className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            >
              Trước
            </button>
            <span className="text-sm text-gray-700">
              Trang {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            >
              Sau
            </button>
          </div>
        </div>
      )}

      {/* Spoiler Analysis Modal */}
      {showModal && selectedReview && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Phân tích Spoiler - {selectedReview.movie?.title}
                </h3>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="h-6 w-6" />
                </button>
              </div>

              {(spoilerResult || selectedReview?.spoiler_analysis) && (
                <div className="space-y-4">
                  {/* Spoiler Detection Result */}
                  <div
                    className={`p-4 rounded-lg border ${
                      spoilerResult?.is_spoiler || selectedReview?.spoiler_analysis?.is_spoiler
                        ? 'border-red-200 bg-red-50'
                        : 'border-green-200 bg-green-50'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      {getConfidenceIcon(
                        spoilerResult?.confidence || selectedReview?.spoiler_analysis?.confidence
                      )}
                      <span
                        className={`font-medium ${
                          spoilerResult?.is_spoiler || selectedReview?.spoiler_analysis?.is_spoiler
                            ? 'text-red-800'
                            : 'text-green-800'
                        }`}
                      >
                        {spoilerResult?.is_spoiler || selectedReview?.spoiler_analysis?.is_spoiler
                          ? 'Có phát hiện spoiler'
                          : 'Không có spoiler'}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-gray-600">
                      Độ tin cậy:{' '}
                      {(
                        (spoilerResult?.confidence ||
                          selectedReview?.spoiler_analysis?.confidence) * 100
                      ).toFixed(1)}
                      %
                    </p>
                  </div>

                  {/* Explanation */}
                  {spoilerResult.explanation && (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="text-sm font-medium text-gray-900 mb-2">Giải thích</h4>
                      <p className="text-sm text-gray-700">{spoilerResult.explanation}</p>
                    </div>
                  )}

                  {/* Detected Patterns */}
                  {spoilerResult.detected_patterns &&
                    spoilerResult.detected_patterns.length > 0 && (
                      <div className="bg-yellow-50 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-yellow-900 mb-2">Mẫu phát hiện</h4>
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
                      <div className="bg-orange-50 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-orange-900 mb-2">
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
                    <div className="bg-blue-50 rounded-lg p-4">
                      <h4 className="text-sm font-medium text-blue-900 mb-2">Hành động đề xuất</h4>
                      <p className="text-sm text-blue-800">{spoilerResult.suggested_action}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Action Buttons */}
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Đóng
                </button>
                <button
                  onClick={() => {
                    handleModerationAction(selectedReview.id, 'approve');
                    setShowModal(false);
                  }}
                  className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700"
                >
                  Phê duyệt
                </button>
                <button
                  onClick={() => {
                    handleModerationAction(selectedReview.id, 'reject');
                    setShowModal(false);
                  }}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700"
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
