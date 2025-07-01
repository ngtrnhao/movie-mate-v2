import { useState, useEffect } from 'react';
import { Send, Star, Eye, EyeOff, AlertTriangle } from 'lucide-react';
import {
  getMovieReviews,
  voteOnReview,
  submitMovieReview,
  getMyReviews,
} from '../../../api/movieService';
import ReviewActions from '../../../components/common/ReviewActions';
import { useSelector } from 'react-redux';

const StarRating = ({ rating, onRatingChange, editable = false, size = 20, showLabel = false }) => {
  const [hoverRating, setHoverRating] = useState(0);

  const handleStarClick = starValue => {
    if (editable && onRatingChange) {
      onRatingChange(starValue);
    }
  };

  const handleStarHover = starValue => {
    if (editable) {
      setHoverRating(starValue);
    }
  };

  const handleStarLeave = () => {
    if (editable) {
      setHoverRating(0);
    }
  };

  const currentRating = hoverRating || rating;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map(star => {
          const isActive = star <= (hoverRating || rating);
          return (
            <button
              key={star}
              onClick={() => handleStarClick(star)}
              onMouseEnter={() => handleStarHover(star)}
              onMouseLeave={handleStarLeave}
              disabled={!editable}
              className={`${editable ? 'cursor-pointer hover:scale-110' : 'cursor-default'} transition-all duration-200`}
            >
              <Star
                size={size}
                className={`${isActive ? 'fill-yellow-400 text-yellow-400' : 'text-gray-400'} transition-all duration-200`}
              />
            </button>
          );
        })}
      </div>
    </div>
  );
};

const CommentTab = ({ movieId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [myReview, setMyReview] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showSpoilers, setShowSpoilers] = useState(false);
  const [newComment, setNewComment] = useState('');

  // Get auth state from Redux store
  const isAuthenticated = useSelector(state => state.auth.isAuthenticated);

  useEffect(() => {
    fetchReviews();
    // Only fetch my reviews if user is authenticated
    if (isAuthenticated) {
      fetchMyReview();
    }
  }, [movieId, currentPage, isAuthenticated]);

  const fetchReviews = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch reviews sorted by recent for comment-style display
      const data = await getMovieReviews(movieId, currentPage, 10, 'recent');
      setReviews(data.data || []);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      console.error('Error fetching reviews:', err);
      setError('Không thể tải bình luận.');
    } finally {
      setLoading(false);
    }
  };

  const fetchMyReview = async () => {
    if (!isAuthenticated) {
      console.log('User not authenticated, skipping my_reviews fetch');
      return;
    }

    try {
      const data = await getMyReviews(movieId);
      if (data.data && data.data.length > 0) {
        setMyReview(data.data[0]);
      }
    } catch (err) {
      console.error('Error fetching my review:', err);
      // Don't set error state as this is not critical
    }
  };

  const handleLike = async reviewId => {
    if (!isAuthenticated) {
      // Show login prompt
      return;
    }

    try {
      await voteOnReview(reviewId, 'helpful');
      // Update local state
      setReviews(prev =>
        prev.map(review =>
          review.id === reviewId
            ? {
                ...review,
                helpful_votes: (review.helpful_votes || 0) + 1,
                total_votes: (review.total_votes || 0) + 1,
                user_vote: 'helpful',
              }
            : review
        )
      );
    } catch (err) {
      console.error('Error liking review:', err);
    }
  };

  const handleDislike = async reviewId => {
    if (!isAuthenticated) {
      // Show login prompt
      return;
    }

    try {
      await voteOnReview(reviewId, 'not_helpful');
      // Update local state
      setReviews(prev =>
        prev.map(review =>
          review.id === reviewId
            ? {
                ...review,
                total_votes: (review.total_votes || 0) + 1,
                user_vote: 'not_helpful',
              }
            : review
        )
      );
    } catch (err) {
      console.error('Error disliking review:', err);
    }
  };

  const handleSubmitComment = async () => {
    if (!isAuthenticated) {
      // Show login prompt
      return;
    }

    if (newComment.trim().length >= 10) {
      try {
        const reviewData = {
          title: '',
          content: newComment.trim(),
          rating: null,
          is_public: true,
          is_spoiler: false,
        };

        await submitMovieReview(movieId, reviewData);
        setNewComment('');
        fetchReviews();
      } catch (err) {
        console.error('Error submitting comment:', err);
        setError('Không thể gửi bình luận.');
      }
    }
  };

  if (loading) return <div className="text-center text-gray-400">Đang tải bình luận...</div>;
  if (error) return <div className="text-center text-red-400">{error}</div>;

  return (
    <div className="space-y-6">
      {/* Comment Input */}
      <div className="rounded-lg bg-gray-800/50 p-4">
        <h3 className="mb-4 font-medium text-white">Viết bình luận</h3>
        <div className="space-y-3">
          <textarea
            value={newComment}
            onChange={e => setNewComment(e.target.value)}
            placeholder="Chia sẻ suy nghĩ chi tiết của bạn về bộ phim (ít nhất 10 ký tự)..."
            className="w-full resize-none rounded-lg bg-gray-700 p-3 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500"
            rows="3"
            maxLength={500}
          />
          <div className="flex items-center justify-between">
            <div className="flex flex-col">
              <span className="text-xs text-gray-400">{newComment.length} / 500</span>
              {newComment.length > 0 && newComment.length < 10 && (
                <span className="text-xs text-red-400">Bình luận phải có ít nhất 10 ký tự</span>
              )}
            </div>
            <button
              onClick={handleSubmitComment}
              disabled={!newComment.trim() || newComment.length < 10}
              className="flex items-center gap-2 rounded-lg bg-yellow-500 px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-yellow-600 disabled:cursor-not-allowed disabled:bg-gray-600"
            >
              <Send size={16} />
              Gửi
            </button>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        <h3 className="font-medium text-white">Bình luận từ người dùng</h3>

        {/* Spoiler Toggle */}
        <button
          onClick={() => setShowSpoilers(!showSpoilers)}
          className={`flex items-center gap-2 rounded-lg px-3 py-1 text-sm transition-colors ${
            showSpoilers
              ? 'bg-orange-500/20 text-orange-400'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          {showSpoilers ? <EyeOff size={16} /> : <Eye size={16} />}
          {showSpoilers ? 'Ẩn spoiler' : 'Hiện spoiler'}
        </button>
      </div>

      {/* Comment List */}
      <div className="space-y-4">
        {reviews.length > 0 ? (
          reviews.map(review => {
            const isSpoiler = review.is_spoiler;
            const shouldBlur = isSpoiler && !showSpoilers;

            return (
              <div key={review.id} className="rounded-lg bg-gray-800/30 p-4">
                <div className="flex items-start gap-3">
                  <div className="relative">
                    <img
                      src={review.reviewer_avatar || '/api/placeholder/40/40'}
                      alt={review.reviewer_name || 'User'}
                      className="size-10 rounded-full object-cover"
                      onError={e => {
                        e.target.src = `https://ui-avatars.com/api/?name=${review.reviewer_name || 'User'}&background=random&color=fff&size=40`;
                      }}
                    />
                    {review.is_verified_reviewer && (
                      <span className="absolute -right-1 -top-1 text-xs text-yellow-400">⚡</span>
                    )}
                  </div>

                  <div className="flex-1">
                    <div className="mb-1 flex items-center gap-2">
                      <span className="font-medium text-white">
                        {review.reviewer_name || 'User'}
                      </span>
                      {review.is_verified_reviewer && (
                        <span className="text-xs text-yellow-400">⚡</span>
                      )}
                      <span className="text-xs text-gray-400">
                        {new Date(review.created_at).toLocaleDateString('vi-VN', {
                          day: '2-digit',
                          month: '2-digit',
                          year: 'numeric',
                        })}
                      </span>
                      {isSpoiler && (
                        <span className="flex items-center gap-1 rounded bg-orange-500/20 px-2 py-1 text-xs text-orange-400">
                          <AlertTriangle size={12} />
                          Spoiler
                        </span>
                      )}
                    </div>

                    {/* Show rating if available */}
                    {review.rating && (
                      <div className="mb-2 flex items-center gap-2">
                        <StarRating rating={parseFloat(review.rating) || 0} size={14} />
                        <span className="text-xs text-gray-400">({review.rating}/5)</span>
                      </div>
                    )}

                    <div className={`mb-3 ${shouldBlur ? 'blur-sm' : ''}`}>
                      <p className="text-sm leading-relaxed text-gray-200">{review.content}</p>
                      {shouldBlur && (
                        <div className="mt-2">
                          <button
                            onClick={() => setShowSpoilers(true)}
                            className="text-xs text-yellow-400 hover:text-yellow-300"
                          >
                            Nhấn để xem spoiler
                          </button>
                        </div>
                      )}
                    </div>

                    <ReviewActions
                      review={review}
                      onVoteUpdate={(reviewId, result) => {
                        setReviews(prev =>
                          prev.map(r =>
                            r.id === reviewId
                              ? {
                                  ...r,
                                  helpful_votes: result.helpful_votes,
                                  total_votes: result.total_votes,
                                  user_vote: result.user_vote,
                                }
                              : r
                          )
                        );
                      }}
                      onDelete={() => fetchReviews()}
                    />
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center text-gray-400">Chưa có bình luận nào cho phim này.</div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2">
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="rounded bg-gray-700 px-3 py-1 text-sm text-white disabled:cursor-not-allowed disabled:bg-gray-800"
            >
              Trước
            </button>

            <span className="text-sm text-gray-400">
              Trang {currentPage} / {totalPages}
            </span>

            <button
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="rounded bg-gray-700 px-3 py-1 text-sm text-white disabled:cursor-not-allowed disabled:bg-gray-800"
            >
              Sau
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default CommentTab;
