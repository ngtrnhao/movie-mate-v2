import { Category, MovieFilter, LocalMovies } from '@mui/icons-material';
import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { useMemo } from 'react';

const GenreList = ({ genres }) => {
  const { currentLanguage } = useTranslation();

  // Filter genres by current language
  const filteredGenres = useMemo(() => {
    if (!genres) return [];
    return genres.filter(genre => genre.language === currentLanguage || !genre.language);
  }, [genres, currentLanguage]);

  if (!filteredGenres || filteredGenres.length === 0) {
    return (
      <div className="rounded-2xl border border-gray-700 bg-gray-800/95 p-6 shadow-xl backdrop-blur-sm">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-full bg-red-600">
            <Category className="text-white" fontSize="small" />
          </div>
          <h3 className="text-xl font-bold text-white">Favorite Genres</h3>
        </div>

        <div className="py-8 text-center">
          <LocalMovies className="mb-4 text-6xl text-gray-500" />
          <p className="text-gray-400">No favorite genres yet</p>
          <p className="mt-2 text-sm text-gray-500">
            Rate some movies to discover your preferences
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-gray-700 bg-gray-800/95 p-6 shadow-xl backdrop-blur-sm">
      <div className="mb-6 flex items-center gap-3">
        <div className="flex size-10 items-center justify-center rounded-full bg-red-600">
          <MovieFilter className="text-white" fontSize="small" />
        </div>
        <h3 className="text-xl font-bold text-white">Favorite Genres</h3>
      </div>

      <div className="flex flex-wrap gap-2">
        {filteredGenres.map((genre, _index) => (
          <span
            key={genre.id}
            className="rounded-full border border-red-600/30 bg-red-600/10 px-4 py-2 text-sm font-medium text-red-400 transition-all duration-200 hover:bg-red-600/20 hover:text-red-300"
          >
            {genre.name}
            {genre.count && <span className="ml-1 text-red-500">({genre.count})</span>}
          </span>
        ))}
      </div>

      {filteredGenres.length > 6 && (
        <div className="mt-4 text-center">
          <p className="text-sm text-gray-500">{filteredGenres.length} genres total</p>
        </div>
      )}
    </div>
  );
};

export default GenreList;
