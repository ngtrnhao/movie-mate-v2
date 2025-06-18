import axiosInstance from './axios';

// Cache object to store API responses
const cache = {
  trending: null,
  topRated: null,
  upcoming: null,
  featured: null,
  lastFetch: {},
};

// Cache duration in milliseconds (5 minutes)
const CACHE_DURATION = 5 * 60 * 1000;

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

// Get featured movies
export const getFeaturedMovies = async () => {
  try {
    // Check cache first
    if (isCacheValid('featured')) {
      console.log('Returning cached featured movies');
      return cache.featured;
    }

    const response = await axiosInstance.get('/api/movies/featured/');
    const data = handleResponse(response.data);

    // Update cache
    cache.featured = data;
    cache.lastFetch.featured = Date.now();

    return data;
  } catch (error) {
    console.error('Error fetching featured movies:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch featured movies',
      details: error.response?.data,
    };
  }
};

// Get trending movies
export const getTrendingMovies = async () => {
  try {
    // Check cache first
    if (isCacheValid('trending')) {
      console.log('Returning cached trending movies');
      return cache.trending;
    }

    const response = await axiosInstance.get('/api/movies/trending/');
    const data = handleResponse(response.data);

    // Update cache
    cache.trending = data;
    cache.lastFetch.trending = Date.now();

    return data;
  } catch (error) {
    console.error('Error fetching trending movies:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch trending movies',
      details: error.response?.data,
    };
  }
};

// Get top rated movies
export const getTopRatedMovies = async () => {
  try {
    // Check cache first
    if (isCacheValid('topRated')) {
      console.log('Returning cached top rated movies');
      return cache.topRated;
    }

    const response = await axiosInstance.get('/api/movies/top_rated/');
    const data = handleResponse(response.data);

    // Update cache
    cache.topRated = data;
    cache.lastFetch.topRated = Date.now();

    return data;
  } catch (error) {
    console.error('Error fetching top rated movies:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch top rated movies',
      details: error.response?.data,
    };
  }
};

// Get upcoming movies
export const getUpcomingMovies = async () => {
  try {
    // Check cache first
    if (isCacheValid('upcoming')) {
      console.log('Returning cached upcoming movies');
      return cache.upcoming;
    }

    const response = await axiosInstance.get('/api/movies/upcoming/');
    const data = handleResponse(response.data);

    // Update cache
    cache.upcoming = data;
    cache.lastFetch.upcoming = Date.now();

    return data;
  } catch (error) {
    console.error('Error fetching upcoming movies:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch upcoming movies',
      details: error.response?.data,
    };
  }
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
