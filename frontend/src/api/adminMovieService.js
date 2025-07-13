import axiosInstance from './axios';

// Request deduplication cache
const pendingRequests = new Map();

// Helper function to handle API responses
const handleResponse = response => {
  if (response.data.status === 'success') {
    return response.data.data;
  }
  throw new Error(response.data.message || 'API request failed');
};

// Helper function to handle API errors
const handleError = (error, operation) => {
  console.error(`Error ${operation}:`, error);
  throw {
    error: error.response?.data?.message || `Failed to ${operation}`,
    details: error.response?.data,
  };
};

// === DASHBOARD OVERVIEW ===

/**
 * Get admin dashboard overview with stats and recent movies
 */
export const getDashboardOverview = async () => {
  try {
    const response = await axiosInstance.get('/api/admin/movies/dashboard_overview/');
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'fetch dashboard overview');
  }
};

/**
 * Get production metrics for analytics
 */
export const getProductionMetrics = async () => {
  try {
    const response = await axiosInstance.get('/api/admin/movies/production_metrics/');
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'fetch production metrics');
  }
};

/**
 * Get user interaction statistics for admin dashboard
 */
export const getUserInteractionStats = async () => {
  try {
    const response = await axiosInstance.get('/api/admin/movies/user_interaction_stats/');
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'fetch user interaction stats');
  }
};

/**
 * Get trending analytics for admin dashboard
 */
export const getTrendingAnalytics = async () => {
  try {
    const response = await axiosInstance.get('/api/admin/movies/trending_analytics/');
    return handleResponse(response);
  } catch (error) {
    handleError(error, 'fetch trending analytics');
  }
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

    const queryParams = new URLSearchParams({
      page_size: params.pageSize || 30,
      ...cleanFilters,
    });

    if (params.search?.trim()) {
      queryParams.append('search', params.search.trim());
    }

    const requestKey = `/api/admin/movies/?${queryParams}`;

    // Check if there's already a pending request with the same parameters
    if (pendingRequests.has(requestKey)) {
      return await pendingRequests.get(requestKey);
    }

    // Create new request promise
    const requestPromise = (async () => {
      try {
        const response = await axiosInstance.get(requestKey);

        // Handle both paginated and non-paginated responses
        if (response.data.status === 'success') {
          return {
            results: response.data.data || response.data.results, // Support both formats
            count: response.data.count,
            next: response.data.next_after_created_at,
            previous: response.data.prev_after_created_at,
            totalPages: Math.ceil(response.data.count / (params.pageSize || 30)),
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
