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
  PlusIcon,
  PencilIcon,
  TrashIcon,
  AdjustmentsHorizontalIcon,
  BoltIcon,
  GlobeAltIcon,
  ShieldCheckIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  ExclamationTriangleIcon,
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
        className={`bg-white rounded-lg shadow-sm border transition-all duration-200 hover:shadow-md ${
          selectedMovies.includes(movie.id)
            ? 'ring-2 ring-blue-500 border-blue-300'
            : 'border-gray-200'
        }`}
      >
        <div className="p-4">
          {/* Movie Header */}
          <div className="flex items-start justify-between mb-3">
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
                  className="w-12 h-16 object-cover rounded"
                />
              ) : (
                <div className="w-12 h-16 bg-gray-200 rounded flex items-center justify-center">
                  <EyeIcon className="w-6 h-6 text-gray-400" />
                </div>
              )}

              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-medium text-gray-900 truncate">{movie.title}</h3>
                <p className="text-xs text-gray-500 mt-1">
                  ID: {movie.id} • Priority:{' '}
                  <span className="font-medium text-gray-700">{movie.admin_priority || 0}</span>
                </p>
              </div>
            </div>

            {/* Status Indicator */}
            {isActive && category && (
              <div
                className={`p-2 rounded-full ${category.bgColor} ${category.borderColor} border`}
              >
                <category.iconSolid className={`w-4 h-4 ${category.iconColor}`} />
              </div>
            )}
          </div>

          {/* Status Badges */}
          <div className="flex flex-wrap gap-2 mb-3">
            {movie.admin_featured && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200">
                <StarIconSolid className="w-3 h-3 mr-1" />
                Featured
              </span>
            )}
            {movie.is_popular && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 border border-red-200">
                <FireIconSolid className="w-3 h-3 mr-1" />
                Popular
              </span>
            )}
            {movie.is_top_rated && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
                <TrophyIconSolid className="w-3 h-3 mr-1" />
                Top Rated
              </span>
            )}
            {movie.is_upcoming && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200">
                <CalendarIcon className="w-3 h-3 mr-1" />
                Upcoming
              </span>
            )}
          </div>

          {/* Movie Info */}
          <div className="grid grid-cols-2 gap-2 text-xs mb-3">
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
          <div className="grid grid-cols-2 gap-2 text-xs mb-3">
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
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200">
                  <CheckCircleIcon className="w-3 h-3 mr-1" />
                  Đạt chuẩn
                </span>
              ) : (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 border border-red-200">
                  <XCircleIcon className="w-3 h-3 mr-1" />
                  Chưa đạt chuẩn
                </span>
              )}
            </div>
          )}

          {/* Enhanced Production Metrics */}
          {movie.production_metrics && (
            <div className="grid grid-cols-3 gap-1 text-xs mb-3">
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
            <div className="text-xs text-gray-500 mb-3">
              <ClockIcon className="w-3 h-3 inline mr-1" />
              Featured: {movie.featured_from && new Date(movie.featured_from).toLocaleDateString()}
              {movie.featured_until && ` - ${new Date(movie.featured_until).toLocaleDateString()}`}
            </div>
          )}

          {/* Quick Actions */}
          <div className="flex items-center justify-between pt-3 border-t border-gray-100">
            <div className="flex space-x-2">
              <button
                onClick={() => toggleVisibility(movie.id, activeSection)}
                className={`inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded-md text-white transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                  isActive
                    ? 'bg-gray-600 hover:bg-gray-700 focus:ring-gray-500'
                    : category?.buttonColor + ' focus:ring-' + category.color + '-500'
                }`}
                title={isActive ? `Bỏ ${category?.title}` : `Đặt ${category?.title}`}
              >
                {isActive ? (
                  <>
                    <XMarkIcon className="w-3 h-3 mr-1" />
                    Bỏ {category?.color === 'yellow' ? 'Featured' : category?.title.split(' ')[0]}
                  </>
                ) : (
                  <>
                    <category.icon className="w-3 h-3 mr-1" />
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
                  className="inline-flex items-center px-2 py-1 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
                  title="Lên lịch hiển thị"
                >
                  <ClockIcon className="w-3 h-3 mr-1" />
                  Lên lịch
                </button>
              )}
            </div>

            <div className="flex space-x-1">
              <button
                className="p-1 text-gray-400 hover:text-blue-600 rounded transition-colors"
                title="Chỉnh sửa"
              >
                <PencilIcon className="w-4 h-4" />
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
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
        </div>
      );
    }

    if (metricsError) {
      return (
        <div className="text-center py-8">
          <div className="text-red-600 mb-4">{metricsError}</div>
          <button
            onClick={refreshMetrics}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Thử lại
          </button>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                <AdjustmentsHorizontalIcon className="w-8 h-8 text-purple-600 mr-3" />
                Điều khiển hiển thị
              </h1>
              <p className="text-gray-600 mt-2">
                Quản lý visibility và featured status của phim trên production
              </p>
            </div>

            <div className="flex items-center space-x-3">
              <button
                onClick={() => setShowScheduler(true)}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
              >
                <ClockIcon className="w-4 h-4 mr-2" />
                Lên lịch hiển thị
              </button>
            </div>
          </div>

          {/* Visibility Stats */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
            {Object.entries(visibilityCategories).map(([key, category]) => (
              <div
                key={key}
                className={`${category.bgColor} rounded-lg p-4 border ${category.borderColor} cursor-pointer transition-all duration-200 hover:shadow-md ${
                  activeSection === key ? 'ring-2 ring-purple-500' : ''
                }`}
                onClick={() => setActiveSection(key)}
              >
                <div className="flex items-center">
                  <category.icon className={`w-8 h-8 ${category.iconColor}`} />
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

            <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
              <div className="flex items-center">
                <ClockIcon className="w-8 h-8 text-purple-600" />
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
            <div className="flex-1 max-w-md">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={handleSearchChange}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 text-gray-900 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Tìm kiếm phim..."
                />
                {searchQuery && (
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                    <button
                      onClick={() => setSearchQuery('')}
                      className="text-gray-400 hover:text-gray-500 transition-colors"
                    >
                      <XMarkIcon className="h-4 w-4" />
                    </button>
                  </div>
                )}
              </div>
            </div>

            {selectedMovies.length > 0 && (
              <div className="flex items-center space-x-3">
                <span className="text-sm text-gray-600 font-medium">
                  Đã chọn {selectedMovies.length} phim
                </span>

                <div className="flex space-x-2">
                  <button
                    onClick={() => bulkToggleVisibility(selectedMovies, activeSection, true)}
                    className={`inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
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
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-gray-600 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
                  >
                    <XMarkIcon className="w-4 h-4 mr-1" />
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
                <p className="text-sm text-gray-600 mt-1">
                  {visibilityCategories[activeSection]?.description}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Movies Grid */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
              <span className="ml-3 text-gray-600">Đang tải...</span>
            </div>
          ) : movies.length === 0 ? (
            <div className="text-center py-12">
              <EyeSlashIcon className="mx-auto h-12 w-12 text-gray-400" />
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
                    className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
                  >
                    Xóa tìm kiếm
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
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

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {movies.map(renderMovieCard)}
              </div>
            </div>
          )}
        </div>

        {/* Scheduler Modal */}
        {showScheduler && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Lên lịch hiển thị</h3>
                <button
                  onClick={() => setShowScheduler(false)}
                  className="text-gray-400 hover:text-gray-500 transition-colors"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Loại hiển thị
                  </label>
                  <select
                    value={schedulerData.type}
                    onChange={e => setSchedulerData({ ...schedulerData, type: e.target.value })}
                    className="block w-full border-gray-300 rounded-md shadow-sm text-gray-900 focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                  >
                    {Object.entries(visibilityCategories).map(([key, category]) => (
                      <option key={key} value={key}>
                        {category.title}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Ngày bắt đầu
                  </label>
                  <input
                    type="datetime-local"
                    value={schedulerData.start_date}
                    onChange={e =>
                      setSchedulerData({ ...schedulerData, start_date: e.target.value })
                    }
                    className="block w-full border-gray-300 rounded-md shadow-sm text-gray-900 focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Ngày kết thúc
                  </label>
                  <input
                    type="datetime-local"
                    value={schedulerData.end_date}
                    onChange={e => setSchedulerData({ ...schedulerData, end_date: e.target.value })}
                    className="block w-full border-gray-300 rounded-md shadow-sm text-gray-900 focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
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
                    className="block w-full border-gray-300 rounded-md shadow-sm text-gray-900 focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                  />
                </div>
              </div>

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setShowScheduler(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
                >
                  Hủy
                </button>
                <button
                  onClick={scheduleVisibility}
                  className="px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 transition-colors"
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
