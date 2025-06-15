import axiosInstance from './axios';

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
    const response = await axiosInstance.get('/api/movies/featured/');
    return handleResponse(response.data);
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
    const response = await axiosInstance.get('/api/movies/trending/');
    return handleResponse(response.data);
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
    const response = await axiosInstance.get('/api/movies/top_rated/');
    return handleResponse(response.data);
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
    const response = await axiosInstance.get('/api/movies/upcoming/');
    return handleResponse(response.data);
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
