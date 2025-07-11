import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  FilmIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  EyeIcon,
  EyeSlashIcon,
  StarIcon,
  ChartBarIcon,
  CalendarIcon,
  ExclamationTriangleIcon,
  TrashIcon,
  PhotoIcon,
  ShieldCheckIcon,
  Bars3Icon,
  TableCellsIcon,
  XMarkIcon,
  DocumentCheckIcon,
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid, FilmIcon as FilmIconSolid } from '@heroicons/react/24/solid';
import MovieDetailsModal from '../../../components/common/MovieDetailsModal';
import {
  getAdminMovies,
  toggleMovieFeatured,
  approveMovie,
  rejectMovie,
  updateMoviePriority,
  performBulkAction,
  getDashboardOverview,
} from '../../../api/adminMovieService';
import { useDebounce } from '../../../hooks/useDebounce';
import { useRefreshDashboard } from '../../../hooks/useDashboardData';

// UTILITY FUNCTIONS FOR NEW NORMALIZED STRUCTURE
const getAdminField = (movie, field, fallback = null) => {
  // Try new nested structure first, fallback to legacy direct access
  return movie.admin_control?.[field] ?? movie[field] ?? fallback;
};

const getApprovalInfo = movie => {
  // Use approval_info from API response
  return (
    movie?.approval_info || {
      status: 'PENDING',
      can_approve: false,
      can_reject: false,
      requires_review: false,
      approved_by: null,
      approved_at: null,
    }
  );
};

const getProductionMetrics = movie => {
  return (
    movie?.production_metrics || {
      homepage_views: 0,
      detail_views: 0,
      search_appearances: 0,
      performance_score: 0,
    }
  );
};

const isAdminFeatured = movie => {
  return movie?.admin_featured || false;
};

const MovieManagement = () => {
  const refreshDashboard = useRefreshDashboard();

  // State Management
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedMovies, setSelectedMovies] = useState([]);
  const [viewMode, setViewMode] = useState('grid'); // grid, table, kanban
  const [showFilters, setShowFilters] = useState(false);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [overviewData, setOverviewData] = useState({
    total_movies: 0,
    published_movies: 0,
    pending_approval: 0,
    admin_featured: 0,
    quality_issues: 0,
  });
  const [selectedMovie, setSelectedMovie] = useState(null);

  // Search & Filter States
  const [searchQuery, setSearchQuery] = useState('');
  const debouncedSearchQuery = useDebounce(searchQuery, 500); // 500ms debounce
  const [filters, setFilters] = useState({
    approval_status: 'NEEDS_REVIEW', // Mặc định luôn có filter hợp lệ cho ES
    visibility_status: '',
    is_published: '',
    admin_featured: '',
    minimum_quality_met: '',
    category: '',
    sort_by: '-created_at',
  });
  // Keyset pagination state
  const [afterStack, setAfterStack] = useState([]); // Stack of after_created_at for prev
  const [currentAfter, setCurrentAfter] = useState(null); // Current after_created_at
  const [hasNext, setHasNext] = useState(false);
  const [hasPrevious, setHasPrevious] = useState(false);

  // Fetch Movies (keyset)
  const fetchMovies = useCallback(
    async (direction = 'init') => {
      setLoading(true);
      setError(null);
      try {
        const params = {
          pageSize: 30,
          filters: { ...filters, sort_by: '-created_at' },
          search: debouncedSearchQuery,
        };
        if (currentAfter) params.filters.after_created_at = currentAfter;
        const data = await getAdminMovies(params);
        setMovies(data.results || []);
        // Keyset logic
        if (direction === 'next') {
          setAfterStack(prev => [...prev, currentAfter]);
          setHasPrevious(true);
        } else if (direction === 'prev') {
          setHasPrevious(afterStack.length > 1);
        } else {
          setAfterStack([]);
          setHasPrevious(false);
        }
        setHasNext((data.results || []).length === 5); // Có thể còn trang sau nếu đủ 5 bản ghi
      } catch (error) {
        setError('Không thể tải danh sách phim. Vui lòng thử lại.');
      } finally {
        setLoading(false);
      }
    },
    [filters, debouncedSearchQuery, currentAfter, afterStack]
  );

  // Fetch overview data
  const fetchOverviewData = useCallback(async () => {
    try {
      const data = await getDashboardOverview();
      setOverviewData({
        total_movies: data.total_movies || 0,
        published_movies: data.published_movies || 0,
        pending_approval: data.pending_approval || 0,
        admin_featured: data.admin_featured || 0,
        quality_issues: data.quality_issues || 0,
      });
    } catch (error) {
      console.error('Error fetching overview data:', error);
    }
  }, []);

  // Fetch data on mount and after actions
  useEffect(() => {
    fetchOverviewData();
  }, [fetchOverviewData]);

  // Initial fetch and refetch when filters/search change
  useEffect(() => {
    setCurrentAfter(null);
    fetchMovies('init');
    // eslint-disable-next-line
  }, [filters, debouncedSearchQuery]);

  // Next page
  const handleNextPage = () => {
    if (movies.length > 0) {
      const lastCreatedAt = movies[movies.length - 1].created_at;
      setCurrentAfter(lastCreatedAt);
      fetchMovies('next');
    }
  };
  // Prev page
  const handlePrevPage = () => {
    if (afterStack.length > 0) {
      const prevStack = [...afterStack];
      prevStack.pop();
      setAfterStack(prevStack);
      setCurrentAfter(prevStack[prevStack.length - 1] || null);
      fetchMovies('prev');
    }
  };

  // Update overview after actions
  const handleActionSuccess = useCallback(async () => {
    await Promise.all([fetchMovies(), fetchOverviewData(), refreshDashboard()]);
  }, [fetchMovies, fetchOverviewData, refreshDashboard]);

  // Movie Actions with Redux
  const toggleFeatured = useCallback(
    async movieId => {
      try {
        await toggleMovieFeatured(movieId);
        await handleActionSuccess();
      } catch (error) {
        console.error('Error toggling featured:', error);
      }
    },
    [handleActionSuccess]
  );

  const approveMovieAction = useCallback(
    async movieId => {
      try {
        await approveMovie(movieId);
        await handleActionSuccess();
      } catch (error) {
        console.error('Error approving movie:', error);
      }
    },
    [handleActionSuccess]
  );

  const rejectMovieAction = useCallback(
    async (movieId, reason = '') => {
      try {
        await rejectMovie(movieId, reason);
        await handleActionSuccess();
      } catch (error) {
        console.error('Error rejecting movie:', error);
      }
    },
    [handleActionSuccess]
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
        refreshDashboard();
      } catch (error) {
        console.error('Error performing bulk action:', error);
      }
    },
    [fetchMovies, refreshDashboard]
  );

  // Event Handlers
  const handleSearchChange = e => {
    setSearchQuery(e.target.value);
    setFilters(prev => ({ ...prev, page: 1 }));
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      page: 1,
    }));
  };

  const handlePageChange = newPage => {
    setFilters(prev => ({
      ...prev,
      page: newPage,
    }));
  };

  const handleMovieSelect = movieId => {
    setSelectedMovies(prev =>
      prev.includes(movieId) ? prev.filter(id => id !== movieId) : [...prev, movieId]
    );
  };

  const handleSelectAll = () => {
    setSelectedMovies(selectedMovies.length === movies.length ? [] : movies.map(m => m.id));
  };

  const handleViewDetails = useCallback(movie => {
    setSelectedMovie(movie);
  }, []);

  const handleCloseDetails = useCallback(() => {
    setSelectedMovie(null);
  }, []);

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
        className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${config.styles}`}
      >
        <IconComponent className="mr-1 size-3" />
        {config.label}
      </span>
    );
  };

  // Add renderMovieCard function
  const renderMovieCard = useCallback(
    movie => {
      if (!movie?.id) return null;

      const approvalInfo = getApprovalInfo(movie);
      const metrics = getProductionMetrics(movie);
      const isFeatured = isAdminFeatured(movie);
      const releaseYear = movie?.release_date ? new Date(movie.release_date).getFullYear() : 'N/A';
      const genres = movie?.genres?.map(g => g.name).join(', ') || 'N/A';
      const runtime = movie?.runtime ? `${movie.runtime} min` : 'N/A';
      const qualityScore = movie?.quality_score || 0;
      const completeness = movie?.content_completeness || 0;

      return (
        <div
          key={movie.id}
          className="relative overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm transition-shadow hover:shadow-md"
        >
          {/* Selection Checkbox */}
          <div className="absolute left-2 top-2 z-10">
            <input
              type="checkbox"
              checked={selectedMovies.includes(movie.id)}
              onChange={() => handleMovieSelect(movie.id)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
          </div>

          {/* Movie Poster */}
          <div className="relative aspect-[2/3] bg-gray-100">
            {movie?.poster_path ? (
              <img
                src={movie.poster_path}
                alt={movie?.title || 'Movie poster'}
                className="size-full object-cover"
                loading="lazy"
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center">
                <PhotoIcon className="size-12 text-gray-400" />
              </div>
            )}
            {isFeatured && (
              <div className="absolute right-2 top-2">
                <StarIconSolid className="size-6 text-yellow-400 drop-shadow" />
              </div>
            )}
          </div>

          {/* Movie Info */}
          <div className="p-4">
            <div className="flex items-start justify-between">
              <div className="min-w-0 flex-1">
                <h3 className="truncate text-sm font-medium text-gray-900" title={movie?.title}>
                  {movie?.title || 'Untitled'}
                </h3>
                <div className="mt-1 space-y-1 text-xs text-gray-500">
                  <p className="truncate">{releaseYear}</p>
                  <p className="truncate">{genres}</p>
                  <p className="truncate">{runtime}</p>
                </div>
              </div>
            </div>

            <div className="mt-4 space-y-2">
              {approvalInfo?.status && getStatusBadge(approvalInfo.status, 'approval')}
              {getStatusBadge(movie?.visibility_status || 'DRAFT', 'visibility')}
            </div>

            {/* Quality Metrics */}
            <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center text-gray-500">
                <ChartBarIcon className="mr-1 size-4" />
                {(metrics?.performance_score || 0).toFixed(1)}
              </div>
              <div className="flex items-center text-gray-500">
                <DocumentCheckIcon className="mr-1 size-4" />
                {(completeness || 0).toFixed(1)}%
              </div>
            </div>

            {/* View Metrics */}
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center text-gray-500">
                <EyeIcon className="mr-1 size-4" />
                {metrics?.homepage_views || 0}
              </div>
              <div className="flex items-center text-gray-500">
                <MagnifyingGlassIcon className="mr-1 size-4" />
                {metrics?.search_appearances || 0}
              </div>
            </div>

            {/* Actions */}
            <div className="mt-4 space-y-2">
              {/* Primary Actions Row */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => approveMovieAction(movie.id)}
                  disabled={!approvalInfo?.can_approve}
                  className="inline-flex flex-1 items-center justify-center rounded-md border border-transparent bg-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <CheckCircleIcon className="mr-1.5 size-4" />
                  Duyệt
                </button>
                <button
                  onClick={() => handleViewDetails(movie)}
                  className="inline-flex flex-1 items-center justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
                >
                  <EyeIcon className="mr-1.5 size-4" />
                  Chi tiết
                </button>
              </div>

              {/* Secondary Action */}
              <button
                onClick={() => toggleFeatured(movie.id)}
                className={`inline-flex w-full items-center justify-center rounded-md border px-4 py-2 text-sm font-medium ${
                  isFeatured
                    ? 'border-yellow-300 bg-yellow-50 text-yellow-800 hover:bg-yellow-100'
                    : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                } transition-colors`}
              >
                <StarIcon className="mr-1.5 size-4" />
                {isFeatured ? 'Bỏ Featured' : 'Đánh dấu Featured'}
              </button>
            </div>
          </div>
        </div>
      );
    },
    [selectedMovies, toggleFeatured, approveMovieAction, handleMovieSelect, handleViewDetails]
  );

  // Active filter indicator
  const hasActiveFilters = useMemo(() => {
    return (
      Object.values(filters).some(value => value && value !== '-created_at') || debouncedSearchQuery
    );
  }, [filters, debouncedSearchQuery]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="flex items-center text-2xl font-bold text-gray-900">
              <FilmIconSolid className="mr-3 size-8 text-blue-600" />
              Quản lý phim
            </h1>
            <p className="mt-2 text-gray-600">
              Quản lý nội dung phim và điều khiển hiển thị trên production
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`inline-flex items-center rounded-md border px-4 py-2 text-sm font-medium transition-colors ${
                showFilters || hasActiveFilters
                  ? 'border-blue-300 bg-blue-50 text-blue-700'
                  : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              <FunnelIcon className="mr-2 size-4" />
              Bộ lọc
              {hasActiveFilters && (
                <span className="ml-2 inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
                  Đang lọc
                </span>
              )}
            </button>

            <div className="flex rounded-md shadow-sm">
              <button
                onClick={() => setViewMode('grid')}
                className={`border px-3 py-2 text-sm font-medium ${
                  viewMode === 'grid'
                    ? 'border-blue-600 bg-blue-600 text-white'
                    : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                } rounded-l-md transition-colors`}
              >
                <Bars3Icon className="size-4" />
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`border-y px-3 py-2 text-sm font-medium ${
                  viewMode === 'table'
                    ? 'border-blue-600 bg-blue-600 text-white'
                    : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                } rounded-r-md transition-colors`}
              >
                <TableCellsIcon className="size-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-5">
          <div className="rounded-lg border border-blue-100 bg-blue-50 p-4">
            <div className="flex items-center">
              <FilmIcon className="size-8 text-blue-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-blue-900">Tổng phim</p>
                <p className="text-2xl font-bold text-blue-600">
                  {(overviewData?.total_movies || 0).toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-green-100 bg-green-50 p-4">
            <div className="flex items-center">
              <EyeIcon className="size-8 text-green-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-green-900">Đã xuất bản</p>
                <p className="text-2xl font-bold text-green-600">
                  {(overviewData?.published_movies || 0).toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-yellow-100 bg-yellow-50 p-4">
            <div className="flex items-center">
              <ClockIcon className="size-8 text-yellow-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-yellow-900">Chờ duyệt</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {(overviewData?.pending_approval || 0).toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-purple-100 bg-purple-50 p-4">
            <div className="flex items-center">
              <StarIcon className="size-8 text-purple-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-purple-900">Featured</p>
                <p className="text-2xl font-bold text-purple-600">
                  {(overviewData?.admin_featured || 0).toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-red-100 bg-red-50 p-4">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="size-8 text-red-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-red-900">Vấn đề chất lượng</p>
                <p className="text-2xl font-bold text-red-600">
                  {(overviewData?.quality_issues || 0).toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Search and Bulk Actions */}
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
                className="block w-full rounded-md border border-gray-300 bg-white py-2 pl-10 pr-3 leading-5 text-gray-900 placeholder:text-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:placeholder:text-gray-400"
                placeholder="Tìm kiếm theo tên phim..."
              />
              {searchQuery && (
                <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                  <button
                    onClick={() => setSearchQuery('')}
                    className="text-gray-400 hover:text-gray-500"
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
                  onClick={() => bulkAction('approve', selectedMovies)}
                  className="inline-flex items-center rounded-md border border-transparent bg-green-600 px-3 py-2 text-sm font-medium leading-4 text-white transition-colors hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                >
                  <CheckCircleIcon className="mr-1 size-4" />
                  Duyệt
                </button>

                <button
                  onClick={() => bulkAction('feature', selectedMovies)}
                  className="inline-flex items-center rounded-md border border-transparent bg-yellow-600 px-3 py-2 text-sm font-medium leading-4 text-white transition-colors hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2"
                >
                  <StarIcon className="mr-1 size-4" />
                  Featured
                </button>

                <button
                  onClick={() => bulkAction('publish', selectedMovies)}
                  className="inline-flex items-center rounded-md border border-transparent bg-blue-600 px-3 py-2 text-sm font-medium leading-4 text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  <EyeIcon className="mr-1 size-4" />
                  Xuất bản
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3 lg:grid-cols-6">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Trạng thái duyệt
              </label>
              <select
                value={filters.approval_status}
                onChange={e => handleFilterChange('approval_status', e.target.value)}
                className="block w-full rounded-md border-gray-300 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              >
                <option value="">Tất cả</option>
                <option value="APPROVED">Đã duyệt</option>
                <option value="PENDING">Chờ duyệt</option>
                <option value="REJECTED">Từ chối</option>
                <option value="NEEDS_REVIEW">Cần xem xét</option>
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">Hiển thị</label>
              <select
                value={filters.visibility_status}
                onChange={e => handleFilterChange('visibility_status', e.target.value)}
                className="block w-full rounded-md border-gray-300 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
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
              <label className="mb-2 block text-sm font-medium text-gray-700">Xuất bản</label>
              <select
                value={filters.is_published}
                onChange={e => handleFilterChange('is_published', e.target.value)}
                className="block w-full rounded-md border-gray-300 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              >
                <option value="">Tất cả</option>
                <option value="true">Đã xuất bản</option>
                <option value="false">Chưa xuất bản</option>
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">Featured</label>
              <select
                value={filters.admin_featured}
                onChange={e => handleFilterChange('admin_featured', e.target.value)}
                className="block w-full rounded-md border-gray-300 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              >
                <option value="">Tất cả</option>
                <option value="true">Featured</option>
                <option value="false">Không featured</option>
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">Chất lượng</label>
              <select
                value={filters.minimum_quality_met}
                onChange={e => handleFilterChange('minimum_quality_met', e.target.value)}
                className="block w-full rounded-md border-gray-300 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              >
                <option value="">Tất cả</option>
                <option value="true">Đạt chuẩn</option>
                <option value="false">Chưa đạt chuẩn</option>
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">Sắp xếp</label>
              <select
                value={filters.sort_by}
                onChange={e => handleFilterChange('sort_by', e.target.value)}
                className="block w-full rounded-md border-gray-300 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
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
                  approval_status: 'NEEDS_REVIEW', // Giữ filter hợp lệ cho ES
                  visibility_status: '',
                  is_published: '',
                  admin_featured: '',
                  minimum_quality_met: '',
                  category: '',
                  sort_by: '-created_at',
                  page: 1,
                });
                setSearchQuery('');
              }}
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
            >
              Xóa tất cả bộ lọc
            </button>
            <button
              onClick={() => setShowFilters(false)}
              className="rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Áp dụng
            </button>
          </div>
        </div>
      )}

      {/* Movies Grid/Table */}
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="size-8 animate-spin rounded-full border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Đang tải...</span>
          </div>
        ) : error ? (
          <div className="py-12 text-center">
            <ExclamationTriangleIcon className="mx-auto size-12 text-red-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Có lỗi xảy ra</h3>
            <p className="mt-1 text-sm text-gray-500">{error}</p>
            <div className="mt-6">
              <button
                onClick={fetchMovies}
                className="inline-flex items-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Thử lại
              </button>
            </div>
          </div>
        ) : movies.length === 0 ? (
          <div className="py-12 text-center">
            <FilmIcon className="mx-auto size-12 text-gray-400" />
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
                      approval_status: 'NEEDS_REVIEW', // Giữ filter hợp lệ cho ES
                      visibility_status: '',
                      is_published: '',
                      admin_featured: '',
                      minimum_quality_met: '',
                      category: '',
                      sort_by: '-created_at',
                      page: 1,
                    });
                    setSearchQuery('');
                  }}
                  className="inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
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
                <div className="mb-4 flex items-center justify-between">
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

                <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                  {movies.map(renderMovieCard)}
                </div>
              </div>
            )}

            {/* Pagination */}
            <div className="flex items-center justify-between border-t border-gray-200 bg-gray-50 px-6 py-4">
              <button
                onClick={handlePrevPage}
                disabled={!hasPrevious}
                className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Trước
              </button>
              <button
                onClick={handleNextPage}
                disabled={!hasNext}
                className="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Sau
              </button>
            </div>
          </>
        )}
      </div>

      {/* Movie Details Modal */}
      <MovieDetailsModal
        movie={selectedMovie}
        open={!!selectedMovie}
        onClose={handleCloseDetails}
      />
    </div>
  );
};

export default MovieManagement;
