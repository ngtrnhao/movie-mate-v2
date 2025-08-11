import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import MovieCard from '../movies/movie-card/MovieCard';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import { useTranslation } from '../../i18n/hooks/useTranslation';

const PersonalizedRecommendations = ({
  context = 'homepage',
  limit = 20,
  title,
  showMethodInfo = true,
  allowRefresh = true,
}) => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [recommendationInfo, setRecommendationInfo] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const { user, token } = useSelector(state => state.auth);
  const { t } = useTranslation();

  // Use translated title if not provided
  const displayTitle = title || t('movies.recommendations.personalized.title');

  useEffect(() => {
    if (user && token) {
      fetchRecommendations();
    }
  }, [user, token, context, limit]);

  const fetchRecommendations = async (forceRefresh = false) => {
    try {
      if (forceRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError(null);

      const refreshParam = forceRefresh ? '&refresh=true' : '';
      const response = await fetch(
        `/recommendations/api/personalized/?limit=${limit}&context=${context}${refreshParam}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.status === 'success') {
        setRecommendations(data.data.movies);
        setRecommendationInfo({
          type: data.data.recommendation_type,
          method: data.data.method_used,
          count: data.data.count,
          cached: data.data.cached,
        });
      } else {
        throw new Error(data.message || 'Failed to fetch recommendations');
      }
    } catch (err) {
      console.error('Error fetching recommendations:', err);
      setError(err.message);

      // Fallback to popular movies if recommendations fail
      await fetchFallbackMovies();
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const fetchFallbackMovies = async () => {
    try {
      // Fallback to popular movies
      const response = await fetch(`/api/movies/popular/?limit=${limit}`);
      const data = await response.json();

      if (data.status === 'success') {
        setRecommendations(data.data.results);
        setRecommendationInfo({
          type: 'fallback',
          method: 'popular',
          count: data.data.results.length,
          cached: false,
        });
      }
    } catch (fallbackErr) {
      console.error('Error fetching fallback movies:', fallbackErr);
    }
  };

  const handleMovieClick = async movie => {
    try {
      // Track recommendation click
      await fetch('/recommendations/api/feedback/', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          movie_id: movie.id,
          recommendation_type: recommendationInfo?.type || 'personalized',
          context: context,
          action: 'clicked',
        }),
      });
    } catch (err) {
      console.error('Error tracking recommendation click:', err);
    }
  };

  const handleMovieRating = async (movie, rating) => {
    try {
      // Track recommendation rating
      await fetch('/recommendations/api/feedback/', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          movie_id: movie.id,
          recommendation_type: recommendationInfo?.type || 'personalized',
          context: context,
          action: 'rated',
        }),
      });
    } catch (err) {
      console.error('Error tracking recommendation rating:', err);
    }
  };

  const handleFeedback = async (movie, feedbackType) => {
    try {
      await fetch('/recommendations/api/feedback/', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          movie_id: movie.id,
          recommendation_type: recommendationInfo?.type || 'personalized',
          context: context,
          feedback_type: feedbackType,
        }),
      });

      // Remove movie from recommendations if disliked
      if (feedbackType === 'dislike' || feedbackType === 'not_interested') {
        setRecommendations(prev => prev.filter(rec => rec.id !== movie.id));
      }
    } catch (err) {
      console.error('Error submitting feedback:', err);
    }
  };

  const getMethodDisplayName = method => {
    return t(`movies.recommendations.common.methods.${method}`) || method;
  };

  const getMethodDescription = method => {
    return t(`movies.recommendations.common.methodDescriptions.${method}`) || '';
  };

  if (!user) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-2xl font-bold text-white mb-4">{displayTitle}</h2>
        <p className="text-gray-400">{t('movies.recommendations.personalized.signInRequired')}</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-2xl font-bold text-white mb-4">{displayTitle}</h2>
        <LoadingSpinner />
      </div>
    );
  }

  if (error && recommendations.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-2xl font-bold text-white mb-4">{displayTitle}</h2>
        <ErrorMessage message={error} onRetry={() => fetchRecommendations(true)} />
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-2xl font-bold text-white">{displayTitle}</h2>
          {showMethodInfo && recommendationInfo && (
            <div className="mt-2">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {getMethodDisplayName(recommendationInfo.method)}
              </span>
              {recommendationInfo.cached && (
                <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  {t('movies.recommendations.common.cached')}
                </span>
              )}
              <p className="text-sm text-gray-400 mt-1">
                {getMethodDescription(recommendationInfo.method)}
              </p>
            </div>
          )}
        </div>

        {allowRefresh && (
          <button
            onClick={() => fetchRecommendations(true)}
            disabled={refreshing}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {refreshing ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                {t('movies.recommendations.personalized.refreshing')}
              </>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                {t('movies.recommendations.personalized.refresh')}
              </>
            )}
          </button>
        )}
      </div>

      {/* Error Message (if error but have fallback data) */}
      {error && recommendations.length > 0 && (
        <div className="mb-4 p-3 bg-yellow-100 border border-yellow-400 text-yellow-700 rounded">
          <p className="text-sm">
            <strong>Note:</strong> {t('movies.recommendations.personalized.fallbackNote')}
          </p>
        </div>
      )}

      {/* Movie Grid */}
      {recommendations.length > 0 ? (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {recommendations.map(movie => (
            <div key={movie.id} className="relative group">
              <MovieCard
                movie={movie}
                onClick={() => handleMovieClick(movie)}
                onRating={rating => handleMovieRating(movie, rating)}
                showQuickActions={true}
              />

              {/* Feedback Buttons */}
              <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="flex flex-col space-y-1">
                  <button
                    onClick={e => {
                      e.stopPropagation();
                      handleFeedback(movie, 'like');
                    }}
                    className="p-1 bg-green-600 text-white rounded-full hover:bg-green-700"
                    title={t('movies.recommendations.common.feedback.like')}
                  >
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </button>
                  <button
                    onClick={e => {
                      e.stopPropagation();
                      handleFeedback(movie, 'dislike');
                    }}
                    className="p-1 bg-red-600 text-white rounded-full hover:bg-red-700"
                    title={t('movies.recommendations.common.feedback.dislike')}
                  >
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8">
          <p className="text-gray-400 text-lg">{t('movies.recommendations.personalized.empty')}</p>
          <button
            onClick={() => fetchRecommendations(true)}
            className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            {t('movies.recommendations.personalized.tryAgain')}
          </button>
        </div>
      )}

      {/* Recommendation Info */}
      {recommendationInfo && recommendations.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-700">
          <p className="text-sm text-gray-400 text-center">
            {t('movies.recommendations.common.showing', {
              count: recommendationInfo.count,
              method: getMethodDisplayName(recommendationInfo.method),
            })}
            {recommendationInfo.cached && ` (${t('movies.recommendations.common.cached')})`}
          </p>
        </div>
      )}
    </div>
  );
};

export default PersonalizedRecommendations;
