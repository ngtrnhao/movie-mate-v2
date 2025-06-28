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

// Import existing components
import HeroSection from './components/HeroSection';
import MainContent from './components/MainContent';
import ActionPanel from './components/ActionPanel';
import MovieTrailerModal from '../../components/movies/movie-trailer/MovieTrailerModal';

const MovieDetailsPage = () => {
  const { movieId } = useParams();
  const [movie, setMovie] = useState(null);
  const [cast, setCast] = useState([]);
  const [similarMovies, setSimilarMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isLoadingCast, setIsLoadingCast] = useState(false);
  const [castError, setCastError] = useState(null);
  const [showTrailer, setShowTrailer] = useState(false);
  const [currentTrailerUrl, setCurrentTrailerUrl] = useState(null);

  useEffect(() => {
    const fetchMovieData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Try optimized consolidated API first
        try {
          console.log('🚀 Trying optimized API...');
          const optimizedData = await getMovieDetailsComplete(movieId);

          if (optimizedData?.movie) {
            console.log('✅ Optimized API success:', optimizedData);
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
          console.log('🔄 Trying parallel API...');
          const parallelData = await getMovieDetailsParallel(movieId);

          if (parallelData?.movie) {
            console.log('✅ Parallel API success:', parallelData);
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
        console.log('🐌 Using sequential API calls...');

        // Fetch movie details
        const movieData = await getMovieDetails(movieId);
        console.log('Movie data:', movieData);
        setMovie(movieData?.data || movieData);

        // Fetch movie cast
        setIsLoadingCast(true);
        setCastError(null);
        try {
          const castData = await getMovieCast(movieId);
          console.log('Cast data:', castData);
          setCast(castData?.data || []);
        } catch (castError) {
          console.error('Error fetching cast:', castError);
          setCastError('Không thể tải thông tin diễn viên');
          setCast([]);
        } finally {
          setIsLoadingCast(false);
        }

        // Fetch similar movies based on genres
        if (movieData?.data?.genres?.length || movieData?.genres?.length) {
          try {
            const genres = movieData?.data?.genres || movieData?.genres || [];
            const similarData = await getSimilarMovies(movieId, genres, 6);
            console.log('Similar movies data:', similarData);
            setSimilarMovies(similarData?.results || similarData?.data || []);
          } catch (similarError) {
            console.error('Error fetching similar movies:', similarError);
            setSimilarMovies([]);
          }
        }
      } catch (err) {
        console.error('Error fetching movie details:', err);
        setError(err.error || 'Failed to fetch movie details');
      } finally {
        setLoading(false);
      }
    };

    if (movieId) {
      fetchMovieData();
    }
  }, [movieId]);

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
          <h2 className="mb-2 text-2xl font-bold">Error</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!movie) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-900">
        <div className="text-center text-white">
          <h2 className="mb-2 text-2xl font-bold">Movie Not Found</h2>
          <p>The requested movie could not be found.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Hero Section - Backdrop Only */}
      <HeroSection movie={movie} />

      {/* Movie Info and Main Content Section */}
      <div className="relative w-full px-4 pb-8 pt-0">
        {/* Gradient overlay từ section lên backdrop */}
        <div
          className="pointer-events-none absolute inset-x-0 top-0 z-10 h-32"
          style={{
            background:
              'linear-gradient(0deg, #18181b 0%, rgba(24,24,27,0.9) 40%, rgba(24,24,27,0.3) 70%, rgba(24,24,27,0.0) 100%)',
          }}
        />
        <div className="relative z-20 grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Left Side: Movie Info Card (1/4 width) */}
          <div className="ml-4 lg:col-span-1">
            <div className="space-y-4 rounded-lg bg-gray-800/50 p-6 text-white backdrop-blur-sm">
              {/* Poster */}
              <div className="relative">
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

              {/* Movie Details */}
              <div className="space-y-3">
                {/* Title */}
                <div>
                  <h1 className="mb-1 text-2xl font-bold">
                    {movie.title_vi || movie.title || movie.title_en}
                  </h1>
                  {movie.title_en && movie.title_en !== (movie.title_vi || movie.title) && (
                    <h2 className="text-sm italic text-gray-300">{movie.title_en}</h2>
                  )}
                </div>

                {/* Quick Info Badges */}
                <div className="flex flex-wrap gap-2">
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
                  {movie.adult !== undefined && (
                    <div className="rounded-full bg-white px-3 py-1 text-xs font-bold text-black">
                      {movie.adult ? '18+' : 'T16'}
                    </div>
                  )}

                  {/* Year Badge */}
                  {movie.release_date && (
                    <div className="rounded-full bg-gray-600 px-3 py-1 text-xs font-semibold text-white">
                      {new Date(movie.release_date).getFullYear()}
                    </div>
                  )}

                  {/* Runtime Badge */}
                  {movie.runtime && (
                    <div className="flex items-center gap-1 rounded-full bg-blue-500 px-3 py-1 text-xs font-semibold text-white">
                      <span>🕐</span>
                      <span>
                        {Math.floor(movie.runtime / 60)}h {movie.runtime % 60}m
                      </span>
                    </div>
                  )}
                </div>

                {/* Detailed Information */}
                <div className="space-y-3 text-sm">
                  {/* Thời lượng */}
                  {movie.runtime && (
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-300">Thời lượng:</span>
                      <span className="text-white">
                        {Math.floor(movie.runtime / 60)}h {movie.runtime % 60}m
                      </span>
                    </div>
                  )}

                  {/* Quốc gia */}
                  {(movie.production_info?.production_countries?.length > 0 ||
                    movie.production_countries?.length > 0) && (
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-300">Quốc gia:</span>
                      <span className="text-white">
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
                      <span className="font-medium text-gray-300">Ngôn ngữ:</span>
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
                      <span className="font-medium text-gray-300">Trạng thái:</span>
                      <span className="text-white">
                        {movie.status === 'Released'
                          ? 'Đã phát hành'
                          : movie.status === 'In Production'
                            ? 'Đang sản xuất'
                            : movie.status === 'Post Production'
                              ? 'Hậu kỳ'
                              : movie.status}
                      </span>
                    </div>
                  )}

                  {/* Sản xuất */}
                  {(movie.production_info?.production_companies?.length > 0 ||
                    movie.production_companies?.length > 0) && (
                    <div className="flex items-start justify-between">
                      <span className="font-medium text-gray-300">Sản xuất:</span>
                      <span className="max-w-32 text-right text-white">
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
                      <span className="font-medium text-gray-300">Đạo diễn:</span>
                      <span className="max-w-32 text-right text-white">
                        {movie.directors
                          .slice(0, 2)
                          .map(director => director.name || director)
                          .join(', ')}
                      </span>
                    </div>
                  )}
                </div>

                {/* Genres */}
                {movie.genres && movie.genres.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {movie.genres.slice(0, 3).map((genre, index) => (
                      <span
                        key={index}
                        className="rounded bg-white/20 px-2 py-1 text-xs font-medium backdrop-blur-sm"
                      >
                        {genre.name || genre}
                      </span>
                    ))}
                  </div>
                )}

                {/* Overview */}
                {(movie.overview_vi || movie.overview_en || movie.overview) && (
                  <p className="line-clamp-4 text-sm leading-relaxed text-gray-200">
                    {movie.overview_vi || movie.overview_en || movie.overview}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Right Side: Main Content Card (3/4 width) */}
          <div className="lg:col-span-2">
            <div className="mr-8 space-x-2 rounded-lg bg-gray-800/50 p-6 backdrop-blur-sm">
              {/* Action Buttons at the top */}
              <ActionPanel movie={movie} onTrailerClick={handleTrailerClick} />

              {/* Main Content with filtered tabs */}
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
    </div>
  );
};

export default MovieDetailsPage;
