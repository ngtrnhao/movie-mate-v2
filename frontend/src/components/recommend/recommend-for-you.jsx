import { useRef, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  loadPersonalizedRecommendations,
  markMovieClicked,
} from '../../store/slices/recommendationSlice';
import { trackRecommendationInteraction } from '../../api/recommendationService';
import MovieCard from '../movies/movie-card';

const MOVIES_PER_VIEW = 5;
const CARD_WIDTH = 270; // px (desktop)
const SCROLL_AMOUNT = MOVIES_PER_VIEW * CARD_WIDTH + (MOVIES_PER_VIEW - 1) * 28;

// Fallback mock data for when API is not available
const mockRecommendations = [
  {
    id: 101,
    title: 'Inception',
    poster_path: 'https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg',
    vote_average: 8.7,
    match: 97,
    release_date: '2019-10-04',
    recommendReason: 'Because you liked Sci-Fi thrillers',
  },
  {
    id: 102,
    title: 'Interstellar',
    poster_path: 'https://image.tmdb.org/t/p/w500/rAiYTfKGqDCRIIqo664sY9XZIvQ.jpg',
    vote_average: 8.6,
    match: 95,
    release_date: '2019-10-04',
    recommendReason: 'Based on your interest in space adventures',
  },
  {
    id: 103,
    title: 'Parasite',
    poster_path: 'https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg',
    vote_average: 8.5,
    match: 92,
    release_date: '2019-10-04',
    recommendReason: 'Because you watched Oscar-winning movies',
  },
  {
    id: 104,
    title: 'Joker',
    poster_path: 'https://image.tmdb.org/t/p/w500/udDclJoHjfjb8Ekgsd4FDteOkCU.jpg',
    vote_average: 8.4,
    match: 90,
    release_date: '2019-10-04',
    recommendReason: 'Recommended for psychological drama fans',
  },
  {
    id: 105,
    title: 'Avengers: Endgame',
    poster_path: 'https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg',
    vote_average: 8.4,
    match: 89,
    release_date: '2019-10-04',
    recommendReason: 'Because you like superhero blockbusters',
  },
];

const RecommendForYou = () => {
  const scrollRef = useRef(null);
  const dispatch = useDispatch();

  // Get data from Redux store
  const { recommendations, loading, error, isInitialized } = useSelector(
    state => state.recommendations
  );

  const { isAuthenticated } = useSelector(state => state.auth);

  // Load personalized recommendations
  useEffect(() => {
    if (isAuthenticated && !isInitialized) {
      dispatch(
        loadPersonalizedRecommendations({
          context: 'homepage',
          limit: 10,
        })
      );
    }
  }, [dispatch, isAuthenticated, isInitialized]);

  // Get personalized recommendations or fallback to mock data
  const movies = recommendations.homepage?.personalized || [];
  const displayMovies = movies.length > 0 ? movies : isAuthenticated ? [] : mockRecommendations;

  const handleScroll = direction => {
    if (scrollRef.current) {
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -SCROLL_AMOUNT : SCROLL_AMOUNT,
        behavior: 'smooth',
      });
    }
  };

  const handleMovieClick = async movie => {
    // Track interaction if it's a real recommendation
    if (movies.length > 0 && isAuthenticated) {
      dispatch(
        markMovieClicked({
          movieId: movie.id,
          recommendationType: movie.recommendationType || 'personalized',
          context: 'homepage',
        })
      );

      // Track in backend
      await trackRecommendationInteraction(
        movie.id,
        movie.recommendationType || 'personalized',
        'homepage',
        'clicked'
      );
    }
  };

  // Show loading state
  if (loading.personalized && displayMovies.length === 0) {
    return (
      <div className="px-4 py-8 md:px-8">
        <div className="mx-auto max-w-[1400px]">
          <h2 className="mb-6 text-2xl font-bold text-white">Recommended for You</h2>
          <div className="flex items-center justify-center py-12">
            <div className="text-white">Loading personalized recommendations...</div>
          </div>
        </div>
      </div>
    );
  }

  // Show error state with fallback
  if (error.personalized && displayMovies.length === 0) {
    return (
      <div className="px-4 py-8 md:px-8">
        <div className="mx-auto max-w-[1400px]">
          <h2 className="mb-6 text-2xl font-bold text-white">Recommended for You</h2>
          <div className="flex items-center justify-center py-12">
            <div className="text-red-400">
              Failed to load recommendations. Please try again later.
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-8 md:px-8">
      <div className="mx-auto max-w-[1400px]">
        {/* Section Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white">
              {isAuthenticated ? 'Recommended for You' : 'Popular Movies'}
            </h2>
            {isAuthenticated && movies.length > 0 && (
              <p className="text-sm text-gray-400 mt-1">
                Based on your preferences and viewing history
              </p>
            )}
          </div>

          {/* Navigation buttons */}
          <div className="flex gap-2">
            <button
              onClick={() => handleScroll('left')}
              className="rounded-full bg-gray-800/50 p-2 text-white transition hover:bg-gray-800"
              aria-label="Scroll left"
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
            <button
              onClick={() => handleScroll('right')}
              className="rounded-full bg-gray-800/50 p-2 text-white transition hover:bg-gray-800"
              aria-label="Scroll right"
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
          </div>
        </div>

        {/* Movies Scroll Container */}
        <div
          ref={scrollRef}
          className="flex gap-7 overflow-x-auto scroll-smooth pb-4"
          style={{
            scrollbarWidth: 'none',
            msOverflowStyle: 'none',
            WebkitScrollbar: { display: 'none' },
          }}
        >
          {displayMovies.map((movie, index) => {
            // Calculate match percentage
            const match =
              movie.match ||
              (movie.predicted_rating ? Math.round((movie.predicted_rating / 5.0) * 100) : null) ||
              (movie.confidence_score ? Math.round(movie.confidence_score * 100) : null);

            // Format movie data for MovieCard component
            const formattedMovie = {
              ...movie,
              // Ensure poster path is correct
              poster_path: movie.poster_path || movie.poster_url,
              // Add recommendation-specific data
              match,
              recommendReason: movie.explanation?.reason || movie.recommendReason,
              // Add rank for debugging
              rank: movie.rank || index + 1,
            };

            return (
              <div key={movie.id} className="min-w-[270px]">
                <MovieCard
                  movie={formattedMovie}
                  onClick={() => handleMovieClick(movie)}
                  showRecommendationInfo={isAuthenticated && movies.length > 0}
                />

                {/* Recommendation-specific info */}
                {isAuthenticated && movies.length > 0 && (
                  <div className="mt-2 px-2">
                    {match && (
                      <div className="text-xs text-green-400 font-medium">{match}% match</div>
                    )}
                    {movie.explanation?.reason && (
                      <div className="text-xs text-gray-400 mt-1 line-clamp-2">
                        {movie.explanation.reason}
                      </div>
                    )}

                    {/* Debug info in development */}
                    {process.env.NODE_ENV === 'development' && (
                      <div className="text-xs text-gray-500 mt-1">
                        Type: {movie.recommendationType || 'personalized'} | Rank:{' '}
                        {movie.rank || index + 1}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Empty state for authenticated users */}
        {isAuthenticated && movies.length === 0 && !loading.personalized && !error.personalized && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="text-gray-400 mb-4">
              <svg
                className="h-16 w-16 mx-auto mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1}
                  d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2h4a1 1 0 110 2h-1v12a2 2 0 01-2 2H6a2 2 0 01-2-2V6H3a1 1 0 110-2h4zM6 6v12h12V6H6zm4-2V3h4v1H10z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-white mb-2">No recommendations yet</h3>
            <p className="text-gray-400 max-w-md">
              Start rating some movies to get personalized recommendations tailored to your taste!
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default RecommendForYou;
