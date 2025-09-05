import { axiosInstance } from './axios';

// Cache for recommendation responses
const recommendationCache = new Map();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

// Helper function to handle API calls with caching
const makeRecommendationApiCall = async (endpoint, params = {}, cacheKey = null) => {
  try {
    // Check cache if cacheKey provided
    if (cacheKey) {
      const cachedData = recommendationCache.get(cacheKey);
      if (cachedData && Date.now() - cachedData.timestamp < CACHE_DURATION) {
        return cachedData.data;
      }
    }

    const response = await axiosInstance.get(endpoint, { params });

    // Cache the result if cacheKey provided
    if (cacheKey && response.data.status === 'success') {
      recommendationCache.set(cacheKey, {
        data: response.data,
        timestamp: Date.now(),
      });
    }

    return response.data;
  } catch (error) {
    console.error(`Error in recommendation API call to ${endpoint}:`, error);
    throw {
      error: error.response?.data?.message || `Failed to fetch recommendations from ${endpoint}`,
      details: error.response?.data,
    };
  }
};

// Get personalized recommendations (hybrid system)
export const getPersonalizedRecommendations = async (limit = 20, context = 'homepage') => {
  const cacheKey = `personalized_${limit}_${context}`;
  return makeRecommendationApiCall(
    '/api/recommendations/personalized/',
    { limit, context },
    cacheKey
  );
};

// Get collaborative filtering recommendations
export const getCollaborativeRecommendations = async (limit = 20) => {
  const cacheKey = `collaborative_${limit}`;
  return makeRecommendationApiCall('/api/recommendations/collaborative/', { limit }, cacheKey);
};

// Get demographic filtering recommendations
export const getDemographicRecommendations = async (limit = 20) => {
  const cacheKey = `demographic_${limit}`;
  return makeRecommendationApiCall('/api/recommendations/demographic/', { limit }, cacheKey);
};

// Get trending recommendations
export const getTrendingRecommendations = async (limit = 10) => {
  const cacheKey = `trending_${limit}`;
  return makeRecommendationApiCall('/api/recommendations/trending/', { limit }, cacheKey);
};

// Find similar users
export const getSimilarUsers = async (limit = 10, method = 'pearson') => {
  const cacheKey = `similar_users_${limit}_${method}`;
  return makeRecommendationApiCall(
    '/api/recommendations/similar_users/',
    { limit, method },
    cacheKey
  );
};

// Find similar movies
export const getSimilarMovies = async (movieId, limit = 10) => {
  const cacheKey = `similar_movies_${movieId}_${limit}`;
  return makeRecommendationApiCall(
    `/api/recommendations/${movieId}/similar_movies/`,
    { limit },
    cacheKey
  );
};

// Get user preferences
export const getUserPreferences = async () => {
  const cacheKey = 'user_preferences';
  return makeRecommendationApiCall('/api/recommendations/user_preferences/', {}, cacheKey);
};

// Get recommendation analytics
export const getRecommendationAnalytics = async () => {
  const cacheKey = 'recommendation_analytics';
  return makeRecommendationApiCall('/api/recommendations/analytics/', {}, cacheKey);
};

// Track recommendation interaction
export const trackRecommendationInteraction = async (
  movieId,
  action,
  recommendationType = null,
  context = null
) => {
  try {
    const interactionData = {
      movie_id: movieId,
      action: action, // 'click', 'rate', 'watch', 'like', 'dislike'
      timestamp: new Date().toISOString(),
    };

    if (recommendationType) {
      interactionData.recommendation_type = recommendationType;
    }

    if (context) {
      interactionData.context = context;
    }

    // Send to backend tracking endpoint
    await axiosInstance.post('/api/users/interactions/', {
      interactions: [interactionData],
    });

    return { success: true };
  } catch (error) {
    console.error('Error tracking recommendation interaction:', error);
    return { success: false, error: error.message };
  }
};

// Clear recommendation cache
export const clearRecommendationCache = () => {
  recommendationCache.clear();
  console.log('Recommendation cache cleared');
};

// Get cache statistics
export const getRecommendationCacheStats = () => {
  const now = Date.now();
  const stats = {
    totalEntries: recommendationCache.size,
    validEntries: 0,
    expiredEntries: 0,
    cacheKeys: [],
  };

  for (const [key, value] of recommendationCache.entries()) {
    if (now - value.timestamp < CACHE_DURATION) {
      stats.validEntries++;
    } else {
      stats.expiredEntries++;
    }
    stats.cacheKeys.push(key);
  }

  return stats;
};

// Enhanced recommendation service with fallback
export const getRecommendationsWithFallback = async (
  type = 'personalized',
  limit = 20,
  context = 'homepage'
) => {
  try {
    let recommendations = null;

    // Try the requested type first
    switch (type) {
      case 'personalized':
        recommendations = await getPersonalizedRecommendations(limit, context);
        break;
      case 'collaborative':
        recommendations = await getCollaborativeRecommendations(limit);
        break;
      case 'demographic':
        recommendations = await getDemographicRecommendations(limit);
        break;

      case 'trending':
        recommendations = await getTrendingRecommendations(limit);
        break;
      default:
        recommendations = await getPersonalizedRecommendations(limit, context);
    }

    // If successful, return the recommendations
    if (
      recommendations?.status === 'success' &&
      recommendations?.data?.recommendations?.length > 0
    ) {
      return recommendations;
    }

    // Fallback to trending if no recommendations found
    console.log(`No ${type} recommendations found, falling back to trending`);
    const trendingFallback = await getTrendingRecommendations(limit);

    if (trendingFallback?.status === 'success') {
      return {
        ...trendingFallback,
        fallback_used: true,
        original_type: type,
      };
    }

    // Final fallback - return empty with error
    return {
      status: 'error',
      message: 'No recommendations available',
      data: {
        recommendations: [],
        total: 0,
        fallback_used: true,
      },
    };
  } catch (error) {
    console.error(`Error getting ${type} recommendations:`, error);

    // Try trending as fallback
    try {
      const trendingFallback = await getTrendingRecommendations(limit);
      if (trendingFallback?.status === 'success') {
        return {
          ...trendingFallback,
          fallback_used: true,
          original_type: type,
          error: error.message,
        };
      }
    } catch (fallbackError) {
      console.error('Fallback also failed:', fallbackError);
    }

    return {
      status: 'error',
      message: error.message || 'Failed to get recommendations',
      data: {
        recommendations: [],
        total: 0,
        fallback_used: true,
      },
    };
  }
};

// Batch recommendation service for multiple types
export const getBatchRecommendations = async (types = ['personalized', 'trending'], limit = 10) => {
  const results = {};

  await Promise.allSettled(
    types.map(async type => {
      try {
        const result = await getRecommendationsWithFallback(type, limit);
        results[type] = result;
      } catch (error) {
        results[type] = {
          status: 'error',
          message: error.message,
          data: { recommendations: [], total: 0 },
        };
      }
    })
  );

  return results;
};

export default {
  getPersonalizedRecommendations,
  getCollaborativeRecommendations,
  getDemographicRecommendations,

  getTrendingRecommendations,
  getSimilarUsers,
  getSimilarMovies,
  getUserPreferences,
  getRecommendationAnalytics,
  trackRecommendationInteraction,
  clearRecommendationCache,
  getRecommendationCacheStats,
  getRecommendationsWithFallback,
  getBatchRecommendations,
};
