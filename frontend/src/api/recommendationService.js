import axiosInstance from './axios';

const API_BASE_URL = '/api/recommendations';

/**
 * Recommendation API Service
 * Handles all communication with the backend recommendation system
 */

// Personalized recommendations (automatically chooses best method)
export const fetchPersonalizedRecommendations = async ({
  context = 'homepage',
  limit = 20,
  refresh = false,
}) => {
  try {
    const response = await axiosInstance.get(`${API_BASE_URL}/personalized/`, {
      params: { context, limit, refresh },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching personalized recommendations:', error);
    throw error;
  }
};

// Collaborative filtering recommendations
export const fetchCollaborativeRecommendations = async ({
  context = 'homepage',
  limit = 20,
  refresh = false,
}) => {
  try {
    const response = await axiosInstance.get(`${API_BASE_URL}/collaborative/`, {
      params: { context, limit, refresh },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching collaborative recommendations:', error);
    throw error;
  }
};

// Demographic filtering recommendations
export const fetchDemographicRecommendations = async ({
  context = 'homepage',
  limit = 20,
  refresh = false,
}) => {
  try {
    const response = await axiosInstance.get(`${API_BASE_URL}/demographic/`, {
      params: { context, limit, refresh },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching demographic recommendations:', error);
    throw error;
  }
};

// Hybrid recommendations
export const fetchHybridRecommendations = async ({
  context = 'homepage',
  limit = 20,
  refresh = false,
}) => {
  try {
    const response = await axiosInstance.get(`${API_BASE_URL}/hybrid/`, {
      params: { context, limit, refresh },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching hybrid recommendations:', error);
    throw error;
  }
};

// Submit feedback on recommendations
export const submitRecommendationFeedback = async ({
  movie_id,
  recommendation_type,
  context = 'homepage',
  feedback_type,
  action,
}) => {
  try {
    const response = await axiosInstance.post(`${API_BASE_URL}/feedback/`, {
      movie_id,
      recommendation_type,
      context,
      feedback_type,
      action,
    });
    return response.data;
  } catch (error) {
    console.error('Error submitting recommendation feedback:', error);
    throw error;
  }
};

// Get user's recommendation profile
export const fetchUserRecommendationProfile = async () => {
  try {
    const response = await axiosInstance.get(`${API_BASE_URL}/profile/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching user recommendation profile:', error);
    throw error;
  }
};

// Get recommendation system statistics (public endpoint)
export const fetchRecommendationStats = async () => {
  try {
    const response = await axiosInstance.get(`${API_BASE_URL}/stats/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching recommendation stats:', error);
    throw error;
  }
};

/**
 * Helper functions for recommendation management
 */

// Get the best recommendation type for the current user context
export const getBestRecommendationType = (userProfile, context = 'homepage') => {
  if (!userProfile || !userProfile.preferences) {
    return 'demographic'; // Default for new users
  }

  const { rating_count, interaction_count } = userProfile.preferences;

  // If user has many ratings, use collaborative filtering
  if (rating_count >= 20) {
    return 'collaborative';
  }

  // If user has demographic data but few ratings, use demographic
  if (
    userProfile.demographicInfo?.age &&
    userProfile.demographicInfo?.gender &&
    rating_count < 10
  ) {
    return 'demographic';
  }

  // Otherwise use hybrid
  return 'hybrid';
};

// Check if recommendations need refresh based on cache and timestamp
export const shouldRefreshRecommendations = (lastUpdated, cacheTimeout = 3600000) => {
  // 1 hour default
  if (!lastUpdated) return true;

  const now = new Date().getTime();
  const lastUpdateTime = new Date(lastUpdated).getTime();

  return now - lastUpdateTime > cacheTimeout;
};

// Format recommendation for display
export const formatRecommendationForDisplay = (movie, recommendationType, rank) => {
  return {
    ...movie,
    // Add recommendation-specific metadata
    recommendationType,
    rank,
    match: movie.predicted_rating ? Math.round((movie.predicted_rating / 5.0) * 100) : null,
    confidence: movie.confidence_score ? Math.round(movie.confidence_score * 100) : null,
    novelty: movie.novelty_score ? Math.round(movie.novelty_score * 100) : null,
    explanation: movie.explanation || {},

    // Ensure required fields exist
    vote_average: movie.vote_average || movie.tmdb_rating || 0,
    poster_path: movie.poster_path || movie.poster_url,
    backdrop_path: movie.backdrop_path || movie.backdrop_url,
    release_date: movie.release_date || movie.release_year,

    // Add recommendation context
    recommendedAt: new Date().toISOString(),
    source: 'recommendation_system',
  };
};

// Batch fetch multiple recommendation types
export const fetchAllRecommendationTypes = async ({ context = 'homepage', limit = 20 }) => {
  try {
    const promises = [
      fetchPersonalizedRecommendations({ context, limit }),
      fetchCollaborativeRecommendations({ context, limit }),
      fetchDemographicRecommendations({ context, limit }),
      fetchHybridRecommendations({ context, limit }),
    ];

    const [personalized, collaborative, demographic, hybrid] = await Promise.allSettled(promises);

    return {
      personalized: personalized.status === 'fulfilled' ? personalized.value : null,
      collaborative: collaborative.status === 'fulfilled' ? collaborative.value : null,
      demographic: demographic.status === 'fulfilled' ? demographic.value : null,
      hybrid: hybrid.status === 'fulfilled' ? hybrid.value : null,
      errors: {
        personalized: personalized.status === 'rejected' ? personalized.reason : null,
        collaborative: collaborative.status === 'rejected' ? collaborative.reason : null,
        demographic: demographic.status === 'rejected' ? demographic.reason : null,
        hybrid: hybrid.status === 'rejected' ? hybrid.reason : null,
      },
    };
  } catch (error) {
    console.error('Error fetching all recommendation types:', error);
    throw error;
  }
};

// Track recommendation interaction
export const trackRecommendationInteraction = async (
  movieId,
  recommendationType,
  context,
  action
) => {
  try {
    await submitRecommendationFeedback({
      movie_id: movieId,
      recommendation_type: recommendationType,
      context,
      action,
    });
  } catch (error) {
    // Don't throw error for tracking failures - just log
    console.warn('Failed to track recommendation interaction:', error);
  }
};

export default {
  fetchPersonalizedRecommendations,
  fetchCollaborativeRecommendations,
  fetchDemographicRecommendations,
  fetchHybridRecommendations,
  submitRecommendationFeedback,
  fetchUserRecommendationProfile,
  fetchRecommendationStats,
  getBestRecommendationType,
  shouldRefreshRecommendations,
  formatRecommendationForDisplay,
  fetchAllRecommendationTypes,
  trackRecommendationInteraction,
};
