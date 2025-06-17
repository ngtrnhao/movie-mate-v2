// import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { memo, useMemo } from 'react';

const Info = memo(
  ({ title, originalTitle, releaseDate, overview, genres, isPopular, isTopRated, isUpcoming }) => {
    // const { t } = useTranslation('movies');
    // Memoize computed values
    const year = useMemo(
      () => (releaseDate ? new Date(releaseDate).getFullYear() : 'N/A'),
      [releaseDate]
    );

    return (
      <div className="flex flex-col gap-2">
        {/* Title and Year */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex flex-col">
            <h3 className="line-clamp-2 text-lg font-semibold text-white">{title}</h3>
            {originalTitle && originalTitle !== title && (
              <span className="text-sm text-gray-400">{originalTitle}</span>
            )}
          </div>
          <span className="shrink-0 text-sm text-gray-400">{year}</span>
        </div>

        {/* Status Badges */}
        <div className="flex flex-wrap gap-1">
          {isPopular && (
            <span className="rounded-full bg-blue-500/20 px-2 py-0.5 text-xs text-blue-400">
              Popular
            </span>
          )}
          {isTopRated && (
            <span className="rounded-full bg-yellow-500/20 px-2 py-0.5 text-xs text-yellow-400">
              Top Rated
            </span>
          )}
          {isUpcoming && (
            <span className="rounded-full bg-green-500/20 px-2 py-0.5 text-xs text-green-400">
              Upcoming
            </span>
          )}
        </div>

        {/* Overview */}
        {overview && <p className="line-clamp-2 text-sm text-gray-300">{overview}</p>}

        {/* Genres */}
        {genres && genres.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {genres.slice(0, 2).map(genre => (
              <span
                key={genre.id}
                className="rounded-full bg-gray-700 px-2 py-0.5 text-xs text-gray-300"
              >
                {genre.name}
              </span>
            ))}
            {genres.length > 2 && (
              <span className="text-xs text-gray-400">+{genres.length - 2}</span>
            )}
          </div>
        )}
      </div>
    );
  }
);

Info.displayName = 'Info';

export default Info;
