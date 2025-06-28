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

  const handleTrailerClick = (movie, trailerUrl) => {
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
      <div className="w-full px-4 pt-0 pb-8 relative">
        {/* Gradient overlay từ section lên backdrop */}
        <div
          className="absolute top-0 left-0 right-0 h-32 pointer-events-none z-10"
          style={{
            background:
              'linear-gradient(0deg, #18181b 0%, rgba(24,24,27,0.9) 40%, rgba(24,24,27,0.3) 70%, rgba(24,24,27,0.0) 100%)',
          }}
        />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 relative z-20">
          {/* Left Side: Movie Info Card (1/4 width) */}
          <div className="lg:col-span-1 ml-4">
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg p-6 text-white space-y-4">
              {/* Poster */}
              <div className="relative">
                <img
                  src={movie.poster_url || movie.poster_path}
                  alt={movie.title}
                  className="w-full object-cover rounded-lg shadow-2xl"
                  onError={e => {
                    e.target.src = 'https://via.placeholder.com/266x400?text=No+Image';
                  }}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent rounded-lg"></div>
              </div>

              {/* Movie Details */}
              <div className="space-y-3">
                {/* Title */}
                <div>
                  <h1 className="text-2xl font-bold mb-1">
                    {movie.title_vi || movie.title || movie.title_en}
                  </h1>
                  {movie.title_en && movie.title_en !== (movie.title_vi || movie.title) && (
                    <h2 className="text-sm text-gray-300 italic">{movie.title_en}</h2>
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
                    <div className="bg-white text-black px-3 py-1 rounded-full text-xs font-bold">
                      {movie.adult ? '18+' : 'T16'}
                    </div>
                  )}

                  {/* Year Badge */}
                  {movie.release_date && (
                    <div className="bg-gray-600 text-white px-3 py-1 rounded-full text-xs font-semibold">
                      {new Date(movie.release_date).getFullYear()}
                    </div>
                  )}

                  {/* Runtime Badge */}
                  {movie.runtime && (
                    <div className="bg-blue-500 text-white px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1">
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
                    <div className="flex justify-between items-center">
                      <span className="text-gray-300 font-medium">Thời lượng:</span>
                      <span className="text-white">
                        {Math.floor(movie.runtime / 60)}h {movie.runtime % 60}m
                      </span>
                    </div>
                  )}

                  {/* Quốc gia */}
                  {(movie.production_info?.production_countries?.length > 0 ||
                    movie.production_countries?.length > 0) && (
                    <div className="flex justify-between items-center">
                      <span className="text-gray-300 font-medium">Quốc gia:</span>
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
                    <div className="flex justify-between items-center">
                      <span className="text-gray-300 font-medium">Ngôn ngữ:</span>
                      <span className="text-white uppercase">
                        {movie.original_language ||
                          movie.production_info?.spoken_languages?.[0]?.name ||
                          movie.production_info?.spoken_languages?.[0]}
                      </span>
                    </div>
                  )}

                  {/* Trạng thái */}
                  {movie.status && (
                    <div className="flex justify-between items-center">
                      <span className="text-gray-300 font-medium">Trạng thái:</span>
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
                    <div className="flex justify-between items-start">
                      <span className="text-gray-300 font-medium">Sản xuất:</span>
                      <span className="text-white text-right max-w-32">
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
                    <div className="flex justify-between items-start">
                      <span className="text-gray-300 font-medium">Đạo diễn:</span>
                      <span className="text-white text-right max-w-32">
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
                        className="px-2 py-1 bg-white/20 backdrop-blur-sm rounded text-xs font-medium"
                      >
                        {genre.name || genre}
                      </span>
                    ))}
                  </div>
                )}

                {/* Overview */}
                {(movie.overview_vi || movie.overview_en || movie.overview) && (
                  <p className="text-sm leading-relaxed text-gray-200 line-clamp-4">
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
