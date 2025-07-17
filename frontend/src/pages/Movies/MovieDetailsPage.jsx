import { useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import {
  getMovieDetails,
  getMovieCast,
  getSimilarMovies,
  getMovieDetailsComplete,
  getMovieDetailsParallel,
} from '../../api/movieService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { getPrimaryRating, getRatingBadgeColors } from '../../utils/ratingUtils';
import { getDisplayTitle, getDisplayOverview } from '../../utils/titleUtils';
import { useTranslation } from '../../i18n/hooks/useTranslation';
import useUserTracking from '../../hooks/useUserTracking';

import HeroSection from './components/HeroSection';
import MainContent from './components/MainContent';
import ActionPanel from './components/ActionPanel';
import MovieTrailerModal from '../../components/movies/movie-trailer/MovieTrailerModal';

const MovieDetailsPage = () => {
  const { movieId } = useParams();
  const { currentLanguage, t } = useTranslation('movies');
  const { trackDetailView } = useUserTracking();
  const [movie, setMovie] = useState(null);
  const [cast, setCast] = useState([]);
  const [similarMovies, setSimilarMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isLoadingCast, setIsLoadingCast] = useState(false);
  const [castError, setCastError] = useState(null);
  const [showTrailer, setShowTrailer] = useState(false);
  const [currentTrailerUrl, setCurrentTrailerUrl] = useState(null);

  // Track movie details page view
  useEffect(() => {
    if (movieId) {
      trackDetailView(parseInt(movieId), {
        page: 'movie_details',
        timestamp: new Date().toISOString(),
      });
    }
  }, [movieId, trackDetailView]);

  // Filter genres by current language
  const filteredGenres =
    movie?.genres?.filter(genre => genre.language === currentLanguage || !genre.language) || [];

  useEffect(() => {
    const fetchMovieData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Try optimized consolidated API first
        try {
          const optimizedData = await getMovieDetailsComplete(movieId);

          if (optimizedData?.movie) {
            setMovie(optimizedData.movie);
            setCast(optimizedData.cast || []);
            setSimilarMovies(optimizedData.similarMovies || []);
            setLoading(false);
            return; // Success! Exit early
          }
        } catch (optimizedError) {
          console.log('⚠️ Optimized API failed, trying parallel approach...', optimizedError);
        }

        // Fallback: Try parallel loading
        try {
          const parallelData = await getMovieDetailsParallel(movieId);

          if (parallelData?.movie) {
            setMovie(parallelData.movie);
            setCast(parallelData.cast || []);
            setSimilarMovies(parallelData.similarMovies || []);
            setLoading(false);
            return; // Success! Exit early
          }
        } catch (parallelError) {
          console.log('⚠️ Parallel API failed, trying sequential approach...', parallelError);
        }

        // Final fallback: Sequential loading (original approach)

        // Fetch movie details
        const movieData = await getMovieDetails(movieId);
        setMovie(movieData?.data || movieData);

        // Fetch movie cast
        setIsLoadingCast(true);
        setCastError(null);
        try {
          const castData = await getMovieCast(movieId);
          setCast(castData?.data || []);
        } catch (castError) {
          console.error('Error fetching cast:', castError);
          setCastError(t('details.cannotLoadCast'));
          setCast([]);
        } finally {
          setIsLoadingCast(false);
        }

        // Fetch similar movies based on genres
        if (movieData?.data?.genres?.length || movieData?.genres?.length) {
          try {
            const allGenres = movieData?.data?.genres || movieData?.genres || [];
            // Filter genres by current language for similar movies
            const filteredGenresForSimilar = allGenres.filter(
              genre => genre.language === currentLanguage || !genre.language
            );
            const similarData = await getSimilarMovies(movieId, filteredGenresForSimilar, 6);

            // Handle both response formats
            const similarResults = similarData?.results || similarData?.data || similarData || [];
            setSimilarMovies(similarResults);
          } catch (similarError) {
            console.error('Error fetching similar movies:', similarError);
            setSimilarMovies([]);
          }
        }
      } catch (err) {
        console.error('Error fetching movie details:', err);
        setError(err.error || 'Movies Not Found!');
      } finally {
        setLoading(false);
      }
    };

    if (movieId) {
      fetchMovieData();
    }
  }, [movieId, currentLanguage, t]);

  const handleTrailerClick = movie => {
    // Get trailer URL from movie object
    const trailers = movie?.trailers || [];
    const trailer = trailers.find(t => t.type === 'TRAILER') || trailers[0];
    const trailerUrl = trailer?.youtube_key
      ? `https://www.youtube.com/watch?v=${trailer.youtube_key}`
      : null;

    setCurrentTrailerUrl(trailerUrl);
    setShowTrailer(true);
  };

  const handleCloseTrailer = () => {
    setShowTrailer(false);
    setCurrentTrailerUrl(null);
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-900">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-900">
        <div className="text-center text-white">
          <h2 className="mb-2 text-2xl font-bold">{t('details.error')}</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!movie) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-900">
        <div className="text-center text-white">
          <h2 className="mb-2 text-2xl font-bold">{t('details.notFound')}</h2>
          <p>{t('details.notFoundDesc')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Hero Section - Backdrop Only */}
      <HeroSection movie={movie} />

      {/* Movie Info and Main Content Section */}
      <div className="relative w-full px-2 pb-8 pt-0 sm:px-4 md:px-6 lg:px-8">
        {/* Gradient overlay từ section lên backdrop */}
        <div
          className="pointer-events-none absolute inset-x-0 top-0 z-10 h-16 sm:h-24 md:h-32"
          style={{
            background:
              'linear-gradient(0deg, #18181b 0%, rgba(24,24,27,0.9) 40%, rgba(24,24,27,0.3) 70%, rgba(24,24,27,0.0) 100%)',
          }}
        />

        {/* Responsive Grid Layout */}
        <div className="relative z-20 grid grid-cols-1 gap-4 sm:gap-6 lg:grid-cols-3 xl:gap-8">
          {/* Left Side: Movie Info Card - Responsive Layout */}
          <div className="order-2 lg:order-1 lg:col-span-1">
            <div className="mx-auto max-w-sm space-y-4 rounded-lg bg-gray-800/50 p-4 text-white backdrop-blur-sm sm:max-w-md sm:p-6 lg:mx-0 lg:max-w-none">
              {/* Poster - Responsive sizing */}
              <div className="relative mx-auto w-48 sm:w-56 md:w-64 lg:w-full">
                <img
                  src={movie.poster_url || movie.poster_path}
                  alt={movie.title}
                  className="w-full rounded-lg object-cover shadow-2xl"
                  onError={e => {
                    e.target.src = 'https://via.placeholder.com/266x400?text=No+Image';
                  }}
                />
                <div className="absolute inset-0 rounded-lg bg-gradient-to-t from-black/50 to-transparent"></div>
              </div>

              {/* Movie Details - Responsive text sizing */}
              <div className="space-y-3">
                {/* Title - Responsive font sizes */}
                <div>
                  <h1 className="mb-1 text-xl font-bold sm:text-2xl lg:text-2xl">
                    {getDisplayTitle(movie, currentLanguage)}
                  </h1>
                  {/* Show alternative title if different from main title */}
                  {currentLanguage === 'vi' &&
                    movie.original_title &&
                    movie.original_title !== movie.title_vi && (
                      <h2 className="text-xs italic text-gray-300 sm:text-sm">
                        {movie.original_title}
                      </h2>
                    )}
                  {currentLanguage === 'en' &&
                    movie.original_title &&
                    movie.original_title !== movie.title_en && (
                      <h2 className="text-xs italic text-gray-300 sm:text-sm">
                        {movie.original_title}
                      </h2>
                    )}
                </div>

                {/* Quick Info Badges - Responsive flex layout */}
                <div className="flex flex-wrap gap-1 sm:gap-2">
                  {/* Rating Badge - Using Shared Rating Utility */}
                  {(() => {
                    const ratingInfo = getPrimaryRating(movie);
                    if (!ratingInfo) return null;

                    const colors = getRatingBadgeColors(ratingInfo.source);
                    return (
                      <div
                        className={`flex items-center gap-1 rounded-md px-2 py-1 text-xs font-bold ${colors.bg} ${colors.text}`}
                      >
                        <span>{ratingInfo.source}</span>
                        <span>{ratingInfo.value.toFixed(1)}</span>
                      </div>
                    );
                  })()}

                  {/* Age Rating Badge */}
                  {movie.is_adult !== undefined && (
                    <div className="rounded-full bg-white px-2 py-1 text-xs font-bold text-black sm:px-3">
                      {movie.is_adult ? t('details.age18') : t('details.age16')}
                    </div>
                  )}

                  {/* Year Badge */}
                  {movie.release_date && (
                    <div className="rounded-full bg-gray-600 px-2 py-1 text-xs font-semibold text-white sm:px-3">
                      {new Date(movie.release_date).getFullYear()}
                    </div>
                  )}

                  {/* Runtime Badge */}
                  {movie.runtime && (
                    <div className="flex items-center gap-1 rounded-full bg-blue-500 px-2 py-1 text-xs font-semibold text-white sm:px-3">
                      <span>🕐</span>
                      <span>
                        {Math.floor(movie.runtime / 60)}h {movie.runtime % 60}m
                      </span>
                    </div>
                  )}
                </div>

                {/* Detailed Information - Responsive layout */}
                <div className="space-y-2 text-xs sm:space-y-3 sm:text-sm">
                  {/* Thời lượng */}
                  {movie.runtime && (
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-300">{t('details.duration')}:</span>
                      <span className="text-white">
                        {Math.floor(movie.runtime / 60)}h {movie.runtime % 60}m
                      </span>
                    </div>
                  )}

                  {/* Quốc gia */}
                  {(movie.production_info?.production_countries?.length > 0 ||
                    movie.production_countries?.length > 0) && (
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-300">{t('details.country')}:</span>
                      <span className="max-w-24 text-right text-white sm:max-w-32">
                        {movie.production_info?.production_countries?.[0]?.name ||
                          movie.production_info?.production_countries?.[0] ||
                          movie.production_countries?.[0]?.name ||
                          movie.production_countries?.[0]}
                      </span>
                    </div>
                  )}

                  {/* Ngôn ngữ */}
                  {(movie.original_language ||
                    movie.production_info?.spoken_languages?.length > 0) && (
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-300">{t('details.language')}:</span>
                      <span className="uppercase text-white">
                        {movie.original_language ||
                          movie.production_info?.spoken_languages?.[0]?.name ||
                          movie.production_info?.spoken_languages?.[0]}
                      </span>
                    </div>
                  )}

                  {/* Trạng thái */}
                  {movie.status && (
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-300">{t('details.status')}:</span>
                      <span className="text-white">
                        {movie.status === 'Released'
                          ? t('details.released')
                          : movie.status === 'In Production'
                            ? t('details.inProduction')
                            : movie.status === 'Post Production'
                              ? t('details.postProduction')
                              : movie.status}
                      </span>
                    </div>
                  )}

                  {/* Sản xuất */}
                  {(movie.production_info?.production_companies?.length > 0 ||
                    movie.production_companies?.length > 0) && (
                    <div className="flex items-start justify-between">
                      <span className="font-medium text-gray-300">{t('details.production')}:</span>
                      <span className="max-w-24 text-right text-white sm:max-w-32">
                        {(
                          movie.production_info?.production_companies ||
                          movie.production_companies ||
                          []
                        )
                          .slice(0, 2)
                          .map(company => company.name || company)
                          .join(', ')}
                      </span>
                    </div>
                  )}

                  {/* Đạo diễn */}
                  {movie.directors && movie.directors.length > 0 && (
                    <div className="flex items-start justify-between">
                      <span className="font-medium text-gray-300">{t('details.directors')}:</span>
                      <span className="max-w-24 text-right text-white sm:max-w-32">
                        {movie.directors
                          .slice(0, 2)
                          .map(director => director.name || director)
                          .join(', ')}
                      </span>
                    </div>
                  )}
                </div>

                {/* Genres - Responsive flex layout */}
                {filteredGenres.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {filteredGenres.slice(0, 3).map((genre, index) => (
                      <span
                        key={index}
                        className="rounded bg-white/20 px-2 py-1 text-xs font-medium backdrop-blur-sm"
                      >
                        {genre.name || genre}
                      </span>
                    ))}
                  </div>
                )}

                {/* Overview - Responsive text sizing */}
                {(movie.overview_vi || movie.overview_en || movie.overview) && (
                  <p className="text-xs leading-relaxed text-gray-200 sm:text-sm">
                    {getDisplayOverview(movie, currentLanguage)}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Right Side: Main Content Card - Responsive Layout */}
          <div className="order-1 lg:order-2 lg:col-span-2">
            <div className="space-y-4 rounded-lg bg-gray-800/50 p-4 backdrop-blur-sm sm:p-6 lg:mr-8">
              {/* Action Buttons at the top - Responsive layout */}
              <ActionPanel movie={movie} onTrailerClick={handleTrailerClick} />

              {/* Main Content with filtered tabs - Responsive spacing */}
              <MainContent
                movie={movie}
                cast={cast}
                similarMovies={similarMovies}
                isLoadingCast={isLoadingCast}
                castError={castError}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Movie Trailer Modal */}
      <MovieTrailerModal
        isOpen={showTrailer}
        onClose={handleCloseTrailer}
        movie={movie}
        trailerUrl={currentTrailerUrl}
      />

      {/* Debug Panel - Development Only
      {process.env.NODE_ENV === 'development' && (
        <FavoritesDebugPanel movieId={parseInt(movieId)} movieData={movie} />
      )} */}
    </div>
  );
};

export default MovieDetailsPage;
