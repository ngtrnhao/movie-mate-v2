import { useRef, useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {
  getPersonalizedRecommendations,
  trackRecommendationInteraction,
} from '../../api/recommendationService';

const HeroBannerRecommendation = () => {
  const heroRef = useRef(null);
  const navigate = useNavigate();
  const [heroBannerMovie, setHeroBannerMovie] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { isAuthenticated } = useSelector(state => state.auth);

  // Load recommendations on component mount
  useEffect(() => {
    const fetchHeroMovie = async () => {
      if (!isAuthenticated) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const response = await getPersonalizedRecommendations(1, 'homepage');

        if (response.status === 'success' && response.data?.recommendations?.length > 0) {
          setHeroBannerMovie(response.data.recommendations[0]);
        } else {
          setError('No recommendations available');
        }
      } catch (err) {
        console.error('Error fetching hero movie:', err);
        setError(err.message || 'Failed to load recommendations');
      } finally {
        setLoading(false);
      }
    };

    fetchHeroMovie();
  }, [isAuthenticated]);

  // Fallback to default movie if no recommendations available
  const mockMovie = {
    id: 'hero-banner-fallback',
    title: 'The Shawshank Redemption',
    vote_average: 9.3,
    release_date: '1994-09-23',
    genres: ['Drama', 'Crime'],
    match: 94,
    overview:
      'Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.',
    poster_path: 'https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg',
    backdrop_path: 'https://image.tmdb.org/t/p/original/kXfqcdQKsToO0OUXHcrrNCHDBzO.jpg',
    trailer_url: 'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-576p.mp4',
  };

  // Use recommendation data or fallback
  const movie = heroBannerMovie || mockMovie;
  const userRating = movie.vote_average ? Math.round(movie.vote_average / 2) : 0;

  // Calculate match percentage from predicted rating or confidence
  const matchPercentage =
    movie.match ||
    (movie.predicted_rating ? Math.round((movie.predicted_rating / 5.0) * 100) : null) ||
    (movie.confidence_score ? Math.round(movie.confidence_score * 100) : null) ||
    94; // fallback

  const handleViewDetails = async () => {
    // Track interaction
    if (heroBannerMovie) {
      try {
        await trackRecommendationInteraction(movie.id, 'click', 'personalized', 'homepage');
      } catch (error) {
        console.error('Error tracking interaction:', error);
      }
    }

    navigate(`/movies/${movie.id}`);
  };

  const handleWhyRecommended = () => {
    // Navigate to recommendation explanation page or show modal
    // This could show the recommendation explanation from movie.explanation
    console.log('Recommendation explanation:', movie.explanation);
    // For now, just alert - you can implement a modal later
    if (movie.explanation && movie.explanation.reason) {
      alert(`Recommended because: ${movie.explanation.reason}`);
    } else {
      alert('This movie was recommended based on your preferences and viewing history.');
    }
  };

  // Show loading state
  if (loading && !heroBannerMovie) {
    return (
      <section className="relative min-h-[105vh] w-full bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading personalized recommendations...</div>
      </section>
    );
  }

  // Show error state (but still show fallback movie)
  if (error && !heroBannerMovie) {
    console.warn('Failed to load recommendations, using fallback movie:', error);
  }

  return (
    <section ref={heroRef} className="relative min-h-[105vh] w-full">
      {/* Background Video */}
      <div className="absolute inset-0">
        <video
          autoPlay
          loop
          muted
          playsInline
          className="size-full object-cover"
          poster={movie.poster_url}
        >
          <source src={movie.trailer_url} type="video/mp4" />
          {/* Fallback image if video fails to load */}
          <img src={movie.poster_url} alt={movie.title} className="size-full object-cover" />
        </video>
        {/* Enhanced Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-r from-black/60 via-black/40 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-b from-black/30 via-transparent to-black/60" />
      </div>

      {/* Content */}
      <div className="relative ml-14 flex h-full max-w-[1400px] items-center">
        <div className="mt-60 max-w-2xl">
          {/* Genre and Recommendation Badge */}
          <div className="mb-4 flex gap-2">
            {heroBannerMovie && (
              <span className="rounded-full bg-red-600 px-3 py-1 text-xs font-semibold text-white shadow-lg">
                Recommended for You
              </span>
            )}
            {movie.genres?.map(genre => (
              <span
                key={typeof genre === 'string' ? genre : genre.name}
                className="rounded-full bg-gray-800/80 px-3 py-1 text-xs font-medium text-white shadow-lg backdrop-blur-sm"
              >
                {typeof genre === 'string' ? genre : genre.name}
              </span>
            ))}
          </div>

          {/* Title */}
          <h1 className="mb-2 max-w-2xl break-words text-6xl font-bold text-white drop-shadow-lg">
            {movie.title}
          </h1>

          {/* Rating, Year, Match */}
          <div className="mb-4 flex items-center gap-3">
            <div className="flex items-center">
              {[1, 2, 3, 4, 5].map(star => (
                <span
                  key={star}
                  className={`text-lg ${star <= userRating ? 'text-yellow-400' : 'text-gray-400'}`}
                >
                  ★
                </span>
              ))}
              <span className="ml-2 font-medium text-white drop-shadow-md">{userRating}/5</span>
            </div>
            <span className="text-gray-300 drop-shadow-md">
              | {new Date(movie.release_date).getFullYear()}
            </span>
            <span className="flex items-center font-semibold text-green-400 drop-shadow-md">
              <svg className="mr-1 size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  d="M5 13l4 4L19 7"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              {matchPercentage}% match
            </span>
          </div>

          {/* Overview */}
          <p className="max-w-xl break-words text-lg font-medium text-gray-200 drop-shadow-md">
            {movie.overview}
          </p>

          {/* Action Buttons */}
          <div className="mt-6 flex flex-wrap gap-4">
            <button
              onClick={handleViewDetails}
              className="rounded-sm bg-red-600 px-6 py-2 font-semibold text-white shadow-lg transition hover:bg-red-700"
            >
              View Details
            </button>
            <button
              onClick={handleWhyRecommended}
              className="rounded-sm bg-white/10 px-6 py-2 font-semibold text-white shadow-lg backdrop-blur-sm transition hover:bg-white/20"
            >
              Why Recommended?
            </button>
          </div>

          {/* Recommendation Debug Info (only in development) */}
          {process.env.NODE_ENV === 'development' && heroBannerMovie && (
            <div className="mt-4 text-xs text-gray-400">
              Recommendation Type: {movie.recommendationType || 'personalized'} | Rank:{' '}
              {movie.rank || 1} | Confidence: {movie.confidence || 'N/A'}%
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

export default HeroBannerRecommendation;
