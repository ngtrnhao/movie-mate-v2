import axiosInstance from './axios';

// Enhanced cache object to store API responses
const cache = {
  trending: null,
  topRated: null,
  upcoming: null,
  featured: null,
  search: new Map(), // Use Map for search results caching
  suggestions: new Map(), // Use Map for suggestions caching
  lastFetch: {},
};

// Cache duration in milliseconds
const CACHE_DURATION = 10 * 60 * 1000; // 10 minutes
const SEARCH_CACHE_DURATION = 5 * 60 * 1000; // 5 minutes for search results

// Helper function to check if cache is valid
const isCacheValid = (key, duration = CACHE_DURATION) => {
  const lastFetch = cache.lastFetch[key];
  if (!lastFetch) return false;
  return Date.now() - lastFetch < duration;
};

// Helper function to handle API responses
const handleResponse = response => {
  if (response.status === 'success') {
    return response.data; // Return the full response object, not just response.data
  }
  throw new Error(response.message || 'API request failed');
};

// Helper function to make API call with caching
const makeApiCall = async (endpoint, cacheKey) => {
  try {
    // Check cache first
    if (isCacheValid(cacheKey)) {
      return cache[cacheKey];
    }

    const response = await axiosInstance.get(endpoint);
    const data = handleResponse(response.data);

    // Update cache
    cache[cacheKey] = data;
    cache.lastFetch[cacheKey] = Date.now();

    return data;
  } catch (error) {
    console.error(`Error fetching ${cacheKey} movies:`, error);
    throw {
      error: error.response?.data?.message || `Failed to fetch ${cacheKey} movies`,
      details: error.response?.data,
    };
  }
};

// Get featured movies
export const getFeaturedMovies = async () => {
  return makeApiCall('/api/movies/featured/', 'featured');
};

// Get trending movies
export const getTrendingMovies = async () => {
  return makeApiCall('/api/movies/trending/', 'trending');
};

// Get top rated movies
export const getTopRatedMovies = async () => {
  return makeApiCall('/api/movies/top_rated/', 'topRated');
};

// Get upcoming movies
export const getUpcomingMovies = async () => {
  return makeApiCall('/api/movies/upcoming/', 'upcoming');
};

// Get movie details
export const getMovieDetails = async movieId => {
  try {
    const response = await axiosInstance.get(`/api/movies/${movieId}/`);
    return handleResponse(response.data);
  } catch (error) {
    console.error('Error fetching movie details:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch movie details',
      details: error.response?.data,
    };
  }
};

// Get complete movie details (optimized single API call)
export const getMovieDetailsComplete = async movieId => {
  try {
    const response = await axiosInstance.get(`/api/movies/${movieId}/details_complete/`);
    const data = handleResponse(response.data);

    return {
      movie: data.movie,
      cast: data.movie.cast || [],
      similarMovies: data.similar_movies || [],
      stats: data.stats || {},
    };
  } catch (error) {
    console.error('Error fetching complete movie details:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch complete movie details',
      details: error.response?.data,
    };
  }
};

// Get movie cast
export const getMovieCast = async movieId => {
  try {
    const response = await axiosInstance.get(`/api/movies/${movieId}/cast/`);
    return handleResponse(response.data);
  } catch (error) {
    console.error('Error fetching movie cast:', error);
    // Return empty array if cast endpoint fails
    return { data: [] };
  }
};

// Parallel loading of movie data (fallback for current implementation)
export const getMovieDetailsParallel = async movieId => {
  try {
    // Load all data in parallel for better performance
    const [movieResponse, castResponse] = await Promise.allSettled([
      axiosInstance.get(`/api/movies/${movieId}/`),
      axiosInstance.get(`/api/movies/${movieId}/cast/`),
    ]);

    // Handle movie response
    const movie =
      movieResponse.status === 'fulfilled' ? handleResponse(movieResponse.value.data) : null;

    // Handle cast response
    const cast = castResponse.status === 'fulfilled' ? handleResponse(castResponse.value.data) : [];

    // Get similar movies based on movie genres
    let similarMovies = [];
    if (movie?.genres?.length) {
      try {
        const genreIds = movie.genres.slice(0, 3).map(g => g.id || g);
        const params = new URLSearchParams();
        genreIds.forEach(id => params.append('genres', id));
        params.append('page_size', '6');
        params.append('sort_by', 'rating');

        const similarResponse = await axiosInstance.get(`/api/movies/search/?${params}`);
        const similarData = handleResponse(similarResponse.data);

        // Filter out current movie
        similarMovies = (similarData.results || [])
          .filter(m => m.id !== parseInt(movieId))
          .slice(0, 6);
      } catch (error) {
        console.error('Error fetching similar movies:', error);
      }
    }

    return {
      movie,
      cast: cast.data || cast || [],
      similarMovies,
      error: movieResponse.status === 'rejected' ? movieResponse.reason : null,
    };
  } catch (error) {
    console.error('Error in parallel movie details fetch:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch movie details',
      details: error.response?.data,
    };
  }
};

// Get similar movies (using search with same genres)
export const getSimilarMovies = async (movieId, genres = [], limit = 6) => {
  try {
    const params = new URLSearchParams();

    // Add genres for similarity
    if (genres?.length) {
      genres.forEach(genre => params.append('genres', genre.id || genre));
    }

    params.append('page_size', limit + 2); // Get a few extra to filter out current movie
    params.append('sort_by', 'rating');
    params.append('order', 'desc');

    const response = await axiosInstance.get(`/api/movies/search/?${params}`);
    const data = handleResponse(response.data);

    // Handle both response formats
    let results = data.results || data.data || data || [];

    // Filter out the current movie from results
    if (results.length > 0) {
      results = results.filter(movie => movie.id !== parseInt(movieId));
      results = results.slice(0, limit);
    }

    return {
      results,
      count: data.count || results.length,
      search_engine: data.search_engine || 'unknown',
    };
  } catch (error) {
    console.error('Error fetching similar movies:', error);
    return { results: [], count: 0 };
  }
};

// Get movie reviews (updated for unified review system)
export const getMovieReviews = async (
  movieId,
  page = 1,
  limit = 20,
  sortBy = 'recent',
  showSpoilers = false
) => {
  try {
    const response = await axiosInstance.get(`/api/movies/${movieId}/reviews/`, {
      params: { page, page_size: limit, sort_by: sortBy, show_spoilers: showSpoilers },
    });

    // Standardize response format
    const responseData = response.data;
    return {
      data: responseData.data || [],
      total_pages: responseData.total_pages || 1,
      current_page: responseData.current_page || page,
      count: responseData.count || 0,
      // Add rating distribution if available
      rating_distribution: responseData.rating_distribution || {},
      average_rating: responseData.average_rating || 0,
      total_ratings: responseData.total_ratings || 0,
    };
  } catch (error) {
    console.error('Error fetching movie reviews:', error);
    throw error;
  }
};

// Submit movie review with rating (updated for unified review system)
export const submitMovieReview = async (movieId, reviewData) => {
  try {
    const response = await axiosInstance.post(`/api/movies/${movieId}/reviews/`, {
      movie: movieId,
      ...reviewData,
    });
    return response.data;
  } catch (error) {
    console.error('Error submitting movie review:', error);
    throw error;
  }
};

// Vote on a review (helpful/not helpful)
export const voteOnReview = async (reviewId, voteType) => {
  try {
    const response = await axiosInstance.post(`/api/reviews/${reviewId}/vote/`, {
      vote: voteType, // 'helpful' or 'not_helpful'
    });
    return response.data;
  } catch (error) {
    console.error('Error voting on review:', error);
    throw error;
  }
};

// Update a review
export const updateReview = async (reviewId, reviewData) => {
  try {
    const response = await axiosInstance.patch(`/api/reviews/${reviewId}/`, reviewData);
    return response.data;
  } catch (error) {
    console.error('Error updating review:', error);
    throw error;
  }
};

// Delete a review
export const deleteReview = async reviewId => {
  try {
    const response = await axiosInstance.delete(`/api/reviews/${reviewId}/`);
    return response.data;
  } catch (error) {
    console.error('Error deleting review:', error);
    throw error;
  }
};

// Get user's own review for a movie
export const getUserReview = async movieId => {
  try {
    const response = await axiosInstance.get(`/api/reviews/my_reviews/`, {
      params: { movie_id: movieId },
    });

    // Standardize response format
    const responseData = response.data;
    return {
      data: responseData.data || [],
      results: responseData.data || [], // Keep backward compatibility
      count: responseData.count || 0,
      status: responseData.status || 'success',
    };
  } catch (error) {
    console.error('Error fetching user review:', error);
    throw error;
  }
};

// Legacy support for rating submission (maps to review submission)
export const submitMovieRating = async (movieId, rating, review = '') => {
  return submitMovieReview(movieId, {
    content: review || `Rated ${rating} stars`,
    rating,
    isPublic: true,
    isSpoiler: false,
  });
};

// Watchlist functionality has been moved to profileService.js

// Enhanced search movies with caching and request cancellation
let searchController = null; // Store AbortController for request cancellation

// Search movies with enhanced caching and fallback
export const searchMovies = async (filters = {}, pageOrSearchAfter = 1, pageSize = 50) => {
  try {
    // Build query parameters
    const params = new URLSearchParams();

    // Add search query
    if (filters.query) {
      params.append('q', filters.query.trim());
    }

    // Add genre filters
    if (filters.genres && filters.genres.length > 0) {
      filters.genres.forEach(genre => {
        // Send genre name instead of ID to match Elasticsearch mapping
        params.append('genres', genre.name || genre);
      });
    }

    // Add country filter
    if (filters.country) {
      params.append('countries', filters.country);
    }

    // Add status filter
    if (filters.status) {
      params.append('status', filters.status);
    }

    // Add adult filter
    if (filters.adult !== undefined) {
      params.append('adult', filters.adult.toString());
    }

    // Add year filters
    if (filters.yearFrom) {
      params.append('year_from', filters.yearFrom);
    }
    if (filters.yearTo) {
      params.append('year_to', filters.yearTo);
    }

    // Add sorting
    if (filters.sortBy) {
      params.append('sort_by', filters.sortBy);
    }
    if (filters.order) {
      params.append('order', filters.order);
    }

    // Add poster filter
    if (filters.hasPoster !== undefined) {
      params.append('has_poster', filters.hasPoster.toString());
    }

    // Add pagination
    if (typeof pageOrSearchAfter === 'number') {
      params.append('page', pageOrSearchAfter.toString());
    } else if (pageOrSearchAfter && typeof pageOrSearchAfter === 'string') {
      // Handle search_after pagination
      params.append('search_after', pageOrSearchAfter);
    } else if (Array.isArray(pageOrSearchAfter)) {
      // Handle search_after array from Elasticsearch
      pageOrSearchAfter.forEach(value => {
        params.append('search_after', value.toString());
      });
    }

    params.append('page_size', pageSize.toString());

    // Create cache key
    const cacheKey = `search_${params.toString()}`;

    // Check cache first
    if (cache.search.has(cacheKey)) {
      const cached = cache.search.get(cacheKey);
      if (Date.now() - cached.timestamp < SEARCH_CACHE_DURATION) {
        // Return the full cached object except timestamp
        const { timestamp, ...rest } = cached;
        return rest;
      }
      cache.search.delete(cacheKey);
    }

    // Make API call
    const response = await axiosInstance.get(`/api/movies/search/?${params}`);
    const responseData = response.data; // Lấy response.data trực tiếp

    // Standardize response format for frontend compatibility
    const standardizedData = {
      data: responseData.data || responseData.results || [], // Always prioritize 'data' over 'results'
      count: responseData.count || 0,
      next: responseData.next, // Keep original next for ORM
      next_search_after: responseData.next_search_after, // Keep original next_search_after for Elasticsearch
      previous: responseData.previous,
      search_engine: responseData.search_engine || 'unknown',
      total_pages: responseData.total_pages || Math.ceil((responseData.count || 0) / pageSize),
    };

    // Cache the result (spread standardizedData, not as nested 'data')
    cache.search.set(cacheKey, {
      ...standardizedData,
      timestamp: Date.now(),
    });

    return standardizedData;
  } catch (error) {
    console.error('Error searching movies:', error);
    throw {
      error: error.response?.data?.message || 'Failed to search movies',
      details: error.response?.data,
    };
  }
};
//Get search suggestions for autocomplete
export const getSearchSuggestions = async (query, language = 'en', limit = 5) => {
  try {
    if (!query || query.length < 2) {
      return { data: [] };
    }

    //create cache key for suggestions
    const cacheKey = `suggestions_${language}_${btoa(query)
      .replace(/[^a-zA-Z0-9]/g, '')
      .slice(0, 20)}_${limit}`;

    //check cache first
    if (cache.suggestions.has(cacheKey) && isCacheValid(`suggestions_${cacheKey}`, 300000)) {
      //5 minutes cache for suggestions
      return cache.suggestions.get(cacheKey);
    }
    const params = new URLSearchParams();
    params.append('q', query);
    params.append('language', language);
    params.append('limit', limit);
    const response = await axiosInstance.get(`/api/movies/search_suggestions/?${params}`);

    if (response.data.status === 'success') {
      const result = {
        data: response.data.data || [],
      };

      //Cache suggetions
      cache.suggestions.set(cacheKey, result);
      cache.lastFetch[`suggestions_${cacheKey}`] = Date.now();

      // Limit cache size
      if (cache.suggestions.size > 50) {
        const firstKey = cache.suggestions.keys().next().value;
        cache.suggestions.delete(firstKey);
        delete cache.lastFetch[`suggestions_${firstKey}`];
      }

      return result;
    } else {
      throw new Error(response.data.message || 'Failed to get suggestions');
    }
  } catch (error) {
    console.error('Error getting search suggestions:', error);
    //Return empty array on error to prevent UI breaking
    return { data: [] };
  }
};
// Clear search cache - useful when filters change significantly
export const clearSearchCache = () => {
  cache.search.clear();
  // Clear search-related lastFetch entries
  Object.keys(cache.lastFetch).forEach(key => {
    if (key.startsWith('search_')) {
      delete cache.lastFetch[key];
    }
  });
};

// Clear all cache
export const clearAllCache = () => {
  cache.trending = null;
  cache.topRated = null;
  cache.upcoming = null;
  cache.featured = null;
  cache.search.clear();
  cache.lastFetch = {};
};

// Get cache stats - useful for debugging
export const getCacheStats = () => {
  return {
    searchCacheSize: cache.search.size,
    cachedEndpoints: Object.keys(cache.lastFetch).filter(key => !key.startsWith('search_')),
    totalCacheEntries: Object.keys(cache.lastFetch).length,
  };
};

// ==================== MOVIE BUZZ SECTION APIs ====================

// Get comprehensive Movie Buzz data
export const getMovieBuzzData = async () => {
  try {
    const response = await axiosInstance.get('/api/movies/movie_buzz_data/');
    return handleResponse(response.data);
  } catch (error) {
    console.error('Error fetching movie buzz data:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch movie buzz data',
      details: error.response?.data,
    };
  }
};

// Get hot movies based on recent activity
export const getHotMovies = async (limit = 10, days = 7) => {
  try {
    const params = new URLSearchParams();
    params.append('limit', limit);
    params.append('days', days);

    const response = await axiosInstance.get(`/api/movies/hot_movies/?${params}`);
    return handleResponse(response.data);
  } catch (error) {
    console.error('Error fetching hot movies:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch hot movies',
      details: error.response?.data,
    };
  }
};

// Get trending genres
export const getTrendingGenres = async (language = 'vi', days = 7, limit = 9) => {
  try {
    const params = new URLSearchParams();
    params.append('language', language);
    params.append('days', days);
    params.append('limit', limit);

    const response = await axiosInstance.get(`/api/genres/trending/?${params}`);
    return handleResponse(response.data);
  } catch (error) {
    console.error('Error fetching trending genres:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch trending genres',
      details: error.response?.data,
    };
  }
};

// Get featured reviews (most helpful)
export const getFeaturedReviews = async (limit = 5) => {
  try {
    const params = new URLSearchParams();
    params.append('featured', 'true');
    params.append('limit', limit);

    const response = await axiosInstance.get(`/api/movies/reviews/?${params}`);
    return handleResponse(response.data);
  } catch (error) {
    console.error('Error fetching featured reviews:', error);
    return { data: [] };
  }
};

// Get live comments (recent user activity)
export const getLiveComments = async (hours = 24, limit = 20) => {
  try {
    const params = new URLSearchParams();
    params.append('hours', hours);
    params.append('limit', limit);
    params.append('type', 'USER');

    const response = await axiosInstance.get(`/api/movies/reviews/?${params}`);
    return handleResponse(response.data);
  } catch (error) {
    console.error('Error fetching live comments:', error);
    return { data: [] };
  }
};

// Get community stats
export const getCommunityStats = async () => {
  try {
    const response = await axiosInstance.get('/api/users/community_stats/');
    return handleResponse(response.data);
  } catch (error) {
    console.error('Error fetching community stats:', error);
    return {
      total_comments: 0,
      active_users: 0,
      new_reviews: 0,
      top_contributors: [],
    };
  }
};

// Get my reviews for a movie (with auth check)
export const getMyReviews = async movieId => {
  try {
    // Check if user is authenticated by checking token in localStorage
    const token = localStorage.getItem('token');
    if (!token) {
      return { data: [] }; // Return empty list if not authenticated
    }

    const response = await axiosInstance.get('/api/reviews/my_reviews/', {
      params: { movie_id: movieId },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching my reviews:', error);
    return { data: [] }; // Return empty list on error
  }
};

// Reply to review
export const replyToReview = async (reviewId, replyData) => {
  try {
    const response = await axiosInstance.post(`/api/reviews/${reviewId}/reply/`, replyData);
    return response.data;
  } catch (error) {
    console.error('Error replying to review:', error);
    throw error;
  }
};

// Get replies for a review
export const getReviewReplies = async (reviewId, page = 1, pageSize = 10) => {
  try {
    const response = await axiosInstance.get(`/api/reviews/${reviewId}/replies/`, {
      params: { page, page_size: pageSize },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching review replies:', error);
    throw error;
  }
};

// Spoiler Detection API
export const detectSpoilers = async (content, language = 'en', movieTitle = '') => {
  try {
    const response = await axiosInstance.post('/api/reviews/detect_spoilers/', {
      content,
      language,
      movie_title: movieTitle,
    });
    return response.data;
  } catch (error) {
    console.error('Error detecting spoilers:', error);
    throw error;
  }
};

// Analyze spoiler for a specific review (updated endpoint)
export const analyzeReviewSpoiler = async reviewId => {
  try {
    const response = await axiosInstance.post(`/api/reviews/${reviewId}/analyze_spoiler/`);
    return response.data;
  } catch (error) {
    console.error('Error analyzing review spoiler:', error);
    throw error;
  }
};

// Get spoiler statistics (updated endpoint)
export const getSpoilerStatistics = async () => {
  try {
    const response = await axiosInstance.get('/api/reviews/spoiler_statistics/');
    return response.data;
  } catch (error) {
    console.error('Error getting spoiler statistics:', error);
    throw error;
  }
};

// Enhanced review submission with spoiler detection
export const submitMovieReviewWithSpoilerDetection = async (movieId, reviewData) => {
  try {
    // First, detect spoilers
    const spoilerDetection = await detectSpoilers(
      reviewData.content,
      reviewData.language || 'en',
      reviewData.movieTitle || ''
    );

    // Prepare review data with spoiler detection result
    const enhancedReviewData = {
      ...reviewData,
      is_spoiler: spoilerDetection.is_spoiler || reviewData.is_spoiler || false,
    };

    // Submit the review
    const response = await submitMovieReview(movieId, enhancedReviewData);

    // Add spoiler detection info to response
    return {
      ...response,
      spoiler_detection: spoilerDetection,
    };
  } catch (error) {
    console.error('Error submitting review with spoiler detection:', error);
    throw error;
  }
};

// ====== OPTIMIZED MODERATION API CALLS ======

// Optimized moderation queue API (replaces getModerationQueue for better performance)
export const getModerationQueueOptimized = async (page = 1, pageSize = 20, filters = {}) => {
  try {
    const params = new URLSearchParams();
    params.append('page', page);
    params.append('page_size', pageSize);

    // Add filters
    if (filters.status) params.append('status', filters.status);
    if (filters.language) params.append('language', filters.language);
    if (filters.priority) params.append('priority', filters.priority);
    if (filters.has_spoiler !== undefined) params.append('has_spoiler', filters.has_spoiler);
    if (filters.date_from) params.append('date_from', filters.date_from);
    if (filters.date_to) params.append('date_to', filters.date_to);

    const response = await axiosInstance.get(`/api/reviews/moderation_queue_optimized/?${params}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching optimized moderation queue:', error);
    throw error;
  }
};

// Optimized spoiler statistics API (replaces getSpoilerStatistics for better performance)
export const getSpoilerStatisticsOptimized = async (days = 30) => {
  try {
    const params = new URLSearchParams();
    params.append('days', days);

    const response = await axiosInstance.get(
      `/api/reviews/spoiler_statistics_optimized/?${params}`
    );
    return response.data;
  } catch (error) {
    console.error('Error getting optimized spoiler statistics:', error);
    throw error;
  }
};

// ====== ORIGINAL MODERATION API CALLS (keeping for backward compatibility) ======

// Moderation Queue API
export const getModerationQueue = async (page = 1, pageSize = 20, filters = {}) => {
  try {
    const params = new URLSearchParams();
    params.append('page', page);
    params.append('page_size', pageSize);

    // Add filters
    if (filters.status) params.append('status', filters.status);
    if (filters.language) params.append('language', filters.language);
    if (filters.has_spoiler !== undefined) params.append('has_spoiler', filters.has_spoiler);
    if (filters.date_from) params.append('date_from', filters.date_from);
    if (filters.date_to) params.append('date_to', filters.date_to);

    const response = await axiosInstance.get(`/api/reviews/moderation_queue/?${params}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching moderation queue:', error);
    throw error;
  }
};

// Moderate a review
export const moderateReview = async (reviewId, action, reason = '') => {
  try {
    const response = await axiosInstance.post(`/api/reviews/${reviewId}/moderate/`, {
      action,
      reason,
    });
    return response.data;
  } catch (error) {
    console.error('Error moderating review:', error);
    throw error;
  }
};

// Bulk moderate reviews
export const bulkModerateReviews = async (reviewIds, action, reason = '') => {
  try {
    const response = await axiosInstance.post('/api/reviews/bulk_moderate/', {
      review_ids: reviewIds,
      action,
      reason,
    });
    return response.data;
  } catch (error) {
    console.error('Error bulk moderating reviews:', error);
    throw error;
  }
};

// Get reviews pending spoiler detection
export const getReviewsPendingSpoilerDetection = async (page = 1, pageSize = 20) => {
  try {
    const params = new URLSearchParams();
    params.append('page', page);
    params.append('page_size', pageSize);
    params.append('pending_spoiler_detection', 'true');

    const response = await axiosInstance.get(`/api/reviews/?${params}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching reviews pending spoiler detection:', error);
    throw error;
  }
};

// Report a review
export const reportReview = async (reviewId, reason, description = '') => {
  try {
    const response = await axiosInstance.post('/api/review-reports/', {
      review: reviewId,
      reason,
      description,
    });
    return response.data;
  } catch (error) {
    console.error('Error reporting review:', error);
    throw {
      error: error.response?.data?.message || 'Failed to report review',
      details: error.response?.data,
    };
  }
};

// Get review reports (admin/moderator only)
export const getReviewReports = async (page = 1, pageSize = 20) => {
  try {
    const response = await axiosInstance.get(
      `/api/review-reports/reports_for_moderation/?page=${page}&page_size=${pageSize}`
    );
    return response.data;
  } catch (error) {
    console.error('Error fetching review reports:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch review reports',
      details: error.response?.data,
    };
  }
};

// Get unified moderation queue (spoiler detection + reports)
export const getUnifiedModerationQueue = async (page = 1, pageSize = 50, filters = {}) => {
  try {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      ...filters,
    });

    const response = await axiosInstance.get(`/api/reviews/unified_moderation_queue/?${params}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching unified moderation queue:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch moderation queue',
      details: error.response?.data,
    };
  }
};

// Update task status for kanban board
export const updateTaskStatus = async (taskId, status) => {
  try {
    const response = await axiosInstance.post('/api/reviews/update_task_status/', {
      task_id: taskId,
      status: status,
    });
    return response.data;
  } catch (error) {
    console.error('Error updating task status:', error);
    throw error;
  }
};

// ====== ENHANCED MODERATION API CALLS ======

// Get auto-marked reviews for moderator review
export const getAutoMarkedReviews = async (page = 1, pageSize = 20, filters = {}) => {
  try {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      confidence_min: filters.confidenceMin || '0.8',
      confidence_max: filters.confidenceMax || '1.0',
      reviewed_status: filters.reviewedStatus || 'pending',
    });

    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);

    const response = await axiosInstance.get(`/api/reviews/auto_marked_reviews/?${params}`);
    return handleResponse(response.data);
  } catch (error) {
    console.error('Error fetching auto-marked reviews:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch auto-marked reviews',
      details: error.response?.data,
    };
  }
};

// Submit moderator feedback for learning system
export const submitModerationFeedback = async (reviewId, feedbackData) => {
  try {
    const response = await axiosInstance.post(`/api/reviews/${reviewId}/submit_feedback/`, {
      feedback_type: feedbackData.feedbackType,
      moderator_decision: feedbackData.moderatorDecision,
      is_spoiler_correct: feedbackData.isSpoilerCorrect,
      difficulty_level: feedbackData.difficultyLevel || 'medium',
      notes: feedbackData.notes || '',
      time_spent_seconds: feedbackData.timeSpentSeconds || 0,
    });
    return handleResponse(response.data);
  } catch (error) {
    console.error('Error submitting moderation feedback:', error);
    throw {
      error: error.response?.data?.message || 'Failed to submit feedback',
      details: error.response?.data,
    };
  }
};

// Get moderation analytics and performance metrics
export const getModerationAnalytics = async (days = 30) => {
  try {
    const response = await axiosInstance.get(`/api/reviews/moderation_analytics/?days=${days}`);
    return handleResponse(response.data);
  } catch (error) {
    console.error('Error fetching moderation analytics:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch moderation analytics',
      details: error.response?.data,
    };
  }
};

// Get active moderation configuration
export const getModerationConfig = async () => {
  try {
    const response = await axiosInstance.get('/api/moderation-config/active_config/');
    return handleResponse(response.data);
  } catch (error) {
    console.error('Error fetching moderation config:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch moderation config',
      details: error.response?.data,
    };
  }
};

// Update moderation thresholds
export const updateModerationThresholds = async thresholds => {
  try {
    const response = await axiosInstance.post('/api/moderation-config/update_thresholds/', {
      auto_mark_threshold: thresholds.autoMarkThreshold,
      flag_for_review_threshold: thresholds.flagForReviewThreshold,
      suggest_warning_threshold: thresholds.suggestWarningThreshold,
    });
    return handleResponse(response.data);
  } catch (error) {
    console.error('Error updating moderation thresholds:', error);
    throw {
      error: error.response?.data?.message || 'Failed to update thresholds',
      details: error.response?.data,
    };
  }
};

// Toggle learning system
export const toggleLearningSystem = async enabled => {
  try {
    const response = await axiosInstance.post('/api/moderation-config/toggle_learning/', {
      enabled: enabled,
    });
    return handleResponse(response.data);
  } catch (error) {
    console.error('Error toggling learning system:', error);
    throw {
      error: error.response?.data?.message || 'Failed to toggle learning system',
      details: error.response?.data,
    };
  }
};

// Get moderation feedback data
export const getModerationFeedback = async (page = 1, pageSize = 20, filters = {}) => {
  try {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });

    if (filters.feedbackType) params.append('feedback_type', filters.feedbackType);

    const response = await axiosInstance.get(`/api/moderation-feedback/?${params}`);
    return handleResponse(response.data);
  } catch (error) {
    console.error('Error fetching moderation feedback:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch moderation feedback',
      details: error.response?.data,
    };
  }
};

// Get accuracy summary for different time periods
export const getAccuracySummary = async () => {
  try {
    const response = await axiosInstance.get('/api/moderation-feedback/accuracy_summary/');
    return handleResponse(response.data);
  } catch (error) {
    console.error('Error fetching accuracy summary:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch accuracy summary',
      details: error.response?.data,
    };
  }
};

// Update API endpoints to use new structure
export const testCalculationMetrics = async () => {
  try {
    const response = await axiosInstance.get('/test/calculation-metrics/');
    return response.data;
  } catch (error) {
    console.error('Error testing calculation metrics:', error);
    throw error;
  }
};

export const calculateSampleMetrics = async (sampleSize = 5) => {
  try {
    const response = await axiosInstance.post('/test/calculate-sample/', {
      sample_size: sampleSize,
    });
    return response.data;
  } catch (error) {
    console.error('Error calculating sample metrics:', error);
    throw error;
  }
};
