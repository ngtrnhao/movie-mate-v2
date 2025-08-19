import { useState, useEffect, useCallback, useMemo } from 'react';
import { useTranslation } from '../../i18n/hooks/useTranslation';
import { motion, AnimatePresence } from 'framer-motion';
import { useInView } from 'react-intersection-observer';
import { SlidersHorizontal, X, Search, Filter, Calendar, Eye, EyeOff, ArrowUp } from 'lucide-react';
import { searchMovies } from '../../api/movieService';
import { useCategories } from '../../hooks/useCategories';
import { useInfiniteQuery } from '@tanstack/react-query';
import MovieCard from '../../components/movies/movie-card';
import MovieTrailerModal from '../../components/movies/movie-trailer/MovieTrailerModal';
import { useTrailerModal } from '../../hooks/useTrailerModal';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { useThrottledScroll } from '../../hooks/useThrottledScroll';
import { useScrollPosition } from '../../hooks/useScrollPosition';
import animationCache from '../../utils/animationCache';
import ImagePreloader from '../../components/common/ImagePreloader';
import { useNavigate, useLocation } from 'react-router-dom';
import useUserTracking from '../../hooks/useUserTracking';
import { useRef } from 'react';

const MoviesPage = () => {
  const { t } = useTranslation('movies');
  const navigate = useNavigate();
  const location = useLocation();
  const { trackInteraction, trackSearch } = useUserTracking();
  const [showFilters, setShowFilters] = useState(false);
  const [showBackToTop, setShowBackToTop] = useState(false);
  const [genres, setGenres] = useState([]);

  // Track movies page view
  useEffect(() => {
    trackInteraction({
      action: 'page_view',
      metadata: {
        page: 'movies',
        timestamp: new Date().toISOString(),
      },
    });
  }, [trackInteraction]);

  // Define default filters with useMemo to prevent recreating on each render
  const defaultFilters = useMemo(
    () => ({
      genres: [],
      yearFrom: '',
      yearTo: '',
      country: '',
      status: '',
      adult: false,
      language: 'en',
      query: '',
      sortBy: 'most_popular',
      order: 'desc',
    }),
    []
  );

  const [filters, setFilters] = useState(defaultFilters);
  const [pendingFilters, setPendingFilters] = useState(defaultFilters);

  // Listen for URL parameter changes (including from header search) - simplified approach
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const newFilters = { ...defaultFilters };

    // Get all filter values from URL
    if (searchParams.has('q')) {
      newFilters.query = searchParams.get('q');
    }
    if (searchParams.has('genres')) {
      const genreIds = searchParams.get('genres').split(',').map(Number);
      newFilters.genres = genreIds;
    }
    if (searchParams.has('yearFrom')) {
      newFilters.yearFrom = searchParams.get('yearFrom');
    }
    if (searchParams.has('yearTo')) {
      newFilters.yearTo = searchParams.get('yearTo');
    }
    if (searchParams.has('country')) {
      newFilters.country = searchParams.get('country');
    }
    if (searchParams.has('status')) {
      newFilters.status = searchParams.get('status');
    }
    if (searchParams.has('adult')) {
      newFilters.adult = searchParams.get('adult') === 'true';
    }
    if (searchParams.has('language')) {
      newFilters.language = searchParams.get('language');
    }
    if (searchParams.has('sort_by')) {
      newFilters.sortBy = searchParams.get('sort_by');
    }
    if (searchParams.has('order')) {
      newFilters.order = searchParams.get('order');
    }

    // Only update if filters actually changed to prevent unnecessary re-renders
    setFilters(prevFilters => {
      const hasChanged = JSON.stringify(prevFilters) !== JSON.stringify(newFilters);
      return hasChanged ? newFilters : prevFilters;
    });

    setPendingFilters(prevPendingFilters => {
      const hasChanged = JSON.stringify(prevPendingFilters) !== JSON.stringify(newFilters);
      return hasChanged ? newFilters : prevPendingFilters;
    });
  }, [location.search]); // Only depend on location.search

  // Handle reset filters
  const handleResetFilters = useCallback(() => {
    setFilters(defaultFilters);
    setPendingFilters(defaultFilters);

    // Preserve search query but clear other filter parameters
    const searchParams = new URLSearchParams(location.search);
    const query = searchParams.get('q');

    // Clear all parameters except query
    const newParams = new URLSearchParams();
    if (query) {
      newParams.set('q', query);
    }

    navigate(`/movies${newParams.toString() ? `?${newParams.toString()}` : ''}`, { replace: true });
  }, [navigate, defaultFilters, location.search]);

  // Reset filters when leaving page or on reload
  useEffect(() => {
    const resetFilters = () => {
      setFilters(defaultFilters);
      setPendingFilters(defaultFilters);
    };

    // Reset on page unload
    window.addEventListener('beforeunload', resetFilters);

    // Reset on component mount if no search params
    if (!location.search) {
      resetFilters();
    }

    return () => {
      window.removeEventListener('beforeunload', resetFilters);
      resetFilters(); // Reset when leaving page
    };
  }, [defaultFilters, location.search]);

  // Fetch genres using hook
  const { data: genresData, isLoading: genresLoading } = useCategories();

  // Trailer modal hook
  const { isTrailerOpen, modalMovie, modalTrailerUrl, closeTrailerModal, handleTrailerClick } =
    useTrailerModal();

  // Get scroll state để apply performance optimizations
  const { isFastScrolling, isScrolling } = useThrottledScroll();

  // Use scroll position hook - now handles everything automatically
  useScrollPosition();

  // Auto infinite scroll trigger với scroll awareness
  const { ref: infiniteScrollRef, inView } = useInView({
    threshold: 0.1,
    rootMargin: '900px 0px', // Trigger sớm hơn để load trước khi user scroll đến cuối
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
      queryFn: ({ pageParam = null }) =>
        pageParam ? searchMovies(filters, pageParam, 50) : searchMovies(filters, 1, 50),
      getNextPageParam: lastPage => {
        if (!lastPage) return undefined;

        // For Elasticsearch: check for next_search_after field
        if (lastPage.search_engine === 'elasticsearch' && lastPage.next_search_after) {
          return lastPage.next_search_after;
        }

        // For ORM fallback: check for next URL and extract page number
        if (lastPage.search_engine === 'django_orm' && lastPage.next) {
          const url = new URL(lastPage.next, window.location.origin);
          const pageParam = url.searchParams.get('page');
          if (pageParam) {
            return parseInt(pageParam, 10);
          }
        }

        // Fallback: check if next field exists (for backward compatibility)
        if (lastPage.next && typeof lastPage.next !== 'string') {
          return lastPage.next;
        }

        return undefined;
      },
      enabled: true,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error) => {
        if (failureCount < 3 && error?.response?.status >= 500) {
          return true;
        }
        return false;
      },
    });

  // Log the full data object after fetching
  if (data && data.pages) {
    data.pages.forEach((page, idx) => {});
  }

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
    if (!data?.pages) {
      return [];
    }

    // Safely extract movies from all pages với deduplication
    const allMovies = data.pages.reduce((accumulator, page, idx) => {
      if (page) {
        if (Array.isArray(page.data)) {
          return [...accumulator, ...page.data];
        }
        if (Array.isArray(page.results)) {
          return [...accumulator, ...page.results];
        }
        if (Array.isArray(page)) {
          return [...accumulator, ...page];
        }
      }
      return accumulator;
    }, []);

    // Optimized deduplication using Map for O(n) performance
    const uniqueMoviesMap = new Map();
    allMovies.forEach(movie => {
      if (movie && movie.id && !uniqueMoviesMap.has(movie.id)) {
        uniqueMoviesMap.set(movie.id, {
          ...movie,
          poster_url: movie.poster_url || movie.poster_path || '', // Map poster_path to poster_url
        });
      }
    });

    const uniqueMovies = Array.from(uniqueMoviesMap.values());

    return uniqueMovies;
  }, [data]);

  // Tracking search thực tế khi có query và kết quả
  const lastTrackedQueryRef = useRef('');
  const lastTrackedIdsRef = useRef([]);
  useEffect(() => {
    if (filters.query && movies.length > 0) {
      const resultIds = movies.map(movie => movie.id);
      // Chỉ gửi nếu query hoặc danh sách id thay đổi
      const isSameQuery = lastTrackedQueryRef.current === filters.query;
      const isSameIds = JSON.stringify(lastTrackedIdsRef.current) === JSON.stringify(resultIds);
      if (!isSameQuery || !isSameIds) {
        trackSearch(filters.query, resultIds);
        lastTrackedQueryRef.current = filters.query;
        lastTrackedIdsRef.current = resultIds;
      }
    }
  }, [filters.query, movies, trackSearch]);

  // Safe count extraction
  const totalCount = useMemo(() => {
    if (!data?.pages?.[0]) return 0;
    return data.pages[0].count || 0;
  }, [data]);

  // Filter options
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: currentYear - 2009 }, (_, i) => currentYear - i);

  const statusOptions = [
    { value: '', label: t('filterOptions.anyStatus') },
    { value: 'RELEASED', label: t('filterOptions.released') },
    { value: 'UPCOMING', label: t('filterOptions.upcoming') },
    { value: 'IN_PRODUCTION', label: t('filterOptions.inProduction') },
    { value: 'POST_PRODUCTION', label: t('filterOptions.postProduction') },
  ];

  const sortOptions = [
    { value: 'most_popular', label: t('sortOptions.most_popular', 'Phổ biến nhất') },
    // { value: 'popularity', label: t('sortOptions.popularity') },
    { value: 'rating', label: t('sortOptions.rating') },
    { value: 'release_date', label: t('sortOptions.release_date') },
    { value: 'title', label: t('sortOptions.title') },
    { value: 'runtime', label: t('sortOptions.runtime') },
    { value: 'vote_count', label: t('sortOptions.vote_count') },
  ];

  const countries = [
    { value: '', label: t('filterOptions.anyCountry') },
    { value: 'US', label: t('countries.US') },
    { value: 'GB', label: t('countries.GB') },
    { value: 'FR', label: t('countries.FR') },
    { value: 'DE', label: t('countries.DE') },
    { value: 'IT', label: t('countries.IT') },
    { value: 'ES', label: t('countries.ES') },
    { value: 'CA', label: t('countries.CA') },
    { value: 'AU', label: t('countries.AU') },
    { value: 'JP', label: t('countries.JP') },
    { value: 'KR', label: t('countries.KR') },
    { value: 'CN', label: t('countries.CN') },
    { value: 'IN', label: t('countries.IN') },
    { value: 'BR', label: t('countries.BR') },
    { value: 'MX', label: t('countries.MX') },
    { value: 'RU', label: t('countries.RU') },
    { value: 'SE', label: t('countries.SE') },
    { value: 'NO', label: t('countries.NO') },
    { value: 'DK', label: t('countries.DK') },
    { value: 'NL', label: t('countries.NL') },
    { value: 'BE', label: t('countries.BE') },
    { value: 'CH', label: t('countries.CH') },
    { value: 'AT', label: t('countries.AT') },
    { value: 'PL', label: t('countries.PL') },
    { value: 'CZ', label: t('countries.CZ') },
    { value: 'HU', label: t('countries.HU') },
    { value: 'RO', label: t('countries.RO') },
    { value: 'BG', label: t('countries.BG') },
    { value: 'HR', label: t('countries.HR') },
    { value: 'SI', label: t('countries.SI') },
    { value: 'SK', label: t('countries.SK') },
    { value: 'LT', label: t('countries.LT') },
    { value: 'LV', label: t('countries.LV') },
    { value: 'EE', label: t('countries.EE') },
    { value: 'FI', label: t('countries.FI') },
    { value: 'IE', label: t('countries.IE') },
    { value: 'PT', label: t('countries.PT') },
    { value: 'GR', label: t('countries.GR') },
    { value: 'TR', label: t('countries.TR') },
    { value: 'IL', label: t('countries.IL') },
    { value: 'ZA', label: t('countries.ZA') },
    { value: 'EG', label: t('countries.EG') },
    { value: 'MA', label: t('countries.MA') },
    { value: 'TN', label: t('countries.TN') },
    { value: 'DZ', label: t('countries.DZ') },
    { value: 'TH', label: t('countries.TH') },
    { value: 'VN', label: t('countries.VN') },
    { value: 'PH', label: t('countries.PH') },
    { value: 'MY', label: t('countries.MY') },
    { value: 'SG', label: t('countries.SG') },
    { value: 'ID', label: t('countries.ID') },
    { value: 'NZ', label: t('countries.NZ') },
    { value: 'AR', label: t('countries.AR') },
    { value: 'CL', label: t('countries.CL') },
    { value: 'PE', label: t('countries.PE') },
    { value: 'CO', label: t('countries.CO') },
    { value: 'VE', label: t('countries.VE') },
    { value: 'UY', label: t('countries.UY') },
    { value: 'PY', label: t('countries.PY') },
    { value: 'BO', label: t('countries.BO') },
    { value: 'EC', label: t('countries.EC') },
    { value: 'GY', label: t('countries.GY') },
    { value: 'SR', label: t('countries.SR') },
    { value: 'FK', label: t('countries.FK') },
    { value: 'GF', label: t('countries.GF') },
  ];

  const handleFilterChange = useCallback((type, value) => {
    setPendingFilters(prev => ({
      ...prev,
      [type]: value,
    }));

    // Clear animation cache khi filter thay đổi để cho phép re-animate
    // Chỉ clear movies cache, giữ poster cache để tránh re-load ảnh
    animationCache.clearMovies();
  }, []);

  const handleGenreToggle = useCallback(genreId => {
    setPendingFilters(prev => ({
      ...prev,
      genres: prev.genres.includes(genreId)
        ? prev.genres.filter(id => id !== genreId)
        : [...prev.genres, genreId],
    }));

    // Clear animation cache khi filter thay đổi
    animationCache.clearMovies();
  }, []);

  const resetFilters = useCallback(() => {
    // Preserve current query from header search but reset other filters
    const defaultFilters = {
      genres: [],
      yearFrom: '',
      yearTo: '',
      country: '',
      status: '',
      adult: false,
      language: 'en',
      query: filters.query, // Preserve current search query from header
      sortBy: 'most_popular',
      order: 'desc',
    };

    setFilters(defaultFilters);
    setPendingFilters(defaultFilters);

    // Clear animation cache khi reset filters
    animationCache.clearMovies();
  }, [filters.query]);

  // Apply pending filters
  const applyFilters = useCallback(() => {
    setFilters(pendingFilters);
    setShowFilters(false);
  }, [pendingFilters]);

  // Cancel pending changes
  const cancelFilters = useCallback(() => {
    setPendingFilters(filters);
    setShowFilters(false);
  }, [filters]);

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

  // Sync pendingFilters with filters when opening filters panel
  useEffect(() => {
    if (showFilters) {
      setPendingFilters(filters);
    }
  }, [showFilters, filters]);

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
          contain: 'layout', // Grid giữ nguyên kích thước, không ảnh hưởng layout xung quanh(tránh resize khi load thêm movies làm nhảy layout)
          willChange: 'auto', // Giúp trình duyệt tối ưu hóa rendering khi scroll
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

  // Check if there are pending changes
  const hasPendingChanges = useMemo(() => {
    return JSON.stringify(pendingFilters) !== JSON.stringify(filters);
  }, [pendingFilters, filters]);

  // Count changed filters
  const changedFiltersCount = useMemo(() => {
    let count = 0;
    Object.keys(pendingFilters).forEach(key => {
      if (JSON.stringify(pendingFilters[key]) !== JSON.stringify(filters[key])) {
        count++;
      }
    });
    return count;
  }, [pendingFilters, filters]);

  // Memoize priority images (first 8 movies) for preloading
  const priorityImages = useMemo(() => {
    return (
      movies
        ?.slice(0, 8)
        .map(movie => movie.poster_path)
        .filter(Boolean) || []
    );
  }, [movies]);

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
    <>
      {/* Back to Top Button - Elegant floating design */}
      <AnimatePresence>
        {showBackToTop && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 20 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            onClick={scrollToTop}
            className="group fixed bottom-8 right-8 z-[9999] flex size-14 items-center justify-center rounded-2xl border border-gray-600/50 bg-gradient-to-tr from-gray-800/90 to-gray-700/90 text-white shadow-2xl backdrop-blur-md transition-all duration-300 hover:scale-105 hover:border-red-400/50 hover:from-red-600/90 hover:to-red-500/90 hover:shadow-red-500/25 focus:outline-none focus:ring-2 focus:ring-red-500/50 focus:ring-offset-2 focus:ring-offset-gray-900"
            aria-label="Back to top"
          >
            <ArrowUp
              size={22}
              className="transition-transform duration-300 group-hover:-translate-y-0.5"
            />
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-tr from-white/10 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
          </motion.button>
        )}
      </AnimatePresence>

      <div className="movies-page min-h-screen bg-gray-900 text-white">
        <ImagePreloader priorityImages={priorityImages}>
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
                  {showFilters ? t('actions.hideFilters') : t('actions.showFilters')}
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleResetFilters}
                  className="focus-ring flex items-center gap-2 rounded-md bg-gray-700 px-4 py-2 text-white transition-colors hover:bg-gray-600"
                >
                  {t('actions.reset')}
                </motion.button>
              </div>
            </div>

            {/* Filter Panel */}
            <AnimatePresence>
              {showFilters && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="mb-8 overflow-hidden"
                >
                  <div className="space-y-6 rounded-lg bg-gray-800 p-6">
                    {/* Genres */}
                    <div>
                      <label className="mb-3 flex items-center gap-2 text-sm font-medium text-white">
                        <Filter size={16} />
                        {t('filters.genres')}
                      </label>
                      <div className="flex flex-wrap gap-2">
                        {genres.map(genre => (
                          <button
                            key={genre.id}
                            onClick={() => handleGenreToggle(genre.id)}
                            className={`rounded-full px-3 py-1 text-sm transition-all ${
                              pendingFilters.genres.includes(genre.id)
                                ? 'bg-red-600 text-white ring-2 ring-red-400'
                                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                            }`}
                          >
                            {genre.name}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Year Range with Search */}
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <label className="mb-2 flex items-center gap-2 text-sm font-medium text-white">
                          <Calendar size={16} />
                          {t('filters.yearRange')}
                        </label>
                        <div className="flex flex-wrap gap-2">
                          <button
                            onClick={() => {
                              handleFilterChange('yearFrom', '');
                              handleFilterChange('yearTo', '');
                            }}
                            className={`rounded-full px-3 py-1 text-sm transition-all ${
                              !pendingFilters.yearFrom && !pendingFilters.yearTo
                                ? 'bg-red-600 text-white ring-2 ring-red-400'
                                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                            }`}
                          >
                            {t('filterOptions.allYears')}
                          </button>
                          {years.map(year => (
                            <button
                              key={year}
                              onClick={() => {
                                handleFilterChange('yearFrom', year.toString());
                                handleFilterChange('yearTo', year.toString());
                              }}
                              className={`rounded-full px-3 py-1 text-sm transition-all ${
                                pendingFilters.yearFrom === year.toString() &&
                                pendingFilters.yearTo === year.toString()
                                  ? 'bg-red-600 text-white ring-2 ring-red-400'
                                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                              }`}
                            >
                              {year}
                            </button>
                          ))}
                        </div>
                      </div>
                      <div>
                        <label className="mb-2 flex items-center gap-2 text-sm font-medium text-white">
                          <Search size={16} />
                          {t('filters.customYear')}
                        </label>
                        <input
                          type="number"
                          placeholder={t('filters.customYearPlaceholder')}
                          min="1900"
                          max="2030"
                          value={pendingFilters.yearFrom}
                          onChange={e => {
                            const year = e.target.value;
                            handleFilterChange('yearFrom', year);
                            handleFilterChange('yearTo', year);
                          }}
                          className={`w-full rounded-md p-3 text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500 ${
                            pendingFilters.yearFrom &&
                            pendingFilters.yearFrom === pendingFilters.yearTo &&
                            !years.includes(parseInt(pendingFilters.yearFrom))
                              ? 'border border-red-500 bg-red-600/20'
                              : 'bg-gray-700'
                          }`}
                        />
                        {pendingFilters.yearFrom &&
                          pendingFilters.yearFrom === pendingFilters.yearTo &&
                          !years.includes(parseInt(pendingFilters.yearFrom)) && (
                            <p className="mt-1 text-xs text-red-400">
                              {t('filters.customYearSelected')}
                            </p>
                          )}
                      </div>
                    </div>

                    {/* Country, Status, Sort, Content Filter */}
                    <div className="grid gap-4 md:grid-cols-4">
                      <div>
                        <label className="mb-2 flex items-center gap-2 text-sm font-medium text-white">
                          <Filter size={16} />
                          {t('filters.country')}
                        </label>
                        <select
                          value={pendingFilters.country}
                          onChange={e => handleFilterChange('country', e.target.value)}
                          className="w-full rounded-md bg-gray-700 p-3 text-white focus:outline-none focus:ring-2 focus:ring-red-500"
                        >
                          {countries.map(country => (
                            <option key={country.value} value={country.value}>
                              {country.label}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="mb-2 flex items-center gap-2 text-sm font-medium text-white">
                          <Filter size={16} />
                          {t('filters.status')}
                        </label>
                        <select
                          value={pendingFilters.status}
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
                        <label className="mb-2 flex items-center gap-2 text-sm font-medium text-white">
                          <Filter size={16} />
                          {t('filters.sortBy')}
                        </label>
                        <select
                          value={pendingFilters.sortBy}
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
                          {t('filters.contentFilter')}
                        </label>
                        <button
                          onClick={() => handleFilterChange('adult', !pendingFilters.adult)}
                          className={`flex w-full items-center justify-center gap-2 rounded-md p-3 transition-all ${
                            pendingFilters.adult
                              ? 'bg-red-600 text-white'
                              : 'bg-gray-700 text-white'
                          }`}
                        >
                          {pendingFilters.adult ? <Eye size={16} /> : <EyeOff size={16} />}
                          {pendingFilters.adult
                            ? t('filters.showAllContent')
                            : t('filters.familyFriendly')}
                        </button>
                        <p className="mt-1 text-xs text-gray-400">
                          {pendingFilters.adult
                            ? t('filters.includingAdult')
                            : t('filters.excludingAdult')}
                        </p>
                      </div>
                    </div>

                    {/* Filter Action Buttons */}
                    <div className="flex gap-3 border-t border-gray-700 pt-4">
                      <button
                        onClick={applyFilters}
                        disabled={!hasPendingChanges}
                        className={`flex-1 rounded-md px-4 py-3 font-medium text-white transition-colors focus:outline-none focus:ring-2 ${
                          hasPendingChanges
                            ? 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
                            : 'cursor-not-allowed bg-gray-500'
                        }`}
                      >
                        {hasPendingChanges
                          ? `${t('filters.apply')} (${t('filterOptions.changesCount', { count: changedFiltersCount })})`
                          : t('messages.noChanges')}
                      </button>
                      <button
                        onClick={cancelFilters}
                        className="flex-1 rounded-md bg-gray-600 px-4 py-3 font-medium text-white transition-colors hover:bg-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-500"
                      >
                        {t('actions.cancel')}
                      </button>
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
                        <span>{t('actions.loading')}</span>
                      </div>
                    )}
                    {!isFetchingNextPage && isFastScrolling && (
                      <div className="text-gray-400">
                        <span>{t('actions.scrollSlower')}</span>
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
                      {isFetchingNextPage ? t('actions.loading') : t('actions.loadMore')}
                    </button>
                  </div>
                )}

                {/* End of Results Message
                {!data?.pages?.[data.pages.length - 1]?.next_search_after && movies.length > 0 && (
                  <div className="mt-8 text-center text-gray-400">
                    <div className="inline-flex items-center gap-2 rounded-lg bg-gray-800/50 px-4 py-2">
                      <span>
                        {t('messages.exploreAll', { count: movies.length.toLocaleString() })}
                      </span>
                    </div>
                  </div>
                )} */}

                {/* Empty State */}
                {movies.length === 0 && !isLoading && (
                  <div className="py-12 text-center text-gray-400">
                    <div className="mx-auto max-w-md">
                      <div className="mb-4 text-6xl">🎬</div>
                      <p className="text-xl font-semibold text-white">{t('messages.noMovies')}</p>
                      <p className="mt-2">{t('messages.tryAdjusting')}</p>
                      <button
                        onClick={resetFilters}
                        className="mt-4 rounded-md bg-red-600 px-4 py-2 text-white transition-colors hover:bg-red-700"
                      >
                        {t('actions.clearFilters')}
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
        </ImagePreloader>
      </div>
    </>
  );
};

export default MoviesPage;
