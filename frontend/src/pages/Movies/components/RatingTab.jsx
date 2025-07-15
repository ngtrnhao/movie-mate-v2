import { useState, useEffect } from 'react';
import { Star, Filter, AlertTriangle, Eye, EyeOff } from 'lucide-react';
import { useSelector } from 'react-redux';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  getMovieReviews,
  submitMovieReview,
  voteOnReview,
  updateReview,
  deleteReview,
  getUserReview,
} from '../../../api/movieService';
import ReviewActions from '../../../components/common/ReviewActions';
import ReplySection from '../../../components/common/ReplySection';
import { useSpoilerDetection } from '../../../hooks/useSpoilerDetection';
import SpoilerDetectionAlert from '../../../components/common/SpoilerDetectionAlert';
import ModerationNotification from '../../../components/common/ModerationNotification';
import SpoilerBadge from '../../../components/common/SpoilerBadge';

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
  const navigate = useNavigate();
  const location = useLocation();
  const isAuthenticated = useSelector(state => state.auth.isAuthenticated);
  const [userRating, setUserRating] = useState(0);
  const [ratingComment, setRatingComment] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [stats, setStats] = useState({ averageRating: 0, totalRatings: 0, distribution: {} });
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [sortBy, setSortBy] = useState('recent');
  const [revealedSpoilers, setRevealedSpoilers] = useState(new Set()); // Track individually revealed spoiler reviews
  const [editingReview, setEditingReview] = useState(null);
  const [editingContent, setEditingContent] = useState('');
  const [editingRating, setEditingRating] = useState(0);
  const [editingSpoiler, setEditingSpoiler] = useState(false);
  const [userReview, setUserReview] = useState(null);
  const [isSpoiler, setIsSpoiler] = useState(false);
  const [showRejectedReviews, setShowRejectedReviews] = useState(false); // Toggle hiển thị review bị từ chối

  // Spoiler detection hook
  const {
    isAnalyzing,
    detectionResult,
    error: spoilerError,
    analyzeContentDebounced,
    clearAnalysis,
    shouldAutoMark,
    shouldShowWarning,
    getAdvancedClassification,
  } = useSpoilerDetection('vi', ''); // Default to Vietnamese

  // Get current classification for background processing
  const currentResult = detectionResult || null;
  const reviewClassification = getAdvancedClassification(currentResult, ratingComment);

  // Auto-hide moderation notification after 5 seconds
  const [showModerationNotification, setShowModerationNotification] = useState(false);

  useEffect(() => {
    if (reviewClassification?.action === 'moderation_required' && detectionResult) {
      setShowModerationNotification(true);
      const timer = setTimeout(() => {
        setShowModerationNotification(false);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [reviewClassification?.action, detectionResult]);

  useEffect(() => {
    fetchReviews();
    if (isAuthenticated) {
      fetchUserReview();
    }
    // Reset revealed spoilers when page or sort changes
    setRevealedSpoilers(new Set());
  }, [movieId, currentPage, sortBy, isAuthenticated]);

  const handleAuthRequired = () => {
    const returnPath = {
      pathname: location.pathname,
      search: location.search,
    };
    navigate('/login', { state: { from: returnPath } });
  };

  const fetchReviews = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMovieReviews(movieId, currentPage, 10, sortBy, true);

      setReviews(data.data || []);
      setTotalPages(data.total_pages || 1);

      // Use rating distribution from backend if available, otherwise calculate from reviews
      let distribution = {};
      let total = 0;
      let sum = 0;

      if (data.rating_distribution && Object.keys(data.rating_distribution).length > 0) {
        // Use backend rating distribution
        distribution = data.rating_distribution;
        total = data.total_ratings || 0;
        sum = (data.average_rating || 0) * total;
      } else {
        // Calculate from reviews (fallback)
        (data.data || []).forEach(r => {
          const ratingValue = parseFloat(r.rating) || 0;
          const stars = Math.round(ratingValue);
          if (stars > 0) {
            distribution[stars] = (distribution[stars] || 0) + 1;
            total += 1;
            sum += ratingValue;
          }
        });
      }

      setStats({
        averageRating: data.average_rating || (total ? (sum / total).toFixed(1) : 0),
        totalRatings: data.total_ratings || total,
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
    if (!isAuthenticated) return;

    try {
      const data = await getUserReview(movieId);
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
    if (!isAuthenticated) {
      handleAuthRequired();
      return;
    }

    if (userRating > 0 && ratingComment.trim().length >= 10) {
      try {
        const reviewData = {
          title: '',
          content: ratingComment.trim(),
          rating: userRating,
          is_public: true,
          is_spoiler: isSpoiler || shouldAutoMark,
        };
        if (isSpoiler || shouldAutoMark) {
          reviewData.is_approved = false;
        }
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
    if (!isAuthenticated) {
      handleAuthRequired();
      return;
    }

    try {
      const result = await voteOnReview(reviewId, voteType);
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
    if (!isAuthenticated) {
      handleAuthRequired();
      return;
    }

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
    if (!isAuthenticated) {
      handleAuthRequired();
      return;
    }

    setEditingReview(review);
    setEditingContent(review.content || '');
    setEditingRating(parseFloat(review.rating) || 0);
    setEditingSpoiler(review.is_spoiler || false);
  };

  const handleCancelEdit = () => {
    setEditingReview(null);
    setEditingContent('');
    setEditingRating(0);
    setEditingSpoiler(false);
  };

  const handleSaveEdit = async () => {
    if (!editingReview || !editingContent.trim() || editingContent.length < 10) {
      return;
    }

    try {
      const reviewData = {
        title: '',
        content: editingContent.trim(),
        rating: editingRating,
        is_public: true,
        is_spoiler: editingSpoiler,
      };

      await updateReview(editingReview.id, reviewData);

      // Update the review in the list
      setReviews(prev =>
        prev.map(r =>
          r.id === editingReview.id
            ? {
                ...r,
                content: editingContent.trim(),
                rating: editingRating,
                is_spoiler: editingSpoiler,
              }
            : r
        )
      );

      // Update user review if it's the same
      if (userReview && userReview.id === editingReview.id) {
        setUserReview(prev => ({
          ...prev,
          content: editingContent.trim(),
          rating: editingRating,
          is_spoiler: editingSpoiler,
        }));
      }

      handleCancelEdit();
    } catch (err) {
      console.error('Error updating review:', err);
      setError('Không thể cập nhật đánh giá. Vui lòng thử lại.');
    }
  };

  const handleSortChange = newSort => {
    setSortBy(newSort);
    setCurrentPage(1);
    setRevealedSpoilers(new Set()); // Clear revealed spoilers when sort changes
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

  // Filter reviews based on moderation status only (always show spoiler reviews)
  const filteredReviews = showRejectedReviews
    ? reviews // Show all reviews including rejected ones
    : reviews.filter(review => review.is_approved !== false); // Hide rejected reviews

  // Check if there are rejected reviews
  const rejectedReviewsCount = reviews.filter(review => review.is_approved === false).length;

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

        {isAuthenticated ? (
          <div className="space-y-3">
            <StarRating
              rating={userRating}
              onRatingChange={setUserRating}
              editable={true}
              size={24}
              showLabel={true}
            />
            <textarea
              value={ratingComment}
              onChange={e => {
                const newContent = e.target.value;
                setRatingComment(newContent);

                // Trigger spoiler detection on content change
                if (newContent.trim().length >= 10) {
                  analyzeContentDebounced(newContent);
                } else {
                  clearAnalysis();
                }
              }}
              placeholder={getPlaceholderText(userRating)}
              className="w-full resize-none rounded-lg bg-gray-700 p-3 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500"
              rows="3"
              maxLength={500}
            />

            {/* Spoiler Detection Alert - Only show for user confirmation */}
            {reviewClassification?.action === 'user_confirmation' && detectionResult && (
              <SpoilerDetectionAlert
                detectionResult={detectionResult}
                isAnalyzing={isAnalyzing}
                onMarkAsSpoiler={() => setIsSpoiler(true)}
                onDismiss={clearAnalysis}
                onReviewContent={() => {
                  // Focus back to textarea for review
                  const textarea = document.querySelector('textarea');
                  if (textarea) textarea.focus();
                }}
              />
            )}

            {/* Moderation Notification - Show briefly when review is sent to moderation */}
            {showModerationNotification &&
              reviewClassification?.action === 'moderation_required' && (
                <ModerationNotification
                  classification={reviewClassification}
                  onDismiss={() => setShowModerationNotification(false)}
                />
              )}
            <div className="flex items-center justify-between">
              <div className="flex flex-col">
                <span className="text-xs text-gray-400">{ratingComment.length} / 500</span>
                {ratingComment.length > 0 && ratingComment.length < 10 && (
                  <span className="text-xs text-red-400">Đánh giá phải có ít nhất 10 ký tự</span>
                )}
              </div>

              {/* Spoiler Toggle */}
              <div className="flex items-center gap-x-2">
                <button
                  type="button"
                  aria-pressed={isSpoiler}
                  onClick={() => setIsSpoiler(v => !v)}
                  className={`relative inline-flex h-6 w-12 items-center rounded-full transition-colors focus:outline-none ${
                    isSpoiler ? 'bg-orange-500' : 'bg-gray-400'
                  }`}
                >
                  <span
                    className={`inline-block size-5 rounded-full bg-white shadow transition-transform ${
                      isSpoiler ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
                <label
                  htmlFor="spoiler-toggle"
                  className="flex cursor-pointer items-center text-sm font-semibold text-orange-500"
                  onClick={() => setIsSpoiler(v => !v)}
                >
                  <AlertTriangle className="mr-1 size-4" /> Chứa spoiler
                </label>
                <span className="text-xs text-orange-400">(Review sẽ bị ẩn khỏi công khai)</span>
              </div>
              <button
                onClick={handleSubmitRating}
                disabled={!userRating || !ratingComment.trim() || ratingComment.length < 10}
                className="flex items-center gap-2 rounded-lg bg-yellow-500 px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-yellow-600 disabled:cursor-not-allowed disabled:bg-gray-600"
              >
                <Star size={16} />
                {userReview ? 'Cập nhật đánh giá' : 'Gửi đánh giá'}
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center space-y-4 py-6">
            <p className="text-center text-gray-400">Bạn cần đăng nhập để đánh giá phim này</p>
            <button
              onClick={handleAuthRequired}
              className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
            >
              Đăng nhập ngay
            </button>
          </div>
        )}
      </div>

      {/* Review Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <h3 className="font-medium text-white">
            Đánh giá từ người dùng
            <span className="ml-2 text-sm text-gray-400">
              ({filteredReviews.length}/{reviews.length})
              {rejectedReviewsCount > 0 && (
                <span className="ml-2 text-red-400">({rejectedReviewsCount} bị từ chối)</span>
              )}
            </span>
          </h3>

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

        <div className="flex items-center gap-2">
          {/* Show/Hide Rejected Reviews Toggle */}
          {rejectedReviewsCount > 0 && (
            <button
              onClick={() => setShowRejectedReviews(!showRejectedReviews)}
              className={`flex items-center gap-2 rounded-lg px-3 py-1 text-sm transition-colors ${
                showRejectedReviews
                  ? 'bg-red-500/20 text-red-400'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {showRejectedReviews ? <EyeOff size={16} /> : <Eye size={16} />}
              {showRejectedReviews ? 'Ẩn' : 'Hiện'} Review bị từ chối ({rejectedReviewsCount})
            </button>
          )}
        </div>
      </div>

      {/* Review List */}
      <div className="space-y-4">
        {filteredReviews.length > 0 ? (
          filteredReviews.map(review => {
            const isSpoiler = review.is_spoiler;
            const shouldBlur = isSpoiler && !revealedSpoilers.has(review.id);

            // Check moderation status
            const isRejected = review.is_approved === false;
            const isApproved = review.is_approved === true;
            const isPending = review.is_approved === null || review.is_approved === undefined;

            return (
              <div
                key={review.id}
                className={`rounded-lg border-l-4 p-4 ${
                  isRejected
                    ? 'border-red-500 bg-red-900/20'
                    : isApproved
                      ? 'border-green-500 bg-green-900/20'
                      : isPending
                        ? 'border-yellow-500 bg-yellow-900/20'
                        : 'border-gray-600 bg-gray-800/30'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="relative">
                    <img
                      src={review.reviewer_avatar || '/api/placeholder/40/40'}
                      alt={review.reviewer_username || 'User'}
                      className="size-10 rounded-full object-cover"
                      onError={e => {
                        e.target.src = `https://ui-avatars.com/api/?name=${review.reviewer_name || 'User'}&background=random&color=fff&size=40`;
                      }}
                    />
                    {/* {review.is_verified_reviewer && (
                      <span className="absolute -right-1 -top-1 text-xs text-yellow-400">⚡</span>
                    )} */}
                  </div>

                  <div className="flex-1">
                    <div className="mb-1 flex items-center gap-2">
                      <span className="font-medium text-white">
                        {review.reviewer_name || 'User'}
                      </span>
                      {/* {review.is_verified_reviewer && (
                        <span className="text-xs text-yellow-400">⚡</span>
                      )} */}
                      <span className="text-xs text-gray-400">
                        {new Date(review.created_at).toLocaleDateString('vi-VN', {
                          day: '2-digit',
                          month: '2-digit',
                          year: 'numeric',
                        })}
                      </span>
                      <SpoilerBadge isSpoiler={isSpoiler} size="sm" />
                    </div>

                    {/* Show rating if available */}
                    {review.rating && (
                      <div className="mb-2 flex items-center gap-2">
                        <StarRating rating={parseFloat(review.rating) || 0} size={14} />
                        <span className="text-xs text-gray-400">({review.rating}/5)</span>
                      </div>
                    )}

                    {review.content && (
                      <>
                        {editingReview?.id === review.id ? (
                          // Edit Mode
                          <div className="mb-3 space-y-5 pt-5">
                            {/* Rating Edit */}
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-sm text-gray-400">Đánh giá:</span>
                              <StarRating
                                rating={editingRating}
                                onRatingChange={setEditingRating}
                                editable={true}
                                size={20}
                                showLabel={false}
                              />
                            </div>

                            {/* Content Edit */}
                            <textarea
                              value={editingContent}
                              onChange={e => setEditingContent(e.target.value)}
                              placeholder="Chia sẻ cảm nhận của bạn..."
                              className="w-full resize-none rounded-lg bg-gray-700 p-3 pb-10 text-sm text-white focus:outline-none focus:ring-2 focus:ring-yellow-500"
                              rows="3"
                              maxLength={500}
                            />

                            {/* Character Count */}
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-gray-400">
                                {editingContent.length} / 500
                              </span>
                              {editingContent.length > 0 && editingContent.length < 10 && (
                                <span className="text-xs text-red-400">
                                  Đánh giá phải có ít nhất 10 ký tự
                                </span>
                              )}
                            </div>

                            {/* Spoiler Toggle */}
                            <div className="flex items-center gap-x-2">
                              <button
                                type="button"
                                aria-pressed={editingSpoiler}
                                onClick={() => setEditingSpoiler(v => !v)}
                                className={`relative inline-flex h-6 w-12 items-center rounded-full transition-colors focus:outline-none ${
                                  editingSpoiler ? 'bg-orange-500' : 'bg-gray-400'
                                }`}
                              >
                                <span
                                  className={`inline-block size-5 rounded-full bg-white shadow transition-transform ${
                                    editingSpoiler ? 'translate-x-6' : 'translate-x-1'
                                  }`}
                                />
                              </button>
                              <label className="flex cursor-pointer items-center text-sm font-semibold text-orange-500">
                                <AlertTriangle className="mr-1 size-4" /> Chứa spoiler
                              </label>
                            </div>

                            {/* Edit Actions */}
                            <div className="flex items-center gap-2">
                              <button
                                onClick={handleSaveEdit}
                                disabled={!editingContent.trim() || editingContent.length < 10}
                                className="flex items-center gap-2 rounded-lg bg-yellow-500 px-3 py-1 text-sm font-medium text-black transition-colors hover:bg-yellow-600 disabled:cursor-not-allowed disabled:bg-gray-600"
                              >
                                Lưu
                              </button>
                              <button
                                onClick={handleCancelEdit}
                                className="flex items-center gap-2 rounded-lg bg-gray-600 px-3 py-1 text-sm font-medium text-white transition-colors hover:bg-gray-700"
                              >
                                Hủy
                              </button>
                            </div>
                          </div>
                        ) : (
                          // View Mode
                          <>
                            <div className={`mb-3 ${shouldBlur ? 'blur-sm' : ''}`}>
                              <p className="text-sm leading-relaxed text-gray-200">
                                {review.content}
                              </p>
                            </div>
                            {shouldBlur && (
                              <div className="mb-3">
                                <button
                                  onClick={() =>
                                    setRevealedSpoilers(prev => new Set([...prev, review.id]))
                                  }
                                  className="text-xs text-yellow-400 hover:text-yellow-300"
                                >
                                  Nhấn để xem spoiler
                                </button>
                              </div>
                            )}
                            {isSpoiler && revealedSpoilers.has(review.id) && (
                              <div className="mb-3">
                                <button
                                  onClick={() =>
                                    setRevealedSpoilers(prev => {
                                      const newSet = new Set(prev);
                                      newSet.delete(review.id);
                                      return newSet;
                                    })
                                  }
                                  className="text-xs text-gray-400 hover:text-gray-300"
                                >
                                  Ẩn spoiler
                                </button>
                              </div>
                            )}
                          </>
                        )}
                      </>
                    )}

                    {/* Moderation Reason for Rejected Reviews */}
                    {isRejected && review.moderation_reason && (
                      <div className="mb-3 rounded-lg border border-red-500/30 bg-red-500/20 p-3">
                        <p className="text-sm text-red-300">
                          <strong>Lý do từ chối:</strong> {review.moderation_reason}
                        </p>
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

                    {/* Reply Section */}
                    <ReplySection
                      review={review}
                      onReplySuccess={(reviewId, reply) => {
                        setReviews(prev =>
                          prev.map(r =>
                            r.id === reviewId ? { ...r, reply_count: (r.reply_count || 0) + 1 } : r
                          )
                        );
                      }}
                    />
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center text-gray-400">
            {showRejectedReviews
              ? 'Chưa có đánh giá nào cho phim này.'
              : 'Chưa có đánh giá được phê duyệt nào cho phim này.'}
            {rejectedReviewsCount > 0 && !showRejectedReviews && (
              <div className="mt-2">
                <button
                  onClick={() => setShowRejectedReviews(true)}
                  className="text-xs text-red-400 underline hover:text-red-300"
                >
                  Hiện {rejectedReviewsCount} review bị từ chối
                </button>
              </div>
            )}
          </div>
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
