import { memo, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from '../../../i18n/hooks/useTranslation';
import MovieCard from '../movie-card';
import LoadingSpinner from '../../common/LoadingSpinner';
import ErrorMessage from '../../common/ErrorMessage';
import EmptyState from '../../common/EmptyState';
import ImagePreloader from '../../common/ImagePreloader';

// Animation variants - memoize để tránh re-render
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.03, // Giảm delay để load nhanh hơn
    },
  },
  exit: { opacity: 0 },
};

const itemVariants = {
  hidden: { y: 10, opacity: 0 }, // Giảm y offset để ít layout shift
  visible: {
    y: 0,
    opacity: 1,
  },
};

const MovieGrid = memo(
  ({ movies, loading, error, onMovieClick, onTrailerClick, className = '' }) => {
    const { t } = useTranslation('movies');

    // Memoize handlers
    const handleMovieClick = useCallback(
      movie => {
        if (onMovieClick) {
          onMovieClick(movie);
        }
      },
      [onMovieClick]
    );

    // Memoize filtered movies
    const filteredMovies = useMemo(() => {
      return movies || [];
    }, [movies]);

    // Memoize priority images (first 8 movies)
    const priorityImages = useMemo(() => {
      return filteredMovies
        .slice(0, 8)
        .map(movie => movie.poster_path)
        .filter(Boolean);
    }, [filteredMovies]);

    // Loading state
    if (loading) {
      return (
        <div className="flex min-h-[400px] items-center justify-center">
          <LoadingSpinner />
        </div>
      );
    }

    // Error state
    if (error) {
      return (
        <div className="flex min-h-[400px] items-center justify-center">
          <ErrorMessage title={t('errors.loading.title')} message={error} />
        </div>
      );
    }

    // Empty state
    if (!filteredMovies.length) {
      return (
        <div className="flex min-h-[400px] items-center justify-center">
          <EmptyState title={t('empty.title')} message={t('empty.message')} />
        </div>
      );
    }

    return (
      <ImagePreloader images={priorityImages}>
        <AnimatePresence mode="wait">
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className={`grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 ${className}`}
          >
            {filteredMovies.map((movie, index) => (
              <motion.div
                key={movie.id}
                variants={itemVariants}
                whileHover={{ scale: 1.02 }} // Giảm scale để ít layout shift
              >
                <MovieCard
                  movie={movie}
                  index={index} // Truyền index để priority loading
                  onClick={() => handleMovieClick(movie)}
                  onTrailerClick={onTrailerClick}
                />
              </motion.div>
            ))}
          </motion.div>
        </AnimatePresence>
      </ImagePreloader>
    );
  }
);

MovieGrid.displayName = 'MovieGrid';

export default MovieGrid;
