import { useRef, useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import {
  getContentBasedRecommendations,
  trackRecommendationInteraction,
} from '../../api/recommendationService';
import MovieCard from '../movies/movie-card';
import LoadingSpinner from '../common/LoadingSpinner';

const MOVIES_PER_VIEW = 5;
const CARD_WIDTH = 270;
const SCROLL_AMOUNT = MOVIES_PER_VIEW * CARD_WIDTH + (MOVIES_PER_VIEW - 1) * 28;

const ContentBasedRecommendations = () => {
  const scrollRef = useRef(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);

  const isAuthenticated = useSelector(state => state.auth.isAuthenticated);

  // Fetch content-based recommendations
  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!isAuthenticated) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const response = await getContentBasedRecommendations(20);

        if (response.status === 'success' && response.data?.recommendations) {
          setRecommendations(response.data.recommendations);
        } else {
          setError('No content-based recommendations available');
        }
      } catch (err) {
        console.error('Error fetching content-based recommendations:', err);
        setError(err.message || 'Failed to load content-based recommendations');
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [isAuthenticated]);

  // Handle scroll navigation
  const scrollLeft = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      scrollRef.current?.scrollBy({
        left: -SCROLL_AMOUNT,
        behavior: 'smooth',
      });
    }
  };

  const scrollRight = () => {
    if (currentIndex < Math.ceil(recommendations.length / MOVIES_PER_VIEW) - 1) {
      setCurrentIndex(currentIndex + 1);
      scrollRef.current?.scrollBy({
        left: SCROLL_AMOUNT,
        behavior: 'smooth',
      });
    }
  };

  // Handle movie click
  const handleMovieClick = async movie => {
    try {
      await trackRecommendationInteraction(
        movie.id,
        'click',
        'content_based_filtering',
        'homepage'
      );
    } catch (error) {
      console.error('Error tracking movie click:', error);
    }
  };

  // Show loading state
  if (loading) {
    return (
      <section className="w-full py-8">
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-6 shadow-lg">
          <h2 className="mb-6 text-2xl font-semibold text-white">
            <span className="text-purple-500">🎬</span> Content-Based Recommendations
          </h2>
          <p className="mb-4 text-sm text-gray-400">
            Based on genre, cast, director, and movie content similarity
          </p>
          <div className="flex justify-center py-8">
            <LoadingSpinner />
          </div>
        </div>
      </section>
    );
  }

  // Show error state
  if (error) {
    return (
      <section className="w-full py-8">
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-6 shadow-lg">
          <h2 className="mb-6 text-2xl font-semibold text-white">
            <span className="text-purple-500">🎬</span> Content-Based Recommendations
          </h2>
          <p className="mb-4 text-sm text-gray-400">
            Based on genre, cast, director, and movie content similarity
          </p>
          <div className="text-center py-8">
            <p className="text-gray-400">{error}</p>
            {!isAuthenticated && (
              <p className="text-sm text-gray-500 mt-2">
                Sign in to get content-based recommendations
              </p>
            )}
          </div>
        </div>
      </section>
    );
  }

  // Show empty state
  if (!isAuthenticated || recommendations.length === 0) {
    return (
      <section className="w-full py-8">
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-6 shadow-lg">
          <h2 className="mb-6 text-2xl font-semibold text-white">
            <span className="text-purple-500">🎬</span> Content-Based Recommendations
          </h2>
          <p className="mb-4 text-sm text-gray-400">
            Based on genre, cast, director, and movie content similarity
          </p>
          <div className="text-center py-8">
            <p className="text-gray-400">
              {!isAuthenticated
                ? 'Sign in to get content-based recommendations'
                : 'No content-based recommendations available yet. Try rating some movies!'}
            </p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="w-full py-8">
      <div className="rounded-lg border border-gray-800 bg-gray-900 p-6 shadow-lg">
        <h2 className="mb-6 text-2xl font-semibold text-white">
          <span className="text-purple-500">🎬</span> Content-Based Recommendations
        </h2>
        <p className="mb-4 text-sm text-gray-400">
          Based on genre, cast, director, and movie content similarity
        </p>

        <div className="relative">
          {/* Navigation buttons */}
          {currentIndex > 0 && (
            <button
              onClick={scrollLeft}
              className="absolute left-0 top-1/2 z-10 -translate-y-1/2 rounded-full bg-gray-800 p-2 text-white shadow-lg transition hover:bg-gray-700"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </button>
          )}

          {currentIndex < Math.ceil(recommendations.length / MOVIES_PER_VIEW) - 1 && (
            <button
              onClick={scrollRight}
              className="absolute right-0 top-1/2 z-10 -translate-y-1/2 rounded-full bg-gray-800 p-2 text-white shadow-lg transition hover:bg-gray-700"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </button>
          )}

          {/* Movie carousel */}
          <div
            ref={scrollRef}
            className="flex gap-4 overflow-x-auto scrollbar-hide"
            style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
          >
            {recommendations.map(movie => (
              <div key={movie.id} className="flex-shrink-0" style={{ width: CARD_WIDTH }}>
                <MovieCard movie={movie} onClick={() => handleMovieClick(movie)} />
              </div>
            ))}
          </div>
        </div>

        {/* Pagination dots */}
        {recommendations.length > MOVIES_PER_VIEW && (
          <div className="mt-4 flex justify-center space-x-2">
            {Array.from({ length: Math.ceil(recommendations.length / MOVIES_PER_VIEW) }).map(
              (_, index) => (
                <button
                  key={index}
                  onClick={() => {
                    setCurrentIndex(index);
                    const targetScroll = index * SCROLL_AMOUNT;
                    scrollRef.current?.scrollTo({
                      left: targetScroll,
                      behavior: 'smooth',
                    });
                  }}
                  className={`h-2 w-2 rounded-full transition ${
                    index === currentIndex ? 'bg-purple-500' : 'bg-gray-600'
                  }`}
                />
              )
            )}
          </div>
        )}
      </div>
    </section>
  );
};

export default ContentBasedRecommendations;
