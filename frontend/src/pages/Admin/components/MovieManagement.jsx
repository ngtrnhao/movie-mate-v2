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
import MovieQualityModal from '../../../components/common/MovieQualityModal';
import ProductionMetricsCard from './ProductionMetricsCard';
import AdvancedAdminFilters from './AdvancedAdminFilters';
import {
  getAdminMovies,
  toggleMovieFeatured,
  approveMovie,
  rejectMovie,
  updateMoviePriority,
  performBulkAction,
  getDashboardOverview,
  updateMovieQuality,
  resolveMovieIssue,
  enrichMovie,
  getMovieEnrichmentStatus,
  batchEnrichMovies,
  enrichMoviesWithQualityIssues,
  createAdminMovie,
  updateAdminMovie,
  deleteAdminMovie,
  scheduleMovieAction,
} from '../../../api/adminMovieService';
// Note: We intentionally avoid debounce for admin search; apply via explicit button
import { useRefreshDashboard } from '../../../hooks/useDashboardData';
import MovieFormModal from '../../../components/common/MovieFormModal';
import SchedulePublishModal from './SchedulePublishModal';

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

const getQualityMetrics = movie => {
  console.log('getQualityMetrics called with movie:', movie?.title);
  console.log('Raw quality_metrics:', movie?.quality_metrics);

  const qualityData = movie?.quality_metrics || {
    quality_score: null,
    content_completeness: '0.00',
    minimum_quality_met: false,
    overall_quality_rating: 'Not Assessed',
    completion_status: 'Incomplete',
    quality_issues: [],
    quality_suggestions: [],
    quality_breakdown: {},
    basic_info_score: 0,
    visual_assets_score: 0,
    metadata_richness_score: 0,
    rating_validity_score: 0,
    last_quality_check: null,
    assessed_by: null,
    assessment_notes: null,
  };

  console.log('Processed quality data:', qualityData);
  return qualityData;
};

const getSchedulingInfo = movie => {
  return (
    movie?.scheduling || {
      publish_date: null,
      featured_from: null,
      featured_until: null,
      campaign_name: null,
      campaign_type: null,
      is_published_now: true,
      is_featured_now: false,
    }
  );
};

const getProductionMetrics = movie => {
  return (
    movie?.production_metrics || {
      homepage_views: 0,
      detail_page_views: 0,
      engagement_rate: 0.0,
      performance_score: 0,
      trending_category: 'stable',
      trending_score: 0.0,
    }
  );
};

const isAdminFeatured = movie => {
  return movie?.admin_control?.admin_featured || movie?.admin_featured || false;
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
  const [qualityModalOpen, setQualityModalOpen] = useState(false);
  const [selectedQualityMovie, setSelectedQualityMovie] = useState(null);
  const [metricsModalOpen, setMetricsModalOpen] = useState(false);
  const [selectedMetricsMovie, setSelectedMetricsMovie] = useState(null);

  // Enrichment states
  const [enrichmentProgress, setEnrichmentProgress] = useState({});
  const [batchEnrichmentOpen, setBatchEnrichmentOpen] = useState(false);
  const [enrichmentOptions, setEnrichmentOptions] = useState({
    forceRefresh: false,
    focusAreas: [],
    enrichType: 'comprehensive',
  });

  // Loading states for actions
  const [actionLoading, setActionLoading] = useState({}); // key: `${movieId}:${action}` => boolean
  const [bulkActionLoading, setBulkActionLoading] = useState(null); // current bulk action string or null

  const isMovieActionLoading = (movieId, action) => !!actionLoading[`${movieId}:${action}`];
  const setMovieActionLoading = (movieId, action, value) =>
    setActionLoading(prev => ({ ...prev, [`${movieId}:${action}`]: value }));

  // Search & Filter States (draft vs applied)
  const [searchQuery, setSearchQuery] = useState(''); // draft
  const [appliedSearch, setAppliedSearch] = useState('');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const initialFilters = {
    approval_status: 'NEEDS_REVIEW', // Mặc định luôn có filter hợp lệ cho ES
    visibility_status: '',
    is_published: '',
    admin_featured: '',
    minimum_quality_met: '',
    category: '',
    sort_by: '-created_at',
    // Advanced filters
    quality_score_min: null,
    quality_score_max: null,
    content_completeness_min: null,
    overall_quality_rating: null,
    completion_status: null,
    campaign_type: null,
    campaign_priority_min: null,
    is_published_now: null,
    is_featured_now: null,
    performance_score_min: null,
    trending_score_min: null,
    trending_category: null,
    engagement_rate_min: null,
    homepage_views_min: null,
    user_favorites_min: null,
  };
  const [filters, setFilters] = useState(initialFilters); // draft
  const [appliedFilters, setAppliedFilters] = useState(initialFilters);
  // Keyset pagination state
  const [afterStack, setAfterStack] = useState([]); // Stack of after_created_at for prev
  const [currentAfter, setCurrentAfter] = useState(null); // Current after_created_at
  const [hasNext, setHasNext] = useState(false);
  const [hasPrevious, setHasPrevious] = useState(false);

  // State cho modal tạo/sửa phim
  const [showMovieForm, setShowMovieForm] = useState(false);
  const [editMovie, setEditMovie] = useState(null);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [selectedMovieForSchedule, setSelectedMovieForSchedule] = useState(null);

  // Fetch Movies (keyset)
  const fetchMovies = useCallback(
    async (direction = 'init', afterValue = null) => {
      const effectiveAfter = afterValue || currentAfter;
      setLoading(true);
      setError(null);
      try {
        const params = {
          pageSize: 40,
          filters: { ...appliedFilters, sort_by: '-created_at' },
          search: appliedSearch,
        };
        if (effectiveAfter) {
          params.filters.after_created_at = effectiveAfter;
        }

        console.log('[PAGINATION DEBUG] Fetching movies with params:', params);
        console.log('[PAGINATION DEBUG] Direction:', direction, 'Effective after:', effectiveAfter);

        const data = await getAdminMovies(params);
        console.log('[PAGINATION DEBUG] API response:', data);

        setMovies(data.results || []);

        // Keyset logic
        setHasPrevious(afterStack.length > 0);

        // Store next_after_created_at from API response
        const nextAfterCreatedAt = data.next;
        console.log('[PAGINATION DEBUG] Next after created at:', nextAfterCreatedAt);
        setHasNext(nextAfterCreatedAt);
      } catch (error) {
        console.error('[PAGINATION DEBUG] Error:', error);
        setError('Không thể tải danh sách phim. Vui lòng thử lại.');
      } finally {
        setLoading(false);
      }
    },
    [appliedFilters, appliedSearch, currentAfter, afterStack]
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

  // Initial fetch and refetch when APPLIED filters/search change
  useEffect(() => {
    setCurrentAfter(null);
    fetchMovies('init');
    // eslint-disable-next-line
  }, [appliedFilters, appliedSearch]);

  // Apply search and filters explicitly
  const applySearchAndFilters = useCallback(() => {
    setAppliedSearch(searchQuery.trim());
    setAppliedFilters(prev => ({ ...prev, ...filters }));
    // Reset pagination
    setCurrentAfter(null);
    setAfterStack([]);
    setHasPrevious(false);
    // Trigger fetch
    fetchMovies('init', null);
  }, [searchQuery, filters, fetchMovies]);

  // Next page
  const handleNextPage = () => {
    if (hasNext && (typeof hasNext === 'string' || Array.isArray(hasNext))) {
      // Only push currentAfter if it's not null (don't push on first page)
      setAfterStack(prev => (currentAfter ? [...prev, currentAfter] : prev));
      setCurrentAfter(hasNext);
      fetchMovies('next', hasNext);
    }
  };

  // Prev page
  const handlePrevPage = () => {
    if (afterStack.length > 0) {
      // Remove the current page's after value
      const prevStack = [...afterStack];
      prevStack.pop();
      // The new last value is the previous page's after value (or null for first page)
      const newCurrentAfter = prevStack.length > 0 ? prevStack[prevStack.length - 1] : null;
      setAfterStack(prevStack);
      setCurrentAfter(newCurrentAfter);
      fetchMovies('prev', newCurrentAfter);
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
        setMovieActionLoading(movieId, 'toggle_featured', true);
        await toggleMovieFeatured(movieId);
        await handleActionSuccess();
      } catch (error) {
        console.error('Error toggling featured:', error);
      } finally {
        setMovieActionLoading(movieId, 'toggle_featured', false);
      }
    },
    [handleActionSuccess]
  );

  const approveMovieAction = useCallback(
    async movieId => {
      try {
        setMovieActionLoading(movieId, 'approve', true);
        await approveMovie(movieId);
        await handleActionSuccess();
      } catch (error) {
        console.error('Error approving movie:', error);
      } finally {
        setMovieActionLoading(movieId, 'approve', false);
      }
    },
    [handleActionSuccess]
  );

  const rejectMovieAction = useCallback(
    async (movieId, reason = '') => {
      try {
        setMovieActionLoading(movieId, 'reject', true);
        await rejectMovie(movieId, reason);
        await handleActionSuccess();
      } catch (error) {
        console.error('Error rejecting movie:', error);
      } finally {
        setMovieActionLoading(movieId, 'reject', false);
      }
    },
    [handleActionSuccess]
  );

  const updatePriorityAction = useCallback(
    async (movieId, priority) => {
      try {
        setMovieActionLoading(movieId, 'update_priority', true);
        await updateMoviePriority(movieId, priority);
        fetchMovies();
      } catch (error) {
        console.error('Error updating priority:', error);
      } finally {
        setMovieActionLoading(movieId, 'update_priority', false);
      }
    },
    [fetchMovies]
  );

  const togglePublishStatus = useCallback(
    async movieId => {
      try {
        setMovieActionLoading(movieId, 'toggle_publish', true);
        await performBulkAction('toggle_publish', [movieId]);
        await handleActionSuccess();
      } catch (error) {
        console.error('Error toggling publish status:', error);
      } finally {
        setMovieActionLoading(movieId, 'toggle_publish', false);
      }
    },
    [handleActionSuccess]
  );

  const handleQualityReview = useCallback(movie => {
    console.log('Opening quality modal for:', movie.title);

    // Create enhanced movie object with quality metrics for testing
    const enhancedMovie = {
      ...movie,
      quality_metrics: movie.quality_metrics || {
        quality_score: 7.2,
        content_completeness: 85.5,
        minimum_quality_met: true,
        overall_quality_rating: 'Good',
        completion_status: 'Nearly Complete',
        basic_info_score: 8.5,
        visual_assets_score: 7.0,
        metadata_richness_score: 6.8,
        rating_validity_score: 8.0,
        quality_issues: [
          {
            category: 'Visual Assets',
            description: 'Movie poster resolution is below recommended 2000x3000 pixels',
            priority: 'medium',
            suggested_fix: 'Replace with higher resolution poster image',
          },
          {
            category: 'Metadata',
            description: 'Missing cast information for supporting actors',
            priority: 'low',
            suggested_fix: 'Add complete cast and crew information',
          },
        ],
        quality_suggestions: [
          {
            category: 'Enhancement',
            description: 'Add movie trailers to improve user engagement',
            priority: 'medium',
            expected_impact: 'Increase detail page views by 20-30%',
          },
          {
            category: 'SEO',
            description: 'Optimize movie description for better search visibility',
            priority: 'low',
            expected_impact: 'Improve search ranking and organic traffic',
          },
        ],
        quality_breakdown: {
          poster_quality: 7.0,
          metadata_completeness: 8.5,
          content_accuracy: 8.0,
          technical_quality: 6.8,
          user_engagement: 7.5,
          content_freshness: 7.8,
        },
        last_quality_check: new Date().toISOString(),
        assessed_by: 'System Auto-Assessment',
        assessment_notes:
          'Overall good quality movie with minor improvements needed in visual assets and metadata completeness.',
      },
    };

    console.log('Enhanced movie object:', enhancedMovie);
    setSelectedQualityMovie(enhancedMovie);
    setQualityModalOpen(true);
  }, []);

  const handleQualityUpdate = useCallback(
    async (movieId, qualityData) => {
      try {
        await updateMovieQuality(movieId, qualityData);
        await fetchMovies(); // Refresh the movie list
        await refreshDashboard(); // Refresh dashboard stats
      } catch (error) {
        console.error('Error updating quality:', error);
        throw error;
      }
    },
    [fetchMovies, refreshDashboard]
  );

  const handleIssueResolve = useCallback(
    async (movieId, issueIndex) => {
      try {
        await resolveMovieIssue(movieId, issueIndex);
        await fetchMovies(); // Refresh the movie list
        await refreshDashboard(); // Refresh dashboard stats
      } catch (error) {
        console.error('Error resolving issue:', error);
        throw error;
      }
    },
    [fetchMovies, refreshDashboard]
  );

  // Enrichment handlers
  const handleEnrichMovie = useCallback(
    async (movieId, options = {}) => {
      setEnrichmentProgress(prev => ({ ...prev, [movieId]: { status: 'loading', progress: 0 } }));

      try {
        const result = await enrichMovie(movieId, {
          forceRefresh: options.forceRefresh || false,
          focusAreas: options.focusAreas || ['basic'],
          enrichType: options.enrichType || 'comprehensive',
        });

        setEnrichmentProgress(prev => ({
          ...prev,
          [movieId]: { status: 'completed', progress: 100, result },
        }));

        await fetchMovies(); // Refresh the movie list
        await refreshDashboard(); // Refresh dashboard stats

        // Clear progress after 3 seconds
        setTimeout(() => {
          setEnrichmentProgress(prev => {
            const updated = { ...prev };
            delete updated[movieId];
            return updated;
          });
        }, 3000);
      } catch (error) {
        console.error('Error enriching movie:', error);
        setEnrichmentProgress(prev => ({
          ...prev,
          [movieId]: { status: 'error', progress: 0, error: error.message },
        }));
      }
    },
    [fetchMovies, refreshDashboard]
  );

  const handleBatchEnrichment = useCallback(async () => {
    if (selectedMovies.length === 0) return;

    setBatchEnrichmentOpen(false);

    try {
      const result = await batchEnrichMovies(selectedMovies, enrichmentOptions);
      console.log('Batch enrichment result:', result);

      await fetchMovies();
      await refreshDashboard();
      setSelectedMovies([]);
    } catch (error) {
      console.error('Error batch enriching movies:', error);
    }
  }, [selectedMovies, enrichmentOptions, fetchMovies, refreshDashboard]);

  const handleEnrichQualityIssues = useCallback(async () => {
    try {
      const result = await enrichMoviesWithQualityIssues({
        qualityScoreMax: 7.0,
        hasQualityIssues: true,
        limit: 20,
      });
      console.log('Quality issues enrichment result:', result);

      await fetchMovies();
      await refreshDashboard();
    } catch (error) {
      console.error('Error enriching quality issues:', error);
    }
  }, [fetchMovies, refreshDashboard]);

  const bulkAction = useCallback(
    async (action, movieIds) => {
      try {
        setBulkActionLoading(action);
        await performBulkAction(action, movieIds);
        setSelectedMovies([]);
        fetchMovies();
        refreshDashboard();
      } catch (error) {
        console.error('Error performing bulk action:', error);
      } finally {
        setBulkActionLoading(null);
      }
    },
    [fetchMovies, refreshDashboard]
  );

  // Thêm các hàm kiểm tra trạng thái cho bulk action ngược lại
  const allFeatured =
    selectedMovies.length > 0 &&
    selectedMovies.every(id => movies.find(m => m.id === id)?.admin_control?.admin_featured);
  const allPublished =
    selectedMovies.length > 0 &&
    selectedMovies.every(
      id => movies.find(m => m.id === id)?.admin_control?.visibility_status === 'PUBLISHED'
    );
  const allApproved =
    selectedMovies.length > 0 &&
    selectedMovies.every(
      id => movies.find(m => m.id === id)?.admin_control?.approval_status === 'APPROVED'
    );
  const allRejected =
    selectedMovies.length > 0 &&
    selectedMovies.every(
      id => movies.find(m => m.id === id)?.admin_control?.approval_status === 'REJECTED'
    );

  // Event Handlers
  const handleSearchChange = e => {
    setSearchQuery(e.target.value);
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
    }));
    // Do not auto-fetch; wait for explicit apply
  };

  const handleAdvancedFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
    }));
    // Do not auto-fetch; wait for explicit apply
  };

  const handleResetAdvancedFilters = () => {
    setFilters(prev => ({
      ...prev,
      // Reset only advanced filters, keep basic ones
      quality_score_min: null,
      quality_score_max: null,
      content_completeness_min: null,
      overall_quality_rating: null,
      completion_status: null,
      campaign_type: null,
      campaign_priority_min: null,
      is_published_now: null,
      is_featured_now: null,
      performance_score_min: null,
      trending_score_min: null,
      trending_category: null,
      engagement_rate_min: null,
      homepage_views_min: null,
      user_favorites_min: null,
    }));
  };

  const toggleAdvancedFilters = () => {
    setShowAdvancedFilters(prev => !prev);
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
    console.log('Opening movie details modal for:', movie?.title || 'Unknown Movie');
    const enhancedMovie = {
      ...movie,
      title: movie?.title || 'Unknown Movie',
    };
    setSelectedMovie(enhancedMovie);
  }, []);

  const handleCloseDetails = useCallback(() => {
    console.log('Closing movie details modal');
    setSelectedMovie(null);
  }, []);

  const handleViewMetrics = useCallback(movie => {
    setSelectedMetricsMovie(movie);
    setMetricsModalOpen(true);
  }, []);

  // Xử lý tạo mới phim
  const handleCreateMovie = async movieData => {
    try {
      await createAdminMovie(movieData);
      setShowMovieForm(false);
      await fetchMovies();
      // Không cần throw error vì MovieFormModal sẽ xử lý success toast
    } catch (error) {
      console.error('Error creating movie:', error);
      // Throw error để MovieFormModal xử lý error toast
      throw error;
    }
  };

  // Xử lý cập nhật phim
  const handleEditMovie = async (movieId, movieData) => {
    try {
      await updateAdminMovie(movieId, movieData);
      setShowMovieForm(false);
      setEditMovie(null);
      await fetchMovies();
      // Không cần throw error vì MovieFormModal sẽ xử lý success toast
    } catch (error) {
      console.error('Error updating movie:', error);
      // Throw error để MovieFormModal xử lý error toast
      throw error;
    }
  };

  // Xử lý xóa phim
  const handleDeleteMovie = async movieId => {
    if (!window.confirm('Bạn có chắc chắn muốn xóa phim này?')) return;
    try {
      await deleteAdminMovie(movieId);
      fetchMovies();
    } catch (error) {
      alert(error.error || 'Không thể xóa phim');
    }
  };

  // Xử lý mở modal lên lịch xuất bản phim
  const handleOpenScheduleModal = movie => {
    setSelectedMovieForSchedule(movie);
    setShowScheduleModal(true);
  };

  // Xử lý lên lịch xuất bản phim từ modal
  const handleSchedulePublish = async scheduleData => {
    try {
      const fullScheduleData = {
        movie_id: selectedMovieForSchedule.id,
        action_type: 'publish',
        ...scheduleData,
      };

      await scheduleMovieAction(fullScheduleData);
      alert('Đã lên lịch xuất bản phim thành công!');
      setShowScheduleModal(false);
      setSelectedMovieForSchedule(null);
      fetchMovies();
    } catch (error) {
      alert(error.error || 'Không thể lên lịch xuất bản phim');
    }
  };

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
      const qualityMetrics = getQualityMetrics(movie);
      const schedulingInfo = getSchedulingInfo(movie);
      const productionMetrics = getProductionMetrics(movie);
      const isFeatured = isAdminFeatured(movie);
      const releaseYear = movie?.release_date ? new Date(movie.release_date).getFullYear() : 'N/A';
      const genres = movie?.genres?.map(g => g.name).join(', ') || 'N/A';
      const runtime = movie?.runtime ? `${movie.runtime} min` : 'N/A';
      const qualityScore = qualityMetrics?.quality_score || 0;
      const completeness = qualityMetrics?.content_completeness || 0;

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
            <div className="mt-4">
              <div className="flex items-center justify-between text-xs text-gray-700 mb-2">
                <span className="font-medium">Chất lượng:</span>
                <span
                  className={`px-2 py-1 rounded text-xs ${
                    qualityMetrics?.minimum_quality_met
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {qualityMetrics?.overall_quality_rating || 'Chưa đánh giá'}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="flex items-center text-gray-500">
                  <DocumentCheckIcon className="mr-1 size-3" />
                  {parseFloat(completeness || 0).toFixed(1)}%
                </div>
                <div className="flex items-center text-gray-500">
                  <ChartBarIcon className="mr-1 size-3" />
                  {qualityMetrics?.quality_score
                    ? parseFloat(qualityMetrics.quality_score).toFixed(1)
                    : 'N/A'}
                </div>
              </div>
              {qualityMetrics?.quality_issues?.length > 0 && (
                <div className="mt-1 text-xs text-red-600">
                  <ExclamationTriangleIcon className="inline size-3 mr-1" />
                  {qualityMetrics.quality_issues.length} vấn đề
                </div>
              )}
            </div>

            {/* Production Metrics */}
            <div className="mt-4">
              <div className="flex items-center justify-between text-xs text-gray-700 mb-2">
                <span className="font-medium">Hiệu suất:</span>
                <span
                  className={`px-2 py-1 rounded text-xs ${
                    productionMetrics?.trending_category === 'trending'
                      ? 'bg-orange-100 text-orange-800'
                      : productionMetrics?.trending_category === 'rising'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {productionMetrics?.trending_category || 'stable'}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="flex items-center text-gray-500">
                  <EyeIcon className="mr-1 size-3" />
                  {productionMetrics?.homepage_views || 0}
                </div>
                <div className="flex items-center text-gray-500">
                  <MagnifyingGlassIcon className="mr-1 size-3" />
                  {productionMetrics?.detail_page_views || 0}
                </div>
              </div>
              <div className="mt-1 text-xs text-gray-500">
                Engagement: {(productionMetrics?.engagement_rate * 100 || 0).toFixed(1)}%
              </div>
            </div>

            {/* Scheduling Info */}
            {(schedulingInfo?.featured_from || schedulingInfo?.campaign_name) && (
              <div className="mt-4">
                <div className="text-xs text-gray-700 font-medium mb-1">Lịch trình:</div>
                {schedulingInfo?.campaign_name && (
                  <div className="text-xs text-blue-600 mb-1">
                    <CalendarIcon className="inline size-3 mr-1" />
                    {schedulingInfo.campaign_name}
                  </div>
                )}
                {schedulingInfo?.featured_from && (
                  <div className="text-xs text-gray-500">
                    Featured: {new Date(schedulingInfo.featured_from).toLocaleDateString()}
                    {schedulingInfo?.featured_until &&
                      ` - ${new Date(schedulingInfo.featured_until).toLocaleDateString()}`}
                  </div>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="mt-4 space-y-2">
              {/* Primary Actions Row */}
              <div className="space-y-2">
                {/* Always show View Details button */}
                <button
                  onClick={() => handleViewDetails(movie)}
                  className="inline-flex w-full items-center justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
                >
                  <EyeIcon className="mr-1.5 size-4" />
                  Xem chi tiết
                </button>

                {/* Approval actions for movies needing review or pending */}
                {(approvalInfo?.status === 'NEEDS_REVIEW' ||
                  approvalInfo?.status === 'PENDING') && (
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => approveMovieAction(movie.id)}
                      disabled={
                        !approvalInfo?.can_approve || isMovieActionLoading(movie.id, 'approve')
                      }
                      className="inline-flex flex-1 items-center justify-center rounded-md border border-transparent bg-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {isMovieActionLoading(movie.id, 'approve') ? (
                        <>
                          <div className="mr-1 h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                          Đang duyệt...
                        </>
                      ) : (
                        <>
                          <CheckCircleIcon className="mr-1.5 size-4" />
                          Duyệt
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => rejectMovieAction(movie.id, 'Không đạt yêu cầu chất lượng')}
                      disabled={
                        !approvalInfo?.can_reject || isMovieActionLoading(movie.id, 'reject')
                      }
                      className="inline-flex flex-1 items-center justify-center rounded-md border border-transparent bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {isMovieActionLoading(movie.id, 'reject') ? (
                        <>
                          <div className="mr-1 h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                          Đang từ chối...
                        </>
                      ) : (
                        <>
                          <XCircleIcon className="mr-1.5 size-4" />
                          Từ chối
                        </>
                      )}
                    </button>
                  </div>
                )}

                {/* Schedule publish button for pending movies */}
                {approvalInfo?.status === 'PENDING' && (
                  <button
                    onClick={() => handleOpenScheduleModal(movie)}
                    className="inline-flex w-full items-center justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  >
                    <CalendarIcon className="mr-1.5 size-4" />
                    Lên lịch xuất bản
                  </button>
                )}
              </div>

              {/* Admin Control Actions */}
              {approvalInfo?.status === 'APPROVED' && (
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => toggleFeatured(movie.id)}
                    className={`inline-flex items-center justify-center rounded-md border px-3 py-2 text-xs font-medium ${
                      isFeatured
                        ? 'border-yellow-300 bg-yellow-50 text-yellow-800 hover:bg-yellow-100'
                        : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                    } transition-colors`}
                    disabled={isMovieActionLoading(movie.id, 'toggle_featured')}
                  >
                    {isMovieActionLoading(movie.id, 'toggle_featured') ? (
                      <>
                        <div className="mr-1 h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
                        Đang xử lý...
                      </>
                    ) : (
                      <>
                        <StarIcon className="mr-1 size-3" />
                        {isFeatured ? 'Bỏ Featured' : 'Featured'}
                      </>
                    )}
                  </button>

                  <button
                    onClick={() => togglePublishStatus(movie.id)}
                    className={`inline-flex items-center justify-center rounded-md border px-3 py-2 text-xs font-medium ${
                      movie?.admin_control?.visibility_status === 'PUBLISHED'
                        ? 'border-blue-300 bg-blue-50 text-blue-800 hover:bg-blue-100'
                        : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                    } transition-colors`}
                    disabled={isMovieActionLoading(movie.id, 'toggle_publish')}
                  >
                    {isMovieActionLoading(movie.id, 'toggle_publish') ? (
                      <>
                        <div className="mr-1 h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
                        Đang cập nhật...
                      </>
                    ) : (
                      <>
                        <EyeIcon className="mr-1 size-3" />
                        {movie?.admin_control?.visibility_status === 'PUBLISHED'
                          ? 'Ẩn'
                          : 'Xuất bản'}
                      </>
                    )}
                  </button>
                </div>
              )}

              {/* Quality & Priority Actions */}
              <div className="space-y-2">
                {qualityMetrics?.quality_issues?.length > 0 && (
                  <button
                    onClick={() => handleQualityReview(movie)}
                    className="inline-flex w-full items-center justify-center rounded-md border border-orange-300 bg-orange-50 px-3 py-2 text-xs font-medium text-orange-800 hover:bg-orange-100 transition-colors"
                  >
                    <ExclamationTriangleIcon className="mr-1 size-3" />
                    Khắc phục chất lượng ({qualityMetrics.quality_issues.length})
                  </button>
                )}

                {/* Always show Quality Review button for testing */}
                <button
                  onClick={() => handleQualityReview(movie)}
                  className="inline-flex w-full items-center justify-center rounded-md border border-blue-300 bg-blue-50 px-3 py-2 text-xs font-medium text-blue-800 hover:bg-blue-100 transition-colors"
                >
                  <ChartBarIcon className="mr-1 size-3" />
                  Đánh giá chất lượng
                </button>

                {/* Movie Enrichment Button */}
                <button
                  onClick={() =>
                    handleEnrichMovie(movie.id, {
                      focusAreas: ['basic', 'visual'],
                      enrichType: 'quality_based',
                    })
                  }
                  disabled={enrichmentProgress[movie.id]?.status === 'loading'}
                  className="inline-flex w-full items-center justify-center rounded-md border border-green-300 bg-green-50 px-3 py-2 text-xs font-medium text-green-800 hover:bg-green-100 transition-colors disabled:cursor-not-allowed disabled:opacity-50"
                  title="Bổ sung dữ liệu phim từ TMDB/IMDB"
                >
                  {enrichmentProgress[movie.id]?.status === 'loading' ? (
                    <>
                      <div className="mr-1 h-3 w-3 animate-spin rounded-full border-2 border-green-800 border-t-transparent" />
                      Đang xử lý...
                    </>
                  ) : enrichmentProgress[movie.id]?.success === 'true' ? (
                    <>
                      <CheckCircleIcon className="mr-1 size-3" />
                      Đã cập nhật ✓
                    </>
                  ) : enrichmentProgress[movie.id]?.success === 'false' ? (
                    <>
                      <ExclamationTriangleIcon className="mr-1 size-3" />
                      Lỗi
                    </>
                  ) : (
                    <>
                      <DocumentCheckIcon className="mr-1 size-3" />
                      Bổ sung dữ liệu
                    </>
                  )}
                </button>
                <button
                  onClick={() => handleViewMetrics(movie)}
                  className="inline-flex w-full items-center justify-center rounded-md border border-purple-300 bg-purple-50 px-3 py-2 text-xs font-medium text-purple-800 hover:bg-purple-100 transition-colors"
                >
                  <ChartBarIcon className="mr-1 size-3" />
                  Xem Production Metrics
                </button>
              </div>

              {/* Priority Adjustment */}
              {approvalInfo?.status === 'APPROVED' && (
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-gray-500">Ưu tiên:</span>
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() =>
                        updatePriorityAction(
                          movie.id,
                          Math.max(0, (movie?.admin_control?.admin_priority || 0) - 1)
                        )
                      }
                      className="rounded border text-gray-700 border-gray-300 px-2 py-1 text-xs hover:bg-gray-50"
                      disabled={isMovieActionLoading(movie.id, 'update_priority')}
                    >
                      -
                    </button>
                    <span className="text-xs text-gray-700 font-medium w-6 text-center">
                      {movie?.admin_control?.admin_priority || 0}
                    </span>
                    <button
                      onClick={() =>
                        updatePriorityAction(
                          movie.id,
                          Math.min(10, (movie?.admin_control?.admin_priority || 0) + 1)
                        )
                      }
                      className="rounded border text-gray-700 border-gray-300 px-2 py-1 text-xs hover:bg-gray-50"
                      disabled={isMovieActionLoading(movie.id, 'update_priority')}
                    >
                      +
                    </button>
                  </div>
                </div>
              )}
              <div className="flex space-x-2 mt-2">
                <button
                  onClick={() => {
                    setEditMovie(movie);
                    setShowMovieForm(true);
                  }}
                  className="inline-flex items-center rounded-md border border-yellow-500 bg-yellow-50 px-3 py-1 text-xs font-medium text-yellow-700 hover:bg-yellow-100"
                >
                  Sửa
                </button>
                <button
                  onClick={() => handleDeleteMovie(movie.id)}
                  className="inline-flex items-center rounded-md border border-red-500 bg-red-50 px-3 py-1 text-xs font-medium text-red-700 hover:bg-red-100"
                >
                  Xóa
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    },
    [selectedMovies, toggleFeatured, approveMovieAction, handleMovieSelect, handleViewDetails]
  );

  // Active filter indicator
  const hasActiveFilters = useMemo(() => {
    const basicFilters = [
      'approval_status',
      'visibility_status',
      'is_published',
      'admin_featured',
      'minimum_quality_met',
      'category',
    ];
    const advancedFilterKeys = [
      'quality_score_min',
      'quality_score_max',
      'content_completeness_min',
      'overall_quality_rating',
      'completion_status',
      'campaign_type',
      'campaign_priority_min',
      'is_published_now',
      'is_featured_now',
      'performance_score_min',
      'trending_score_min',
      'trending_category',
      'engagement_rate_min',
      'homepage_views_min',
      'user_favorites_min',
    ];

    const hasBasicFilters = basicFilters.some(
      key => filters[key] && filters[key] !== '-created_at'
    );
    const hasAdvancedFilters = advancedFilterKeys.some(
      key => filters[key] !== null && filters[key] !== undefined && filters[key] !== ''
    );

    return hasBasicFilters || hasAdvancedFilters || appliedSearch;
  }, [filters, appliedSearch]);

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
              onClick={() => {
                setEditMovie(null);
                setShowMovieForm(true);
              }}
              className="inline-flex items-center rounded-md border border-blue-600 bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
            >
              <FilmIcon className="mr-2 size-4" />
              Thêm phim mới
            </button>
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

            {/* Bulk Enrichment Button */}
            {selectedMovies.length > 0 && (
              <button
                onClick={() => setBatchEnrichmentOpen(true)}
                className="inline-flex items-center rounded-md border border-green-300 bg-green-50 px-4 py-2 text-sm font-medium text-green-700 hover:bg-green-100 transition-colors"
              >
                <DocumentCheckIcon className="mr-2 size-4" />
                Bổ sung dữ liệu ({selectedMovies.length})
              </button>
            )}

            {/* Quality Issues Enrichment */}
            <button
              onClick={handleEnrichQualityIssues}
              className="inline-flex items-center rounded-md border border-orange-300 bg-orange-50 px-4 py-2 text-sm font-medium text-orange-700 hover:bg-orange-100 transition-colors"
              title="Tự động bổ sung dữ liệu cho phim có vấn đề chất lượng"
            >
              <ExclamationTriangleIcon className="mr-2 size-4" />
              Khắc phục chất lượng
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
                onKeyDown={e => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    applySearchAndFilters();
                  }
                }}
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
          <div className="ml-3">
            <button
              onClick={applySearchAndFilters}
              className="inline-flex items-center rounded-md border border-blue-600 bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
            >
              <MagnifyingGlassIcon className="mr-2 size-4" />
              Tìm kiếm
            </button>
          </div>

          {selectedMovies.length > 0 && (
            <div className="flex items-center space-x-3">
              <span className="text-sm font-medium text-gray-600">
                Đã chọn {selectedMovies.length} phim
              </span>

              <div className="flex space-x-2">
                {/* Bulk Approve */}
                <button
                  onClick={() => bulkAction('approve', selectedMovies)}
                  className="inline-flex items-center rounded-md border border-transparent bg-green-600 px-3 py-2 text-sm font-medium leading-4 text-white transition-colors hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                  disabled={!!bulkActionLoading}
                >
                  {bulkActionLoading === 'approve' ? (
                    <>
                      <div className="mr-1 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      Đang duyệt...
                    </>
                  ) : (
                    <>
                      <CheckCircleIcon className="mr-1 size-4" />
                      Duyệt
                    </>
                  )}
                </button>
                {/* Bulk Reject */}
                <button
                  onClick={() => bulkAction('reject', selectedMovies)}
                  disabled={!allApproved && !allRejected}
                  className="inline-flex items-center rounded-md border border-transparent bg-red-600 px-3 py-2 text-sm font-medium leading-4 text-white transition-colors hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {bulkActionLoading === 'reject' ? (
                    <>
                      <div className="mr-1 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      Đang từ chối...
                    </>
                  ) : (
                    <>
                      <XCircleIcon className="mr-1 size-4" />
                      Từ chối
                    </>
                  )}
                </button>
                {/* Bulk Feature */}
                <button
                  onClick={() => bulkAction('feature', selectedMovies)}
                  className="inline-flex items-center rounded-md border border-transparent bg-yellow-600 px-3 py-2 text-sm font-medium leading-4 text-white transition-colors hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2"
                  disabled={!!bulkActionLoading}
                >
                  {bulkActionLoading === 'feature' ? (
                    <>
                      <div className="mr-1 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      Đang gắn featured...
                    </>
                  ) : (
                    <>
                      <StarIcon className="mr-1 size-4" />
                      Featured
                    </>
                  )}
                </button>
                {/* Bulk Unfeature */}
                <button
                  onClick={() => bulkAction('unfeature', selectedMovies)}
                  disabled={!allFeatured}
                  className="inline-flex items-center rounded-md border border-transparent bg-yellow-400 px-3 py-2 text-sm font-medium leading-4 text-white transition-colors hover:bg-yellow-500 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {bulkActionLoading === 'unfeature' ? (
                    <>
                      <div className="mr-1 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      Đang bỏ featured...
                    </>
                  ) : (
                    <>
                      <StarIcon className="mr-1 size-4" />
                      Bỏ Featured
                    </>
                  )}
                </button>
                {/* Bulk Publish */}
                <button
                  onClick={() => bulkAction('publish', selectedMovies)}
                  className="inline-flex items-center rounded-md border border-transparent bg-blue-600 px-3 py-2 text-sm font-medium leading-4 text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  disabled={!!bulkActionLoading}
                >
                  {bulkActionLoading === 'publish' ? (
                    <>
                      <div className="mr-1 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      Đang xuất bản...
                    </>
                  ) : (
                    <>
                      <EyeIcon className="mr-1 size-4" />
                      Xuất bản
                    </>
                  )}
                </button>
                {/* Bulk Unpublish */}
                <button
                  onClick={() => bulkAction('unpublish', selectedMovies)}
                  disabled={!allPublished}
                  className="inline-flex items-center rounded-md border border-transparent bg-blue-400 px-3 py-2 text-sm font-medium leading-4 text-white transition-colors hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {bulkActionLoading === 'unpublish' ? (
                    <>
                      <div className="mr-1 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      Đang bỏ xuất bản...
                    </>
                  ) : (
                    <>
                      <EyeSlashIcon className="mr-1 size-4" />
                      Bỏ xuất bản
                    </>
                  )}
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
                });
                setSearchQuery('');
                // Reset pagination
                setCurrentAfter(null);
                setAfterStack([]);
                setHasPrevious(false);
              }}
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
            >
              Xóa tất cả bộ lọc
            </button>
            <button
              onClick={() => {
                setAppliedFilters(filters);
                setShowFilters(false);
                applySearchAndFilters();
              }}
              className="rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Áp dụng
            </button>
          </div>
        </div>
      )}

      {/* Advanced Filters */}
      <AdvancedAdminFilters
        filters={filters}
        onFilterChange={handleAdvancedFilterChange}
        onResetFilters={handleResetAdvancedFilters}
        showAdvanced={showAdvancedFilters}
        onToggleAdvanced={toggleAdvancedFilters}
      />

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
              {appliedSearch || Object.values(filters).some(v => v && v !== '-created_at')
                ? 'Không tìm thấy phim nào với tiêu chí đã chọn.'
                : 'Chưa có phim nào trong hệ thống.'}
            </p>
            {(appliedSearch || hasActiveFilters) && (
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
                    });
                    setSearchQuery('');
                    // Reset pagination
                    setCurrentAfter(null);
                    setAfterStack([]);
                    setHasPrevious(false);
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
                      {appliedSearch && (
                        <span className="text-gray-500">
                          {' '}
                          • Tìm kiếm: "<span className="font-medium">{appliedSearch}</span>"
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

      {/* Movie Quality Modal */}
      {selectedQualityMovie && (
        <MovieQualityModal
          movie={selectedQualityMovie}
          isOpen={qualityModalOpen}
          onClose={() => {
            setQualityModalOpen(false);
            setSelectedQualityMovie(null);
          }}
          onQualityUpdate={handleQualityUpdate}
          onIssueResolve={handleIssueResolve}
          userRole="admin"
        />
      )}

      {/* Batch Enrichment Modal */}
      {batchEnrichmentOpen && (
        <div
          className="fixed inset-0 z-50 overflow-y-auto"
          aria-labelledby="modal-title"
          role="dialog"
          aria-modal="true"
        >
          <div className="flex min-h-screen items-end justify-center px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            <div
              className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
              aria-hidden="true"
              onClick={() => setBatchEnrichmentOpen(false)}
            ></div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">
              &#8203;
            </span>
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <div>
                <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
                  <DocumentCheckIcon className="h-6 w-6 text-green-600" aria-hidden="true" />
                </div>
                <div className="mt-3 text-center sm:mt-5">
                  <h3 className="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                    Bổ sung dữ liệu hàng loạt
                  </h3>
                  <div className="mt-2">
                    <p className="text-sm text-gray-500">
                      Sẽ bổ sung dữ liệu cho {selectedMovies.length} phim đã chọn từ TMDB/IMDB.
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-5 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Loại bổ sung
                  </label>
                  <select
                    value={enrichmentOptions.enrichType}
                    onChange={e =>
                      setEnrichmentOptions(prev => ({ ...prev, enrichType: e.target.value }))
                    }
                    className="block w-full rounded-md text-gray-500 border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm"
                  >
                    <option className="text-gray-500" value="comprehensive">
                      Toàn diện
                    </option>
                    <option className="text-gray-500" value="quality_based">
                      Dựa trên chất lượng
                    </option>
                  </select>
                </div>

                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={enrichmentOptions.forceRefresh}
                      onChange={e =>
                        setEnrichmentOptions(prev => ({ ...prev, forceRefresh: e.target.checked }))
                      }
                      className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Làm mới dữ liệu có sẵn</span>
                  </label>
                </div>
              </div>

              <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                <button
                  type="button"
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-green-600 text-base font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 sm:col-start-2 sm:text-sm"
                  onClick={handleBatchEnrichment}
                >
                  Bắt đầu bổ sung
                </button>
                <button
                  type="button"
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 sm:mt-0 sm:col-start-1 sm:text-sm"
                  onClick={() => setBatchEnrichmentOpen(false)}
                >
                  Hủy
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Production Metrics Modal */}
      {metricsModalOpen && selectedMetricsMovie && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 relative">
            <button
              onClick={() => setMetricsModalOpen(false)}
              className="absolute top-3 right-3 text-gray-400 hover:text-gray-600"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
            <ProductionMetricsCard movie={selectedMetricsMovie} />
          </div>
        </div>
      )}

      {/* Movie Form Modal */}
      <MovieFormModal
        open={showMovieForm}
        onClose={() => {
          setShowMovieForm(false);
          setEditMovie(null);
        }}
        onSubmit={editMovie ? data => handleEditMovie(editMovie.id, data) : handleCreateMovie}
        movie={editMovie}
      />

      {/* Schedule Publish Modal */}
      <SchedulePublishModal
        isOpen={showScheduleModal}
        onClose={() => {
          setShowScheduleModal(false);
          setSelectedMovieForSchedule(null);
        }}
        onSchedule={handleSchedulePublish}
        movieTitle={selectedMovieForSchedule?.title}
      />
    </div>
  );
};

export default MovieManagement;
