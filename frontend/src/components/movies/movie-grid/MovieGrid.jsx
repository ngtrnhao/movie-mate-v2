import { memo, useCallback, useMemo, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { useInView } from 'react-intersection-observer';
import { useThrottledScroll } from '../../../hooks/useThrottledScroll';
import useUserTracking from '../../../hooks/useUserTracking';
import MovieCard from '../movie-card';
import LoadingSpinner from '../../common/LoadingSpinner';
import ErrorMessage from '../../common/ErrorMessage';
import EmptyState from '../../common/EmptyState';
import ImagePreloader from '../../common/ImagePreloader';
import LoadingGrid from '../../common/LoadingGrid';

// Simplified animation variants - chỉ animate container
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      duration: 0.3, // Giảm duration
    },
  },
};

const MovieGrid = memo(
  ({
    movies,
    loading,
    error,
    onMovieClick,
    onTrailerClick,
    className = '',
    hasNextPage,
    fetchNextPage,
  }) => {
    const { t } = useTranslation('movies');
    const { trackInteraction } = useUserTracking();

    // Track grid view when movies are loaded
    useEffect(() => {
      if (movies && movies.length > 0 && !loading) {
        trackInteraction({
          action: 'grid_view',
          metadata: {
            movies_count: movies.length,
            context: 'movie_grid',
            timestamp: new Date().toISOString(),
          },
        });
      }
    }, [movies?.length, loading, trackInteraction]);

    // Get scroll state để optimize rendering
    const { isFastScrolling, isScrolling, scrollSpeed } = useThrottledScroll();

    // Auto infinite scroll với scroll awareness
    const { ref: loadMoreRef, inView } = useInView({
      threshold: 0.1,
      rootMargin: '800px 0px',
      skip: isFastScrolling, // Skip auto-loading khi scroll quá nhanh
    });

    // Trigger auto-load với debouncing
    useEffect(() => {
      if (inView && hasNextPage && !loading && !isFastScrolling) {
        const loadTimer = setTimeout(
          () => {
            fetchNextPage();
          },
          isScrolling ? 300 : 100
        ); // Delay longer nếu đang scroll

        return () => clearTimeout(loadTimer);
      }
    }, [inView, hasNextPage, loading, isFastScrolling, isScrolling, fetchNextPage]);

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

    // Memoized movies list với scroll-aware rendering
    const moviesList = useMemo(() => {
      if (!movies || movies.length === 0) return null;

      // Determine rendering strategy based on scroll speed
      const renderStrategy = isFastScrolling ? 'minimal' : 'full';

      return movies.map((movie, index) => {
        // Priority loading cho first visible movies
        const isPriority = index < 6;

        // Skip complex rendering khi scroll nhanh
        const shouldRenderFull = renderStrategy === 'full' || isPriority;

        return (
          <MovieCard
            key={movie.id}
            movie={movie}
            priority={isPriority}
            minimal={!shouldRenderFull}
            onClick={handleMovieClick}
            style={
              isFastScrolling
                ? {
                    // Reduce animations during fast scroll
                    transition: 'none',
                    transform: 'translateZ(0)', // Force GPU layer
                  }
                : undefined
            }
            onTrailerClick={onTrailerClick}
          />
        );
      });
    }, [movies, isFastScrolling, onTrailerClick]);

    // Container animations với scroll-aware behavior
    const containerVariants = useMemo(
      () => ({
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: {
            duration: 0.2,
            staggerChildren: 0,
          },
        },
      }),
      []
    );

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
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className={`grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 ${className}`}
          transition={{ duration: 0 }}
        >
          {moviesList}
        </motion.div>

        {/* Loading state với scroll awareness */}
        {loading && (
          <div className="mt-8">
            <LoadingGrid count={6} />
          </div>
        )}

        {/* Auto-load trigger với manual fallback */}
        {hasNextPage && !loading && (
          <div ref={loadMoreRef} className="mt-8 text-center">
            {/* Manual load button - visible khi fast scrolling */}
            {isFastScrolling && (
              <button
                onClick={fetchNextPage}
                className="rounded-lg bg-blue-600 px-6 py-3 text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Load More Movies
              </button>
            )}

            {/* Auto-load indicator */}
            {!isFastScrolling && (
              <div className="text-gray-400">
                <div className="animate-pulse">Loading more movies...</div>
              </div>
            )}
          </div>
        )}

        {/* Scroll performance indicator (debug mode) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="fixed bottom-4 right-4 rounded bg-black/80 p-2 text-xs text-white">
            <div>Scroll Speed: {scrollSpeed.toFixed(2)}</div>
            <div>Fast Scroll: {isFastScrolling ? 'Yes' : 'No'}</div>
            <div>Is Scrolling: {isScrolling ? 'Yes' : 'No'}</div>
          </div>
        )}
      </ImagePreloader>
    );
  }
);

MovieGrid.displayName = 'MovieGrid';

export default MovieGrid;
