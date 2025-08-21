import axiosInstance from './axios';

// Request deduplication cache
const pendingRequests = new Map();

// Helper function to handle API responses
const handleResponse = response => {
  // Nếu response có status field và là success
  if (response.data && response.data.status === 'success') {
    return response.data.data;
  }

  // Nếu response không có status field nhưng có data (thành công)
  if (response.data && response.data.data) {
    return response.data.data;
  }

  // Nếu response trực tiếp là data (thành công) - trường hợp này
  if (response.data && !response.data.status && response.data.id) {
    return response.data;
  }

  // Nếu có message error
  if (response.data && response.data.message) {
    throw new Error(response.data.message);
  }

  // Fallback
  throw new Error('API request failed');
};

// Helper function to handle API errors
const handleError = (error, operation) => {
  console.error(`Error ${operation}:`, error);
  throw {
    error: error.response?.data?.message || `Failed to ${operation}`,
    details: error.response?.data,
  };
};

// Helper function to retry API requests
const retryRequest = async (requestFn, retries = 2, delay = 1000) => {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await requestFn();
    } catch (error) {
      console.log(`Attempt ${attempt + 1} failed:`, error.message);

      if (attempt === retries) {
        throw error; // Last attempt failed, throw the error
      }

      // Skip retry for certain errors
      if (error.response?.status === 401 || error.response?.status === 403) {
        throw error; // Don't retry auth errors
      }

      // Don't retry if request was canceled/aborted
      if (
        error.name === 'AbortError' ||
        error.name === 'CanceledError' ||
        error.code === 'ERR_CANCELED'
      ) {
        throw error; // Don't retry canceled requests
      }

      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay * (attempt + 1)));
    }
  }
};

// === DASHBOARD OVERVIEW ===

/**
 * Get admin dashboard overview with stats and recent movies
 */
export const getDashboardOverview = async (options = {}) => {
  const { signal } = options;
  return retryRequest(async () => {
    try {
      const response = await axiosInstance.get('/api/admin/movies/dashboard_overview/', {
        signal,
        timeout: 15000, // 15 second timeout
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error, 'fetch dashboard overview');
    }
  });
};

/**
 * Get production metrics for analytics
 */
export const getProductionMetrics = async (options = {}) => {
  const { signal } = options;
  return retryRequest(async () => {
    try {
      const response = await axiosInstance.get('/api/admin/movies/production_metrics/', {
        signal,
        timeout: 45000, // 45 second timeout for complex data
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error, 'fetch production metrics');
    }
  }, 1); // Only 1 retry for production metrics due to complexity
};

// === MOVIE ENRICHMENT SERVICES ===

/**
 * Enrich a specific movie with comprehensive data (async, poll for result)
 * @param {number} movieId - ID of the movie to enrich
 * @param {Object} options - Enrichment options
 * @param {boolean} options.forceRefresh - Force refresh existing data
 * @param {Array<string>} options.focusAreas - Specific areas to focus on ['basic', 'visual', 'metadata', 'ratings']
 * @param {string} options.enrichType - Type of enrichment ('comprehensive' or 'quality_based')
 */
export const enrichMovie = async (movieId, options = {}) => {
  try {
    await axiosInstance.post(`/api/admin/movies/${movieId}/enrich/`, {
      force_refresh: options.forceRefresh || false,
      focus_areas: options.focusAreas || null,
      enrich_type: options.enrichType || 'comprehensive',
    });
    // Poll enrichment-status endpoint until result is ready
    const pollStatus = async (retries = 60, interval = 2000) => {
      for (let i = 0; i < retries; i++) {
        const statusResp = await axiosInstance.get(
          `/api/admin/movies/${movieId}/enrichment-status/`
        );
        if (
          statusResp.data &&
          statusResp.data.enrichment_status &&
          statusResp.data.enrichment_status.quality_metrics
        ) {
          return statusResp.data;
        }
        await new Promise(res => setTimeout(res, interval));
      }
      throw new Error('Enrichment timed out');
    };
    return await pollStatus();
  } catch (error) {
    handleError(error, 'enrich movie');
  }
};

/**
 * Batch enrich multiple movies
 * @param {Array<number>} movieIds - Array of movie IDs to enrich
 * @param {Object} options - Enrichment options
 * @param {Array<string>} options.focusAreas - Specific areas to focus on
 * @param {number} options.maxConcurrent - Maximum concurrent processing
 */
export const batchEnrichMovies = async (movieIds, options = {}) => {
  try {
    const response = await axiosInstance.post('/api/admin/movies/batch-enrich/', {
      movie_ids: movieIds,
      focus_areas: options.focusAreas || null,
      max_concurrent: options.maxConcurrent || 5,
    });
    return response.data;
  } catch (error) {
    handleError(error, 'batch enrich movies');
  }
};

/**
 * Get enrichment status for a specific movie
 * @param {number} movieId - ID of the movie
 */
export const getMovieEnrichmentStatus = async movieId => {
  try {
    const response = await axiosInstance.get(`/api/admin/movies/${movieId}/enrichment-status/`);
    return response.data;
  } catch (error) {
    handleError(error, 'get movie enrichment status');
  }
};

/**
 * Enrich movies that have quality issues
 * @param {Object} options - Filtering and enrichment options
 * @param {number} options.qualityScoreMax - Maximum quality score to filter by
 * @param {boolean} options.hasQualityIssues - Filter for movies with quality issues
 * @param {number} options.limit - Maximum number of movies to process
 */
export const enrichMoviesWithQualityIssues = async (options = {}) => {
  try {
    const response = await axiosInstance.post('/api/admin/movies/enrich-quality-issues/', {
      quality_score_max: options.qualityScoreMax || 7.0,
      has_quality_issues: options.hasQualityIssues !== false,
      limit: options.limit || 50,
    });
    return response.data;
  } catch (error) {
    handleError(error, 'enrich movies with quality issues');
  }
};

/**
 * Get user interaction statistics for admin dashboard
 */
export const getUserInteractionStats = async (options = {}) => {
  const { signal } = options;
  return retryRequest(async () => {
    try {
      const response = await axiosInstance.get('/api/admin/movies/user_interaction_stats/', {
        signal,
        timeout: 30000, // 30 second timeout
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error, 'fetch user interaction stats');
    }
  });
};

/**
 * Get trending analytics for admin dashboard
 */
export const getTrendingAnalytics = async (options = {}) => {
  const { signal } = options;
  return retryRequest(async () => {
    try {
      const response = await axiosInstance.get('/api/admin/movies/trending_analytics/', {
        signal,
        timeout: 35000, // 35 second timeout
      });
      return handleResponse(response);
    } catch (error) {
      handleError(error, 'fetch trending analytics');
    }
  });
};

/**
 * Get real-time user interactions data for admin dashboard
 */
export const getRealTimeInteractions = async (options = {}) => {
  const { signal } = options;
  console.log('🔍 [getRealTimeInteractions] Starting API call...');
  return retryRequest(async () => {
    try {
      console.log(
        '🔍 [getRealTimeInteractions] Making request to /api/admin/movies/real_time_interactions/'
      );
      const response = await axiosInstance.get('/api/admin/movies/real_time_interactions/', {
        signal,
        timeout: 30000, // 30 second timeout
      });
      console.log('🔍 [getRealTimeInteractions] Response received:', response.data);
      return handleResponse(response);
    } catch (error) {
      console.error('🔍 [getRealTimeInteractions] Error:', error);
      handleError(error, 'fetch real-time interactions');
    }
  });
};

// === MOVIE MANAGEMENT ===

/**
 * Get movies list with keyset pagination, search, and filters
 */
export const getAdminMovies = async (params = {}) => {
  try {
    // Filter out empty string values from filters
    const cleanFilters = {};
    if (params.filters) {
      Object.entries(params.filters).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== '') {
          cleanFilters[key] = value;
        }
      });
    }

    console.log('Clean filters:', cleanFilters);

    const queryParams = new URLSearchParams({
      page_size: params.pageSize || 40,
      ...cleanFilters,
    });

    // Handle array values for after_created_at (Elasticsearch keyset pagination)
    if (cleanFilters.after_created_at && Array.isArray(cleanFilters.after_created_at)) {
      // Remove the array from queryParams and add each value separately
      queryParams.delete('after_created_at');
      cleanFilters.after_created_at.forEach(value => {
        queryParams.append('after_created_at', value.toString());
      });
      console.log('After handling array after_created_at:', queryParams.toString());
    }

    if (params.search?.trim()) {
      queryParams.append('search', params.search.trim());
    }

    const requestKey = `/api/admin/movies/?${queryParams}`;
    console.log('Request URL:', requestKey);

    // Check if there's already a pending request with the same parameters
    if (pendingRequests.has(requestKey)) {
      return await pendingRequests.get(requestKey);
    }

    // Create new request promise
    const requestPromise = (async () => {
      try {
        const response = await axiosInstance.get(requestKey);
        console.log('Raw response:', response.data);

        // Handle both paginated and non-paginated responses
        if (response.data.status === 'success') {
          return {
            results: response.data.data || response.data.results, // Support both formats
            count: response.data.count,
            next: response.data.next_after_created_at,
            previous: response.data.prev_after_created_at,
            totalPages: Math.ceil(response.data.count / (params.pageSize || 40)),
          };
        }

        throw new Error('Invalid response format');
      } finally {
        // Remove from pending requests after completion
        pendingRequests.delete(requestKey);
      }
    })();

    // Store the promise in pending requests
    pendingRequests.set(requestKey, requestPromise);

    return await requestPromise;
  } catch (error) {
    console.error('Error in getAdminMovies:', error);
    handleError(error, 'fetch admin movies');
  }
};

/**
 * Get single movie details for admin
 */
export const getAdminMovieDetails = async movieId => {
  try {
    const response = await axiosInstance.get(`/api/admin/movies/${movieId}/`);
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'fetch admin movie details');
  }
};

// === MOVIE ACTIONS ===

/**
 * Toggle featured status for a movie
 */
export const toggleMovieFeatured = async movieId => {
  try {
    const response = await axiosInstance.post(`/api/admin/movies/${movieId}/toggle_featured/`, {});
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'toggle movie featured status');
  }
};

/**
 * Approve a movie for production
 */
export const approveMovie = async movieId => {
  try {
    const response = await axiosInstance.post(`/api/admin/movies/${movieId}/approve_movie/`, {});
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'approve movie');
  }
};

/**
 * Reject a movie from production
 */
export const rejectMovie = async (movieId, reason = '') => {
  try {
    const response = await axiosInstance.post(`/api/admin/movies/${movieId}/reject_movie/`, {
      reason,
    });
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'reject movie');
  }
};

/**
 * Update movie priority
 */
export const updateMoviePriority = async (movieId, priority) => {
  try {
    const response = await axiosInstance.post(`/api/admin/movies/${movieId}/update_priority/`, {
      priority,
    });
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'update movie priority');
  }
};

/**
 * Update movie visibility settings
 */
export const updateMovieVisibility = async (movieId, visibilityData) => {
  try {
    const response = await axiosInstance.post(
      `/api/admin/movies/${movieId}/update_visibility/`,
      visibilityData
    );
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'update movie visibility');
  }
};

// === VISIBILITY CONTROLS ===

/**
 * Toggle popular status for a movie
 */
export const toggleMoviePopular = async movieId => {
  try {
    const response = await axiosInstance.post(`/api/admin/movies/${movieId}/toggle_popular/`, {});
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'toggle movie popular status');
  }
};

/**
 * Toggle top rated status for a movie
 */
export const toggleMovieTopRated = async movieId => {
  try {
    const response = await axiosInstance.post(`/api/admin/movies/${movieId}/toggle_top_rated/`, {});
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'toggle movie top rated status');
  }
};

/**
 * Toggle upcoming status for a movie
 */
export const toggleMovieUpcoming = async movieId => {
  try {
    const response = await axiosInstance.post(`/api/admin/movies/${movieId}/toggle_upcoming/`, {});
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'toggle movie upcoming status');
  }
};

/**
 * Schedule visibility changes for a movie
 */
export const scheduleMovieVisibility = async (movieId, scheduleData) => {
  try {
    const response = await axiosInstance.post(
      `/api/admin/movies/${movieId}/schedule_visibility/`,
      scheduleData
    );
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'schedule movie visibility');
  }
};

/**
 * Get all scheduled actions for movies
 */
export const getScheduledActions = async () => {
  try {
    const response = await axiosInstance.get('/api/admin/movies/scheduled_actions/');
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'fetch scheduled actions');
  }
};

/**
 * Cancel a scheduled action
 */
export const cancelScheduledAction = async actionId => {
  try {
    const response = await axiosInstance.delete(`/api/admin/movies/scheduled_actions/${actionId}/`);
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'cancel scheduled action');
  }
};

/**
 * Schedule a movie action (publish, unpublish, feature, etc.)
 */
export const scheduleMovieAction = async scheduleData => {
  try {
    const response = await axiosInstance.post('/api/admin/movies/schedule_action/', scheduleData);
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'schedule movie action');
  }
};

// === QUALITY MANAGEMENT ===

/**
 * Update movie quality assessment
 */
export const updateMovieQuality = async (movieId, qualityData) => {
  try {
    const response = await axiosInstance.put(`/api/admin/movies/${movieId}/quality/`, qualityData);
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'update movie quality');
  }
};

/**
 * Resolve a specific quality issue
 */
export const resolveMovieIssue = async (movieId, issueIndex) => {
  try {
    const response = await axiosInstance.post(`/api/admin/movies/${movieId}/resolve_issue/`, {
      issue_index: issueIndex,
    });
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'resolve movie issue');
  }
};

/**
 * Trigger quality recalculation for a movie
 */
export const recalculateMovieQuality = async movieId => {
  try {
    const response = await axiosInstance.post(`/api/admin/movies/${movieId}/recalculate_quality/`);
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'recalculate movie quality');
  }
};

/**
 * Get detailed quality metrics for a movie
 */
export const getMovieQualityDetails = async movieId => {
  try {
    const response = await axiosInstance.get(`/api/admin/movies/${movieId}/quality_details/`);
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'fetch movie quality details');
  }
};

// === BULK OPERATIONS ===

/**
 * Perform bulk action on multiple movies
 */
export const performBulkAction = async (action, movieIds, additionalData = {}) => {
  try {
    const response = await axiosInstance.post('/api/admin/movies/bulk_action/', {
      action,
      movie_ids: movieIds,
      ...additionalData,
    });
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'perform bulk action');
  }
};

// === CONVENIENCE FUNCTIONS ===

/**
 * Bulk approve movies
 */
export const bulkApproveMovies = async movieIds => {
  return performBulkAction('approve', movieIds);
};

/**
 * Bulk reject movies
 */
export const bulkRejectMovies = async (movieIds, reason = '') => {
  return performBulkAction('reject', movieIds, { reason });
};

/**
 * Bulk publish movies
 */
export const bulkPublishMovies = async movieIds => {
  return performBulkAction('publish', movieIds);
};

/**
 * Bulk unpublish movies
 */
export const bulkUnpublishMovies = async movieIds => {
  return performBulkAction('unpublish', movieIds);
};

/**
 * Bulk feature movies
 */
export const bulkFeatureMovies = async movieIds => {
  return performBulkAction('enable_featured', movieIds);
};

/**
 * Bulk unfeature movies
 */
export const bulkUnfeatureMovies = async movieIds => {
  return performBulkAction('disable_featured', movieIds);
};

/**
 * Bulk set movies as popular
 */
export const bulkSetPopularMovies = async movieIds => {
  return performBulkAction('enable_popular', movieIds);
};

/**
 * Bulk remove movies from popular
 */
export const bulkRemovePopularMovies = async movieIds => {
  return performBulkAction('disable_popular', movieIds);
};

/**
 * Bulk set movies as top rated
 */
export const bulkSetTopRatedMovies = async movieIds => {
  return performBulkAction('enable_top_rated', movieIds);
};

/**
 * Bulk remove movies from top rated
 */
export const bulkRemoveTopRatedMovies = async movieIds => {
  return performBulkAction('disable_top_rated', movieIds);
};

/**
 * Bulk set movies as upcoming
 */
export const bulkSetUpcomingMovies = async movieIds => {
  return performBulkAction('enable_upcoming', movieIds);
};

/**
 * Bulk remove movies from upcoming
 */
export const bulkRemoveUpcomingMovies = async movieIds => {
  return performBulkAction('disable_upcoming', movieIds);
};

// === CACHE MANAGEMENT ===

/**
 * Clear admin movie cache (if implemented)
 */

/**
 * 🔄 Get auto-processing status for admin dashboard
 */
export const getAutoProcessingStatus = async () => {
  try {
    const response = await axiosInstance.get('/api/admin/movies/auto_processing_status/');
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'fetch auto-processing status');
  }
};

/**
 * ⚡ Trigger manual processing (interactions, metrics, trending)
 */
export const triggerManualProcessing = async data => {
  try {
    const response = await axiosInstance.post('/api/admin/movies/trigger_manual_processing/', data);
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'trigger manual processing');
  }
};

export const clearAdminMovieCache = () => {
  // Future implementation for caching admin data
  console.log('Admin movie cache cleared');
};

/**
 * Clear pending requests cache
 */
export const clearPendingRequests = () => {
  pendingRequests.clear();
  console.log('Pending requests cache cleared');
};

/**
 * Tạo mới phim (Admin)
 */
export const createAdminMovie = async data => {
  try {
    const response = await axiosInstance.post('/api/admin/movies/', data);
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'tạo mới phim');
  }
};

/**
 * Cập nhật phim (Admin)
 */
export const updateAdminMovie = async (movieId, data) => {
  try {
    const response = await axiosInstance.put(`/api/admin/movies/${movieId}/`, data);
    return handleResponse(response);
  } catch (error) {
    console.error('Error in updateAdminMovie:', error);
    handleError(error, 'cập nhật phim');
  }
};

/**
 * Xóa phim (Admin)
 */
export const deleteAdminMovie = async movieId => {
  try {
    const response = await axiosInstance.delete(`/api/admin/movies/${movieId}/`);
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'xóa phim');
  }
};

// Export all functions as default object for easier importing
export default {
  // Dashboard
  getDashboardOverview,
  getProductionMetrics,
  getUserInteractionStats,
  getTrendingAnalytics,

  // Movie Management
  getAdminMovies,
  getAdminMovieDetails,
  createAdminMovie,
  updateAdminMovie,
  deleteAdminMovie,

  // Movie Actions
  toggleMovieFeatured,
  approveMovie,
  rejectMovie,
  updateMoviePriority,
  updateMovieVisibility,

  // Visibility Controls
  toggleMoviePopular,
  toggleMovieTopRated,
  toggleMovieUpcoming,
  scheduleMovieVisibility,

  // Bulk Operations
  performBulkAction,
  bulkApproveMovies,
  bulkRejectMovies,
  bulkPublishMovies,
  bulkUnpublishMovies,
  bulkFeatureMovies,
  bulkUnfeatureMovies,
  bulkSetPopularMovies,
  bulkRemovePopularMovies,
  bulkSetTopRatedMovies,
  bulkRemoveTopRatedMovies,
  bulkSetUpcomingMovies,
  bulkRemoveUpcomingMovies,

  // Auto-Processing
  getAutoProcessingStatus,
  triggerManualProcessing,

  // Cache
  clearAdminMovieCache,
};

// Fetch genres for admin movie form - lấy tất cả ngôn ngữ
export const getGenresForAdmin = async () => {
  try {
    // Lấy tất cả genres cho admin (không filter theo language)
    const response = await axiosInstance.get('/api/metadata/categories/?language=all');
    if (response.data.status !== 'success') {
      throw new Error(response.data.message || 'Failed to fetch genres');
    }
    return response.data.data;
  } catch (error) {
    console.error('Error fetching genres for admin:', error);
    throw error;
  }
};

// Fetch movie status options
export const getMovieStatusOptions = async () => {
  // Since status options are static, we can return them directly
  // But in the future, this could be fetched from an API endpoint
  return [
    { value: '', label: 'Chọn trạng thái' },
    { value: 'RUMORED', label: 'Đồn đoán' },
    { value: 'PLANNED', label: 'Đã lên kế hoạch' },
    { value: 'IN_PRODUCTION', label: 'Đang sản xuất' },
    { value: 'POST_PRODUCTION', label: 'Hậu kỳ' },
    { value: 'RELEASED', label: 'Đã phát hành' },
    { value: 'UPCOMING', label: 'Sắp ra mắt' },
  ];
};

// Fetch approval status options
export const getApprovalStatusOptions = async () => {
  return [
    { value: '', label: 'Chọn trạng thái duyệt' },
    { value: 'PENDING', label: 'Chờ duyệt' },
    { value: 'APPROVED', label: 'Đã duyệt' },
    { value: 'REJECTED', label: 'Từ chối' },
    { value: 'NEEDS_REVIEW', label: 'Cần xem xét' },
  ];
};

// Fetch visibility status options
export const getVisibilityStatusOptions = async () => {
  return [
    { value: '', label: 'Chọn trạng thái hiển thị' },
    { value: 'PUBLISHED', label: 'Công khai' },
    { value: 'DRAFT', label: 'Bản nháp' },
    { value: 'SCHEDULED', label: 'Đã lên lịch' },
    { value: 'ARCHIVED', label: 'Lưu trữ' },
    { value: 'RESTRICTED', label: 'Hạn chế' },
    { value: 'HIDDEN', label: 'Ẩn' },
  ];
};
