// import { useTranslation } from '../../../i18n/hooks/useTranslation';

const Info = ({ title, releaseDate, overview, genres }) => {
  // const { t } = useTranslation('movies');
  const year = releaseDate ? new Date(releaseDate).getFullYear() : 'N/A';

  return (
    <div className="flex flex-col gap-2">
      {/* Title and Year */}
      <div className="flex items-start justify-between gap-2">
        <h3 className="line-clamp-2 text-lg font-semibold text-white">{title}</h3>
        <span className="shrink-0 text-sm text-gray-400">{year}</span>
      </div>

      {/* Overview */}
      {overview && <p className="line-clamp-2 text-sm text-gray-300">{overview}</p>}

      {/* Genres */}
      {genres && genres.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {genres.slice(0, 2).map((genre) => (
            <span
              key={genre}
              className="rounded-full bg-gray-700 px-2 py-0.5 text-xs text-gray-300"
            >
              {genre}
            </span>
          ))}
          {genres.length > 2 && <span className="text-xs text-gray-400">+{genres.length - 2}</span>}
        </div>
      )}
    </div>
  );
};

export default Info;
