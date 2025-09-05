import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Heart, MessageCircle, Star, Verified } from 'lucide-react';

const FeaturedCommentsSlider = ({ comments }) => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);

  // Group comments into slides (3 comments per slide)
  const commentsPerSlide = 3;
  const totalSlides = Math.ceil(comments.length / commentsPerSlide);

  const getCommentsForSlide = slideIndex => {
    const startIndex = slideIndex * commentsPerSlide;
    const endIndex = startIndex + commentsPerSlide;
    return comments.slice(startIndex, endIndex);
  };

  // Auto slide every 6 seconds
  useEffect(() => {
    if (!isAutoPlaying) return;

    const interval = setInterval(() => {
      setCurrentSlide(prev => (prev + 1) % totalSlides);
    }, 6000);

    return () => clearInterval(interval);
  }, [isAutoPlaying, totalSlides]);

  const handlePrevSlide = () => {
    setCurrentSlide(prev => (prev - 1 + totalSlides) % totalSlides);
    setIsAutoPlaying(false);
  };

  const handleNextSlide = () => {
    setCurrentSlide(prev => (prev + 1) % totalSlides);
    setIsAutoPlaying(false);
  };

  const handleDotClick = index => {
    setCurrentSlide(index);
    setIsAutoPlaying(false);
  };

  const currentComments = getCommentsForSlide(currentSlide);

  return (
    <div className="relative w-full">
      {/* Slider Container */}
      <div className="relative overflow-hidden rounded-2xl border border-gray-600 bg-gradient-to-br from-yellow-900/30 via-gray-800/50 to-gray-900/70 p-6 backdrop-blur-sm">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentSlide}
            initial={{ opacity: 0, x: 100 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -100 }}
            transition={{ duration: 0.5, ease: 'easeInOut' }}
            className="grid grid-cols-1 gap-4 lg:grid-cols-3"
          >
            {currentComments.map((comment, index) => (
              <motion.div
                key={comment.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="rounded-xl border border-gray-600 bg-gray-800/50 p-4 transition-all hover:bg-gray-800/70"
              >
                {/* Header - User + Movie Poster */}
                <div className="mb-3 flex items-start gap-3">
                  {/* User Avatar */}
                  <div className="shrink-0">
                    <motion.div whileHover={{ scale: 1.1 }} className="relative">
                      <img
                        src={comment.user.avatar}
                        alt={comment.user.name}
                        className="size-12 rounded-full border-2 border-yellow-400 object-cover shadow-lg"
                      />
                      {comment.user.verified && (
                        <motion.div
                          animate={{ scale: [1, 1.2, 1] }}
                          transition={{ duration: 2, repeat: Infinity }}
                          className="absolute -right-1 -top-1 rounded-full bg-blue-500 p-1"
                        >
                          <Verified className="size-2 text-white" />
                        </motion.div>
                      )}
                    </motion.div>
                  </div>

                  {/* Movie Poster */}
                  <div className="shrink-0">
                    <motion.div whileHover={{ scale: 1.05 }} className="relative">
                      <img
                        src={comment.moviePoster}
                        alt={comment.movie}
                        className="h-16 w-12 rounded-lg border border-gray-600 object-cover shadow-lg"
                      />
                      <div className="absolute inset-0 rounded-lg bg-gradient-to-t from-black/50 to-transparent" />
                    </motion.div>
                  </div>

                  {/* User + Movie Info */}
                  <div className="min-w-0 flex-1">
                    <div className="mb-1 flex items-center gap-2">
                      <h4 className="truncate text-sm font-semibold text-white">
                        {comment.user.name}
                      </h4>
                      <div className="rounded-full bg-yellow-500/20 px-2 py-0.5">
                        <span className="text-xs font-medium text-yellow-400">
                          {comment.user.badge}
                        </span>
                      </div>
                    </div>

                    <h3 className="mb-1 text-sm font-bold text-blue-400">{comment.movie}</h3>

                    {/* Rating */}
                    <div className="flex items-center gap-1">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          className={`size-3 ${
                            i < comment.rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-500'
                          }`}
                        />
                      ))}
                      <span className="ml-1 text-xs font-medium text-yellow-400">
                        {comment.rating}/5
                      </span>
                    </div>
                  </div>
                </div>

                {/* Comment Text */}
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.3 + index * 0.1 }}
                  className="mb-3 line-clamp-3 text-sm leading-relaxed text-gray-200"
                >
                  "{comment.text}"
                </motion.p>

                {/* Stats Footer */}
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-3">
                    <motion.div
                      whileHover={{ scale: 1.1 }}
                      className="flex items-center gap-1 text-pink-400"
                    >
                      <Heart className="size-3 fill-current" />
                      <span className="font-medium">{comment.likes.toLocaleString()}</span>
                    </motion.div>

                    <div className="flex items-center gap-1 text-blue-400">
                      <MessageCircle className="size-3" />
                      <span className="font-medium">{comment.replies}</span>
                    </div>
                  </div>

                  <span className="text-gray-500">{comment.timeAgo}</span>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </AnimatePresence>

        {/* Navigation Buttons */}
        <motion.button
          whileHover={{ scale: 1.1, backgroundColor: 'rgba(0, 0, 0, 0.8)' }}
          whileTap={{ scale: 0.9 }}
          onClick={handlePrevSlide}
          className="absolute left-2 top-1/2 -translate-y-1/2 rounded-full bg-black/50 p-2 text-white backdrop-blur-sm transition-all hover:bg-black/70"
        >
          <ChevronLeft className="size-5" />
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.1, backgroundColor: 'rgba(0, 0, 0, 0.8)' }}
          whileTap={{ scale: 0.9 }}
          onClick={handleNextSlide}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full bg-black/50 p-2 text-white backdrop-blur-sm transition-all hover:bg-black/70"
        >
          <ChevronRight className="size-5" />
        </motion.button>

        {/* Sparkle Effects */}
        <motion.div
          animate={{
            opacity: [0.4, 1, 0.4],
            scale: [1, 1.2, 1],
          }}
          transition={{ duration: 3, repeat: Infinity }}
          className="absolute right-4 top-4 text-2xl"
        >
          ✨
        </motion.div>

        <motion.div
          animate={{
            opacity: [0.6, 1, 0.6],
            scale: [1, 1.1, 1],
          }}
          transition={{ duration: 2.5, repeat: Infinity, delay: 1 }}
          className="absolute bottom-4 left-4 text-xl"
        >
          💫
        </motion.div>
      </div>

      {/* Dots Indicator */}
      <div className="mt-4 flex justify-center gap-2">
        {Array.from({ length: totalSlides }).map((_, index) => (
          <motion.button
            key={index}
            whileHover={{ scale: 1.2 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => handleDotClick(index)}
            className={`h-2 w-8 rounded-full transition-all ${
              index === currentSlide
                ? 'bg-yellow-400 shadow-lg shadow-yellow-400/50'
                : 'bg-gray-600 hover:bg-gray-500'
            }`}
          />
        ))}
      </div>

      {/* Auto-play indicator */}
      {isAutoPlaying && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="absolute left-2 top-2"
        >
          <div className="flex items-center gap-1 rounded-full bg-green-500/20 px-2 py-1">
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
              className="size-2 rounded-full bg-green-400"
            />
            <span className="text-xs text-green-400">AUTO</span>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default FeaturedCommentsSlider;
