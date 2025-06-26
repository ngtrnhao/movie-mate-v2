import { motion } from 'framer-motion';
import { MessageSquare, Flame, Star } from 'lucide-react';

const HotMovieCard = ({ movie }) => {
  const renderStars = rating => {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;
    const emptyStars = 5 - Math.ceil(rating);

    return (
      <div className="flex items-center gap-0.5">
        {[...Array(fullStars)].map((_, i) => (
          <Star key={i} className="h-3 w-3 fill-yellow-400 text-yellow-400" />
        ))}
        {hasHalfStar && <Star className="h-3 w-3 fill-yellow-400/50 text-yellow-400" />}
        {[...Array(emptyStars)].map((_, i) => (
          <Star key={i} className="h-3 w-3 text-gray-600" />
        ))}
        <span className="ml-1 text-xs text-gray-400">{rating}</span>
      </div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{
        scale: 1.02,
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.3)',
      }}
      className="relative rounded-xl border border-gray-700 bg-gray-800 p-4 transition-all duration-300"
    >
      {/* Trending Badge */}
      {movie.trending && (
        <motion.div
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          className="absolute -right-2 -top-2 z-10 flex items-center gap-1 rounded-full bg-red-500 px-2 py-1 text-xs font-medium text-white"
        >
          <Flame className="h-3 w-3" />
          Hot
        </motion.div>
      )}

      <div className="flex gap-3">
        {/* Movie Poster */}
        <motion.div whileHover={{ scale: 1.05 }} className="flex-shrink-0">
          <img src={movie.poster} alt={movie.title} className="h-24 w-16 rounded-lg object-cover" />
        </motion.div>

        {/* Movie Info */}
        <div className="flex-1 space-y-2">
          <div>
            <h3 className="line-clamp-1 font-semibold text-white">{movie.title}</h3>
            <p className="text-xs text-gray-400">{movie.year}</p>
          </div>

          {/* Genres */}
          <div className="flex flex-wrap gap-1">
            {movie.genres.slice(0, 2).map(genre => (
              <span
                key={genre}
                className="rounded-full bg-gray-700 px-2 py-1 text-xs text-gray-300"
              >
                {genre}
              </span>
            ))}
          </div>

          {/* Rating */}
          {renderStars(movie.rating)}

          {/* Comment Count */}
          <div className="flex items-center gap-1 text-pink-400">
            <MessageSquare className="h-3 w-3" />
            <span className="text-xs font-medium">{movie.commentCount}</span>
          </div>
        </div>
      </div>

      {/* Latest Comment Preview */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="mt-3 rounded-lg bg-gray-700/50 p-2"
      >
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <div className="h-2 w-2 rounded-full bg-green-500"></div>
          <span className="font-medium text-gray-300">{movie.latestComment.user}</span>
          <span>• {movie.latestComment.timeAgo}</span>
        </div>
        <p className="mt-1 line-clamp-2 text-xs text-gray-300">"{movie.latestComment.text}"</p>
      </motion.div>

      {/* Action Button */}
      <motion.button
        whileHover={{
          backgroundColor: '#DC2626',
          scale: 1.02,
        }}
        whileTap={{ scale: 0.98 }}
        className="mt-3 w-full rounded-lg bg-red-600 py-2 text-xs font-medium text-white transition-colors"
      >
        💬 Xem thêm bình luận
      </motion.button>
    </motion.div>
  );
};

export default HotMovieCard;
