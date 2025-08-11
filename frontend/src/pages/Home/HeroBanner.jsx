import { useRef, useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {
  getPersonalizedRecommendations,
  trackRecommendationInteraction,
} from '../../api/recommendationService';
import { useTranslation } from '../../i18n/hooks/useTranslation';
import { getDisplayTitle, getDisplayOverview } from '../../utils/titleUtils';

const HeroBannerRecommendation = () => {
  const heroRef = useRef(null);
  const navigate = useNavigate();
  const [heroBannerMovie, setHeroBannerMovie] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { isAuthenticated } = useSelector(state => state.auth);
  const { t, i18n } = useTranslation('movies');

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
    poster_url: 'https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg',
    backdrop_url: 'https://image.tmdb.org/t/p/original/kXfqcdQKsToO0OUXHcrrNCHDBzO.jpg',
    trailer_url: 'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-576p.mp4',
  };

  // Use recommendation data or fallback
  const movie = heroBannerMovie || mockMovie;

  // Localized fields
  const localizedTitle = getDisplayTitle(movie, i18n.language);
  const localizedOverview = getDisplayOverview(movie, i18n.language) || movie.overview;

  // Localized genres (only current language if available)
  const localizedGenres = (() => {
    const raw = Array.isArray(movie.genres) ? movie.genres : [];
    const normalized = raw.map(g =>
      typeof g === 'string' ? { id: g, name: g, language: null } : g
    );
    let filtered = normalized.filter(g => !g.language || g.language === i18n.language);
    if (filtered.length === 0) filtered = normalized; // fallback if language-specific not present
    return filtered;
  })();

  // Calculate match percentage from multiple possible fields
  const normalizeMatch = m => {
    if (m == null) return null;
    if (m <= 1) return Math.round(m * 100); // ratio 0..1
    if (m <= 5) return Math.round((m / 5) * 100); // rating 0..5
    if (m <= 100) return Math.round(m); // percentage
    return null;
  };

  const userRating = movie.vote_average ? Math.round(movie.vote_average / 2) : 0;

  const matchPercentage =
    movie.match ??
    normalizeMatch(movie.predicted_rating) ??
    normalizeMatch(movie.confidence_score) ??
    normalizeMatch(movie.recommendation_score) ??
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
        <div className="text-white text-xl">{t('hero.loading')}</div>
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
          <img src={movie.poster_url} alt={localizedTitle} className="size-full object-cover" />
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
                {t('hero.recommendedBadge')}
              </span>
            )}
            {localizedGenres.map(genre => (
              <span
                key={genre.id || genre.name}
                className="rounded-full bg-gray-800/80 px-3 py-1 text-xs font-medium text-white shadow-lg backdrop-blur-sm"
              >
                {genre.name}
              </span>
            ))}
          </div>

          {/* Title */}
          <h1 className="mb-2 max-w-2xl break-words text-6xl font-bold text-white drop-shadow-lg">
            {localizedTitle}
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
            {localizedOverview}
          </p>

          {/* Action Buttons */}
          <div className="mt-6 flex flex-wrap gap-4">
            <button
              onClick={handleViewDetails}
              className="rounded-sm bg-red-600 px-6 py-2 font-semibold text-white shadow-lg transition hover:bg-red-700"
            >
              {t('hero.viewDetails')}
            </button>
            <button
              onClick={handleWhyRecommended}
              className="rounded-sm bg-white/10 px-6 py-2 font-semibold text-white shadow-lg backdrop-blur-sm transition hover:bg-white/20"
            >
              {t('hero.whyRecommended')}
            </button>
          </div>

          {/* Recommendation Debug Info (only in development) */}
          {process.env.NODE_ENV === 'development' && heroBannerMovie && (
            <div className="mt-4 text-xs text-gray-400">
              Recommendation Type: {movie.recommendationType || 'personalized'} | Rank:{' '}
              {movie.rank || 1} | Confidence:{' '}
              {Math.round((movie.confidence_score || 0) * 100) || 'N/A'}%
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

export default HeroBannerRecommendation;
