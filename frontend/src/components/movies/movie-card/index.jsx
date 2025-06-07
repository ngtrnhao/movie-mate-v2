import { motion } from 'framer-motion';
import Poster from './Poster';
import Info from './Info';
import Rating from './Rating';
import Badge from './Badge';
import Actions from './Actions';
import RecommendedInfo from './RecommendedInfo';
import { Link } from 'react-router-dom';

const MovieCard = ({ movie }) => {
  const {
    id,
    title,
    poster_path,
    adult,
    vote_average,
    vote_count,
    release_date,
    overview,
    genres,
    match,
    recommendReason,
  } = movie;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
      className="group relative flex h-full flex-col overflow-hidden rounded-lg bg-gray-800 shadow-lg transition-all duration-300 hover:shadow-xl hover:shadow-red-500/20"
    >
      {/* Adult Content Badge */}
      {adult && <Badge />}

      {/* Movie Poster with Link */}
      <Link to={`/movies/${movie.id}`} className="block">
        <Poster posterPath={poster_path} title={title} />
      </Link>

      {/* Movie Info Section */}
      <div className="flex min-h-[180px] flex-1 flex-col justify-between p-4">
        <Link to={`/movies/${movie.id}`} className="block">
          <div>
            <Info title={title} releaseDate={release_date} overview={overview} genres={genres} />
            <RecommendedInfo match={match} recommendReason={recommendReason} />
            <Rating voteAverage={vote_average} voteCount={vote_count} />
          </div>
        </Link>
        <div className="mt-3 flex items-center gap-2">
          <div className="flex flex-1 gap-2">
            <Actions moviesId={id} onlyMainButton />
            {match && (
              <button
                className="rounded bg-white/10 px-3 py-2 text-xs font-semibold text-white shadow transition hover:bg-white/20"
                type="button"
              >
                Why Recommend?
              </button>
            )}
          </div>
          <Actions moviesId={id} onlyBookmark />
        </div>
      </div>
    </motion.div>
  );
};

export default MovieCard;
