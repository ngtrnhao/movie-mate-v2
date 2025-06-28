import { motion } from 'framer-motion';
import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { Star } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getPrimaryRating, getRatingBadgeColors } from '../../../utils/ratingUtils';

const TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/w500';

const SimilarMovies = ({ movies = [] }) => {
  const { t } = useTranslation('movies');

  if (!movies || movies.length === 0) return null;

  const getImageUrl = path => {
    if (!path) return 'https://via.placeholder.com/500x750?text=No+Image';
    if (path.startsWith('http')) return path;
    return `${TMDB_IMAGE_BASE_URL}${path}`;
  };

  const getRatingInfo = movie => {
    return getPrimaryRating(movie);
  };

  const getTitle = movie => {
    if (movie.title_vi) return movie.title_vi;
    if (movie.title_en) return movie.title_en;
    if (movie.title) return movie.title;
    if (movie.original_title) return movie.original_title;
    return 'No Title';
  };

  return (
    <section className="relative bg-gray-900 py-16">
      <div className="container mx-auto px-4">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-8 text-2xl font-bold text-white sm:text-3xl"
        >
          {t('details.similarMovies')}
        </motion.h2>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
          {movies.map(movie => (
            <motion.div
              key={movie.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="group relative overflow-hidden rounded-lg bg-gray-800"
            >
              <Link to={`/movies/${movie.id}`}>
                <div className="aspect-[2/3] w-full overflow-hidden">
                  <img
                    src={getImageUrl(movie.poster_url || movie.poster_path)}
                    alt={getTitle(movie)}
                    className="size-full object-cover transition-transform duration-300 group-hover:scale-110"
                    onError={e => {
                      e.target.src = 'https://via.placeholder.com/500x750?text=No+Image';
                    }}
                  />
                </div>

                {/* Movie Info */}
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 to-transparent p-4">
                  <h3 className="line-clamp-1 text-sm font-semibold text-white">
                    {getTitle(movie)}
                  </h3>
                  <div className="mt-1 flex items-center gap-2">
                    {(() => {
                      const ratingInfo = getRatingInfo(movie);
                      if (!ratingInfo) return null;

                      const colors = getRatingBadgeColors(ratingInfo.source);
                      return (
                        <div
                          className={`flex items-center gap-1 rounded-md px-1.5 py-0.5 text-xs font-bold ${colors.bg} ${colors.text}`}
                        >
                          <span>{ratingInfo.source}</span>
                          <span>{ratingInfo.value.toFixed(1)}</span>
                        </div>
                      );
                    })()}
                    {movie.release_date && (
                      <span className="text-xs text-gray-400">
                        {new Date(movie.release_date).getFullYear()}
                      </span>
                    )}
                  </div>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default SimilarMovies;
