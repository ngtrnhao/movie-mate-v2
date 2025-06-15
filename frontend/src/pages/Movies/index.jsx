import { useState } from 'react';
import { useTranslation } from '../../i18n/hooks/useTranslation';
import MovieGrid from '../../components/movies/movie-grid/MovieGrid';
import { motion } from 'framer-motion';
import { SlidersHorizontal, X } from 'lucide-react';

const MoviesPage = () => {
  const { t } = useTranslation('movies');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    genres: [],
    year: '',
    rating: '',
    sortBy: 'popularity',
  });

  const genres = [
    { id: 28, name: 'Action' },
    { id: 35, name: 'Comedy' },
    { id: 18, name: 'Drama' },
    { id: 27, name: 'Horror' },
    { id: 10749, name: 'Romance' },
    { id: 878, name: 'Science Fiction' },
    { id: 53, name: 'Thriller' },
  ];

  const years = Array.from({ length: 30 }, (_, i) => (new Date().getFullYear() - i).toString());
  const ratings = ['9+', '8+', '7+', '6+', '5+'];
  const sortOptions = [
    { value: 'popularity', label: 'Most Popular' },
    { value: 'rating', label: 'Highest Rated' },
    { value: 'release_date', label: 'Newest' },
    { value: 'title', label: 'Title A-Z' },
  ];

  const handleFilterChange = (type, value) => {
    setFilters(prev => ({
      ...prev,
      [type]: value,
    }));
  };

  return (
    <div className="min-h-screen bg-gray-900 py-8 pt-20">
      <div className="container mx-auto px-4">
        {/* Header Section */}
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white">{t('title')}</h1>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 rounded-md bg-red-600 px-4 py-2 text-white transition-colors hover:bg-red-700"
          >
            {showFilters ? <X size={20} /> : <SlidersHorizontal size={20} />}
            {showFilters ? t('hideFilters') : t('showFilters')}
          </motion.button>
        </div>

        {/* Filters Section */}
        <motion.div
          initial={false}
          animate={{ height: showFilters ? 'auto' : 0 }}
          className="mb-8 overflow-hidden"
        >
          <div className="grid gap-6 rounded-lg bg-gray-800 p-6 md:grid-cols-4">
            {/* Genre Filter */}
            <div>
              <label className="mb-2 block text-sm font-medium text-white">
                {t('filters.genres')}
              </label>
              <div className="flex flex-wrap gap-2">
                {genres.map(genre => (
                  <button
                    key={genre.id}
                    onClick={() =>
                      handleFilterChange(
                        'genres',
                        filters.genres.includes(genre.id)
                          ? filters.genres.filter(id => id !== genre.id)
                          : [...filters.genres, genre.id]
                      )
                    }
                    className={`rounded-full px-3 py-1 text-sm ${
                      filters.genres.includes(genre.id)
                        ? 'bg-red-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {genre.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Year Filter */}
            <div>
              <label className="mb-2 block text-sm font-medium text-white">
                {t('filters.year')}
              </label>
              <select
                value={filters.year}
                onChange={e => handleFilterChange('year', e.target.value)}
                className="w-full rounded-md bg-gray-700 p-2 text-white"
              >
                <option value="">{t('filters.selectYear')}</option>
                {years.map(year => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
            </div>

            {/* Rating Filter */}
            <div>
              <label className="mb-2 block text-sm font-medium text-white">
                {t('filters.rating')}
              </label>
              <select
                value={filters.rating}
                onChange={e => handleFilterChange('rating', e.target.value)}
                className="w-full rounded-md bg-gray-700 p-2 text-white"
              >
                <option value="">{t('filters.selectRating')}</option>
                {ratings.map(rating => (
                  <option key={rating} value={rating}>
                    {rating}
                  </option>
                ))}
              </select>
            </div>

            {/* Sort Filter */}
            <div>
              <label className="mb-2 block text-sm font-medium text-white">
                {t('filters.sortBy')}
              </label>
              <select
                value={filters.sortBy}
                onChange={e => handleFilterChange('sortBy', e.target.value)}
                className="w-full rounded-md bg-gray-700 p-2 text-white"
              >
                {sortOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </motion.div>

        {/* Movies Grid */}
        <MovieGrid filters={filters} />
      </div>
    </div>
  );
};

export default MoviesPage;
