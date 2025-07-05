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
    return response.data;
  }
  throw new Error(response.message || 'API request failed');
};

// Helper function to make API call with caching
const makeApiCall = async (endpoint, cacheKey) => {
  try {
    // Check cache first
    if (isCacheValid(cacheKey)) {
      console.log(`Returning cached ${cacheKey} movies`);
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

    // Filter out the current movie from results
    let results = response.data?.results || [];
    if (results.length > 0) {
      results = results.filter(movie => movie.id !== parseInt(movieId));
      results = results.slice(0, limit);
    }

    return { results };
  } catch (error) {
    console.error('Error fetching similar movies:', error);
    return { results: [] };
  }
};

// Get movie reviews (updated for unified review system)
export const getMovieReviews = async (movieId, page = 1, limit = 20, sortBy = 'recent') => {
  try {
    const response = await axiosInstance.get(`/api/movies/${movieId}/reviews/`, {
      params: { page, page_size: limit, sort_by: sortBy },
    });
    return response.data;
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
    return response.data;
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

export const searchMovies = async (filters = {}, page = 1, pageSize = 50) => {
  try {
    // Cancel previous request if exists
    if (searchController) {
      searchController.abort();
    }

    // Create new AbortController for this request
    searchController = new AbortController();

    // Create cache key from filters
    const cacheKey = JSON.stringify({
      ...filters,
      page,
      pageSize,
    });

    // Check cache first for search results
    if (cache.search.has(cacheKey) && isCacheValid(`search_${cacheKey}`, SEARCH_CACHE_DURATION)) {
      console.log('Returning cached search results');
      return cache.search.get(cacheKey);
    }

    const params = new URLSearchParams();

    // Add filters to params - optimized parameter building
    const filterMappings = {
      genres: value => value?.length && value.forEach(genre => params.append('genres', genre)),
      yearFrom: value => value && params.append('year_from', value),
      yearTo: value => value && params.append('year_to', value),
      country: value => value && params.append('country', value),
      status: value => value && params.append('status', value),
      adult: value => value !== undefined && params.append('adult', value.toString()),
      language: value => value && params.append('language', value),
      query: value => value && params.append('q', value),
      sortBy: value => value && params.append('sort_by', value),
      order: value => value && params.append('order', value),
    };

    // Apply filters efficiently
    Object.entries(filterMappings).forEach(([key, handler]) => {
      if (filters[key] !== undefined && filters[key] !== null && filters[key] !== '') {
        handler(filters[key]);
      }
    });

    params.append('page', page);
    params.append('page_size', pageSize);

    const response = await axiosInstance.get(`/api/movies/search/?${params}`, {
      signal: searchController.signal,
      timeout: 30000, // 30 second timeout for search
    });

    // Cache the search results
    cache.search.set(cacheKey, response.data);
    cache.lastFetch[`search_${cacheKey}`] = Date.now();

    // Limit cache size to prevent memory issues
    if (cache.search.size > 100) {
      const firstKey = cache.search.keys().next().value;
      cache.search.delete(firstKey);
      delete cache.lastFetch[`search_${firstKey}`];
    }

    return response.data;
  } catch (error) {
    // Don't throw error if request was cancelled
    if (error.name === 'CanceledError' || error.code === 'ERR_CANCELED') {
      console.log('Search request was cancelled');
      return null;
    }

    console.error('Error searching movies:', error);
    throw error;
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
      console.log('Returning cached suggestions');
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
