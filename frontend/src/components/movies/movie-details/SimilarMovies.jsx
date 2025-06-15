import { motion } from 'framer-motion';
import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { Star } from 'lucide-react';
import { Link } from 'react-router-dom';

const TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/w500';

// Mock data cho similar movies
const mockSimilarMovies = [
  {
    id: 1,
    title: 'Inception',
    poster_path: '/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg',
    vote_average: 8.8,
    release_date: '2010-07-16',
  },
  {
    id: 2,
    title: 'Interstellar',
    poster_path: '/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg',
    vote_average: 8.6,
    release_date: '2014-11-07',
  },
  {
    id: 3,
    title: 'The Prestige',
    poster_path: '/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg',
    vote_average: 8.5,
    release_date: '2006-10-20',
  },
  {
    id: 4,
    title: 'Memento',
    poster_path: '/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg',
    vote_average: 8.4,
    release_date: '2000-10-11',
  },
  {
    id: 5,
    title: 'Dunkirk',
    poster_path: '/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg',
    vote_average: 7.8,
    release_date: '2017-07-19',
  },
  {
    id: 6,
    title: 'Tenet',
    poster_path: '/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg',
    vote_average: 7.4,
    release_date: '2020-08-22',
  },
];

const SimilarMovies = () => {
  const { t } = useTranslation('movies');

  // Sử dụng mock data nếu không có similar movies
  const displayMovies = mockSimilarMovies;

  if (!displayMovies || displayMovies.length === 0) return null;

  return (
    <section className="relative mt-0 bg-gray-900 py-16">
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
          {displayMovies.map(movie => (
            <motion.div
              key={movie.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              whileHover={{ scale: 1.05 }}
              className="group relative overflow-hidden rounded-lg bg-gray-800/50 transition-all duration-300 hover:bg-gray-800/70"
            >
              <Link to={`/movies/${movie.id}`}>
                {/* Movie Poster */}
                <div className="aspect-[2/3] w-full overflow-hidden">
                  <img
                    src={`${TMDB_IMAGE_BASE_URL}${movie.poster_path}`}
                    alt={movie.title}
                    className="size-full object-cover transition-transform duration-300 group-hover:scale-110"
                    onError={e => {
                      e.target.onerror = null;
                      e.target.src = 'https://via.placeholder.com/500x750?text=No+Image';
                    }}
                  />
                </div>

                {/* Movie Info */}
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 to-transparent p-4">
                  <h3 className="line-clamp-1 text-sm font-semibold text-white">{movie.title}</h3>
                  <div className="mt-1 flex items-center gap-2">
                    <div className="flex items-center gap-1">
                      <Star className="size-3 fill-yellow-400 text-yellow-400" />
                      <span className="text-xs text-gray-300">{movie.vote_average.toFixed(1)}</span>
                    </div>
                    <span className="text-xs text-gray-400">
                      {new Date(movie.release_date).getFullYear()}
                    </span>
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
