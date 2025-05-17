import { motion } from 'framer-motion';
import Poster from './Poster';
import Info from './Info';
import Rating from './Rating';
import Badge from './Badge';
import Actions from './Actions';

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

      {/* Movie Poster */}
      <Poster posterPath={poster_path} title={title} />

      {/* Movie Info Section */}
      <div className="flex min-h-[180px] flex-1 flex-col justify-between p-4">
        <div>
          <Info title={title} releaseDate={release_date} overview={overview} genres={genres} />
          <Rating voteAverage={vote_average} voteCount={vote_count} />
        </div>
        <Actions movieId={id} />
      </div>
    </motion.div>
  );
};

export default MovieCard;
