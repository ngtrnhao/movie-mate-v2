import { useState, useEffect, useCallback, useMemo } from 'react';
import { useTranslation } from '../../i18n/hooks/useTranslation';
import { motion, AnimatePresence } from 'framer-motion';
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
} from 'lucide-react';
import { searchMovies } from '../../api/movieService';
import { useCategories } from '../../hooks/useCategories';
import { useInfiniteQuery } from '@tanstack/react-query';
import MovieCard from '../../components/movies/movie-card';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const MoviesPage = () => {
  const { t } = useTranslation('movies');
  const [showFilters, setShowFilters] = useState(false);
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

  useEffect(() => {
    if (genresData && !genresLoading) {
      setGenres(genresData);
    }
  }, [genresData, genresLoading]);

  // Infinite query for movies
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading, error, refetch } =
    useInfiniteQuery({
      queryKey: ['movies', filters],
      queryFn: ({ pageParam = 1 }) => searchMovies(filters, pageParam, 20),
      getNextPageParam: lastPage => {
        if (lastPage.has_next) {
          return lastPage.current_page + 1;
        }
        return undefined;
      },
      enabled: true,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    });

  // Memoized movie list
  const movies = useMemo(() => {
    return data?.pages?.flatMap(page => page.data) || [];
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
  }, []);

  const handleGenreToggle = useCallback(genreId => {
    setFilters(prev => ({
      ...prev,
      genres: prev.genres.includes(genreId)
        ? prev.genres.filter(id => id !== genreId)
        : [...prev.genres, genreId],
    }));
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
  }, []);

  const loadMore = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  return (
    <div className="min-h-screen bg-gray-900 py-8 pt-20">
      <div className="container mx-auto px-4">
        {/* Header Section */}
        <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">{t('title', 'Discover Movies')}</h1>
            <p className="text-gray-400">
              {data?.pages?.[0]?.count
                ? `${data.pages[0].count.toLocaleString()} movies found`
                : 'Loading...'}
            </p>
          </div>

          <div className="flex gap-2">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2 rounded-md bg-red-600 px-4 py-2 text-white transition-colors hover:bg-red-700"
            >
              {showFilters ? <X size={20} /> : <SlidersHorizontal size={20} />}
              {showFilters ? 'Hide Filters' : 'Show Filters'}
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={resetFilters}
              className="flex items-center gap-2 rounded-md bg-gray-700 px-4 py-2 text-white transition-colors hover:bg-gray-600"
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
                    className="w-full rounded-md bg-gray-700 py-3 pl-10 pr-4 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500"
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
                      className="w-full rounded-md bg-gray-700 p-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500"
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
                      className="w-full rounded-md bg-gray-700 p-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500"
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
        {error && (
          <div className="mb-8 rounded-lg bg-red-900/20 border border-red-500 p-4 text-red-400">
            Error loading movies: {error.message}
          </div>
        )}

        {isLoading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : (
          <>
            <div className="grid gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
              {movies.map((movie, index) => (
                <MovieCard key={`${movie.id}-${index}`} movie={movie} />
              ))}
            </div>

            {/* Load More Button */}
            {hasNextPage && (
              <div className="mt-8 flex justify-center">
                <button
                  onClick={loadMore}
                  disabled={isFetchingNextPage}
                  className="rounded-md bg-red-600 px-6 py-3 text-white transition-colors hover:bg-red-700 disabled:bg-gray-600"
                >
                  {isFetchingNextPage ? 'Loading...' : 'Load More Movies'}
                </button>
              </div>
            )}

            {!hasNextPage && movies.length > 0 && (
              <div className="mt-8 text-center text-gray-400">
                You've reached the end of the results
              </div>
            )}

            {movies.length === 0 && !isLoading && (
              <div className="py-12 text-center text-gray-400">
                <p className="text-xl">No movies found</p>
                <p className="mt-2">Try adjusting your filters</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default MoviesPage;
