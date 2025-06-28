import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { Bookmark, Play } from 'lucide-react';

const Actions = ({ movie, onlyMainButton, onlyBookmark, onTrailerClick }) => {
  const { t } = useTranslation('movies');

  const handleTrailerClick = e => {
    if (e && e.preventDefault) {
      e.preventDefault();
    }
    if (onTrailerClick && movie) {
      onTrailerClick(movie);
    }
  };

  return (
    <div className="flex items-center gap-2">
      {/* Watch Trailer Button */}
      {!onlyBookmark && (
        <button
          onClick={handleTrailerClick}
          className="flex flex-1 items-center justify-center gap-2 rounded bg-red-600 px-4 py-2 text-xs font-semibold text-white shadow transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={!movie?.trailers?.length}
          title={movie?.trailers?.length ? t('details.watchTrailer') : t('details.noTrailer')}
        >
          <Play size={16} />
          {t('details.watchTrailer')}
        </button>
      )}
      {/* Add to Watchlist Button */}
      {!onlyMainButton && (
        <button
          className="flex items-center justify-center rounded border border-gray-600 p-2 text-gray-400 transition-colors hover:border-red-600 hover:text-red-600"
          title={t('details.addToWatchlist')}
        >
          <Bookmark size={16} />
        </button>
      )}
    </div>
  );
};

export default Actions;
