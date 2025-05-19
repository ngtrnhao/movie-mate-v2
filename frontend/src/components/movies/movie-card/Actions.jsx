import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { Link } from 'react-router-dom';
import { Bookmark, Play } from 'lucide-react';

const Actions = ({ movieId, onlyMainButton, onlyBookmark }) => {
  const { t } = useTranslation('movies');

  return (
    <div className="flex items-center gap-2">
      {/* Watch Trailer Button */}
      {!onlyBookmark && (
        <Link
          to={`/movie/${movieId}`}
          className="flex flex-1 items-center justify-center gap-2 rounded bg-red-600 px-4 py-2 text-xs font-semibold text-white shadow transition hover:bg-red-700"
        >
          <Play size={16} />
          {t('details.watchTrailer')}
        </Link>
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
