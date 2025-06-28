import { useState } from 'react';
import MovieTrailerModal from '../../../components/movies/movie-trailer/MovieTrailerModal';

const TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/original';

const HeroSection = ({ movie }) => {
  const [showTrailer, setShowTrailer] = useState(false);
  const [isLiked, setIsLiked] = useState(false);
  const [isInWatchlist, setIsInWatchlist] = useState(false);

  if (!movie) return null;

  // Handle different image URL formats (same as InfoSection)
  const getImageUrl = path => {
    if (!path) return null;
    if (path.startsWith('http')) return path;
    return `${TMDB_IMAGE_BASE_URL}${path}`;
  };

  const releaseYear = movie.release_date ? new Date(movie.release_date).getFullYear() : 'TBA';
  const runtime = movie.runtime ? `${movie.runtime} phút` : '';
  const rating = movie.vote_average || movie.rating?.imdb || 0;
  const genres = movie.genres || [];
  const trailers = movie.trailers || [];

  const handleWatchTrailer = () => {
    if (trailers.length > 0) {
      setShowTrailer(true);
    }
  };

  const handleToggleLike = () => {
    setIsLiked(!isLiked);
    // TODO: Implement API call to add/remove from favorites
  };

  const handleToggleWatchlist = () => {
    setIsInWatchlist(!isInWatchlist);
    // TODO: Implement API call to add/remove from watchlist
  };

  return (
    <>
      {/* Backdrop Only */}
      <div className="relative h-[90vh] w-full overflow-hidden">
        <div
          className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat"
          style={{
            backgroundImage: `url(${getImageUrl(
              movie.backdrop_url || movie.backdrop_path || movie.poster_url
            )})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center center',
            backgroundRepeat: 'no-repeat',
          }}
        />

        {/* Gradient phủ hai bên */}
        <div
          className="pointer-events-none absolute inset-0 z-20"
          style={{
            background:
              'linear-gradient(90deg, #18181b 0%, rgba(24,24,27,0.0) 20%, rgba(24,24,27,0.0) 80%, #18181b 100%)',
          }}
        />

        {/* Gradient từ trên xuống dưới - kết nối với section */}
        <div
          className="pointer-events-none absolute inset-0 z-30"
          style={{
            background:
              'linear-gradient(180deg, rgba(24,24,27,0.0) 0%, rgba(24,24,27,0.1) 60%, rgba(24,24,27,0.7) 85%, #18181b 100%)',
          }}
        />

        {/* Overlay làm tối */}
        <div className="absolute inset-0 z-10 bg-gray-900/20"></div>

        {/* Dot Grid Overlay */}
        <div className="bg-dot-grid absolute inset-0 z-20"></div>
      </div>

      {/* Trailer Modal */}
      {showTrailer && trailers.length > 0 && (
        <MovieTrailerModal
          isOpen={showTrailer}
          onClose={() => setShowTrailer(false)}
          trailers={trailers}
        />
      )}
    </>
  );
};

export default HeroSection;
