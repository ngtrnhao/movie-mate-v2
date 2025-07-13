import { useState, useEffect } from 'react';
import { getBackdropUrl } from '../../../utils/imageUtils';
import { useNavigate } from 'react-router-dom';

const HeroSection = ({ movie }) => {
  const [showTrailer, setShowTrailer] = useState(false);
  const [isLiked, setIsLiked] = useState(false);
  const [isInWatchlist, setIsInWatchlist] = useState(false);
  const navigate = useNavigate();

  // Log backdrop URL information
  useEffect(() => {
    if (movie) {
      console.log('Backdrop URL Debug:');
      console.log('movie.backdrop_url:', movie.backdrop_url);
      console.log('movie.backdrop_path:', movie.backdrop_path);
      console.log('movie.poster_url:', movie.poster_url);
      console.log('Final backdrop URL:', getBackdropUrl(movie));
    }
  }, [movie]);

  if (!movie) return null;

  // const releaseYear = movie.release_date ? new Date(movie.release_date).getFullYear() : 'TBA';
  // const runtime = movie.runtime ? `${movie.runtime} phút` : '';
  // const rating = movie.vote_average || movie.rating?.imdb || 0;
  // const genres = movie.genres || [];
  // const trailers = movie.trailers || [];

  // const handleWatchTrailer = () => {
  //   if (trailers.length > 0) {
  //     setShowTrailer(true);
  //   }
  // };

  // const handleToggleLike = () => {
  //   setIsLiked(!isLiked);
  //   // TODO: Implement API call to add/remove from favorites
  // };

  // const handleToggleWatchlist = () => {
  //   setIsInWatchlist(!isInWatchlist);
  //   // TODO: Implement API call to add/remove from watchlist
  // };

  // const handleBack = e => {
  //   e.preventDefault();
  //   navigate(-1, { replace: true });
  // };

  return (
    <>
      {/* Backdrop Only - Responsive height */}
      <div className="relative h-[60vh] w-full overflow-hidden sm:h-[70vh] md:h-[80vh] lg:h-[90vh]">
        <div
          className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat"
          style={{
            backgroundImage: `url(${getBackdropUrl(movie)})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center center',
            backgroundRepeat: 'no-repeat',
          }}
        />

        {/* Gradient phủ hai bên - Responsive */}
        <div
          className="pointer-events-none absolute inset-0 z-20"
          style={{
            background:
              'linear-gradient(90deg, #18181b 0%, rgba(24,24,27,0.0) 20%, rgba(24,24,27,0.0) 80%, #18181b 100%)',
          }}
        />

        {/* Gradient từ trên xuống dưới - kết nối với section - Responsive */}
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
      {/* {showTrailer && trailers.length > 0 && (
        <MovieTrailerModal
          isOpen={showTrailer}
          onClose={() => setShowTrailer(false)}
          trailers={trailers}
        />
      )} */}
    </>
  );
};

export default HeroSection;
