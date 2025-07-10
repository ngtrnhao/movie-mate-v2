import React, { useState, useEffect, useCallback } from 'react';
import {
  EyeIcon,
  EyeSlashIcon,
  StarIcon,
  FireIcon,
  TrophyIcon,
  CalendarIcon,
  ClockIcon,
  CheckCircleIcon,
  XMarkIcon,
  PencilIcon,
  AdjustmentsHorizontalIcon,
  MagnifyingGlassIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import {
  StarIcon as StarIconSolid,
  FireIcon as FireIconSolid,
  TrophyIcon as TrophyIconSolid,
} from '@heroicons/react/24/solid';
import {
  getAdminMovies,
  getProductionMetrics,
  toggleMovieFeatured,
  toggleMoviePopular,
  toggleMovieTopRated,
  toggleMovieUpcoming,
  performBulkAction,
  scheduleMovieVisibility,
} from '../../../api/adminMovieService';
import { useDebounce } from '../../../hooks/useDebounce';
import { useProductionMetrics } from '../../../hooks/useProductionMetrics';

const VisibilityControl = () => {
  // State Management
  const [activeSection, setActiveSection] = useState('featured');
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedMovies, setSelectedMovies] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const debouncedSearchQuery = useDebounce(searchQuery, 500);
  const [showScheduler, setShowScheduler] = useState(false);
  const [schedulerData, setSchedulerData] = useState({
    movie_id: null,
    type: 'featured',
    start_date: '',
    end_date: '',
    priority: 1,
  });

  // Visibility Stats
  const [stats, setStats] = useState({
    featured: 0,
    popular: 0,
    top_rated: 0,
    upcoming: 0,
    scheduled: 0,
  });

  const {
    data: productionMetrics,
    loading: metricsLoading,
    error: metricsError,
    refreshMetrics,
  } = useProductionMetrics();
  const [localData, setLocalData] = useState({});

  // Visibility Categories Configuration with Enhanced Styling
  const visibilityCategories = {
    featured: {
      title: 'Featured Movies',
      description: 'Phim được đặc biệt nổi bật trên trang chủ',
      icon: StarIcon,
      iconSolid: StarIconSolid,
      color: 'yellow',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      textColor: 'text-yellow-900',
      iconColor: 'text-yellow-600',
      buttonColor: 'bg-yellow-600 hover:bg-yellow-700',
      field: 'admin_featured',
      api_action: 'toggle_featured',
    },
    popular: {
      title: 'Popular Movies',
      description: 'Phim phổ biến và hot trend',
      icon: FireIcon,
      iconSolid: FireIconSolid,
      color: 'red',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      textColor: 'text-red-900',
      iconColor: 'text-red-600',
      buttonColor: 'bg-red-600 hover:bg-red-700',
      field: 'is_popular',
      api_action: 'toggle_popular',
    },
    top_rated: {
      title: 'Top Rated Movies',
      description: 'Phim có rating cao nhất',
      icon: TrophyIcon,
      iconSolid: TrophyIconSolid,
      color: 'blue',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      textColor: 'text-blue-900',
      iconColor: 'text-blue-600',
      buttonColor: 'bg-blue-600 hover:bg-blue-700',
      field: 'is_top_rated',
      api_action: 'toggle_top_rated',
    },
    upcoming: {
      title: 'Upcoming Movies',
      description: 'Phim sắp ra mắt và đáng chờ đợi',
      icon: CalendarIcon,
      iconSolid: CalendarIcon,
      color: 'green',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      textColor: 'text-green-900',
      iconColor: 'text-green-600',
      buttonColor: 'bg-green-600 hover:bg-green-700',
      field: 'is_upcoming',
      api_action: 'toggle_upcoming',
    },
  };

  // Fetch Movies for Current Section
  const fetchMovies = useCallback(async () => {
    setLoading(true);
    try {
      const category = visibilityCategories[activeSection];
      const filters = {
        ordering: '-admin_priority,-created_at',
      };

      // Add category filter if not showing all
      if (activeSection !== 'all') {
        filters[category.field] = 'true';
      }

      const params = {
        pageSize: 5,
        filters,
        search: debouncedSearchQuery, // Use debounced search
      };

      const data = await getAdminMovies(params);

      if (data.results) {
        setMovies(data.results);
      } else {
        setMovies(data || []);
      }
    } catch (error) {
      console.error('Error fetching movies:', error);
    } finally {
      setLoading(false);
    }
  }, [activeSection, debouncedSearchQuery]); // Use debounced search

  // Fetch Visibility Stats
  const fetchStats = useCallback(async () => {
    try {
      const data = await getProductionMetrics();
      setStats({
        featured: data.admin_featured_count || 0,
        popular: data.popular_count || 0,
        top_rated: data.top_rated_count || 0,
        upcoming: data.upcoming_count || 0,
        scheduled: data.scheduled_count || 0,
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  }, []);

  // Toggle Visibility Action
  const toggleVisibility = useCallback(
    async (movieId, type) => {
      try {
        // Map API actions to service functions
        const actionToServiceMap = {
          toggle_featured: toggleMovieFeatured,
          toggle_popular: toggleMoviePopular,
          toggle_top_rated: toggleMovieTopRated,
          toggle_upcoming: toggleMovieUpcoming,
        };

        const category = visibilityCategories[type];
        const serviceFunction = actionToServiceMap[category.api_action];

        if (serviceFunction) {
          await serviceFunction(movieId);
          // Refresh current list and stats
          fetchMovies();
          fetchStats();
        } else {
          console.error('Unknown visibility type:', type);
        }
      } catch (error) {
        console.error('Error toggling visibility:', error);
      }
    },
    [fetchMovies, fetchStats]
  );

  // Bulk Toggle Visibility
  const bulkToggleVisibility = useCallback(
    async (movieIds, type, enable) => {
      try {
        const action = enable ? `enable_${type}` : `disable_${type}`;
        await performBulkAction(action, movieIds);
        setSelectedMovies([]);
        fetchMovies();
        fetchStats();
      } catch (error) {
        console.error('Error performing bulk toggle:', error);
      }
    },
    [fetchMovies, fetchStats]
  );

  // Schedule Visibility
  const scheduleVisibility = useCallback(async () => {
    try {
      await scheduleMovieVisibility(schedulerData.movie_id, schedulerData);
      setShowScheduler(false);
      setSchedulerData({
        movie_id: null,
        type: 'featured',
        start_date: '',
        end_date: '',
        priority: 1,
      });
      fetchMovies();
      fetchStats();
    } catch (error) {
      console.error('Error scheduling visibility:', error);
    }
  }, [schedulerData, fetchMovies, fetchStats]);

  // Event Handlers
  const handleSelectAll = () => {
    setSelectedMovies(selectedMovies.length === movies.length ? [] : movies.map(m => m.id));
  };

  const handleMovieSelect = movieId => {
    setSelectedMovies(prev =>
      prev.includes(movieId) ? prev.filter(id => id !== movieId) : [...prev, movieId]
    );
  };

  const handleSearchChange = e => {
    setSearchQuery(e.target.value);
  };

  // Load data on mount and when dependencies change
  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  useEffect(() => {
    fetchMovies();
  }, [fetchMovies]);

  // Render Movie Card
  const renderMovieCard = movie => {
    const category = visibilityCategories[activeSection];
    const isActive = movie[category?.field] || false;

    return (
      <div
        key={movie.id}
        className={`rounded-lg border bg-white shadow-sm transition-all duration-200 hover:shadow-md ${
          selectedMovies.includes(movie.id)
            ? 'border-blue-300 ring-2 ring-blue-500'
            : 'border-gray-200'
        }`}
      >
        <div className="p-4">
          {/* Movie Header */}
          <div className="mb-3 flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={selectedMovies.includes(movie.id)}
                onChange={() => handleMovieSelect(movie.id)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />

              {movie.poster_url ? (
                <img
                  src={movie.poster_url}
                  alt={movie.title}
                  className="h-16 w-12 rounded object-cover"
                />
              ) : (
                <div className="flex h-16 w-12 items-center justify-center rounded bg-gray-200">
                  <EyeIcon className="size-6 text-gray-400" />
                </div>
              )}

              <div className="min-w-0 flex-1">
                <h3 className="truncate text-sm font-medium text-gray-900">{movie.title}</h3>
                <p className="mt-1 text-xs text-gray-500">
                  ID: {movie.id} • Priority:{' '}
                  <span className="font-medium text-gray-700">{movie.admin_priority || 0}</span>
                </p>
              </div>
            </div>

            {/* Status Indicator */}
            {isActive && category && (
              <div
                className={`rounded-full p-2 ${category.bgColor} ${category.borderColor} border`}
              >
                <category.iconSolid className={`size-4 ${category.iconColor}`} />
              </div>
            )}
          </div>

          {/* Status Badges */}
          <div className="mb-3 flex flex-wrap gap-2">
            {movie.admin_featured && (
              <span className="inline-flex items-center rounded-full border border-yellow-200 bg-yellow-100 px-2 py-1 text-xs font-medium text-yellow-800">
                <StarIconSolid className="mr-1 size-3" />
                Featured
              </span>
            )}
            {movie.is_popular && (
              <span className="inline-flex items-center rounded-full border border-red-200 bg-red-100 px-2 py-1 text-xs font-medium text-red-800">
                <FireIconSolid className="mr-1 size-3" />
                Popular
              </span>
            )}
            {movie.is_top_rated && (
              <span className="inline-flex items-center rounded-full border border-blue-200 bg-blue-100 px-2 py-1 text-xs font-medium text-blue-800">
                <TrophyIconSolid className="mr-1 size-3" />
                Top Rated
              </span>
            )}
            {movie.is_upcoming && (
              <span className="inline-flex items-center rounded-full border border-green-200 bg-green-100 px-2 py-1 text-xs font-medium text-green-800">
                <CalendarIcon className="mr-1 size-3" />
                Upcoming
              </span>
            )}
          </div>

          {/* Movie Info */}
          <div className="mb-3 grid grid-cols-2 gap-2 text-xs">
            <div className="text-gray-600">
              <span className="text-gray-500">Rating:</span>{' '}
              <span className="font-medium text-gray-700">{movie.cached_imdb_rating || 'N/A'}</span>
            </div>
            <div className="text-gray-600">
              <span className="text-gray-500">Views:</span>{' '}
              <span className="font-medium text-gray-700">
                {movie.production_metrics?.homepage_views || 0}
              </span>
            </div>
          </div>

          {/* Enhanced Movie Info */}
          <div className="mb-3 grid grid-cols-2 gap-2 text-xs">
            <div className="text-gray-600">
              <span className="text-gray-500">Quality:</span>{' '}
              <span className="font-medium text-gray-700">{movie.quality_score || 'N/A'}</span>
            </div>
            <div className="text-gray-600">
              <span className="text-gray-500">Complete:</span>{' '}
              <span className="font-medium text-gray-700">{movie.content_completeness || 0}%</span>
            </div>
          </div>

          {/* Quality Standards Indicator */}
          {movie.minimum_quality_met !== undefined && (
            <div className="mb-3">
              {movie.minimum_quality_met ? (
                <span className="inline-flex items-center rounded-full border border-green-200 bg-green-100 px-2 py-1 text-xs font-medium text-green-800">
                  <CheckCircleIcon className="mr-1 size-3" />
                  Đạt chuẩn
                </span>
              ) : (
                <span className="inline-flex items-center rounded-full border border-red-200 bg-red-100 px-2 py-1 text-xs font-medium text-red-800">
                  <XCircleIcon className="mr-1 size-3" />
                  Chưa đạt chuẩn
                </span>
              )}
            </div>
          )}

          {/* Enhanced Production Metrics */}
          {movie.production_metrics && (
            <div className="mb-3 grid grid-cols-3 gap-1 text-xs">
              <div className="text-gray-600">
                <span className="text-gray-500">Detail:</span>{' '}
                <span className="font-medium text-gray-700">
                  {movie.production_metrics.detail_page_views || 0}
                </span>
              </div>
              <div className="text-gray-600">
                <span className="text-gray-500">Trailers:</span>{' '}
                <span className="font-medium text-gray-700">
                  {movie.production_metrics.trailer_plays || 0}
                </span>
              </div>
              <div className="text-gray-600">
                <span className="text-gray-500">CTR:</span>{' '}
                <span className="font-medium text-gray-700">
                  {movie.production_metrics.click_through_rate || 0}%
                </span>
              </div>
            </div>
          )}

          {/* Scheduling Information */}
          {(movie.featured_from || movie.featured_until) && (
            <div className="mb-3 text-xs text-gray-500">
              <ClockIcon className="mr-1 inline size-3" />
              Featured: {movie.featured_from && new Date(movie.featured_from).toLocaleDateString()}
              {movie.featured_until && ` - ${new Date(movie.featured_until).toLocaleDateString()}`}
            </div>
          )}

          {/* Quick Actions */}
          <div className="flex items-center justify-between border-t border-gray-100 pt-3">
            <div className="flex space-x-2">
              <button
                onClick={() => toggleVisibility(movie.id, activeSection)}
                className={`inline-flex items-center rounded-md border border-transparent px-3 py-1 text-xs font-medium text-white transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                  isActive
                    ? 'bg-gray-600 hover:bg-gray-700 focus:ring-gray-500'
                    : category?.buttonColor + ' focus:ring-' + category.color + '-500'
                }`}
                title={isActive ? `Bỏ ${category?.title}` : `Đặt ${category?.title}`}
              >
                {isActive ? (
                  <>
                    <XMarkIcon className="mr-1 size-3" />
                    Bỏ {category?.color === 'yellow' ? 'Featured' : category?.title.split(' ')[0]}
                  </>
                ) : (
                  <>
                    <category.icon className="mr-1 size-3" />
                    Đặt {category?.color === 'yellow' ? 'Featured' : category?.title.split(' ')[0]}
                  </>
                )}
              </button>

              {!isActive && (
                <button
                  onClick={() => {
                    setSchedulerData({ ...schedulerData, movie_id: movie.id, type: activeSection });
                    setShowScheduler(true);
                  }}
                  className="inline-flex items-center rounded border border-gray-300 bg-white px-2 py-1 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                  title="Lên lịch hiển thị"
                >
                  <ClockIcon className="mr-1 size-3" />
                  Lên lịch
                </button>
              )}
            </div>

            <div className="flex space-x-1">
              <button
                className="rounded p-1 text-gray-400 transition-colors hover:text-blue-600"
                title="Chỉnh sửa"
              >
                <PencilIcon className="size-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderContent = () => {
    if (metricsLoading || loading) {
      return (
        <div className="flex h-64 items-center justify-center">
          <div className="size-12 animate-spin rounded-full border-b-2 border-purple-600"></div>
        </div>
      );
    }

    if (metricsError) {
      return (
        <div className="py-8 text-center">
          <div className="mb-4 text-red-600">{metricsError}</div>
          <button
            onClick={refreshMetrics}
            className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
          >
            Thử lại
          </button>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="flex items-center text-2xl font-bold text-gray-900">
                <AdjustmentsHorizontalIcon className="mr-3 size-8 text-purple-600" />
                Điều khiển hiển thị
              </h1>
              <p className="mt-2 text-gray-600">
                Quản lý visibility và featured status của phim trên production
              </p>
            </div>

            <div className="flex items-center space-x-3">
              <button
                onClick={() => setShowScheduler(true)}
                className="inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
              >
                <ClockIcon className="mr-2 size-4" />
                Lên lịch hiển thị
              </button>
            </div>
          </div>

          {/* Visibility Stats */}
          <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-5">
            {Object.entries(visibilityCategories).map(([key, category]) => (
              <div
                key={key}
                className={`${category.bgColor} rounded-lg border p-4 ${category.borderColor} cursor-pointer transition-all duration-200 hover:shadow-md ${
                  activeSection === key ? 'ring-2 ring-purple-500' : ''
                }`}
                onClick={() => setActiveSection(key)}
              >
                <div className="flex items-center">
                  <category.icon className={`size-8 ${category.iconColor}`} />
                  <div className="ml-3">
                    <p className={`text-sm font-medium ${category.textColor}`}>
                      {category.title.split(' ')[0]}
                    </p>
                    <p className={`text-2xl font-bold ${category.iconColor}`}>
                      {stats[key]?.toLocaleString() || 0}
                    </p>
                  </div>
                </div>
              </div>
            ))}

            <div className="rounded-lg border border-purple-200 bg-purple-50 p-4">
              <div className="flex items-center">
                <ClockIcon className="size-8 text-purple-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-purple-900">Đã lên lịch</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {stats.scheduled?.toLocaleString() || 0}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Search and Controls */}
          <div className="flex items-center justify-between">
            <div className="max-w-md flex-1">
              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                  <MagnifyingGlassIcon className="size-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={handleSearchChange}
                  className="block w-full rounded-md border border-gray-300 bg-white py-2 pl-10 pr-3 leading-5 text-gray-900 placeholder:text-gray-500 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 focus:placeholder:text-gray-400"
                  placeholder="Tìm kiếm phim..."
                />
                {searchQuery && (
                  <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                    <button
                      onClick={() => setSearchQuery('')}
                      className="text-gray-400 transition-colors hover:text-gray-500"
                    >
                      <XMarkIcon className="size-4" />
                    </button>
                  </div>
                )}
              </div>
            </div>

            {selectedMovies.length > 0 && (
              <div className="flex items-center space-x-3">
                <span className="text-sm font-medium text-gray-600">
                  Đã chọn {selectedMovies.length} phim
                </span>

                <div className="flex space-x-2">
                  <button
                    onClick={() => bulkToggleVisibility(selectedMovies, activeSection, true)}
                    className={`inline-flex items-center rounded-md border border-transparent px-3 py-2 text-sm font-medium leading-4 text-white transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                      visibilityCategories[activeSection]?.buttonColor +
                      ' focus:ring-' +
                      visibilityCategories[activeSection]?.color +
                      '-500'
                    }`}
                  >
                    {visibilityCategories[activeSection]?.icon &&
                      React.createElement(visibilityCategories[activeSection].icon, {
                        className: 'w-4 h-4 mr-1',
                      })}
                    Bật {visibilityCategories[activeSection]?.title.split(' ')[0]}
                  </button>

                  <button
                    onClick={() => bulkToggleVisibility(selectedMovies, activeSection, false)}
                    className="inline-flex items-center rounded-md border border-transparent bg-gray-600 px-3 py-2 text-sm font-medium leading-4 text-white transition-colors hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                  >
                    <XMarkIcon className="mr-1 size-4" />
                    Tắt
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Current Section Display */}
        {activeSection !== 'all' && (
          <div
            className={`${visibilityCategories[activeSection]?.bgColor} rounded-lg border ${visibilityCategories[activeSection]?.borderColor} p-4`}
          >
            <div className="flex items-center">
              {visibilityCategories[activeSection]?.iconSolid &&
                React.createElement(visibilityCategories[activeSection].iconSolid, {
                  className: `w-6 h-6 ${visibilityCategories[activeSection]?.iconColor} mr-3`,
                })}
              <div>
                <h3
                  className={`text-lg font-medium ${visibilityCategories[activeSection]?.textColor}`}
                >
                  {visibilityCategories[activeSection]?.title}
                </h3>
                <p className="mt-1 text-sm text-gray-600">
                  {visibilityCategories[activeSection]?.description}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Movies Grid */}
        <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="size-8 animate-spin rounded-full border-b-2 border-purple-600"></div>
              <span className="ml-3 text-gray-600">Đang tải...</span>
            </div>
          ) : movies.length === 0 ? (
            <div className="py-12 text-center">
              <EyeSlashIcon className="mx-auto size-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">Không có phim nào</h3>
              <p className="mt-1 text-sm text-gray-500">
                {debouncedSearchQuery
                  ? `Không tìm thấy phim nào với từ khóa "${debouncedSearchQuery}"`
                  : `Chưa có phim nào trong danh mục ${visibilityCategories[activeSection]?.title || 'này'}`}
              </p>
              {debouncedSearchQuery && (
                <div className="mt-6">
                  <button
                    onClick={() => setSearchQuery('')}
                    className="inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                  >
                    Xóa tìm kiếm
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="p-6">
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <input
                    type="checkbox"
                    checked={selectedMovies.length === movies.length && movies.length > 0}
                    onChange={handleSelectAll}
                    className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                  />
                  <span className="text-sm text-gray-600">
                    Hiển thị <span className="font-medium text-gray-900">{movies.length}</span> phim
                    {debouncedSearchQuery && (
                      <span className="text-gray-500">
                        {' '}
                        • Tìm kiếm: "<span className="font-medium">{debouncedSearchQuery}</span>"
                      </span>
                    )}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {movies.map(renderMovieCard)}
              </div>
            </div>
          )}
        </div>

        {/* Scheduler Modal */}
        {showScheduler && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
            <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Lên lịch hiển thị</h3>
                <button
                  onClick={() => setShowScheduler(false)}
                  className="text-gray-400 transition-colors hover:text-gray-500"
                >
                  <XMarkIcon className="size-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Loại hiển thị
                  </label>
                  <select
                    value={schedulerData.type}
                    onChange={e => setSchedulerData({ ...schedulerData, type: e.target.value })}
                    className="block w-full rounded-md border-gray-300 text-gray-900 shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                  >
                    {Object.entries(visibilityCategories).map(([key, category]) => (
                      <option key={key} value={key}>
                        {category.title}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Ngày bắt đầu
                  </label>
                  <input
                    type="datetime-local"
                    value={schedulerData.start_date}
                    onChange={e =>
                      setSchedulerData({ ...schedulerData, start_date: e.target.value })
                    }
                    className="block w-full rounded-md border-gray-300 text-gray-900 shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Ngày kết thúc
                  </label>
                  <input
                    type="datetime-local"
                    value={schedulerData.end_date}
                    onChange={e => setSchedulerData({ ...schedulerData, end_date: e.target.value })}
                    className="block w-full rounded-md border-gray-300 text-gray-900 shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Độ ưu tiên (1-10)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={schedulerData.priority}
                    onChange={e =>
                      setSchedulerData({ ...schedulerData, priority: parseInt(e.target.value) })
                    }
                    className="block w-full rounded-md border-gray-300 text-gray-900 shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                  />
                </div>
              </div>

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setShowScheduler(false)}
                  className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                >
                  Hủy
                </button>
                <button
                  onClick={scheduleVisibility}
                  className="rounded-md border border-transparent bg-purple-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
                >
                  Lên lịch
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  return renderContent();
};

export default VisibilityControl;
