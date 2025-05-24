import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { Star, ChevronDown, MessageSquare, ThumbsUp, X } from 'lucide-react';
import { useState } from 'react';

const INITIAL_REVIEWS_COUNT = 4;
const LOAD_MORE_COUNT = 4;

const ReviewModal = ({ isOpen, onClose, onSubmit }) => {
  const { t } = useTranslation('movies');
  const [rating, setRating] = useState(0);
  const [review, setReview] = useState('');
  const [hoveredRating, setHoveredRating] = useState(0);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ rating, review });
    setRating(0);
    setReview('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="w-full max-w-2xl rounded-lg bg-gray-800 p-6"
        >
          <div className="mb-6 flex items-center justify-between">
            <h3 className="text-xl font-bold text-white">{t('details.writeYourReview')}</h3>
            <button
              onClick={onClose}
              className="rounded-full p-2 text-gray-400 hover:bg-gray-700 hover:text-white"
            >
              <X className="size-5" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Rating Stars */}
            <div>
              <label className="mb-2 block text-sm text-gray-400">{t('details.yourRating')}</label>
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    onMouseEnter={() => setHoveredRating(star)}
                    onMouseLeave={() => setHoveredRating(0)}
                    className="text-2xl text-gray-600 transition-colors hover:text-yellow-400"
                  >
                    <Star
                      className={`size-8 ${
                        star <= (hoveredRating || rating)
                          ? 'fill-yellow-400 text-yellow-400'
                          : 'text-gray-600'
                      }`}
                    />
                  </button>
                ))}
              </div>
              <p className="mt-2 text-sm text-gray-400">
                {rating === 0 ? t('details.selectRating') : t('details.ratingSelected', { rating })}
              </p>
            </div>

            {/* Review Text */}
            <div>
              <label htmlFor="review" className="mb-2 block text-sm text-gray-400">
                {t('details.yourReview')}
              </label>
              <textarea
                id="review"
                value={review}
                onChange={(e) => setReview(e.target.value)}
                placeholder={t('details.reviewPlaceholder')}
                className="h-32 w-full rounded-md bg-gray-700 p-3 text-white placeholder:text-gray-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
                required
              />
            </div>

            {/* Submit Button */}
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={!rating || !review.trim()}
                className="rounded-md bg-red-600 px-6 py-2 text-white transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {t('details.submitReview')}
              </button>
            </div>
          </form>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

const ReviewSection = ({ reviews }) => {
  const { t } = useTranslation('movies');
  const [visibleCount, setVisibleCount] = useState(INITIAL_REVIEWS_COUNT);
  const [showAllReviews, setShowAllReviews] = useState(false);
  const [sortBy, setSortBy] = useState('newest'); // 'newest' | 'helpful' | 'highest' | 'lowest'
  const [selectedRating, setSelectedRating] = useState(null);
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);

  // Mock data nếu không có reviews
  const displayReviews = reviews || [
    {
      id: 1,
      author: 'John Doe',
      content: "One of the best movies ever made. Christopher Nolan's masterpiece.",
      created_at: '2024-01-01T00:00:00.000Z',
      rating: 5,
      helpful_count: 128,
      reply_count: 15,
    },
    {
      id: 2,
      author: 'Jane Smith',
      content: "Heath Ledger's performance as the Joker is absolutely phenomenal.",
      created_at: '2024-01-02T00:00:00.000Z',
      rating: 4,
      helpful_count: 89,
      reply_count: 8,
    },
    // Thêm nhiều reviews hơn để test
    ...Array(15)
      .fill(null)
      .map((_, index) => ({
        id: index + 3,
        author: `User ${index + 3}`,
        content: `This is a sample review ${index + 3}. The movie was amazing!`,
        created_at: new Date(2024, 0, index + 3).toISOString(),
        rating: Math.floor(Math.random() * 3) + 3,
        helpful_count: Math.floor(Math.random() * 100),
        reply_count: Math.floor(Math.random() * 20),
      })),
  ];

  if (!displayReviews || displayReviews.length === 0) return null;

  // Tính toán thống kê rating
  const ratingStats = displayReviews.reduce(
    (acc, review) => {
      acc.total += review.rating;
      acc.count += 1;
      acc.distribution[review.rating] = (acc.distribution[review.rating] || 0) + 1;
      return acc;
    },
    { total: 0, count: 0, distribution: {} }
  );

  const averageRating = (ratingStats.total / ratingStats.count).toFixed(1);

  // Lọc và sắp xếp reviews
  let filteredReviews = [...displayReviews];

  // Lọc theo rating
  if (selectedRating) {
    filteredReviews = filteredReviews.filter((review) => review.rating === selectedRating);
  }

  // Sắp xếp reviews
  switch (sortBy) {
    case 'newest':
      filteredReviews.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      break;
    case 'helpful':
      filteredReviews.sort((a, b) => b.helpful_count - a.helpful_count);
      break;
    case 'highest':
      filteredReviews.sort((a, b) => b.rating - a.rating);
      break;
    case 'lowest':
      filteredReviews.sort((a, b) => a.rating - b.rating);
      break;
  }

  const visibleReviews = showAllReviews ? filteredReviews : filteredReviews.slice(0, visibleCount);
  const hasMoreReviews = !showAllReviews && visibleCount < filteredReviews.length;

  const handleLoadMore = () => {
    setVisibleCount((prev) => prev + LOAD_MORE_COUNT);
  };

  const handleViewAll = () => {
    setShowAllReviews(true);
  };

  const handleSubmitReview = (reviewData) => {
    // TODO: Gửi review lên server
    console.log('New review:', reviewData);
    // Thêm review mới vào danh sách
    const newReview = {
      id: displayReviews.length + 1,
      author: 'Current User', // TODO: Lấy từ user context
      content: reviewData.review,
      created_at: new Date().toISOString(),
      rating: reviewData.rating,
      helpful_count: 0,
      reply_count: 0,
    };
    displayReviews.unshift(newReview);
  };

  return (
    <section className="relative bg-gray-900 py-8">
      <div className="container mx-auto px-4">
        {/* Rating Overview */}
        <div className="mb-12 rounded-lg bg-gray-800/50 p-6">
          <div className="grid gap-8 md:grid-cols-2">
            {/* Rating Summary */}
            <div>
              <h3 className="mb-4 text-xl font-bold text-white">{t('details.ratingOverview')}</h3>
              <div className="flex items-center gap-4">
                <div className="text-center">
                  <div className="text-4xl font-bold text-white">{averageRating}</div>
                  <div className="flex items-center justify-center gap-1">
                    {[...Array(5)].map((_, index) => (
                      <Star
                        key={index}
                        className={`size-5 ${
                          index < Math.round(averageRating)
                            ? 'fill-yellow-400 text-yellow-400'
                            : 'text-gray-600'
                        }`}
                      />
                    ))}
                  </div>
                  <div className="mt-1 text-sm text-gray-400">
                    {ratingStats.count} {t('details.totalRatings')}
                  </div>
                </div>
                <div className="flex-1">
                  {[5, 4, 3, 2, 1].map((rating) => {
                    const count = ratingStats.distribution[rating] || 0;
                    const percentage = (count / ratingStats.count) * 100;
                    return (
                      <div key={rating} className="mb-2 flex items-center gap-2">
                        <div className="w-12 text-sm text-gray-400">{rating} ★</div>
                        <div className="h-2 flex-1 rounded-full bg-gray-700">
                          <div
                            className="h-full rounded-full bg-yellow-400"
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                        <div className="w-12 text-right text-sm text-gray-400">
                          {Math.round(percentage)}%
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Rating Filter */}
            <div>
              <h3 className="mb-4 text-xl font-bold text-white">{t('details.filterReviews')}</h3>
              <div className="space-y-4">
                <div>
                  <label className="mb-2 block text-sm text-gray-400">{t('details.sortBy')}</label>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="w-full rounded-md bg-gray-700 px-4 py-2 text-white"
                  >
                    <option value="newest">{t('details.newest')}</option>
                    <option value="helpful">{t('details.mostHelpful')}</option>
                    <option value="highest">{t('details.highestRating')}</option>
                    <option value="lowest">{t('details.lowestRating')}</option>
                  </select>
                </div>
                <div>
                  <label className="mb-2 block text-sm text-gray-400">
                    {t('details.filterByRating')}
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {[5, 4, 3, 2, 1].map((rating) => (
                      <button
                        key={rating}
                        onClick={() => setSelectedRating(selectedRating === rating ? null : rating)}
                        className={`flex items-center gap-1 rounded-full px-3 py-1 text-sm ${
                          selectedRating === rating
                            ? 'bg-yellow-400 text-gray-900'
                            : 'bg-gray-700 text-white hover:bg-gray-600'
                        }`}
                      >
                        {rating} ★
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Reviews List */}
        <div className="space-y-6">
          {visibleReviews.map((review) => (
            <motion.div
              key={review.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="group rounded-lg bg-gray-800/50 p-6 transition-all duration-300 hover:bg-gray-800/70"
            >
              {/* Review Header */}
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex size-10 items-center justify-center rounded-full bg-red-600/20 text-lg font-semibold text-red-400">
                    {review.author.charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">{review.author}</h3>
                    <p className="text-sm text-gray-400">
                      {new Date(review.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  {[...Array(5)].map((_, index) => (
                    <Star
                      key={index}
                      className={`size-4 ${
                        index < review.rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-600'
                      }`}
                    />
                  ))}
                </div>
              </div>

              {/* Review Content */}
              <p className="text-gray-300">{review.content}</p>

              {/* Review Actions */}
              <div className="mt-4 flex items-center gap-4 text-sm text-gray-400">
                <button className="flex items-center gap-1 hover:text-white">
                  <ThumbsUp className="size-4" />
                  {review.helpful_count} {t('details.helpful')}
                </button>
                <button className="flex items-center gap-1 hover:text-white">
                  <MessageSquare className="size-4" />
                  {review.reply_count} {t('details.replies')}
                </button>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Action Buttons */}
        <div className="mt-8 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          {hasMoreReviews && (
            <motion.button
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              onClick={handleLoadMore}
              className="group flex items-center gap-2 rounded-md border border-white/20 px-6 py-3 text-sm text-white transition-colors hover:bg-white/10"
            >
              {t('details.loadMore')}
              <ChevronDown className="size-4 transition-transform group-hover:translate-y-1" />
            </motion.button>
          )}

          {showAllReviews ? (
            <motion.button
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              onClick={() => {
                setShowAllReviews(false);
                setVisibleCount(INITIAL_REVIEWS_COUNT);
              }}
              className="group flex items-center gap-2 rounded-md bg-gray-700 px-6 py-3 text-sm text-white transition-colors hover:bg-gray-600"
            >
              {t('details.collapseReviews')}
              <ChevronDown className="size-4 rotate-180 transition-transform group-hover:-translate-y-1" />
            </motion.button>
          ) : (
            <motion.button
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              onClick={handleViewAll}
              className="flex items-center gap-2 rounded-md bg-red-600 px-6 py-3 text-sm text-white transition-colors hover:bg-red-700"
            >
              {t('details.viewAllReviews')}
            </motion.button>
          )}

          <motion.button
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            onClick={() => setIsReviewModalOpen(true)}
            className="flex items-center gap-2 rounded-md border border-white/20 px-6 py-3 text-sm text-white transition-colors hover:bg-white/10"
          >
            <MessageSquare className="size-4" />
            {t('details.writeReview')}
          </motion.button>
        </div>
      </div>

      {/* Review Modal */}
      <ReviewModal
        isOpen={isReviewModalOpen}
        onClose={() => setIsReviewModalOpen(false)}
        onSubmit={handleSubmitReview}
      />
    </section>
  );
};

export default ReviewSection;
