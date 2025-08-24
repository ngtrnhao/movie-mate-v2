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
  // PencilIcon,
  AdjustmentsHorizontalIcon,
  MagnifyingGlassIcon,
  XCircleIcon,
  // PlusIcon,
  SparklesIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  // InformationCircleIcon,
  Cog6ToothIcon,
  ChartBarIcon,
  DocumentTextIcon,
  // PlayIcon,
  // PauseIcon,
  // EyeDropperIcon,
  // WrenchScrewdriverIcon,
  // ArrowPathIcon,
  // CheckBadgeIcon,
  // ExclamationCircleIcon,
  TrashIcon,
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
  enrichMovie,
  updateMovieQuality,
  updateMovieVisibility,
  approveMovie,
  rejectMovie,
  updateMoviePriority,
  scheduleMovieAction,
  updateAdminMovie,
  deleteAdminMovie,
  // getMovieEnrichmentStatus,
  // getMovieQualityDetails,
} from '../../../api/adminMovieService';
import { useDebounce } from '../../../hooks/useDebounce';
import { useProductionMetrics } from '../../../hooks/useProductionMetrics';
import MovieDetailsModal from '../../../components/common/MovieDetailsModal';
import MovieFormModal from '../../../components/common/MovieFormModal';
import ProductionMetricsCard from './ProductionMetricsCard';
import SchedulePublishModal from './SchedulePublishModal';

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

  // Filter state for production visibility
  const [visibilityFilter, setVisibilityFilter] = useState('all'); // 'all', 'displayed', 'not_displayed'
  const [statusFilter, setStatusFilter] = useState('all'); // 'all', 'approved', 'pending', 'rejected'
  const [qualityFilter, setQualityFilter] = useState('all'); // 'all', 'quality_met', 'quality_not_met'

  // Pagination state
  const [afterStack, setAfterStack] = useState([]); // Stack of after_created_at for prev
  const [currentAfter, setCurrentAfter] = useState(null); // Current after_created_at
  const [hasNext, setHasNext] = useState(false);
  const [hasPrevious, setHasPrevious] = useState(false);

  // Enhanced functionality state
  const [showEnrichmentModal, setShowEnrichmentModal] = useState(false);
  const [showQualityModal, setShowQualityModal] = useState(false);
  const [showDisplayModeModal, setShowDisplayModeModal] = useState(false);
  const [enrichmentData, setEnrichmentData] = useState({
    movie_id: null,
    sources: ['tmdb', 'imdb', 'omdb'],
    include_cast: true,
    include_crew: true,
    include_reviews: true,
    include_similar: true,
    force_refresh: false,
  });
  const [qualityData, setQualityData] = useState({
    movie_id: null,
    assessment_type: 'comprehensive',
    include_manual_review: true,
    auto_approve_threshold: 80,
    quality_metrics: ['completeness', 'accuracy', 'relevance', 'engagement'],
  });
  const [displayModeData, setDisplayModeData] = useState({
    movie_id: null,
    display_mode: 'auto',
    custom_settings: {
      priority_boost: 0,
      visibility_override: null,
      featured_duration: 7,
      audience_targeting: 'general',
      content_warnings: [],
    },
  });

  // Processing states
  const [enrichmentProcessing, setEnrichmentProcessing] = useState({});
  const [qualityProcessing, setQualityProcessing] = useState({});
  const [displayModeProcessing, setDisplayModeProcessing] = useState({});

  // Status tracking
  const [enrichmentStatus, setEnrichmentStatus] = useState({});
  const [qualityStatus, setQualityStatus] = useState({});
  const [displayModeStatus, setDisplayModeStatus] = useState({});

  // Visibility Stats
  const [stats, setStats] = useState({
    featured: 0,
    popular: 0,
    top_rated: 0,
    upcoming: 0,
    scheduled: 0,
  });

  // Detail / Metrics / Edit / Schedule modals state
  const [detailsModalOpen, setDetailsModalOpen] = useState(false);
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [metricsModalOpen, setMetricsModalOpen] = useState(false);
  const [selectedMetricsMovie, setSelectedMetricsMovie] = useState(null);
  const [showMovieForm, setShowMovieForm] = useState(false);
  const [editMovie, setEditMovie] = useState(null);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [selectedMovieForSchedule, setSelectedMovieForSchedule] = useState(null);

  const {
    loading: metricsLoading,
    error: metricsError,
    refreshMetrics,
  } = useProductionMetrics({ disableAutoRefresh: true });

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
  const fetchMovies = useCallback(
    async (direction = 'init', afterValue = null) => {
      const effectiveAfter = afterValue || currentAfter;
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

        // Add visibility filter
        if (visibilityFilter === 'displayed') {
          filters.is_published = 'true';
          filters.approval_status = 'APPROVED';
          filters.minimum_quality_met = 'true';
        } else if (visibilityFilter === 'not_displayed') {
          filters.is_published = 'false';
        }

        // Add status filter
        if (statusFilter !== 'all') {
          filters.approval_status = statusFilter.toUpperCase();
        }

        // Add quality filter
        if (qualityFilter === 'quality_met') {
          filters.minimum_quality_met = 'true';
        } else if (qualityFilter === 'quality_not_met') {
          filters.minimum_quality_met = 'false';
        }

        const params = {
          pageSize: 40,
          filters,
          search: debouncedSearchQuery, // Use debounced search
        };

        // Add pagination parameter
        if (effectiveAfter) {
          params.filters.after_created_at = effectiveAfter;
        }

        console.log('[VISIBILITY PAGINATION DEBUG] Fetching movies with params:', params);
        console.log(
          '[VISIBILITY PAGINATION DEBUG] Direction:',
          direction,
          'Effective after:',
          effectiveAfter
        );

        const data = await getAdminMovies(params);
        console.log('[VISIBILITY PAGINATION DEBUG] API response:', data);

        if (data.results) {
          setMovies(data.results);
        } else {
          setMovies(data || []);
        }

        // Keyset pagination logic
        setHasPrevious(afterStack.length > 0);

        // Store next_after_created_at from API response
        const nextAfterCreatedAt = data.next;
        console.log('[VISIBILITY PAGINATION DEBUG] Next after created at:', nextAfterCreatedAt);
        setHasNext(nextAfterCreatedAt);
      } catch (error) {
        console.error('Error fetching movies:', error);
      } finally {
        setLoading(false);
      }
    },
    [
      activeSection,
      debouncedSearchQuery,
      currentAfter,
      afterStack,
      visibilityFilter,
      statusFilter,
      qualityFilter,
    ]
  );

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
          fetchMovies('init', currentAfter);
          fetchStats();
        } else {
          console.error('Unknown visibility type:', type);
        }
      } catch (error) {
        console.error('Error toggling visibility:', error);
      }
    },
    [fetchMovies, fetchStats, currentAfter]
  );

  // Bulk Toggle Visibility
  const bulkToggleVisibility = useCallback(
    async (movieIds, type, enable) => {
      try {
        const action = enable ? `enable_${type}` : `disable_${type}`;
        await performBulkAction(action, movieIds);
        setSelectedMovies([]);
        fetchMovies('init', currentAfter);
        fetchStats();
      } catch (error) {
        console.error('Error performing bulk toggle:', error);
      }
    },
    [fetchMovies, fetchStats, currentAfter]
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
      fetchMovies('init', currentAfter);
      fetchStats();
    } catch (error) {
      console.error('Error scheduling visibility:', error);
    }
  }, [schedulerData, fetchMovies, fetchStats, currentAfter]);

  // Enhanced functionality handlers
  const handleEnrichMovieData = useCallback(
    async (movieId, options = {}) => {
      try {
        setEnrichmentProcessing(prev => ({ ...prev, [movieId]: true }));

        const result = await enrichMovie(movieId, {
          forceRefresh: options.forceRefresh || false,
          focusAreas: options.focusAreas || ['basic'],
          enrichType: options.enrichType || 'comprehensive',
        });

        // Update enrichment status
        setEnrichmentStatus(prev => ({
          ...prev,
          [movieId]: {
            status: 'completed',
            timestamp: new Date(),
            data: result,
          },
        }));

        // Refresh movie data
        fetchMovies('init', currentAfter);
        fetchStats();

        // Clear status after 3 seconds
        setTimeout(() => {
          setEnrichmentStatus(prev => {
            const updated = { ...prev };
            delete updated[movieId];
            return updated;
          });
        }, 3000);

        console.log('✅ Movie enrichment completed:', result);
      } catch (error) {
        console.error('❌ Error enriching movie data:', error);
        setEnrichmentStatus(prev => ({
          ...prev,
          [movieId]: {
            status: 'failed',
            timestamp: new Date(),
            error: error.message,
          },
        }));
      } finally {
        setEnrichmentProcessing(prev => ({ ...prev, [movieId]: false }));
      }
    },
    [fetchMovies, fetchStats, currentAfter]
  );

  const handleAssessMovieQuality = useCallback(
    async (movieId, options = {}) => {
      try {
        setQualityProcessing(prev => ({ ...prev, [movieId]: true }));

        const result = await updateMovieQuality(movieId, {
          quality_score: options.quality_score || null,
          content_completeness: options.content_completeness || null,
          minimum_quality_met: options.minimum_quality_met || null,
          quality_issues: options.quality_issues || [],
          assessment_type: options.assessment_type || 'comprehensive',
          auto_approve_threshold: options.auto_approve_threshold || 80,
        });

        // Update quality status
        setQualityStatus(prev => ({
          ...prev,
          [movieId]: {
            status: 'completed',
            timestamp: new Date(),
            data: result,
          },
        }));

        // Refresh movie data
        fetchMovies('init', currentAfter);
        fetchStats();

        // Clear status after 3 seconds
        setTimeout(() => {
          setQualityStatus(prev => {
            const updated = { ...prev };
            delete updated[movieId];
            return updated;
          });
        }, 3000);

        console.log('✅ Quality assessment completed:', result);
      } catch (error) {
        console.error('❌ Error assessing movie quality:', error);
        setQualityStatus(prev => ({
          ...prev,
          [movieId]: {
            status: 'failed',
            timestamp: new Date(),
            error: error.message,
          },
        }));
      } finally {
        setQualityProcessing(prev => ({ ...prev, [movieId]: false }));
      }
    },
    [fetchMovies, fetchStats, currentAfter]
  );

  const handleUpdateDisplayMode = useCallback(
    async (movieId, options = {}) => {
      try {
        setDisplayModeProcessing(prev => ({ ...prev, [movieId]: true }));

        const result = await updateMovieVisibility(movieId, {
          visibility_status: options.visibility_status || 'PUBLISHED',
          admin_featured: options.admin_featured || false,
          admin_priority: options.admin_priority || 0,
          display_mode: options.display_mode || 'auto',
          custom_settings: options.custom_settings || {},
        });

        // Update display mode status
        setDisplayModeStatus(prev => ({
          ...prev,
          [movieId]: {
            status: 'completed',
            timestamp: new Date(),
            data: result,
          },
        }));

        // Refresh movie data
        fetchMovies('init', currentAfter);
        fetchStats();

        // Clear status after 3 seconds
        setTimeout(() => {
          setDisplayModeStatus(prev => {
            const updated = { ...prev };
            delete updated[movieId];
            return updated;
          });
        }, 3000);

        console.log('✅ Display mode updated:', result);
      } catch (error) {
        console.error('❌ Error updating display mode:', error);
        setDisplayModeStatus(prev => ({
          ...prev,
          [movieId]: {
            status: 'failed',
            timestamp: new Date(),
            error: error.message,
          },
        }));
      } finally {
        setDisplayModeProcessing(prev => ({ ...prev, [movieId]: false }));
      }
    },
    [fetchMovies, fetchStats, currentAfter]
  );

  // Bulk operations for enhanced functionality
  const handleBulkEnrichment = useCallback(
    async (movieIds, options = {}) => {
      try {
        console.log('Starting bulk enrichment for', movieIds.length, 'movies');

        const promises = movieIds.map(movieId =>
          handleEnrichMovieData(movieId, {
            forceRefresh: options.forceRefresh || false,
            focusAreas: options.focusAreas || ['basic'],
            enrichType: options.enrichType || 'comprehensive',
          })
        );

        const results = await Promise.allSettled(promises);

        const succeeded = results.filter(r => r.status === 'fulfilled').length;
        const failed = results.filter(r => r.status === 'rejected').length;

        console.log(`✅ Bulk enrichment completed: ${succeeded} succeeded, ${failed} failed`);

        // Refresh data after bulk operation
        fetchMovies('init', currentAfter);
        fetchStats();

        // Clear selection after successful bulk operation
        if (succeeded > 0) {
          setSelectedMovies([]);
        }
      } catch (error) {
        console.error('❌ Error in bulk enrichment:', error);
      }
    },
    [handleEnrichMovieData, fetchMovies, fetchStats, currentAfter]
  );

  const handleBulkQualityAssessment = useCallback(
    async (movieIds, options = {}) => {
      try {
        console.log('Starting bulk quality assessment for', movieIds.length, 'movies');

        const promises = movieIds.map(movieId =>
          handleAssessMovieQuality(movieId, {
            assessment_type: options.assessment_type || 'comprehensive',
            auto_approve_threshold: options.auto_approve_threshold || 80,
            quality_metrics: options.quality_metrics || ['completeness', 'accuracy', 'relevance'],
          })
        );

        const results = await Promise.allSettled(promises);

        const succeeded = results.filter(r => r.status === 'fulfilled').length;
        const failed = results.filter(r => r.status === 'rejected').length;

        console.log(
          `✅ Bulk quality assessment completed: ${succeeded} succeeded, ${failed} failed`
        );

        // Refresh data after bulk operation
        fetchMovies('init', currentAfter);
        fetchStats();

        // Clear selection after successful bulk operation
        if (succeeded > 0) {
          setSelectedMovies([]);
        }
      } catch (error) {
        console.error('❌ Error in bulk quality assessment:', error);
      }
    },
    [handleAssessMovieQuality, fetchMovies, fetchStats, currentAfter]
  );

  const handleBulkDisplayModeUpdate = useCallback(
    async (movieIds, options = {}) => {
      try {
        console.log('Starting bulk display mode update for', movieIds.length, 'movies');

        const promises = movieIds.map(movieId =>
          handleUpdateDisplayMode(movieId, {
            display_mode: options.display_mode || 'auto',
            visibility_status: options.visibility_status || 'PUBLISHED',
            admin_featured: options.admin_featured || false,
            admin_priority: options.admin_priority || 0,
            custom_settings: options.custom_settings || {},
          })
        );

        const results = await Promise.allSettled(promises);

        const succeeded = results.filter(r => r.status === 'fulfilled').length;
        const failed = results.filter(r => r.status === 'rejected').length;

        console.log(
          `✅ Bulk display mode update completed: ${succeeded} succeeded, ${failed} failed`
        );

        // Refresh data after bulk operation
        fetchMovies('init', currentAfter);
        fetchStats();

        // Clear selection after successful bulk operation
        if (succeeded > 0) {
          setSelectedMovies([]);
        }
      } catch (error) {
        console.error('❌ Error in bulk display mode update:', error);
      }
    },
    [handleUpdateDisplayMode, fetchMovies, fetchStats, currentAfter]
  );

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
    // Reset pagination when search changes
    setCurrentAfter(null);
    setAfterStack([]);
    setHasPrevious(false);
  };

  // Approve / Reject actions
  const approveMovieAction = useCallback(
    async movieId => {
      try {
        await approveMovie(movieId);
        await Promise.all([fetchMovies('init', currentAfter), fetchStats()]);
      } catch (error) {
        console.error('Error approving movie:', error);
      }
    },
    [fetchMovies, fetchStats, currentAfter]
  );

  const rejectMovieAction = useCallback(
    async (movieId, reason = 'Không đạt yêu cầu chất lượng') => {
      try {
        await rejectMovie(movieId, reason);
        await Promise.all([fetchMovies('init', currentAfter), fetchStats()]);
      } catch (error) {
        console.error('Error rejecting movie:', error);
      }
    },
    [fetchMovies, fetchStats, currentAfter]
  );

  // Toggle publish (publish/unpublish)
  const togglePublishStatus = useCallback(
    async movieId => {
      try {
        await performBulkAction('toggle_publish', [movieId]);
        await Promise.all([fetchMovies('init', currentAfter), fetchStats()]);
      } catch (error) {
        console.error('Error toggling publish status:', error);
      }
    },
    [fetchMovies, fetchStats, currentAfter]
  );

  // Priority update
  const updatePriorityAction = useCallback(
    async (movieId, priority) => {
      try {
        await updateMoviePriority(movieId, priority);
        await fetchMovies('init', currentAfter);
      } catch (error) {
        console.error('Error updating priority:', error);
      }
    },
    [fetchMovies, currentAfter]
  );

  // Details modal handlers
  const handleViewDetails = useCallback(movie => {
    const enhancedMovie = { ...movie, title: movie?.title || 'Unknown Movie' };
    setSelectedMovie(enhancedMovie);
    setDetailsModalOpen(true);
  }, []);

  const handleCloseDetails = useCallback(() => {
    setSelectedMovie(null);
    setDetailsModalOpen(false);
  }, []);

  // Metrics modal
  const handleViewMetrics = useCallback(movie => {
    setSelectedMetricsMovie(movie);
    setMetricsModalOpen(true);
  }, []);

  // Edit / Delete
  const handleEditMovie = useCallback(
    async (movieId, movieData) => {
      try {
        await updateAdminMovie(movieId, movieData);
        setShowMovieForm(false);
        setEditMovie(null);
        await fetchMovies('init', currentAfter);
      } catch (error) {
        alert(error.error || 'Không thể cập nhật phim');
      }
    },
    [fetchMovies, currentAfter]
  );

  const handleDeleteMovie = useCallback(
    async movieId => {
      if (!window.confirm('Bạn có chắc chắn muốn xóa phim này?')) return;
      try {
        await deleteAdminMovie(movieId);
        await fetchMovies('init', currentAfter);
      } catch (error) {
        alert(error.error || 'Không thể xóa phim');
      }
    },
    [fetchMovies, currentAfter]
  );

  // Schedule publish
  const handleOpenScheduleModal = useCallback(movie => {
    setSelectedMovieForSchedule(movie);
    setShowScheduleModal(true);
  }, []);

  const handleSchedulePublish = useCallback(
    async scheduleData => {
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
        await fetchMovies('init', currentAfter);
      } catch (error) {
        alert(error.error || 'Không thể lên lịch xuất bản phim');
      }
    },
    [selectedMovieForSchedule, fetchMovies, currentAfter]
  );

  // Quality Review handler (borrowed behavior from MovieManagement)
  const handleQualityReview = useCallback(movie => {
    // Open the common MovieQualityModal via local Quality modal flag
    // Reuse existing quality modal state and data
    const enhancedMovie = {
      ...movie,
      quality_metrics: movie.quality_metrics || {
        quality_score: movie.quality_score ?? null,
        content_completeness: movie.content_completeness ?? '0.00',
        minimum_quality_met: movie.minimum_quality_met ?? false,
        overall_quality_rating: movie.overall_quality_rating || 'Not Assessed',
        completion_status: movie.completion_status || 'Incomplete',
        quality_issues: movie.quality_issues || [],
        quality_suggestions: movie.quality_suggestions || [],
      },
    };
    setSelectedMovie(enhancedMovie);
    setQualityData(prev => ({ ...prev, movie_id: movie.id }));
    setShowQualityModal(true);
  }, []);

  // Pagination handlers
  const handleNextPage = () => {
    if (hasNext && (typeof hasNext === 'string' || Array.isArray(hasNext))) {
      // Only push currentAfter if it's not null (don't push on first page)
      setAfterStack(prev => (currentAfter ? [...prev, currentAfter] : prev));
      setCurrentAfter(hasNext);
      fetchMovies('next', hasNext);
    }
  };

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

  // Load data on mount and when dependencies change
  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  useEffect(() => {
    // Reset pagination when section, search, or filters change
    setCurrentAfter(null);
    setAfterStack([]);
    setHasPrevious(false);
    fetchMovies('init');
  }, [activeSection, debouncedSearchQuery, visibilityFilter, statusFilter, qualityFilter]);

  // Render Movie Card
  const renderMovieCard = movie => {
    const category = visibilityCategories[activeSection];
    const isActive = movie[category?.field] || false;
    const releaseYear = movie?.release_date ? new Date(movie.release_date).getFullYear() : 'N/A';
    const genres = movie?.genres?.map(g => g.name).join(', ') || 'N/A';
    const runtime = movie?.runtime ? `${movie.runtime} min` : 'N/A';
    const qualityScore = movie?.quality_score || 0;
    const completeness = movie?.content_completeness || 0;
    const approvalStatus = movie?.approval_status || 'PENDING';
    const isFeatured = !!(movie?.admin_control?.admin_featured ?? movie?.admin_featured);
    const isPublished = !!(movie?.admin_control?.visibility_status
      ? movie.admin_control.visibility_status === 'PUBLISHED'
      : movie?.is_published);
    const adminPriority =
      movie?.admin_control?.admin_priority ??
      (typeof movie?.admin_priority === 'number' ? movie.admin_priority : 0);

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
          {movie?.poster_url ? (
            <img
              src={movie.poster_url}
              alt={movie?.title || 'Movie poster'}
              className="size-full object-cover"
              loading="lazy"
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center">
              <EyeIcon className="size-12 text-gray-400" />
            </div>
          )}
          {isActive && category && (
            <div className="absolute right-2 top-2">
              <category.iconSolid className="size-6 text-yellow-400 drop-shadow" />
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

          {/* Visibility Status Badges */}
          <div className="mt-4 space-y-2">
            {/* Production Status Badge */}
            {/* <div className="flex items-center justify-between">
              {movie.is_published &&
              movie.approval_status === 'APPROVED' &&
              movie.minimum_quality_met ? (
                <span className="inline-flex items-center rounded-full border border-green-200 bg-green-100 px-2 py-1 text-xs font-medium text-green-800">
                  <EyeIcon className="mr-1 size-3" />
                  Đang hiển thị trên Production
                </span>
              ) : (
                <span className="inline-flex items-center rounded-full border border-red-200 bg-red-100 px-2 py-1 text-xs font-medium text-red-800">
                  <EyeSlashIcon className="mr-1 size-3" />
                  Chưa hiển thị trên Production
                </span>
              )}
            </div> */}

            {/* Category Status Badges */}
            <div className="flex flex-wrap gap-1">
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
          </div>

          {/* Quality Metrics */}
          <div className="mt-4">
            <div className="mb-2 flex items-center justify-between text-xs text-gray-700">
              <span className="font-medium">Chất lượng:</span>
              <span
                className={`rounded px-2 py-1 text-xs ${
                  movie?.minimum_quality_met
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}
              >
                {movie?.minimum_quality_met ? 'Đạt chuẩn' : 'Chưa đạt chuẩn'}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center text-gray-500">
                <CheckCircleIcon className="mr-1 size-3" />
                {parseFloat(completeness || 0).toFixed(1)}%
              </div>
              <div className="flex items-center text-gray-500">
                <StarIcon className="mr-1 size-3" />
                {qualityScore ? parseFloat(qualityScore).toFixed(1) : 'N/A'}
              </div>
            </div>
            {movie?.quality_issues?.length > 0 && (
              <div className="mt-1 text-xs text-red-600">
                <XCircleIcon className="mr-1 inline size-3" />
                {movie.quality_issues.length} vấn đề
              </div>
            )}
          </div>

          {/* Production Metrics */}
          <div className="mt-4">
            <div className="mb-2 flex items-center justify-between text-xs text-gray-700">
              <span className="font-medium">Hiệu suất:</span>
              <span className="rounded bg-gray-100 px-2 py-1 text-xs text-gray-800">
                {movie.production_metrics?.trending_category || 'stable'}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center text-gray-500">
                <EyeIcon className="mr-1 size-3" />
                {movie.production_metrics?.homepage_views || 0}
              </div>
              <div className="flex items-center text-gray-500">
                <MagnifyingGlassIcon className="mr-1 size-3" />
                {movie.production_metrics?.detail_page_views || 0}
              </div>
            </div>
            <div className="mt-1 text-xs text-gray-500">
              Rating: {movie.cached_imdb_rating || 'N/A'}
            </div>
          </div>

          {/* Scheduling Info */}
          {(movie.featured_from || movie.featured_until) && (
            <div className="mt-4">
              <div className="mb-1 text-xs font-medium text-gray-700">Lịch trình:</div>
              <div className="text-xs text-gray-500">
                <ClockIcon className="mr-1 inline size-3" />
                Featured:{' '}
                {movie.featured_from && new Date(movie.featured_from).toLocaleDateString()}
                {movie.featured_until &&
                  ` - ${new Date(movie.featured_until).toLocaleDateString()}`}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="mt-4 space-y-2">
            {/* Primary Actions Row - align with MovieManagement */}
            <div className="space-y-2">
              {/* View Details */}
              <button
                onClick={() => handleViewDetails(movie)}
                className="inline-flex w-full items-center justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
              >
                <EyeIcon className="mr-1.5 size-4" />
                Xem chi tiết
              </button>

              {/* Approval actions */}
              {(approvalStatus === 'NEEDS_REVIEW' || approvalStatus === 'PENDING') && (
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => approveMovieAction(movie.id)}
                    className="inline-flex flex-1 items-center justify-center rounded-md border border-transparent bg-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-green-700"
                  >
                    <CheckCircleIcon className="mr-1.5 size-4" />
                    Duyệt
                  </button>
                  <button
                    onClick={() => rejectMovieAction(movie.id, 'Không đạt yêu cầu chất lượng')}
                    className="inline-flex flex-1 items-center justify-center rounded-md border border-transparent bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700"
                  >
                    <XCircleIcon className="mr-1.5 size-4" />
                    Từ chối
                  </button>
                </div>
              )}

              {/* Schedule publish for pending and approved */}
              {(approvalStatus === 'PENDING' || approvalStatus === 'APPROVED') && (
                <button
                  onClick={() => handleOpenScheduleModal(movie)}
                  className="inline-flex w-full items-center justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  <CalendarIcon className="mr-1.5 size-4" />
                  Lên lịch xuất bản
                </button>
              )}

              {/* Admin control actions */}
              {approvalStatus === 'APPROVED' && (
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => toggleVisibility(movie.id, 'featured')}
                    className={`inline-flex items-center justify-center rounded-md border px-3 py-2 text-xs font-medium ${
                      isFeatured
                        ? 'border-yellow-300 bg-yellow-50 text-yellow-800 hover:bg-yellow-100'
                        : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                    } transition-colors`}
                  >
                    <StarIcon className="mr-1 size-3" />
                    {isFeatured ? 'Bỏ Featured' : 'Featured'}
                  </button>

                  <button
                    onClick={() => togglePublishStatus(movie.id)}
                    className={`inline-flex items-center justify-center rounded-md border px-3 py-2 text-xs font-medium ${
                      isPublished
                        ? 'border-blue-300 bg-blue-50 text-blue-800 hover:bg-blue-100'
                        : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                    } transition-colors`}
                  >
                    <EyeIcon className="mr-1 size-3" />
                    {isPublished ? 'Ẩn' : 'Xuất bản'}
                  </button>
                </div>
              )}
            </div>

            {/* Primary Visibility Toggle */}
            <button
              onClick={() => toggleVisibility(movie.id, activeSection)}
              className={`inline-flex w-full items-center justify-center rounded-md border px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                isActive
                  ? 'border-gray-300 bg-gray-100 text-gray-700 hover:bg-gray-200 focus:ring-gray-500'
                  : `${category?.buttonColor} focus:ring- text-white${category?.color}-500`
              }`}
              title={isActive ? `Bỏ ${category?.title}` : `Đặt ${category?.title}`}
            >
              {isActive ? (
                <>
                  <XMarkIcon className="mr-1.5 size-4" />
                  Bỏ {category?.title.split(' ')[0]}
                </>
              ) : (
                <>
                  <category.icon className="mr-1.5 size-4" />
                  Đặt {category?.title.split(' ')[0]}
                </>
              )}
            </button>

            {/* Secondary Actions */}
            <div className="grid grid-cols-2 gap-2">
              {!isActive && (
                <button
                  onClick={() => {
                    setSchedulerData({ ...schedulerData, movie_id: movie.id, type: activeSection });
                    setShowScheduler(true);
                  }}
                  className="inline-flex items-center justify-center rounded-md border border-gray-300 bg-white px-3 py-2 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-50"
                  title="Lên lịch hiển thị"
                >
                  <ClockIcon className="mr-1 size-3" />
                  Lên lịch
                </button>
              )}

              <button
                onClick={() => handleViewMetrics(movie)}
                className="inline-flex items-center justify-center rounded-md border border-purple-300 bg-purple-50 px-3 py-2 text-xs font-medium text-purple-800 transition-colors hover:bg-purple-100"
                title="Xem Production Metrics"
              >
                <ChartBarIcon className="mr-1 size-3" />
                Xem Metrics
              </button>
            </div>

            {/* Quality & Enrichment Actions borrowed from MovieManagement */}
            <div className="space-y-2">
              {Array.isArray(movie?.quality_issues) && movie.quality_issues.length > 0 && (
                <button
                  onClick={() => handleQualityReview(movie)}
                  className="inline-flex w-full items-center justify-center rounded-md border border-orange-300 bg-orange-50 px-3 py-2 text-xs font-medium text-orange-800 hover:bg-orange-100 transition-colors"
                >
                  <ExclamationTriangleIcon className="mr-1 size-3" />
                  Khắc phục chất lượng ({movie.quality_issues.length})
                </button>
              )}

              <button
                onClick={() => handleQualityReview(movie)}
                className="inline-flex w-full items-center justify-center rounded-md border border-blue-300 bg-blue-50 px-3 py-2 text-xs font-medium text-blue-800 hover:bg-blue-100 transition-colors"
              >
                <ChartBarIcon className="mr-1 size-3" />
                Đánh giá chất lượng
              </button>

              <button
                onClick={() =>
                  handleEnrichMovieData(movie.id, {
                    focusAreas: ['basic', 'visual'],
                    enrichType: 'quality_based',
                  })
                }
                disabled={enrichmentProcessing[movie.id]}
                className="inline-flex w-full items-center justify-center rounded-md border border-green-300 bg-green-50 px-3 py-2 text-xs font-medium text-green-800 hover:bg-green-100 transition-colors disabled:cursor-not-allowed disabled:opacity-50"
                title="Bổ sung dữ liệu phim"
              >
                {enrichmentProcessing[movie.id] ? (
                  <>
                    <div className="mr-1 size-3 animate-spin rounded-full border-2 border-green-800 border-t-transparent" />
                    Đang xử lý...
                  </>
                ) : enrichmentStatus[movie.id]?.status === 'completed' ? (
                  <>
                    <CheckCircleIcon className="mr-1 size-3" />
                    Đã cập nhật ✓
                  </>
                ) : enrichmentStatus[movie.id]?.status === 'failed' ? (
                  <>
                    <ExclamationTriangleIcon className="mr-1 size-3" />
                    Lỗi
                  </>
                ) : (
                  <>
                    <DocumentTextIcon className="mr-1 size-3" />
                    Bổ sung dữ liệu
                  </>
                )}
              </button>
            </div>

            {/* Priority Adjustment */}
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-500">Ưu tiên:</span>
              <div className="flex items-center space-x-1">
                <button
                  onClick={() =>
                    updatePriorityAction(movie.id, Math.max(0, (adminPriority || 0) - 1))
                  }
                  className="rounded border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
                >
                  -
                </button>
                <span className="w-6 text-center text-xs font-medium text-gray-700">
                  {adminPriority}
                </span>
                <button
                  onClick={() =>
                    updatePriorityAction(movie.id, Math.min(10, (adminPriority || 0) + 1))
                  }
                  className="rounded border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
                >
                  +
                </button>
              </div>
            </div>

            {/* Edit / Delete */}
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
                <TrashIcon className="mr-1 size-3" />
                Xóa
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

              {/* Enhanced Functionality Bulk Actions */}
              {selectedMovies.length > 0 && (
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleBulkEnrichment(selectedMovies)}
                    className="inline-flex items-center rounded-md border border-blue-300 bg-blue-50 px-3 py-2 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    title="Bổ sung dữ liệu cho phim đã chọn"
                  >
                    <SparklesIcon className="mr-1 size-4" />
                    Bổ sung ({selectedMovies.length})
                  </button>

                  <button
                    onClick={() => handleBulkQualityAssessment(selectedMovies)}
                    className="inline-flex items-center rounded-md border border-green-300 bg-green-50 px-3 py-2 text-sm font-medium text-green-700 transition-colors hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                    title="Đánh giá chất lượng cho phim đã chọn"
                  >
                    <ShieldCheckIcon className="mr-1 size-4" />
                    Chất lượng ({selectedMovies.length})
                  </button>

                  <button
                    onClick={() => handleBulkDisplayModeUpdate(selectedMovies)}
                    className="inline-flex items-center rounded-md border border-purple-300 bg-purple-50 px-3 py-2 text-sm font-medium text-purple-700 transition-colors hover:bg-purple-100 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
                    title="Cập nhật chế độ hiển thị cho phim đã chọn"
                  >
                    <Cog6ToothIcon className="mr-1 size-4" />
                    Hiển thị ({selectedMovies.length})
                  </button>
                </div>
              )}
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

            {/* Filter Controls */}
            <div className="flex items-center space-x-4">
              {/* Visibility Filter */}
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700">Hiển thị:</label>
                <select
                  value={visibilityFilter}
                  onChange={e => setVisibilityFilter(e.target.value)}
                  className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                >
                  <option value="all">Tất cả</option>
                  <option value="displayed">Đang hiển thị</option>
                  <option value="not_displayed">Chưa hiển thị</option>
                </select>
              </div>

              {/* Status Filter */}
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700">Trạng thái:</label>
                <select
                  value={statusFilter}
                  onChange={e => setStatusFilter(e.target.value)}
                  className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                >
                  <option value="all">Tất cả</option>
                  <option value="approved">Đã phê duyệt</option>
                  <option value="pending">Chờ phê duyệt</option>
                  <option value="rejected">Bị từ chối</option>
                </select>
              </div>

              {/* Quality Filter */}
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700">Chất lượng:</label>
                <select
                  value={qualityFilter}
                  onChange={e => setQualityFilter(e.target.value)}
                  className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                >
                  <option value="all">Tất cả</option>
                  <option value="quality_met">Đạt chuẩn</option>
                  <option value="quality_not_met">Chưa đạt chuẩn</option>
                </select>
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

              {/* Pagination */}
              <div className="mt-6 flex items-center justify-between border-t border-gray-200 bg-gray-50 px-6 py-4">
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
            </div>
          )}
        </div>

        {/* Filter Summary */}
        <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <EyeIcon className="size-4 text-green-600" />
                <span className="text-sm text-gray-700">
                  Đang hiển thị:{' '}
                  <span className="font-medium text-green-600">
                    {
                      movies.filter(
                        m =>
                          m.is_published &&
                          m.approval_status === 'APPROVED' &&
                          m.minimum_quality_met
                      ).length
                    }
                  </span>
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <EyeSlashIcon className="size-4 text-red-600" />
                <span className="text-sm text-gray-700">
                  Chưa hiển thị:{' '}
                  <span className="font-medium text-red-600">
                    {
                      movies.filter(
                        m =>
                          !m.is_published ||
                          m.approval_status !== 'APPROVED' ||
                          !m.minimum_quality_met
                      ).length
                    }
                  </span>
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircleIcon className="size-4 text-blue-600" />
                <span className="text-sm text-gray-700">
                  Đạt chuẩn:{' '}
                  <span className="font-medium text-blue-600">
                    {movies.filter(m => m.minimum_quality_met).length}
                  </span>
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <ExclamationTriangleIcon className="size-4 text-orange-600" />
                <span className="text-sm text-gray-700">
                  Chưa đạt chuẩn:{' '}
                  <span className="font-medium text-orange-600">
                    {movies.filter(m => !m.minimum_quality_met).length}
                  </span>
                </span>
              </div>
            </div>

            {/* Active Filters Display */}
            <div className="flex items-center space-x-2">
              {(visibilityFilter !== 'all' ||
                statusFilter !== 'all' ||
                qualityFilter !== 'all') && (
                <>
                  <span className="text-sm text-gray-500">Bộ lọc đang áp dụng:</span>
                  <div className="flex items-center space-x-1">
                    {visibilityFilter !== 'all' && (
                      <span className="inline-flex items-center rounded-full bg-purple-100 px-2 py-1 text-xs font-medium text-purple-800">
                        {visibilityFilter === 'displayed' ? 'Đang hiển thị' : 'Chưa hiển thị'}
                      </span>
                    )}
                    {statusFilter !== 'all' && (
                      <span className="inline-flex items-center rounded-full bg-blue-100 px-2 py-1 text-xs font-medium text-blue-800">
                        {statusFilter === 'approved'
                          ? 'Đã phê duyệt'
                          : statusFilter === 'pending'
                            ? 'Chờ phê duyệt'
                            : 'Bị từ chối'}
                      </span>
                    )}
                    {qualityFilter !== 'all' && (
                      <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-800">
                        {qualityFilter === 'quality_met' ? 'Đạt chuẩn' : 'Chưa đạt chuẩn'}
                      </span>
                    )}
                    <button
                      onClick={() => {
                        setVisibilityFilter('all');
                        setStatusFilter('all');
                        setQualityFilter('all');
                      }}
                      className="ml-2 text-xs text-gray-500 hover:text-gray-700"
                    >
                      Xóa tất cả
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Scheduler Modal */}
        {showScheduler && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
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

        {/* Data Enrichment Modal */}
        {showEnrichmentModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Bổ sung dữ liệu phim</h3>
                <button
                  onClick={() => setShowEnrichmentModal(false)}
                  className="text-gray-400 transition-colors hover:text-gray-500"
                >
                  <XMarkIcon className="size-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Nguồn dữ liệu
                  </label>
                  <div className="space-y-2">
                    {['tmdb', 'imdb', 'omdb'].map(source => (
                      <label key={source} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={enrichmentData.sources.includes(source)}
                          onChange={e => {
                            const newSources = e.target.checked
                              ? [...enrichmentData.sources, source]
                              : enrichmentData.sources.filter(s => s !== source);
                            setEnrichmentData({ ...enrichmentData, sources: newSources });
                          }}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">{source.toUpperCase()}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Loại dữ liệu bổ sung
                  </label>
                  <div className="space-y-2">
                    {[
                      { key: 'include_cast', label: 'Thông tin diễn viên' },
                      { key: 'include_crew', label: 'Thông tin đoàn làm phim' },
                      { key: 'include_reviews', label: 'Đánh giá và review' },
                      { key: 'include_similar', label: 'Phim tương tự' },
                    ].map(item => (
                      <label key={item.key} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={enrichmentData[item.key]}
                          onChange={e =>
                            setEnrichmentData({
                              ...enrichmentData,
                              [item.key]: e.target.checked,
                            })
                          }
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">{item.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Tùy chọn bổ sung
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={enrichmentData.force_refresh}
                        onChange={e =>
                          setEnrichmentData({
                            ...enrichmentData,
                            force_refresh: e.target.checked,
                          })
                        }
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">Cập nhật lại dữ liệu đã có</span>
                    </label>
                  </div>
                </div>
              </div>

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setShowEnrichmentModal(false)}
                  className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                >
                  Hủy
                </button>
                <button
                  onClick={() => {
                    handleEnrichMovieData(enrichmentData.movie_id, {
                      forceRefresh: enrichmentData.force_refresh,
                      focusAreas: enrichmentData.sources,
                      enrichType: 'comprehensive',
                    });
                    setShowEnrichmentModal(false);
                  }}
                  className="rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  Bổ sung dữ liệu
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Quality Assessment Modal */}
        {showQualityModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Đánh giá chất lượng</h3>
                <button
                  onClick={() => setShowQualityModal(false)}
                  className="text-gray-400 transition-colors hover:text-gray-500"
                >
                  <XMarkIcon className="size-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Loại đánh giá
                  </label>
                  <select
                    value={qualityData.assessment_type}
                    onChange={e =>
                      setQualityData({ ...qualityData, assessment_type: e.target.value })
                    }
                    className="block w-full rounded-md border-gray-300 text-gray-900 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm"
                  >
                    <option value="comprehensive">Đánh giá toàn diện</option>
                    <option value="content">Đánh giá nội dung</option>
                    <option value="technical">Đánh giá kỹ thuật</option>
                    <option value="user_experience">Đánh giá trải nghiệm người dùng</option>
                  </select>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Tiêu chí đánh giá
                  </label>
                  <div className="space-y-2">
                    {[
                      { key: 'completeness', label: 'Tính đầy đủ' },
                      { key: 'accuracy', label: 'Tính chính xác' },
                      { key: 'relevance', label: 'Tính liên quan' },
                      { key: 'engagement', label: 'Khả năng tương tác' },
                    ].map(item => (
                      <label key={item.key} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={qualityData.quality_metrics.includes(item.key)}
                          onChange={e => {
                            const newMetrics = e.target.checked
                              ? [...qualityData.quality_metrics, item.key]
                              : qualityData.quality_metrics.filter(m => m !== item.key);
                            setQualityData({ ...qualityData, quality_metrics: newMetrics });
                          }}
                          className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">{item.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Ngưỡng tự động phê duyệt (%)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={qualityData.auto_approve_threshold}
                    onChange={e =>
                      setQualityData({
                        ...qualityData,
                        auto_approve_threshold: parseInt(e.target.value),
                      })
                    }
                    className="block w-full rounded-md border-gray-300 text-gray-900 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Tùy chọn bổ sung
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={qualityData.include_manual_review}
                        onChange={e =>
                          setQualityData({
                            ...qualityData,
                            include_manual_review: e.target.checked,
                          })
                        }
                        className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">Bao gồm đánh giá thủ công</span>
                    </label>
                  </div>
                </div>
              </div>

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setShowQualityModal(false)}
                  className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                >
                  Hủy
                </button>
                <button
                  onClick={() => {
                    handleAssessMovieQuality(qualityData.movie_id, {
                      assessment_type: qualityData.assessment_type,
                      auto_approve_threshold: qualityData.auto_approve_threshold,
                      quality_metrics: qualityData.quality_metrics,
                    });
                    setShowQualityModal(false);
                  }}
                  className="rounded-md border border-transparent bg-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                >
                  Đánh giá chất lượng
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Display Mode Modal */}
        {showDisplayModeModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Điều chỉnh chế độ hiển thị</h3>
                <button
                  onClick={() => setShowDisplayModeModal(false)}
                  className="text-gray-400 transition-colors hover:text-gray-500"
                >
                  <XMarkIcon className="size-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Chế độ hiển thị
                  </label>
                  <select
                    value={displayModeData.display_mode}
                    onChange={e =>
                      setDisplayModeData({ ...displayModeData, display_mode: e.target.value })
                    }
                    className="block w-full rounded-md border-gray-300 text-gray-900 shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                  >
                    <option value="auto">Tự động</option>
                    <option value="manual">Thủ công</option>
                    <option value="scheduled">Theo lịch</option>
                    <option value="conditional">Có điều kiện</option>
                  </select>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Tăng độ ưu tiên
                  </label>
                  <input
                    type="number"
                    min="-10"
                    max="10"
                    value={displayModeData.custom_settings.priority_boost}
                    onChange={e =>
                      setDisplayModeData({
                        ...displayModeData,
                        custom_settings: {
                          ...displayModeData.custom_settings,
                          priority_boost: parseInt(e.target.value),
                        },
                      })
                    }
                    className="block w-full rounded-md border-gray-300 text-gray-900 shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Thời gian hiển thị (ngày)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="30"
                    value={displayModeData.custom_settings.featured_duration}
                    onChange={e =>
                      setDisplayModeData({
                        ...displayModeData,
                        custom_settings: {
                          ...displayModeData.custom_settings,
                          featured_duration: parseInt(e.target.value),
                        },
                      })
                    }
                    className="block w-full rounded-md border-gray-300 text-gray-900 shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Đối tượng mục tiêu
                  </label>
                  <select
                    value={displayModeData.custom_settings.audience_targeting}
                    onChange={e =>
                      setDisplayModeData({
                        ...displayModeData,
                        custom_settings: {
                          ...displayModeData.custom_settings,
                          audience_targeting: e.target.value,
                        },
                      })
                    }
                    className="block w-full rounded-md border-gray-300 text-gray-900 shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm"
                  >
                    <option value="general">Tổng quát</option>
                    <option value="adult">Người lớn</option>
                    <option value="teen">Thanh thiếu niên</option>
                    <option value="children">Trẻ em</option>
                    <option value="family">Gia đình</option>
                  </select>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Cảnh báo nội dung
                  </label>
                  <div className="space-y-2">
                    {[
                      'violence',
                      'language',
                      'sexual_content',
                      'drug_use',
                      'disturbing_content',
                    ].map(warning => (
                      <label key={warning} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={displayModeData.custom_settings.content_warnings.includes(
                            warning
                          )}
                          onChange={e => {
                            const newWarnings = e.target.checked
                              ? [...displayModeData.custom_settings.content_warnings, warning]
                              : displayModeData.custom_settings.content_warnings.filter(
                                  w => w !== warning
                                );
                            setDisplayModeData({
                              ...displayModeData,
                              custom_settings: {
                                ...displayModeData.custom_settings,
                                content_warnings: newWarnings,
                              },
                            });
                          }}
                          className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">
                          {warning.replace('_', ' ')}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setShowDisplayModeModal(false)}
                  className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                >
                  Hủy
                </button>
                <button
                  onClick={() => {
                    handleUpdateDisplayMode(displayModeData.movie_id, {
                      display_mode: displayModeData.display_mode,
                      visibility_status: 'PUBLISHED',
                      admin_featured: false,
                      admin_priority: displayModeData.custom_settings.priority_boost || 0,
                      custom_settings: displayModeData.custom_settings,
                    });
                    setShowDisplayModeModal(false);
                  }}
                  className="rounded-md border border-transparent bg-purple-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
                >
                  Cập nhật chế độ hiển thị
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Movie Details Modal */}
        {detailsModalOpen && selectedMovie && (
          <MovieDetailsModal movie={selectedMovie} open={true} onClose={handleCloseDetails} />
        )}

        {/* Production Metrics Modal */}
        {metricsModalOpen && selectedMetricsMovie && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="w-full max-w-3xl rounded-lg bg-white p-6 shadow-xl">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Production Metrics</h3>
                <button
                  onClick={() => setMetricsModalOpen(false)}
                  className="text-gray-400 transition-colors hover:text-gray-500"
                >
                  <XMarkIcon className="size-6" />
                </button>
              </div>
              <ProductionMetricsCard movie={selectedMetricsMovie} />
            </div>
          </div>
        )}

        {/* Movie Form Modal (Edit) */}
        {showMovieForm && editMovie && (
          <MovieFormModal
            open={showMovieForm}
            onClose={() => {
              setShowMovieForm(false);
              setEditMovie(null);
            }}
            onSubmit={data => handleEditMovie(editMovie.id, data)}
            movie={editMovie}
          />
        )}

        {/* Schedule Publish Modal */}
        {showScheduleModal && selectedMovieForSchedule && (
          <SchedulePublishModal
            isOpen={showScheduleModal}
            onClose={() => {
              setShowScheduleModal(false);
              setSelectedMovieForSchedule(null);
            }}
            onSchedule={handleSchedulePublish}
            movieTitle={selectedMovieForSchedule?.title}
          />
        )}
      </div>
    );
  };

  return renderContent();
};

export default VisibilityControl;
