import { motion } from 'framer-motion';
import { useTranslation } from '../../i18n/hooks/useTranslation';
import MovieCard from '../movies/movie-card';
import RecommendedInfo from '../movies/movie-card/RecommendedInfo'; // Reuse the RecommendedInfo component

const RecommendationCard = ({ movie }) => {
  const { t } = useTranslation('movies');
  const { match, recommendReason, ...movieProps } = movie; // Destructure movie to get recommendation props and rest

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
      className="group relative flex h-full flex-col overflow-hidden rounded-lg bg-gray-800 shadow-lg transition-all duration-300 hover:shadow-xl hover:shadow-red-500/20"
    >
      {/* Render the base MovieCard */}
      <MovieCard movie={movieProps} />

      {/* Add recommendation-specific info and button outside MovieCard's actions */}
      {(match || recommendReason) && (
        <div className="flex flex-col gap-2 p-4 pt-0">
          {/* Recommended Info */}
          <RecommendedInfo match={match} recommendReason={recommendReason} />

          {/* Why Recommend? Button */}
          {match && (
            <button
              className="w-fit rounded bg-white/10 px-3 py-2 text-xs font-semibold text-white shadow transition hover:bg-white/20"
              type="button"
            >
              Why Recommend?
            </button>
          )}
        </div>
      )}
    </motion.div>
  );
};

export default RecommendationCard;
