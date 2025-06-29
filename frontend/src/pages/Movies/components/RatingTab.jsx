import { useState, useEffect } from 'react';
import { Star, Filter, AlertTriangle, Eye, EyeOff } from 'lucide-react';
import {
  getMovieReviews,
  submitMovieReview,
  voteOnReview,
  updateReview,
  deleteReview,
  getUserReview,
} from '../../../api/movieService';
import ReviewActions from '../../../components/common/ReviewActions';

const StarRating = ({ rating, onRatingChange, editable = false, size = 20, showLabel = false }) => {
  const [hoverRating, setHoverRating] = useState(0);

  // Text descriptions for each rating level
  const ratingLabels = {
    1: 'Rất tệ',
    2: 'Tệ',
    3: 'Bình thường',
    4: 'Hay',
    5: 'Xuất sắc',
  };

  // Color coding for different emotion levels
  const ratingColors = {
    1: 'text-red-400',
    2: 'text-orange-400',
    3: 'text-yellow-400',
    4: 'text-green-400',
    5: 'text-emerald-400',
  };

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
  const currentLabel = ratingLabels[currentRating];
  const currentColor = ratingColors[currentRating] || 'text-gray-300';

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

      {/* Rating Label */}
      {showLabel && (
        <div
          className={`flex h-[24px] items-center justify-center text-sm font-medium transition-all duration-200 ${currentColor}`}
        >
          {currentRating > 0 ? currentLabel : '\u00A0'}
        </div>
      )}
    </div>
  );
};

const RatingTab = ({ movieId }) => {
  const [userRating, setUserRating] = useState(0);
  const [ratingComment, setRatingComment] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [stats, setStats] = useState({ averageRating: 0, totalRatings: 0, distribution: {} });
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [sortBy, setSortBy] = useState('recent');
  const [showSpoilers, setShowSpoilers] = useState(false);
  const [editingReview, setEditingReview] = useState(null);
  const [userReview, setUserReview] = useState(null);

  useEffect(() => {
    fetchReviews();
    fetchUserReview();
  }, [movieId, currentPage, sortBy]);

  const fetchReviews = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMovieReviews(movieId, currentPage, 10, sortBy);

      setReviews(data.data || []);
      setTotalPages(data.total_pages || 1);

      // Calculate stats
      const distribution = {};
      let total = 0;
      let sum = 0;
      (data.data || []).forEach(r => {
        const ratingValue = parseFloat(r.rating) || 0;
        const stars = Math.round(ratingValue);
        if (stars > 0) {
          distribution[stars] = (distribution[stars] || 0) + 1;
          total += 1;
          sum += ratingValue;
        }
      });
      setStats({
        averageRating: total ? (sum / total).toFixed(1) : 0,
        totalRatings: total,
        distribution,
      });
    } catch (err) {
      console.error('Error fetching reviews:', err);
      setError('Không thể tải đánh giá.');
    } finally {
      setLoading(false);
    }
  };

  const fetchUserReview = async () => {
    try {
      const data = await getUserReview(movieId);

      // Handle both paginated and non-paginated response formats
      const reviews = data.results || data.data || [];

      if (reviews.length > 0) {
        setUserReview(reviews[0]);
        setUserRating(parseFloat(reviews[0].rating) || 0);
        setRatingComment(reviews[0].content || '');
      } else {
        setUserReview(null);
      }
    } catch (err) {
      console.log('No user review found');
      setUserReview(null);
    }
  };

  const handleSubmitRating = async () => {
    if (userRating > 0 && ratingComment.trim().length >= 10) {
      try {
        const reviewData = {
          title: '',
          content: ratingComment.trim(),
          rating: userRating,
          is_public: true,
          is_spoiler: false,
        };

        if (userReview && userReview.id) {
          await updateReview(userReview.id, reviewData);
        } else {
          await submitMovieReview(movieId, reviewData);
        }

        setUserRating(0);
        setRatingComment('');
        fetchReviews();
        fetchUserReview();
      } catch (err) {
        console.error('Error submitting review:', err);
        setError('Không thể gửi đánh giá. Vui lòng thử lại.');
      }
    }
  };

  const handleVoteReview = async (reviewId, voteType) => {
    try {
      const result = await voteOnReview(reviewId, voteType);

      // Update local review state
      setReviews(prev =>
        prev.map(review =>
          review.id === reviewId
            ? {
                ...review,
                helpful_votes: result.helpful_votes,
                total_votes: result.total_votes,
                user_vote: result.user_vote,
              }
            : review
        )
      );
    } catch (err) {
      console.error('Error voting on review:', err);
    }
  };

  const handleDeleteReview = async reviewId => {
    if (window.confirm('Bạn có chắc muốn xóa đánh giá này?')) {
      try {
        await deleteReview(reviewId);
        fetchReviews();
        if (userReview && userReview.id === reviewId) {
          setUserReview(null);
          setUserRating(0);
          setRatingComment('');
        }
      } catch (err) {
        console.error('Error deleting review:', err);
        setError('Không thể xóa đánh giá.');
      }
    }
  };

  const handleEditReview = review => {
    setEditingReview(review);
    setUserRating(parseFloat(review.rating) || 0);
    setRatingComment(review.content || '');
  };

  const handleSortChange = newSort => {
    setSortBy(newSort);
    setCurrentPage(1);
  };

  const getPlaceholderText = rating => {
    const placeholders = {
      5: 'Phim tuyệt vời! Hãy chia sẻ những điều bạn thích nhất về bộ phim này...',
      4: 'Phim hay! Điều gì khiến bạn ấn tượng nhất?',
      3: 'Phim ổn. Bạn nghĩ gì về nội dung và cách thể hiện?',
      2: 'Có vẻ phim không hợp với bạn. Điều gì khiến bạn thất vọng?',
      1: 'Phim không hay. Hãy chia sẻ lý do tại sao bạn không thích...',
    };
    return (
      placeholders[rating] ||
      'Chia sẻ cảm nhận chi tiết của bạn về bộ phim này (ít nhất 10 ký tự)...'
    );
  };

  const getPercentage = count => {
    return stats.totalRatings ? ((count / stats.totalRatings) * 100).toFixed(1) : 0;
  };

  if (loading) return <div className="text-center text-gray-400">Đang tải đánh giá...</div>;
  if (error) return <div className="text-center text-red-400">{error}</div>;

  return (
    <div className="space-y-6">
      {/* Rating Overview */}
      <div className="rounded-lg bg-gray-800/50 p-6">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {/* Average Rating */}
          <div className="text-center">
            <div className="mb-2 text-4xl font-bold text-white">{stats.averageRating}</div>
            <StarRating rating={parseFloat(stats.averageRating) || 0} size={24} />
            <p className="mt-2 text-sm text-gray-400">
              {stats.totalRatings.toLocaleString()} đánh giá
            </p>
          </div>

          {/* Rating Distribution */}
          <div className="space-y-2">
            {[5, 4, 3, 2, 1].map(stars => {
              const emotionLabels = {
                5: 'Xuất sắc',
                4: 'Hay',
                3: 'Bình thường',
                2: 'Tệ',
                1: 'Rất tệ',
              };

              const emotionColors = {
                5: 'text-emerald-400',
                4: 'text-green-400',
                3: 'text-yellow-400',
                2: 'text-orange-400',
                1: 'text-red-400',
              };

              return (
                <div key={stars} className="flex items-center gap-3">
                  <div className="flex w-20 items-center gap-1">
                    <span className="text-sm text-gray-300">{stars}</span>
                    <Star size={14} className="fill-yellow-400 text-yellow-400" />
                  </div>
                  <div className="h-2 flex-1 rounded-full bg-gray-700">
                    <div
                      className="h-2 rounded-full bg-yellow-400 transition-all duration-300"
                      style={{ width: `${getPercentage(stats.distribution[stars] || 0)}%` }}
                    />
                  </div>
                  <span className="w-12 text-right text-xs text-gray-400">
                    {getPercentage(stats.distribution[stars] || 0)}%
                  </span>
                  <span className={`w-20 text-left text-xs font-medium ${emotionColors[stars]}`}>
                    {emotionLabels[stars]}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* User Rating Form */}
      <div className="rounded-lg bg-gray-800/50 p-4">
        <h3 className="mb-4 font-medium text-white">
          {userReview ? 'Cập nhật đánh giá' : 'Đánh giá phim này'}
        </h3>

        <div className="space-y-4">
          <div className="pb-2">
            <label className="mb-2 block text-sm text-gray-300">Số sao của bạn:</label>
            <div className="flex min-h-[80px] flex-col items-center">
              <StarRating
                rating={userRating}
                onRatingChange={setUserRating}
                editable={true}
                size={28}
                showLabel={true}
              />
              <div className="mt-2 flex h-[20px] items-center">
                {!userRating && (
                  <p className="text-xs italic text-gray-500 transition-opacity duration-200">
                    Hover để xem mức độ đánh giá
                  </p>
                )}
              </div>
            </div>
          </div>

          <div>
            <label className="mb-2 block text-sm text-gray-300">
              Nhận xét (bắt buộc, ít nhất 10 ký tự):
            </label>
            <textarea
              value={ratingComment}
              onChange={e => setRatingComment(e.target.value)}
              placeholder={getPlaceholderText(userRating)}
              className="w-full resize-none rounded-lg bg-gray-700 p-3 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500"
              rows="3"
              maxLength={500}
            />
            <div className="mt-2 flex items-center justify-between">
              <div className="flex flex-col">
                <span className="text-xs text-gray-400">{ratingComment.length} / 500</span>
                {ratingComment.length > 0 && ratingComment.length < 10 && (
                  <span className="text-xs text-red-400">Nhận xét phải có ít nhất 10 ký tự</span>
                )}
              </div>
              <button
                onClick={handleSubmitRating}
                disabled={userRating === 0 || ratingComment.trim().length < 10}
                className="flex items-center gap-2 rounded-lg bg-yellow-500 px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-yellow-600 disabled:cursor-not-allowed disabled:bg-gray-600"
              >
                <Star size={16} />
                {userReview ? 'Cập nhật' : 'Gửi đánh giá'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Review Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <h3 className="font-medium text-white">Đánh giá từ người dùng</h3>

          {/* Sort Options */}
          <div className="flex items-center gap-2">
            <Filter size={16} className="text-gray-400" />
            <select
              value={sortBy}
              onChange={e => handleSortChange(e.target.value)}
              className="rounded bg-gray-700 px-3 py-1 text-sm text-white focus:outline-none focus:ring-2 focus:ring-yellow-500"
            >
              <option value="recent">Mới nhất</option>
              <option value="rating">Đánh giá cao</option>
              <option value="helpful">Hữu ích</option>
            </select>
          </div>
        </div>

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

      {/* Review List */}
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

                    {review.content && (
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
                    )}

                    {/* Review Actions */}
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
                      onEdit={handleEditReview}
                      onDelete={reviewId => {
                        fetchReviews();
                        if (userReview && userReview.id === reviewId) {
                          setUserReview(null);
                          setUserRating(0);
                          setRatingComment('');
                        }
                      }}
                    />
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center text-gray-400">Chưa có đánh giá nào cho phim này.</div>
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

export default RatingTab;
