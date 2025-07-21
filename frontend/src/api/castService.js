import axios from './axios';

/**
 * Get detailed information about a cast member
 * @param {number} castId - ID of the cast member
 * @returns {Promise} API response
 */
export const getCastMemberDetail = async castId => {
  const response = await axios.get(`/api/movies/cast/${castId}/`);
  return response.data;
};

/**
 * Get cast members for a specific movie
 * @param {number} movieId - ID of the movie
 * @returns {Promise} API response
 */
export const getMovieCast = async movieId => {
  const response = await axios.get(`/api/movies/${movieId}/`);
  return response.data.cast || [];
};
