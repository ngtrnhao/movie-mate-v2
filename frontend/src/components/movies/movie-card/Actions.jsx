import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { Link } from 'react-router-dom';
import { Bookmark, Play } from 'lucide-react';

const Actions = ({ movieId }) => {
  const { t } = useTranslation('movies');

  return (
    <div className="mt-4 flex items-center gap-2">
      {/* Watch Trailer Button */}
      <Link
        to={`/movie/${movieId}`}
        className="flex flex-1 items-center justify-center gap-2 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700"
      >
        <Play size={16} />
        {t('details.watchTrailer')}
      </Link>

      {/* Add to Watchlist Button */}
      <button
        className="flex items-center justify-center rounded-md border border-gray-600 p-2 text-gray-400 transition-colors hover:border-red-600 hover:text-red-600"
        title={t('details.addToWatchlist')}
      >
        <Bookmark size={16} />
      </button>
    </div>
  );
};

export default Actions;
