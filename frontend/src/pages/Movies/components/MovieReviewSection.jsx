import { useState } from 'react';
import { MessageCircle, Send, ThumbsUp, ThumbsDown, MoreHorizontal, Star } from 'lucide-react';

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

  // Mock rating data
  const ratingStats = {
    averageRating: 4.2,
    totalRatings: 1248,
    distribution: {
      5: 520,
      4: 380,
      3: 200,
      2: 98,
      1: 50,
    },
  };

  const recentRatings = [
    {
      id: 1,
      user: { name: 'Ethereum', avatar: '/api/placeholder/40/40' },
      rating: 5,
      comment: 'Phim hay nhất năm! Cảnh quay rất đẹp và diễn xuất xuất sắc.',
      createdAt: '2 ngày trước',
    },
    {
      id: 2,
      user: { name: 'TheWolf', avatar: '/api/placeholder/40/40' },
      rating: 4,
      comment: 'Nội dung hấp dẫn, nhưng kết thúc hơi vội vàng.',
      createdAt: '3 ngày trước',
    },
    {
      id: 3,
      user: { name: 'MovieLover', avatar: '/api/placeholder/40/40' },
      rating: 3,
      comment: 'Phim oke, xem giải trí được.',
      createdAt: '5 ngày trước',
    },
  ];

  const handleSubmitRating = () => {
    if (userRating > 0) {
      console.log('Submit rating:', { rating: userRating, comment: ratingComment });
      // TODO: Submit to API
    }
  };

  const getPercentage = count => {
    return ((count / ratingStats.totalRatings) * 100).toFixed(1);
  };

  const getPlaceholderText = rating => {
    const placeholders = {
      5: 'Phim tuyệt vời! Hãy chia sẻ những điều bạn thích nhất...',
      4: 'Phim hay! Điều gì khiến bạn ấn tượng?',
      3: 'Phim ổn. Bạn nghĩ gì về nội dung?',
      2: 'Có vẻ phim không hợp với bạn. Điều gì khiến bạn thất vọng?',
      1: 'Phim không hay. Hãy chia sẻ lý do tại sao...',
    };
    return placeholders[rating] || 'Chia sẻ cảm nhận của bạn về bộ phim...';
  };

  return (
    <div className="space-y-6">
      {/* Rating Overview */}
      <div className="rounded-lg bg-gray-800/50 p-6">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {/* Average Rating */}
          <div className="text-center">
            <div className="mb-2 text-4xl font-bold text-white">{ratingStats.averageRating}</div>
            <StarRating rating={ratingStats.averageRating} size={24} />
            <p className="mt-2 text-sm text-gray-400">
              {ratingStats.totalRatings.toLocaleString()} đánh giá
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
                      style={{ width: `${getPercentage(ratingStats.distribution[stars])}%` }}
                    />
                  </div>
                  <span className="w-12 text-right text-xs text-gray-400">
                    {getPercentage(ratingStats.distribution[stars])}%
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
        <h3 className="mb-4 font-medium text-white">Đánh giá phim này</h3>

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
            <label className="mb-2 block text-sm text-gray-300">Nhận xét (tùy chọn):</label>
            <textarea
              value={ratingComment}
              onChange={e => setRatingComment(e.target.value)}
              placeholder={getPlaceholderText(userRating)}
              className="w-full resize-none rounded-lg bg-gray-700 p-3 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500"
              rows="3"
              maxLength={500}
            />
            <div className="mt-2 flex items-center justify-between">
              <span className="text-xs text-gray-400">{ratingComment.length} / 500</span>
              <button
                onClick={handleSubmitRating}
                disabled={userRating === 0}
                className="flex items-center gap-2 rounded-lg bg-yellow-500 px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-yellow-600 disabled:cursor-not-allowed disabled:bg-gray-600"
              >
                <Star size={16} />
                Gửi đánh giá
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Ratings */}
      <div className="space-y-4">
        <h3 className="font-medium text-white">Đánh giá gần đây</h3>
        {recentRatings.map(rating => (
          <div key={rating.id} className="rounded-lg bg-gray-800/30 p-4">
            <div className="flex items-start gap-3">
              <img
                src={rating.user.avatar}
                alt={rating.user.name}
                className="size-10 rounded-full object-cover"
                onError={e => {
                  e.target.src = `https://ui-avatars.com/api/?name=${rating.user.name}&background=random&color=fff&size=40`;
                }}
              />
              <div className="flex-1">
                <div className="mb-2 flex items-center gap-2">
                  <span className="font-medium text-white">{rating.user.name}</span>
                  <StarRating rating={rating.rating} size={16} />
                  <span className="text-xs text-gray-400">{rating.createdAt}</span>
                </div>
                {rating.comment && (
                  <p className="text-sm leading-relaxed text-gray-200">{rating.comment}</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const CommentTab = ({ movieId }) => {
  const [newComment, setNewComment] = useState('');
  const [showMore, setShowMore] = useState(false);

  // Mock comment data
  const reviews = [
    {
      id: 1,
      user: {
        name: 'Ethereum',
        avatar: '/api/placeholder/40/40',
        isVerified: true,
        badge: '⚡',
      },
      createdAt: '17 ngày trước',
      content:
        'Mẹ nó muốn xem phim không có người để lại comment gì thì làm sao mà biết phim có hay không',
      likes: 23,
      dislikes: 2,
      isLiked: false,
      isDisliked: false,
    },
    {
      id: 2,
      user: {
        name: 'TheWolf',
        avatar: '/api/placeholder/40/40',
        isVerified: true,
        badge: '∞',
      },
      createdAt: '18 ngày trước',
      content:
        'Cảnh sát Pháp cũng vô tích sự như cảnh sát Mỹ nhỉ , xong hết mọi việc mới xuất hiện',
      likes: 8,
      dislikes: 1,
      isLiked: false,
      isDisliked: false,
    },
    {
      id: 3,
      user: {
        name: 'Vinh',
        avatar: '/api/placeholder/40/40',
        isVerified: false,
        badge: '⚡',
      },
      createdAt: '19 ngày trước',
      content:
        'Phim đánh đấm ok, nói dung cơ bản để đoán, quen xem phim Mỹ nên phim này nó cứ là la, tình tiết k muốn như phim Mỹ, xem giải trí ok.',
      likes: 15,
      dislikes: 0,
      isLiked: true,
      isDisliked: false,
    },
  ];

  const handleLike = reviewId => {
    console.log('Like review:', reviewId);
  };

  const handleDislike = reviewId => {
    console.log('Dislike review:', reviewId);
  };

  const handleSubmitComment = () => {
    if (newComment.trim()) {
      console.log('Submit comment:', newComment);
      setNewComment('');
    }
  };

  return (
    <div className="space-y-6">
      {/* Comment Input */}
      <div className="rounded-lg bg-gray-800/50 p-4">
        <p className="mb-4 text-sm text-gray-300">
          Vui lòng <span className="cursor-pointer text-yellow-400 hover:underline">đăng nhập</span>{' '}
          để tham gia bình luận.
        </p>

        <div className="flex gap-3">
          <div className="flex-1">
            <textarea
              value={newComment}
              onChange={e => setNewComment(e.target.value)}
              placeholder="Viết bình luận"
              className="w-full resize-none rounded-lg bg-gray-700 p-3 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500"
              rows="3"
              maxLength={1000}
            />
            <div className="mt-2 flex items-center justify-between">
              <span className="text-xs text-gray-400">{newComment.length} / 1000</span>
              <button
                onClick={handleSubmitComment}
                disabled={!newComment.trim()}
                className="flex items-center gap-2 rounded-lg bg-yellow-500 px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-yellow-600 disabled:cursor-not-allowed disabled:bg-gray-600"
              >
                <Send size={16} />
                Gửi
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Comment List */}
      <div className="space-y-4">
        {reviews.slice(0, showMore ? reviews.length : 3).map(review => (
          <div key={review.id} className="rounded-lg bg-gray-800/30 p-4">
            <div className="flex items-start gap-3">
              <div className="relative">
                <img
                  src={review.user.avatar}
                  alt={review.user.name}
                  className="size-10 rounded-full object-cover"
                  onError={e => {
                    e.target.src = `https://ui-avatars.com/api/?name=${review.user.name}&background=random&color=fff&size=40`;
                  }}
                />
                {review.user.isVerified && (
                  <span className="absolute -right-1 -top-1 text-xs">{review.user.badge}</span>
                )}
              </div>

              <div className="flex-1">
                <div className="mb-1 flex items-center gap-2">
                  <span className="font-medium text-white">{review.user.name}</span>
                  {review.user.isVerified && (
                    <span className="text-xs text-yellow-400">{review.user.badge}</span>
                  )}
                  <span className="text-xs text-gray-400">{review.createdAt}</span>
                </div>

                <p className="mb-3 text-sm leading-relaxed text-gray-200">{review.content}</p>

                <div className="flex items-center gap-4">
                  <button
                    onClick={() => handleLike(review.id)}
                    className={`flex items-center gap-1 text-xs transition-colors ${
                      review.isLiked ? 'text-blue-400' : 'text-gray-400 hover:text-gray-300'
                    }`}
                  >
                    <ThumbsUp size={14} />
                    {review.likes > 0 && review.likes}
                  </button>

                  <button
                    onClick={() => handleDislike(review.id)}
                    className={`flex items-center gap-1 text-xs transition-colors ${
                      review.isDisliked ? 'text-red-400' : 'text-gray-400 hover:text-gray-300'
                    }`}
                  >
                    <ThumbsDown size={14} />
                    {review.dislikes > 0 && review.dislikes}
                  </button>

                  <button className="text-xs text-gray-400 hover:text-gray-300">Trả lời</button>

                  <button className="ml-auto text-gray-400 hover:text-gray-300">
                    <MoreHorizontal size={16} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}

        {reviews.length > 3 && (
          <div className="text-center">
            <button
              onClick={() => setShowMore(!showMore)}
              className="text-sm font-medium text-yellow-400 hover:text-yellow-300"
            >
              {showMore ? '△ 1 bình luận' : `▽ ${reviews.length - 3} bình luận khác`}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

const MovieReviewSection = ({ movieId }) => {
  const [activeTab, setActiveTab] = useState('ratings');

  const tabs = [
    { id: 'ratings', label: 'Đánh giá', icon: Star },
    { id: 'comments', label: 'Bình luận', icon: MessageCircle },
  ];

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="flex items-center gap-4">
        <div className="flex gap-2">
          {tabs.map(tab => {
            const IconComponent = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-yellow-500 text-black'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                <IconComponent size={16} />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'ratings' && <RatingTab movieId={movieId} />}
        {activeTab === 'comments' && <CommentTab movieId={movieId} />}
      </div>
    </div>
  );
};

export default MovieReviewSection;
