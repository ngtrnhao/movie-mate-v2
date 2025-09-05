import { motion } from 'framer-motion';
import { Play, Bookmark } from 'lucide-react';
import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { getBackdropUrl, getPosterUrl } from '../../../utils/imageUtils';
import { getDisplayTitle, getDisplayOverview } from '../../../utils/titleUtils';

const InfoSection = ({ movie }) => {
  const { t, i18n } = useTranslation('movies');

  if (!movie) return null;

  // Get rating info
  const getRating = () => {
    if (movie.cached_imdb_rating) return parseFloat(movie.cached_imdb_rating);
    if (movie.imdb_rating) return parseFloat(movie.imdb_rating);
    if (movie.cached_tmdb_rating) return parseFloat(movie.cached_tmdb_rating);
    if (movie.tmdb_rating) return parseFloat(movie.tmdb_rating);
    if (movie.vote_average) return parseFloat(movie.vote_average);
    return 0;
  };

  // Get genre names
  const getGenres = () => {
    if (movie.genres) return movie.genres;
    return [];
  };

  // Get trailer URL
  const getTrailerUrl = () => {
    if (movie.trailerUrl) return movie.trailerUrl;
    if (movie.trailers && movie.trailers.length > 0) {
      const trailer = movie.trailers.find(t => t.type === 'TRAILER') || movie.trailers[0];
      return `https://www.youtube.com/watch?v=${trailer.youtube_key}`;
    }
    return null;
  };

  const title = getDisplayTitle(movie, i18n.language);
  const overview = getDisplayOverview(movie, i18n.language);

  return (
    <div className="relative h-[90vh] w-full overflow-hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat"
        style={{
          backgroundImage: `url(${getBackdropUrl(movie)})`,
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
      ></div>
      {/* Overlay làm tối */}
      <div className="absolute inset-0 z-10 bg-black/20"></div>
      {/* Dot Grid Overlay */}
      <div className="bg-dot-grid absolute inset-0 z-20"></div>

      {/* Content */}
      <div className="absolute inset-x-0 bottom-20 z-30 pr-36">
        <div className="container mx-auto">
          <div className="flex gap-8">
            {/* Poster */}
            <motion.img
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              src={getPosterUrl(movie)}
              alt={title}
              className="h-[400px] w-[266px] rounded-lg shadow-2xl"
              onError={e => {
                e.target.src = 'https://via.placeholder.com/266x400?text=No+Image';
              }}
            />

            {/* Info */}
            <div className="flex-1 text-white">
              <h1 className="text-4xl font-bold">{title}</h1>
              <div className="mt-2 flex items-center gap-4">
                {movie.release_date && (
                  <>
                    <span>{new Date(movie.release_date).getFullYear()}</span>
                    <span>•</span>
                  </>
                )}
                {movie.runtime && (
                  <>
                    <span>{movie.runtime} min</span>
                    <span>•</span>
                  </>
                )}
                <div className="flex items-center">
                  <span className="text-yellow-400">★</span>
                  <span className="ml-1">{getRating().toFixed(1)}</span>
                </div>
              </div>

              {/* Genres */}
              {getGenres().length > 0 && (
                <div className="mt-4 flex gap-2">
                  {getGenres().map(genre => (
                    <span
                      key={genre.id || genre.name}
                      className="rounded-full bg-red-700/20 px-3 py-1 text-sm text-red-400"
                    >
                      {genre.name}
                    </span>
                  ))}
                </div>
              )}

              {/* Overview */}
              {overview && <p className="mt-6 text-lg text-gray-300">{overview}</p>}

              {/* Actions */}
              <div className="mt-8 flex gap-4">
                {getTrailerUrl() && (
                  <button
                    onClick={() => window.open(getTrailerUrl(), '_blank')}
                    className="flex items-center gap-2 rounded-md bg-red-600 px-6 py-3 text-white hover:bg-red-700"
                  >
                    <Play className="size-5" />
                    {t('watch_trailer')}
                  </button>
                )}
                <button className="flex items-center gap-2 rounded-md border border-white/20 px-6 py-3 text-white hover:bg-white/10">
                  <Bookmark className="size-5" />
                  {t('add_to_watchlist')}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* Movie Info Overlay */}
    </div>
  );
};

export default InfoSection;
