import React, { useState, useEffect } from 'react';
import { getCommunityStats } from '../../../api/movieService';

const ModerationQueue = () => {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedReview, setSelectedReview] = useState(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    fetchModerationQueue();
  }, []);

  const fetchModerationQueue = async () => {
    try {
      setLoading(true);
      // For now, using community stats as placeholder
      // TODO: Create proper moderator API endpoint for moderation queue
      const response = await getCommunityStats();
      // Mock review data for now
      setReviews([]);
    } catch (err) {
      setError('Không thể tải hàng đợi kiểm duyệt');
      console.error('Error fetching moderation queue:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleModerationAction = async (reviewId, action) => {
    try {
      // This would be implemented with a proper API endpoint
      console.log(`Moderation action: ${action} for review ${reviewId}`);

      // Update local state
      setReviews(prevReviews => prevReviews.filter(review => review.id !== reviewId));
      setShowModal(false);

      // Show success message
      alert(`Đã ${action === 'approve' ? 'phê duyệt' : 'từ chối'} review thành công!`);
    } catch (err) {
      console.error('Error performing moderation action:', err);
      alert('Có lỗi xảy ra khi thực hiện hành động kiểm duyệt');
    }
  };

  if (loading) {
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

  return (
    <div className="p-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Hàng đợi kiểm duyệt</h2>
        <p className="text-gray-600">Review chờ kiểm duyệt (7 ngày gần đây)</p>
      </div>

      {reviews.length === 0 ? (
        <div className="text-center py-12">
          <div className="mx-auto h-12 w-12 text-gray-400">
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            Không có review nào chờ kiểm duyệt
          </h3>
          <p className="mt-1 text-sm text-gray-500">Tất cả review đã được xử lý.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {reviews.map(review => (
            <div key={review.id} className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-start justify-between">
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
                            <svg
                              key={i}
                              className={`h-4 w-4 ${
                                i < review.rating ? 'text-yellow-400' : 'text-gray-300'
                              }`}
                              fill="currentColor"
                              viewBox="0 0 20 20"
                            >
                              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                            </svg>
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
                    {review.content.length > 300 && (
                      <button
                        onClick={() => {
                          setSelectedReview(review);
                          setShowModal(true);
                        }}
                        className="text-indigo-600 hover:text-indigo-500 text-sm font-medium mt-2"
                      >
                        Đọc thêm
                      </button>
                    )}
                  </div>

                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <span>Phim: {review.movie?.title}</span>
                    <span>Ngôn ngữ: {review.language}</span>
                    {review.is_spoiler && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        Spoiler
                      </span>
                    )}
                  </div>
                </div>

                <div className="ml-6 flex flex-col space-y-2">
                  <button
                    onClick={() => handleModerationAction(review.id, 'approve')}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                  >
                    <svg
                      className="h-4 w-4 mr-1"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    Phê duyệt
                  </button>
                  <button
                    onClick={() => handleModerationAction(review.id, 'reject')}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  >
                    <svg
                      className="h-4 w-4 mr-1"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                    Từ chối
                  </button>
                  <button
                    onClick={() => {
                      setSelectedReview(review);
                      setShowModal(true);
                    }}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    <svg
                      className="h-4 w-4 mr-1"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                      />
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                      />
                    </svg>
                    Xem chi tiết
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Review Detail Modal */}
      {showModal && selectedReview && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Chi tiết review</h3>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <h4 className="text-lg font-medium text-gray-900 mb-2">
                    {selectedReview.title || `Review cho ${selectedReview.movie?.title}`}
                  </h4>
                  <p className="text-gray-700 whitespace-pre-wrap">{selectedReview.content}</p>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-500">Người dùng:</span>
                    <p className="text-gray-900">{selectedReview.user?.username}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-500">Phim:</span>
                    <p className="text-gray-900">{selectedReview.movie?.title}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-500">Ngày tạo:</span>
                    <p className="text-gray-900">
                      {new Date(selectedReview.created_at).toLocaleDateString('vi-VN')}
                    </p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-500">Ngôn ngữ:</span>
                    <p className="text-gray-900">{selectedReview.language}</p>
                  </div>
                </div>

                <div className="flex justify-end space-x-3 pt-4 border-t">
                  <button
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                  >
                    Đóng
                  </button>
                  <button
                    onClick={() => handleModerationAction(selectedReview.id, 'reject')}
                    className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  >
                    Từ chối
                  </button>
                  <button
                    onClick={() => handleModerationAction(selectedReview.id, 'approve')}
                    className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                  >
                    Phê duyệt
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModerationQueue;
