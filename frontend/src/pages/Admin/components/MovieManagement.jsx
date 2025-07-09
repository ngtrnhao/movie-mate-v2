import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  FilmIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  AdjustmentsHorizontalIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  EyeIcon,
  EyeSlashIcon,
  StarIcon,
  ChartBarIcon,
  PlayIcon,
  CalendarIcon,
  UserIcon,
  TagIcon,
  ExclamationTriangleIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  PhotoIcon,
  GlobeAltIcon,
  ShieldCheckIcon,
  BoltIcon,
  CogIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  Bars3Icon,
  TableCellsIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid, FilmIcon as FilmIconSolid } from '@heroicons/react/24/solid';
import {
  getDashboardOverview,
  getAdminMovies,
  toggleMovieFeatured,
  approveMovie,
  rejectMovie,
  updateMoviePriority,
  performBulkAction,
} from '../../../api/adminMovieService';
import { useDebounce } from '../../../hooks/useDebounce';

// UTILITY FUNCTIONS FOR NEW NORMALIZED STRUCTURE
const getAdminField = (movie, field, fallback = null) => {
  // Try new nested structure first, fallback to legacy direct access
  return movie.admin_control?.[field] ?? movie[field] ?? fallback;
};

const getApprovalInfo = movie => {
  // Use computed approval_info if available, otherwise create from data
  if (movie.approval_info) {
    return movie.approval_info;
  }

  // Fallback: create approval info from available data
  const status = getAdminField(movie, 'approval_status', 'PENDING');
  return {
    status,
    can_approve: status === 'PENDING' || status === 'NEEDS_REVIEW',
    can_reject: status === 'PENDING' || status === 'APPROVED' || status === 'NEEDS_REVIEW',
    requires_review: status === 'NEEDS_REVIEW',
    approved_by: getAdminField(movie, 'approved_by_username') || movie.approved_by?.username,
    approved_at: getAdminField(movie, 'approved_at'),
  };
};

const getProductionMetrics = movie => {
  // Use new production_metrics structure if available
  if (movie.production_metrics) {
    return movie.production_metrics;
  }

  // Fallback: basic metrics
  return {
    homepage_views: 0,
    detail_views: 0,
    detail_page_views: 0,
    trailer_plays: 0,
    click_through_rate: 0,
    engagement_rate: 0,
    performance_score: movie.combined_rating_score || 0,
    trending_score: 0,
  };
};

const isAdminFeatured = movie => {
  // Check if featured with active period
  if (movie.admin_control?.is_featured_active !== undefined) {
    return movie.admin_control.is_featured_active;
  }

  // Fallback to basic featured status
  return getAdminField(movie, 'admin_featured', false);
};

const MovieManagement = () => {
  // State Management
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedMovies, setSelectedMovies] = useState([]);
  const [viewMode, setViewMode] = useState('grid'); // grid, table, kanban
  const [showFilters, setShowFilters] = useState(false);
  const [showBulkActions, setShowBulkActions] = useState(false);

  // Search & Filter States
  const [searchQuery, setSearchQuery] = useState('');
  const debouncedSearchQuery = useDebounce(searchQuery, 500); // 500ms debounce
  const [filters, setFilters] = useState({
    approval_status: '',
    visibility_status: '',
    is_published: '',
    admin_featured: '',
    minimum_quality_met: '',
    category: '',
    sort_by: '-created_at',
  });

  // Dashboard Overview State
  const [overview, setOverview] = useState({
    total_movies: 0,
    published_movies: 0,
    pending_approval: 0,
    admin_featured: 0,
    quality_issues: 0,
    recent_movies: [],
  });

  // Pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrevious, setHasPrevious] = useState(false);

  // Note: Using axiosInstance for all API calls (with automatic auth headers)

  // Fetch Dashboard Overview
  const fetchOverview = useCallback(async () => {
    try {
      const data = await getDashboardOverview();
      setOverview(data);
    } catch (error) {
      console.error('Error fetching overview:', error);
    }
  }, []);

  // Fetch Movies
  const fetchMovies = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = {
        page,
        pageSize: 20,
        filters,
        search: debouncedSearchQuery, // Use debounced search
      };

      const data = await getAdminMovies(params);

      if (data.results) {
        setMovies(data.results);
        setTotalPages(data.totalPages);
        setHasNext(!!data.next);
        setHasPrevious(!!data.previous);
      } else {
        setMovies(data || []);
      }
    } catch (error) {
      console.error('Error fetching movies:', error);
      setError('Không thể tải danh sách phim. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  }, [page, filters, debouncedSearchQuery]); // Use debounced search

  // Movie Actions
  const toggleFeatured = useCallback(
    async movieId => {
      try {
        await toggleMovieFeatured(movieId);
        fetchMovies(); // Refresh list
        fetchOverview(); // Update overview
      } catch (error) {
        console.error('Error toggling featured:', error);
      }
    },
    [fetchMovies, fetchOverview]
  );

  const approveMovieAction = useCallback(
    async movieId => {
      try {
        await approveMovie(movieId);
        fetchMovies();
        fetchOverview();
      } catch (error) {
        console.error('Error approving movie:', error);
      }
    },
    [fetchMovies, fetchOverview]
  );

  const rejectMovieAction = useCallback(
    async (movieId, reason = '') => {
      try {
        await rejectMovie(movieId, reason);
        fetchMovies();
        fetchOverview();
      } catch (error) {
        console.error('Error rejecting movie:', error);
      }
    },
    [fetchMovies, fetchOverview]
  );

  const updatePriorityAction = useCallback(
    async (movieId, priority) => {
      try {
        await updateMoviePriority(movieId, priority);
        fetchMovies();
      } catch (error) {
        console.error('Error updating priority:', error);
      }
    },
    [fetchMovies]
  );

  const bulkAction = useCallback(
    async (action, movieIds) => {
      try {
        await performBulkAction(action, movieIds);
        setSelectedMovies([]);
        fetchMovies();
        fetchOverview();
      } catch (error) {
        console.error('Error performing bulk action:', error);
      }
    },
    [fetchMovies, fetchOverview]
  );

  // Event Handlers
  const handleSearchChange = e => {
    setSearchQuery(e.target.value);
    setPage(1);
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
    }));
    setPage(1);
  };

  const handleMovieSelect = movieId => {
    setSelectedMovies(prev =>
      prev.includes(movieId) ? prev.filter(id => id !== movieId) : [...prev, movieId]
    );
  };

  const handleSelectAll = () => {
    setSelectedMovies(selectedMovies.length === movies.length ? [] : movies.map(m => m.id));
  };

  // Status Badge Component with Fixed Tailwind Classes
  const getStatusBadge = (status, type = 'approval') => {
    const approvalStatusStyles = {
      APPROVED: 'bg-green-100 text-green-800 border-green-200',
      PENDING: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      REJECTED: 'bg-red-100 text-red-800 border-red-200',
      NEEDS_REVIEW: 'bg-orange-100 text-orange-800 border-orange-200',
    };

    const visibilityStatusStyles = {
      PUBLISHED: 'bg-green-100 text-green-800 border-green-200',
      DRAFT: 'bg-gray-100 text-gray-800 border-gray-200',
      SCHEDULED: 'bg-blue-100 text-blue-800 border-blue-200',
      ARCHIVED: 'bg-gray-100 text-gray-800 border-gray-200',
      RESTRICTED: 'bg-red-100 text-red-800 border-red-200',
    };

    const statusConfig = {
      approval: {
        APPROVED: {
          styles: approvalStatusStyles.APPROVED,
          icon: CheckCircleIcon,
          label: 'Đã duyệt',
        },
        PENDING: { styles: approvalStatusStyles.PENDING, icon: ClockIcon, label: 'Chờ duyệt' },
        REJECTED: { styles: approvalStatusStyles.REJECTED, icon: XCircleIcon, label: 'Từ chối' },
        NEEDS_REVIEW: {
          styles: approvalStatusStyles.NEEDS_REVIEW,
          icon: ExclamationTriangleIcon,
          label: 'Cần xem xét',
        },
      },
      visibility: {
        PUBLISHED: { styles: visibilityStatusStyles.PUBLISHED, icon: EyeIcon, label: 'Công khai' },
        DRAFT: { styles: visibilityStatusStyles.DRAFT, icon: EyeSlashIcon, label: 'Bản nháp' },
        SCHEDULED: {
          styles: visibilityStatusStyles.SCHEDULED,
          icon: CalendarIcon,
          label: 'Đã lên lịch',
        },
        ARCHIVED: { styles: visibilityStatusStyles.ARCHIVED, icon: TrashIcon, label: 'Lưu trữ' },
        RESTRICTED: {
          styles: visibilityStatusStyles.RESTRICTED,
          icon: ShieldCheckIcon,
          label: 'Hạn chế',
        },
      },
    };

    const config = statusConfig[type]?.[status];
    if (!config) return null;

    const IconComponent = config.icon;

    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.styles}`}
      >
        <IconComponent className="w-3 h-3 mr-1" />
        {config.label}
      </span>
    );
  };

  // Render Movie Card (Grid View)
  const renderMovieCard = movie => {
    const approvalInfo = getApprovalInfo(movie);
    const productionMetrics = getProductionMetrics(movie);
    const adminFeatured = isAdminFeatured(movie);
    const adminPriority = getAdminField(movie, 'admin_priority', 0);

    return (
      <div
        key={movie.id}
        className={`bg-white rounded-lg shadow-sm border transition-all duration-200 hover:shadow-md ${
          selectedMovies.includes(movie.id)
            ? 'ring-2 ring-blue-500 border-blue-300'
            : 'border-gray-200'
        }`}
      >
        {/* Movie Header */}
        <div className="p-4">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={selectedMovies.includes(movie.id)}
                onChange={() => handleMovieSelect(movie.id)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />

              {movie.poster_path ? (
                <img
                  src={movie.poster_path}
                  alt={movie.title}
                  className="w-12 h-16 object-cover rounded"
                />
              ) : (
                <div className="w-12 h-16 bg-gray-200 rounded flex items-center justify-center">
                  <FilmIcon className="w-6 h-6 text-gray-400" />
                </div>
              )}

              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-medium text-gray-900 truncate">{movie.title}</h3>
                <p className="text-xs text-gray-500 mt-1">
                  ID: {movie.id} • {movie.release_date || 'Chưa có ngày phát hành'}
                </p>

                {/* NEW: Admin Control Info */}
                {movie.admin_control && (
                  <p className="text-xs text-blue-600 mt-1">
                    🆕 Normalized Structure • Priority: {adminPriority}
                  </p>
                )}
              </div>
            </div>

            {/* ENHANCED: Featured Star with active status */}
            {adminFeatured && (
              <div className="flex items-center space-x-1">
                <StarIconSolid className="w-5 h-5 text-yellow-500" />
                {movie.admin_control?.is_featured_active && (
                  <span className="text-xs text-green-600 font-medium">Active</span>
                )}
              </div>
            )}
          </div>

          {/* Status Badges */}
          <div className="flex flex-wrap gap-2 mb-3">
            {getStatusBadge(approvalInfo.status, 'approval')}
            {getStatusBadge(getAdminField(movie, 'visibility_status'), 'visibility')}

            {getAdminField(movie, 'is_published') && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200">
                <EyeIcon className="w-3 h-3 mr-1" />
                Đã xuất bản
              </span>
            )}

            {/* Enhanced approval info */}
            {approvalInfo.approved_by && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
                <UserIcon className="w-3 h-3 mr-1" />
                by {approvalInfo.approved_by}
              </span>
            )}
          </div>

          {/* Quality Metrics */}
          <div className="grid grid-cols-2 gap-2 text-xs mb-3">
            <div className="flex items-center text-gray-600">
              <ChartBarIcon className="w-3 h-3 mr-1 text-blue-500" />
              <span className="text-gray-700">
                Chất lượng:{' '}
                <span className="font-medium text-gray-900">{movie.quality_score || 'N/A'}</span>
              </span>
            </div>
            <div className="flex items-center text-gray-600">
              <BoltIcon className="w-3 h-3 mr-1 text-green-500" />
              <span className="text-gray-700">
                Hoàn thiện:{' '}
                <span className="font-medium text-gray-900">
                  {movie.content_completeness || 0}%
                </span>
              </span>
            </div>
          </div>

          {/* Priority & Rating Info */}
          <div className="grid grid-cols-2 gap-2 text-xs mb-3">
            <div className="text-gray-600">
              <span className="text-gray-500">Priority:</span>{' '}
              <span
                className={`font-medium ${adminPriority > 0 ? 'text-yellow-600' : 'text-gray-700'}`}
              >
                {adminPriority || 0}
              </span>
            </div>
            <div className="text-gray-600">
              <span className="text-gray-500">Rating:</span>{' '}
              <span className="font-medium text-gray-700">
                {movie.combined_rating_score || 'N/A'}
              </span>
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

          {/* Production Metrics */}
          <div className="grid grid-cols-3 gap-2 text-xs mb-3">
            <div className="text-gray-600">
              <span className="text-gray-500">Homepage:</span>{' '}
              <span className="font-medium text-gray-700">{productionMetrics.homepage_views}</span>
            </div>
            <div className="text-gray-600">
              <span className="text-gray-500">Detail:</span>{' '}
              <span className="font-medium text-gray-700">
                {productionMetrics.detail_page_views || productionMetrics.detail_views || 0}
              </span>
            </div>
            <div className="text-gray-600">
              <span className="text-gray-500">Score:</span>{' '}
              <span className="font-medium text-gray-700">
                {productionMetrics.performance_score}
              </span>
            </div>
          </div>

          {/* Additional metrics from new structure */}
          {productionMetrics.trailer_plays > 0 && (
            <div className="grid grid-cols-2 gap-2 text-xs mb-3">
              <div className="text-gray-600">
                <PlayIcon className="w-3 h-3 inline mr-1 text-purple-500" />
                <span className="text-gray-500">Trailers:</span>{' '}
                <span className="font-medium text-gray-700">{productionMetrics.trailer_plays}</span>
              </div>
              <div className="text-gray-600">
                <span className="text-gray-500">CTR:</span>{' '}
                <span className="font-medium text-gray-700">
                  {productionMetrics.click_through_rate}%
                </span>
              </div>
            </div>
          )}

          {/* Scheduling Information */}
          {(movie.featured_from || movie.featured_until) && (
            <div className="text-xs text-gray-500 mb-3">
              <ClockIcon className="w-3 h-3 inline mr-1" />
              Featured: {movie.featured_from} → {movie.featured_until}
            </div>
          )}

          {/* Performance Metrics */}
          {movie.production_metrics && (
            <div className="grid grid-cols-2 gap-2 text-xs mb-3">
              <div className="text-gray-600">
                <span className="text-gray-500">Views:</span>{' '}
                <span className="font-medium text-gray-700">
                  {movie.production_metrics.homepage_views}
                </span>
              </div>
              <div className="text-gray-600">
                <span className="text-gray-500">Score:</span>{' '}
                <span className="font-medium text-gray-700">
                  {movie.production_metrics.performance_score}
                </span>
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <div className="flex items-center justify-between pt-3 border-t border-gray-100">
            <div className="flex space-x-2">
              {approvalInfo.can_approve && (
                <button
                  onClick={() => approveMovieAction(movie.id)}
                  className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors"
                  title="Duyệt phim"
                >
                  <CheckCircleIcon className="w-3 h-3 mr-1" />
                  Duyệt
                </button>
              )}

              {approvalInfo.can_reject && (
                <button
                  onClick={() => rejectMovieAction(movie.id)}
                  className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
                  title="Từ chối"
                >
                  <XCircleIcon className="w-3 h-3 mr-1" />
                  Từ chối
                </button>
              )}
            </div>

            <div className="flex space-x-1">
              <button
                onClick={() => toggleFeatured(movie.id)}
                className={`p-1 rounded transition-colors ${
                  adminFeatured
                    ? 'text-yellow-600 hover:text-yellow-700'
                    : 'text-gray-400 hover:text-yellow-500'
                }`}
                title={adminFeatured ? 'Bỏ featured' : 'Đặt featured'}
              >
                <StarIcon className="w-4 h-4" />
              </button>

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

  // Load data on component mount and when search changes
  useEffect(() => {
    fetchOverview();
  }, [fetchOverview]);

  useEffect(() => {
    fetchMovies();
  }, [fetchMovies]);

  // Active filter indicator
  const hasActiveFilters = useMemo(() => {
    return (
      Object.values(filters).some(value => value && value !== '-created_at') || debouncedSearchQuery
    );
  }, [filters, debouncedSearchQuery]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <FilmIconSolid className="w-8 h-8 text-blue-600 mr-3" />
              Quản lý phim
            </h1>
            <p className="text-gray-600 mt-2">
              Quản lý nội dung phim và điều khiển hiển thị trên production
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`inline-flex items-center px-4 py-2 border rounded-md text-sm font-medium transition-colors ${
                showFilters || hasActiveFilters
                  ? 'border-blue-300 text-blue-700 bg-blue-50'
                  : 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50'
              }`}
            >
              <FunnelIcon className="w-4 h-4 mr-2" />
              Bộ lọc
              {hasActiveFilters && (
                <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  Đang lọc
                </span>
              )}
            </button>

            <div className="flex rounded-md shadow-sm">
              <button
                onClick={() => setViewMode('grid')}
                className={`px-3 py-2 text-sm font-medium border ${
                  viewMode === 'grid'
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                } rounded-l-md transition-colors`}
              >
                <Bars3Icon className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`px-3 py-2 text-sm font-medium border-t border-b ${
                  viewMode === 'table'
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                } rounded-r-md transition-colors`}
              >
                <TableCellsIcon className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-100">
            <div className="flex items-center">
              <FilmIcon className="w-8 h-8 text-blue-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-blue-900">Tổng phim</p>
                <p className="text-2xl font-bold text-blue-600">
                  {overview.total_movies.toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-green-50 rounded-lg p-4 border border-green-100">
            <div className="flex items-center">
              <EyeIcon className="w-8 h-8 text-green-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-green-900">Đã xuất bản</p>
                <p className="text-2xl font-bold text-green-600">
                  {overview.published_movies.toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-100">
            <div className="flex items-center">
              <ClockIcon className="w-8 h-8 text-yellow-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-yellow-900">Chờ duyệt</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {overview.pending_approval.toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-purple-50 rounded-lg p-4 border border-purple-100">
            <div className="flex items-center">
              <StarIcon className="w-8 h-8 text-purple-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-purple-900">Featured</p>
                <p className="text-2xl font-bold text-purple-600">
                  {overview.admin_featured.toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-red-50 rounded-lg p-4 border border-red-100">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="w-8 h-8 text-red-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-red-900">Vấn đề chất lượng</p>
                <p className="text-2xl font-bold text-red-600">
                  {overview.quality_issues.toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Search and Bulk Actions */}
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
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 text-gray-900 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Tìm kiếm theo tên phim..."
              />
              {searchQuery && (
                <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                  <button
                    onClick={() => setSearchQuery('')}
                    className="text-gray-400 hover:text-gray-500"
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
                  onClick={() => bulkAction('approve', selectedMovies)}
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors"
                >
                  <CheckCircleIcon className="w-4 h-4 mr-1" />
                  Duyệt
                </button>

                <button
                  onClick={() => bulkAction('feature', selectedMovies)}
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-yellow-600 hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 transition-colors"
                >
                  <StarIcon className="w-4 h-4 mr-1" />
                  Featured
                </button>

                <button
                  onClick={() => bulkAction('publish', selectedMovies)}
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                >
                  <EyeIcon className="w-4 h-4 mr-1" />
                  Xuất bản
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Trạng thái duyệt
              </label>
              <select
                value={filters.approval_status}
                onChange={e => handleFilterChange('approval_status', e.target.value)}
                className="block w-full border-gray-300 rounded-md shadow-sm text-gray-900 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="">Tất cả</option>
                <option value="APPROVED">Đã duyệt</option>
                <option value="PENDING">Chờ duyệt</option>
                <option value="REJECTED">Từ chối</option>
                <option value="NEEDS_REVIEW">Cần xem xét</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Hiển thị</label>
              <select
                value={filters.visibility_status}
                onChange={e => handleFilterChange('visibility_status', e.target.value)}
                className="block w-full border-gray-300 rounded-md shadow-sm text-gray-900 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="">Tất cả</option>
                <option value="PUBLISHED">Công khai</option>
                <option value="DRAFT">Bản nháp</option>
                <option value="SCHEDULED">Đã lên lịch</option>
                <option value="ARCHIVED">Lưu trữ</option>
                <option value="RESTRICTED">Hạn chế</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Xuất bản</label>
              <select
                value={filters.is_published}
                onChange={e => handleFilterChange('is_published', e.target.value)}
                className="block w-full border-gray-300 rounded-md shadow-sm text-gray-900 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="">Tất cả</option>
                <option value="true">Đã xuất bản</option>
                <option value="false">Chưa xuất bản</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Featured</label>
              <select
                value={filters.admin_featured}
                onChange={e => handleFilterChange('admin_featured', e.target.value)}
                className="block w-full border-gray-300 rounded-md shadow-sm text-gray-900 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="">Tất cả</option>
                <option value="true">Featured</option>
                <option value="false">Không featured</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Chất lượng</label>
              <select
                value={filters.minimum_quality_met}
                onChange={e => handleFilterChange('minimum_quality_met', e.target.value)}
                className="block w-full border-gray-300 rounded-md shadow-sm text-gray-900 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="">Tất cả</option>
                <option value="true">Đạt chuẩn</option>
                <option value="false">Chưa đạt chuẩn</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Sắp xếp</label>
              <select
                value={filters.sort_by}
                onChange={e => handleFilterChange('sort_by', e.target.value)}
                className="block w-full border-gray-300 rounded-md shadow-sm text-gray-900 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="-created_at">Mới nhất</option>
                <option value="created_at">Cũ nhất</option>
                <option value="-release_date">Ngày phát hành (Mới)</option>
                <option value="release_date">Ngày phát hành (Cũ)</option>
                <option value="-admin_priority">Priority (Cao → Thấp)</option>
                <option value="admin_priority">Priority (Thấp → Cao)</option>
                <option value="-combined_rating_score">Rating (Cao → Thấp)</option>
                <option value="combined_rating_score">Rating (Thấp → Cao)</option>
              </select>
            </div>
          </div>

          <div className="mt-4 flex justify-end space-x-3">
            <button
              onClick={() => {
                setFilters({
                  approval_status: '',
                  visibility_status: '',
                  is_published: '',
                  admin_featured: '',
                  minimum_quality_met: '',
                  category: '',
                  sort_by: '-created_at',
                });
                setSearchQuery('');
              }}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
            >
              Xóa tất cả bộ lọc
            </button>
            <button
              onClick={() => setShowFilters(false)}
              className="px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              Áp dụng
            </button>
          </div>
        </div>
      )}

      {/* Movies Grid/Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Đang tải...</span>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Có lỗi xảy ra</h3>
            <p className="mt-1 text-sm text-gray-500">{error}</p>
            <div className="mt-6">
              <button
                onClick={fetchMovies}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                Thử lại
              </button>
            </div>
          </div>
        ) : movies.length === 0 ? (
          <div className="text-center py-12">
            <FilmIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Không có phim nào</h3>
            <p className="mt-1 text-sm text-gray-500">
              {debouncedSearchQuery || Object.values(filters).some(v => v && v !== '-created_at')
                ? 'Không tìm thấy phim nào với tiêu chí đã chọn.'
                : 'Chưa có phim nào trong hệ thống.'}
            </p>
            {(debouncedSearchQuery || hasActiveFilters) && (
              <div className="mt-6">
                <button
                  onClick={() => {
                    setFilters({
                      approval_status: '',
                      visibility_status: '',
                      is_published: '',
                      admin_featured: '',
                      minimum_quality_met: '',
                      category: '',
                      sort_by: '-created_at',
                    });
                    setSearchQuery('');
                  }}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
                >
                  Xóa bộ lọc và tìm kiếm
                </button>
              </div>
            )}
          </div>
        ) : (
          <>
            {/* Grid View */}
            {viewMode === 'grid' && (
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-4">
                    <input
                      type="checkbox"
                      checked={selectedMovies.length === movies.length && movies.length > 0}
                      onChange={handleSelectAll}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-600">
                      Hiển thị <span className="font-medium text-gray-900">{movies.length}</span>{' '}
                      phim
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

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
                <div className="flex-1 flex justify-between sm:hidden">
                  <button
                    onClick={() => setPage(page - 1)}
                    disabled={!hasPrevious}
                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Trước
                  </button>
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={!hasNext}
                    className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Sau
                  </button>
                </div>

                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      Trang <span className="font-medium text-gray-900">{page}</span> /{' '}
                      <span className="font-medium text-gray-900">{totalPages}</span>
                    </p>
                  </div>
                  <div>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                      <button
                        onClick={() => setPage(page - 1)}
                        disabled={!hasPrevious}
                        className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        <ChevronUpIcon className="h-5 w-5 rotate-[-90deg]" />
                      </button>

                      <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                        {page}
                      </span>

                      <button
                        onClick={() => setPage(page + 1)}
                        disabled={!hasNext}
                        className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        <ChevronDownIcon className="h-5 w-5 rotate-[-90deg]" />
                      </button>
                    </nav>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default MovieManagement;
