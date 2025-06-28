import { useState, useEffect, useCallback, useMemo } from 'react';
import { useTranslation } from '../../i18n/hooks/useTranslation';
import { motion, AnimatePresence } from 'framer-motion';
import { useInView } from 'react-intersection-observer';
import {
  SlidersHorizontal,
  X,
  Search,
  Filter,
  Calendar,
  Star,
  Clock,
  Eye,
  EyeOff,
  ArrowUp,
} from 'lucide-react';
import { searchMovies } from '../../api/movieService';
import { useCategories } from '../../hooks/useCategories';
import { useInfiniteQuery } from '@tanstack/react-query';
import MovieCard from '../../components/movies/movie-card';
import MovieTrailerModal from '../../components/movies/movie-trailer/MovieTrailerModal';
import { useTrailerModal } from '../../hooks/useTrailerModal';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { useThrottledScroll } from '../../hooks/useThrottledScroll';
import animationCache from '../../utils/animationCache';

const MoviesPage = () => {
  const { t } = useTranslation('movies');
  const [showFilters, setShowFilters] = useState(false);
  const [showBackToTop, setShowBackToTop] = useState(false);
  const [genres, setGenres] = useState([]);
  const [filters, setFilters] = useState({
    genres: [],
    yearFrom: '',
    yearTo: '',
    ratingMin: '',
    ratingMax: '',
    runtimeMin: '',
    runtimeMax: '',
    status: '',
    adult: false,
    language: 'en',
    query: '',
    sortBy: 'popularity',
    order: 'desc',
  });

  // Fetch genres using hook
  const { data: genresData, isLoading: genresLoading } = useCategories();

  // Trailer modal hook
  const { isTrailerOpen, modalMovie, modalTrailerUrl, closeTrailerModal, handleTrailerClick } =
    useTrailerModal();

  // Get scroll state để apply performance optimizations
  const { isFastScrolling, isScrolling } = useThrottledScroll();

  // Auto infinite scroll trigger với scroll awareness
  const { ref: infiniteScrollRef, inView } = useInView({
    threshold: 0.1,
    rootMargin: '600px 0px', // Trigger sớm hơn để load trước khi user scroll đến cuối
    skip: isFastScrolling, // Skip auto-loading khi scroll quá nhanh
  });

  // Track scroll position để hiển thị back to top button với debounce
  useEffect(() => {
    let timeoutId;

    const handleScroll = () => {
      // Debounce scroll events để tránh lag khi resize
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        const scrollY = window.scrollY;
        setShowBackToTop(scrollY > 800);
      }, 16); // ~60fps
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', handleScroll);
      clearTimeout(timeoutId);
    };
  }, []);

  // Back to top function
  const scrollToTop = useCallback(() => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    });
  }, []);

  // Enhanced trailer click handler with better error handling
  const handleMovieTrailerClick = useCallback(
    movie => {
      try {
        // Check if movie has trailers before attempting to open modal
        if (!movie?.trailers?.length) {
          console.warn('Movie has no trailers:', movie.title);
          // You could add a toast notification here: "No trailer available for this movie"
          return;
        }

        handleTrailerClick(movie);
      } catch (error) {
        console.error('Error opening trailer modal:', error);
        // You could add a toast notification here if needed
      }
    },
    [handleTrailerClick]
  );

  useEffect(() => {
    if (genresData && !genresLoading) {
      setGenres(genresData);
    }
  }, [genresData, genresLoading]);

  // Infinite query for movies
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading, error, refetch } =
    useInfiniteQuery({
      queryKey: ['movies', filters],
      queryFn: ({ pageParam = 1 }) => searchMovies(filters, pageParam, 50),
      getNextPageParam: lastPage => {
        // Handle cases where lastPage might be null or missing has_next
        if (!lastPage) {
          console.warn('getNextPageParam: lastPage is null or undefined');
          return undefined;
        }

        // Check if has_next exists and is true
        if (lastPage.has_next === true) {
          return lastPage.current_page + 1;
        }

        // Fallback: check if we have data and if there might be more pages
        if (lastPage.data && lastPage.data.length > 0) {
          const currentPage = lastPage.current_page || 1;
          const pageSize = lastPage.page_size || 50;
          const totalCount = lastPage.count || 0;

          // If we have more items than what we've seen so far, there might be more pages
          if (totalCount > currentPage * pageSize) {
            return currentPage + 1;
          }
        }

        return undefined;
      },
      enabled: true,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error) => {
        // Retry up to 3 times for network errors, but not for 4xx errors
        if (failureCount < 3 && error?.response?.status >= 500) {
          return true;
        }
        return false;
      },
    });

  // State to prevent duplicate fetchNextPage calls
  const [isFetching, setIsFetching] = useState(false);

  // Debounced fetch function với scroll-aware behavior
  const debouncedFetchNextPage = useCallback(async () => {
    if (isFetching || isFetchingNextPage || !hasNextPage) {
      return;
    }

    setIsFetching(true);
    try {
      // Delay thông minh dựa trên scroll speed
      const delay = isFastScrolling ? 200 : isScrolling ? 100 : 50;

      await new Promise(resolve => setTimeout(resolve, delay));
      await fetchNextPage();
    } catch (error) {
      console.error('Error fetching next page:', error);
    } finally {
      // Reset flag sau delay để tránh re-triggering ngay lập tức
      setTimeout(() => setIsFetching(false), 500);
    }
  }, [fetchNextPage, hasNextPage, isFetchingNextPage, isFetching, isFastScrolling, isScrolling]);

  // Auto fetch next page khi infinite scroll trigger in view (với scroll awareness)
  useEffect(() => {
    if (inView && hasNextPage && !isFetchingNextPage && !isFetching && !isFastScrolling) {
      debouncedFetchNextPage();
    }
  }, [fetchNextPage, hasNextPage, isFetchingNextPage, isFetching, isFastScrolling, isScrolling]);

  // Memoized movie list với optimized deduplication
  const movies = useMemo(() => {
    if (!data?.pages) return [];

    // Safely extract movies from all pages với deduplication
    const allMovies = data.pages.reduce((accumulator, page) => {
      if (page && page.data && Array.isArray(page.data)) {
        return [...accumulator, ...page.data];
      }
      return accumulator;
    }, []);

    // Debug: Track original vs deduplicated count
    const originalCount = allMovies.length;

    // Optimized deduplication using Map for O(n) performance
    const uniqueMoviesMap = new Map();
    allMovies.forEach(movie => {
      if (movie && movie.id && !uniqueMoviesMap.has(movie.id)) {
        uniqueMoviesMap.set(movie.id, movie);
      }
    });

    const uniqueMovies = Array.from(uniqueMoviesMap.values());

    // Debug logging cho development (chỉ log khi thực sự có duplicate)
    if (process.env.NODE_ENV === 'development' && originalCount !== uniqueMovies.length) {
      console.warn(
        `[Movies Deduplication] Found ${originalCount - uniqueMovies.length} duplicate movies`
      );
      console.log(`Original: ${originalCount}, Unique: ${uniqueMovies.length}`);
    }

    return uniqueMovies;
  }, [data]);

  // Safe count extraction
  const totalCount = useMemo(() => {
    if (!data?.pages?.[0]) return 0;
    return data.pages[0].count || 0;
  }, [data]);

  // Filter options
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 50 }, (_, i) => currentYear - i);
  const ratings = [
    { value: '', label: 'Any Rating' },
    { value: '9', label: '9+ Excellent' },
    { value: '8', label: '8+ Very Good' },
    { value: '7', label: '7+ Good' },
    { value: '6', label: '6+ Fair' },
    { value: '5', label: '5+ Poor' },
  ];
  const sortOptions = [
    { value: 'popularity', label: 'Most Popular' },
    { value: 'rating', label: 'Highest Rated' },
    { value: 'release_date', label: 'Newest First' },
    { value: 'title', label: 'Title A-Z' },
    { value: 'runtime', label: 'Longest First' },
    { value: 'vote_count', label: 'Most Voted' },
  ];
  const statusOptions = [
    { value: '', label: 'Any Status' },
    { value: 'RELEASED', label: 'Released' },
    { value: 'UPCOMING', label: 'Upcoming' },
    { value: 'IN_PRODUCTION', label: 'In Production' },
    { value: 'POST_PRODUCTION', label: 'Post Production' },
  ];

  const handleFilterChange = useCallback((type, value) => {
    setFilters(prev => ({
      ...prev,
      [type]: value,
    }));

    // Clear animation cache khi filter thay đổi để cho phép re-animate
    // Chỉ clear movies cache, giữ poster cache để tránh re-load ảnh
    animationCache.clearMovies();
  }, []);

  const handleGenreToggle = useCallback(genreId => {
    setFilters(prev => ({
      ...prev,
      genres: prev.genres.includes(genreId)
        ? prev.genres.filter(id => id !== genreId)
        : [...prev.genres, genreId],
    }));

    // Clear animation cache khi filter thay đổi
    animationCache.clearMovies();
  }, []);

  const resetFilters = useCallback(() => {
    setFilters({
      genres: [],
      yearFrom: '',
      yearTo: '',
      ratingMin: '',
      ratingMax: '',
      runtimeMin: '',
      runtimeMax: '',
      status: '',
      adult: false,
      language: 'en',
      query: '',
      sortBy: 'popularity',
      order: 'desc',
    });

    // Clear animation cache khi reset filters
    animationCache.clearMovies();
  }, []);

  // Manual load more function (for fallback button)
  const loadMore = useCallback(async () => {
    try {
      if (hasNextPage && !isFetchingNextPage && !isFetching) {
        await debouncedFetchNextPage();
      }
    } catch (error) {
      console.error('Error loading more movies:', error);
    }
  }, [hasNextPage, isFetchingNextPage, isFetching, debouncedFetchNextPage]);

  // Apply fast-scroll CSS class to body
  useEffect(() => {
    const body = document.body;
    if (isFastScrolling) {
      body.classList.add('fast-scroll-mode');
    } else {
      body.classList.remove('fast-scroll-mode');
    }

    // Cleanup on unmount
    return () => {
      body.classList.remove('fast-scroll-mode');
    };
  }, [isFastScrolling]);

  // Performance-aware container classes
  const containerClasses = useMemo(() => {
    const baseClasses = 'scroll-container min-h-screen bg-gray-900 py-8 pt-20';
    const performanceClasses = isFastScrolling
      ? 'fast-scroll-mode'
      : isScrolling
        ? 'scrolling-mode'
        : '';

    return `${baseClasses} ${performanceClasses}`.trim();
  }, [isFastScrolling, isScrolling]);

  // Memoized movies grid để tránh re-render khi resize
  const moviesGrid = useMemo(() => {
    if (!movies || movies.length === 0) return null;

    return (
      <div
        className={`movies-grid grid gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 ${
          isFastScrolling ? 'scroll-fast' : ''
        }`}
        style={{
          // Prevent layout shift during resize
          contain: 'layout',
          willChange: 'auto',
        }}
      >
        {movies.map((movie, index) => (
          <MovieCard
            key={movie.id}
            movie={movie}
            index={index}
            minimal={isFastScrolling && index > 12}
            onTrailerClick={() => handleMovieTrailerClick(movie)}
          />
        ))}
      </div>
    );
  }, [movies, isFastScrolling, handleMovieTrailerClick]);

  // Error handling
  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-900">
        <div className="text-center">
          <p className="mb-4 text-red-400">{error.message}</p>
          <button
            onClick={() => window.location.reload()}
            className="rounded-md bg-red-600 px-4 py-2 text-white transition-colors hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="min-h-screen bg-gray-900 text-white"
    >
      {/* Back to Top Button - Fixed to screen corner */}
      <AnimatePresence>
        {showBackToTop && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 20 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            onClick={scrollToTop}
            className="fixed bottom-6 right-6 z-[9999] flex h-12 w-12 items-center justify-center rounded-full bg-red-600 text-white shadow-lg transition-all duration-300 hover:bg-red-700 hover:scale-110 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
            aria-label="Back to top"
          >
            <ArrowUp size={20} />
          </motion.button>
        )}
      </AnimatePresence>

      <div className="container mx-auto px-4 pt-28">
        {/* Header Section */}
        <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-optimize text-3xl font-bold text-white">
              {t('title', 'Discover Movies')}
            </h1>
            <p className="text-gray-400">
              {totalCount ? `${totalCount.toLocaleString()} movies found` : 'Loading...'}
            </p>
          </div>

          <div className="flex gap-2">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowFilters(!showFilters)}
              className="focus-ring flex items-center gap-2 rounded-md bg-red-600 px-4 py-2 text-white transition-colors hover:bg-red-700"
            >
              {showFilters ? <X size={20} /> : <SlidersHorizontal size={20} />}
              {showFilters ? 'Hide Filters' : 'Show Filters'}
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={resetFilters}
              className="focus-ring flex items-center gap-2 rounded-md bg-gray-700 px-4 py-2 text-white transition-colors hover:bg-gray-600"
            >
              Reset
            </motion.button>
          </div>
        </div>
        {/* Advanced Filters */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="mb-8 overflow-hidden"
            >
              <div className="space-y-6 rounded-lg bg-gray-800 p-6">
                {/* Search Bar */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 size-5 -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search movies..."
                    value={filters.query}
                    onChange={e => handleFilterChange('query', e.target.value)}
                    className="w-full rounded-md bg-gray-700 py-3 pl-10 pr-4 text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500"
                  />
                </div>

                {/* Genres */}
                <div>
                  <label className="mb-3 flex items-center gap-2 text-sm font-medium text-white">
                    <Filter size={16} />
                    Genres
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {genres.map(genre => (
                      <button
                        key={genre.id}
                        onClick={() => handleGenreToggle(genre.id)}
                        className={`rounded-full px-3 py-1 text-sm transition-all ${
                          filters.genres.includes(genre.id)
                            ? 'bg-red-600 text-white ring-2 ring-red-400'
                            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                        }`}
                      >
                        {genre.name}
                        {filters.genres.includes(genre.id) && (
                          <span className="ml-1 text-xs">✓</span>
                        )}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Year Range */}
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-2 flex items-center gap-2 text-sm font-medium text-white">
                      <Calendar size={16} />
                      From Year
                    </label>
                    <select
                      value={filters.yearFrom}
                      onChange={e => handleFilterChange('yearFrom', e.target.value)}
                      className="w-full rounded-md bg-gray-700 p-3 text-white focus:outline-none focus:ring-2 focus:ring-red-500"
                    >
                      <option value="">Any Year</option>
                      {years.map(year => (
                        <option key={year} value={year}>
                          {year}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-2 flex items-center gap-2 text-sm font-medium text-white">
                      <Calendar size={16} />
                      To Year
                    </label>
                    <select
                      value={filters.yearTo}
                      onChange={e => handleFilterChange('yearTo', e.target.value)}
                      className="w-full rounded-md bg-gray-700 p-3 text-white focus:outline-none focus:ring-2 focus:ring-red-500"
                    >
                      <option value="">Any Year</option>
                      {years.map(year => (
                        <option key={year} value={year}>
                          {year}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Rating Range */}
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-2 flex items-center gap-2 text-sm font-medium text-white">
                      <Star size={16} />
                      Min Rating
                    </label>
                    <select
                      value={filters.ratingMin}
                      onChange={e => handleFilterChange('ratingMin', e.target.value)}
                      className="w-full rounded-md bg-gray-700 p-3 text-white focus:outline-none focus:ring-2 focus:ring-red-500"
                    >
                      {ratings.map(rating => (
                        <option key={rating.value} value={rating.value}>
                          {rating.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-2 flex items-center gap-2 text-sm font-medium text-white">
                      <Star size={16} />
                      Max Rating
                    </label>
                    <select
                      value={filters.ratingMax}
                      onChange={e => handleFilterChange('ratingMax', e.target.value)}
                      className="w-full rounded-md bg-gray-700 p-3 text-white focus:outline-none focus:ring-2 focus:ring-red-500"
                    >
                      <option value="">No Limit</option>
                      {[10, 9, 8, 7, 6, 5, 4, 3, 2, 1].map(rating => (
                        <option key={rating} value={rating}>
                          {rating}+ Rating
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Runtime Range */}
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-2 flex items-center gap-2 text-sm font-medium text-white">
                      <Clock size={16} />
                      Min Runtime (minutes)
                    </label>
                    <input
                      type="number"
                      placeholder="e.g. 90"
                      value={filters.runtimeMin}
                      onChange={e => handleFilterChange('runtimeMin', e.target.value)}
                      className="w-full rounded-md bg-gray-700 p-3 text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500"
                    />
                  </div>
                  <div>
                    <label className="mb-2 flex items-center gap-2 text-sm font-medium text-white">
                      <Clock size={16} />
                      Max Runtime (minutes)
                    </label>
                    <input
                      type="number"
                      placeholder="e.g. 180"
                      value={filters.runtimeMax}
                      onChange={e => handleFilterChange('runtimeMax', e.target.value)}
                      className="w-full rounded-md bg-gray-700 p-3 text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500"
                    />
                  </div>
                </div>

                {/* Status and Adult Content */}
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <label className="mb-2 block text-sm font-medium text-white">Status</label>
                    <select
                      value={filters.status}
                      onChange={e => handleFilterChange('status', e.target.value)}
                      className="w-full rounded-md bg-gray-700 p-3 text-white focus:outline-none focus:ring-2 focus:ring-red-500"
                    >
                      {statusOptions.map(status => (
                        <option key={status.value} value={status.value}>
                          {status.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-medium text-white">Sort By</label>
                    <select
                      value={filters.sortBy}
                      onChange={e => handleFilterChange('sortBy', e.target.value)}
                      className="w-full rounded-md bg-gray-700 p-3 text-white focus:outline-none focus:ring-2 focus:ring-red-500"
                    >
                      {sortOptions.map(option => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-medium text-white">
                      Adult Content
                    </label>
                    <button
                      onClick={() => handleFilterChange('adult', !filters.adult)}
                      className={`flex w-full items-center justify-center gap-2 rounded-md p-3 transition-all ${
                        filters.adult
                          ? 'bg-red-600 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      {filters.adult ? <Eye size={16} /> : <EyeOff size={16} />}
                      {filters.adult ? 'Include Adult' : 'Family Friendly'}
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        {/* Movies Grid */}
        {isLoading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : (
          <>
            {moviesGrid}

            {/* Auto Infinite Scroll Trigger với scroll awareness */}
            {hasNextPage && (
              <div ref={infiniteScrollRef} className="mt-8 flex justify-center py-4">
                {isFetchingNextPage && (
                  <div className="flex items-center gap-2 text-gray-400">
                    <LoadingSpinner />
                    <span>Loading more movies...</span>
                  </div>
                )}
                {!isFetchingNextPage && isFastScrolling && (
                  <div className="text-gray-400">
                    <span>Scroll slower to auto-load more movies</span>
                  </div>
                )}
              </div>
            )}

            {/* Manual Load More Fallback (chỉ hiển thị khi auto-scroll fails) */}
            {hasNextPage && !inView && movies.length > 20 && (
              <div className="mt-4 flex justify-center">
                <button
                  onClick={loadMore}
                  disabled={isFetchingNextPage}
                  className="rounded-md bg-red-600 px-6 py-3 text-white transition-colors hover:bg-red-700 disabled:bg-gray-600"
                >
                  {isFetchingNextPage ? 'Loading...' : 'Load More Movies'}
                </button>
              </div>
            )}

            {/* End of Results Message */}
            {!hasNextPage && movies.length > 0 && (
              <div className="mt-8 text-center text-gray-400">
                <div className="inline-flex items-center gap-2 rounded-lg bg-gray-800/50 px-4 py-2">
                  <span>✨</span>
                  <span>You've explored all {totalCount.toLocaleString()} movies!</span>
                </div>
              </div>
            )}

            {/* Empty State */}
            {movies.length === 0 && !isLoading && (
              <div className="py-12 text-center text-gray-400">
                <div className="mx-auto max-w-md">
                  <div className="mb-4 text-6xl">🎬</div>
                  <p className="text-xl font-semibold text-white">No movies found</p>
                  <p className="mt-2">Try adjusting your filters or search terms</p>
                  <button
                    onClick={resetFilters}
                    className="mt-4 rounded-md bg-red-600 px-4 py-2 text-white transition-colors hover:bg-red-700"
                  >
                    Clear All Filters
                  </button>
                </div>
              </div>
            )}
          </>
        )}
        {/* Movie Trailer Modal */}
        <MovieTrailerModal
          isOpen={isTrailerOpen}
          onClose={closeTrailerModal}
          movie={modalMovie}
          trailerUrl={modalTrailerUrl}
        />
      </div>
    </motion.div>
  );
};

export default MoviesPage;
