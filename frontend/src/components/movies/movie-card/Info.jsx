import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { memo, useMemo } from 'react';

const Info = memo(
  ({
    title,
    originalTitle,
    releaseDate,
    runtime,
    overview,
    genres,
    isPopular,
    isTopRated,
    isUpcoming,
  }) => {
    const { t, currentLanguage } = useTranslation('movies');

    // Filter genres by current language
    const filteredGenres = useMemo(() => {
      if (!genres) return [];
      return genres.filter(genre => genre.language === currentLanguage || !genre.language);
    }, [genres, currentLanguage]);

    // Memoize computed values
    const year = useMemo(
      () => (releaseDate ? new Date(releaseDate).getFullYear() : 'N/A'),
      [releaseDate]
    );

    const formatRuntime = useMemo(() => {
      if (!runtime) return null;
      const hours = Math.floor(runtime / 60);
      const minutes = runtime % 60;
      if (hours > 0) {
        return `${hours}h ${minutes}m`;
      }
      return `${minutes}m`;
    }, [runtime]);

    return (
      <div className="flex flex-col gap-2">
        {/* Title and Year/Runtime */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex flex-col">
            <h3 className="line-clamp-2 text-lg font-semibold text-white">{title}</h3>
            {originalTitle && originalTitle !== title && (
              <span className="text-sm text-gray-400">{originalTitle}</span>
            )}
          </div>
          <div className="flex shrink-0 flex-col items-end gap-1">
            <span className="text-sm text-gray-400">{year}</span>
            {formatRuntime && <span className="text-xs text-gray-500">{formatRuntime}</span>}
          </div>
        </div>

        {/* Status Badges */}
        <div className="flex flex-wrap gap-1">
          {isPopular && (
            <span className="rounded-full bg-blue-500/20 px-2 py-0.5 text-xs text-blue-400">
              {t('badge.popular')}
            </span>
          )}
          {isTopRated && (
            <span className="rounded-full bg-yellow-500/20 px-2 py-0.5 text-xs text-yellow-400">
              {t('badge.topRated')}
            </span>
          )}
          {isUpcoming && (
            <span className="rounded-full bg-green-500/20 px-2 py-0.5 text-xs text-green-400">
              {t('badge.upcoming')}
            </span>
          )}
        </div>

        {/* Overview */}
        {overview && <p className="line-clamp-2 text-sm text-gray-300">{overview}</p>}

        {/* Genres */}
        {filteredGenres.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {filteredGenres.slice(0, 2).map(genre => (
              <span
                key={genre.id}
                className="rounded-full bg-gray-700 px-2 py-0.5 text-xs text-gray-300"
              >
                {genre.name}
              </span>
            ))}
            {filteredGenres.length > 2 && (
              <span className="text-xs text-gray-400">+{filteredGenres.length - 2}</span>
            )}
          </div>
        )}
      </div>
    );
  }
);

Info.displayName = 'Info';

export default Info;
