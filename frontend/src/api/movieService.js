import axiosInstance from './axios';

// Cache object to store API responses
const cache = {
  trending: null,
  topRated: null,
  upcoming: null,
  featured: null,
  lastFetch: {},
};

// Cache duration in milliseconds (10 minutes)
const CACHE_DURATION = 10 * 60 * 1000;

// Helper function to check if cache is valid
const isCacheValid = key => {
  const lastFetch = cache.lastFetch[key];
  if (!lastFetch) return false;
  return Date.now() - lastFetch < CACHE_DURATION;
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

// API service for movies

export const searchMovies = async (filters = {}, page = 1, pageSize = 20) => {
  try {
    const params = new URLSearchParams();

    // Add filters to params
    if (filters.genres?.length) {
      filters.genres.forEach(genre => params.append('genres', genre));
    }
    if (filters.yearFrom) params.append('year_from', filters.yearFrom);
    if (filters.yearTo) params.append('year_to', filters.yearTo);
    if (filters.ratingMin) params.append('rating_min', filters.ratingMin);
    if (filters.ratingMax) params.append('rating_max', filters.ratingMax);
    if (filters.runtimeMin) params.append('runtime_min', filters.runtimeMin);
    if (filters.runtimeMax) params.append('runtime_max', filters.runtimeMax);
    if (filters.status) params.append('status', filters.status);
    if (filters.adult !== undefined) params.append('adult', filters.adult);
    if (filters.language) params.append('language', filters.language);
    if (filters.query) params.append('q', filters.query);
    if (filters.sortBy) params.append('sort_by', filters.sortBy);
    if (filters.order) params.append('order', filters.order);

    params.append('page', page);
    params.append('page_size', pageSize);

    const response = await axiosInstance.get(`/api/movies/search/?${params}`);
    return response.data;
  } catch (error) {
    console.error('Error searching movies:', error);
    throw error;
  }
};
