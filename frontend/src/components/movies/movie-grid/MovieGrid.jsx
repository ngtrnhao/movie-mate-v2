import { motion } from 'framer-motion';
import MovieCard from '../movie-card';

const MovieGrid = ({ movies, loading, error }) => {
  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="size-8 animate-spin rounded-full border-4 border-red-600 border-t-transparent"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center text-red-500">
          <h2 className="mb-2 text-2xl font-bold">Error</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!movies.length) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center text-gray-400">
          <p className="text-lg">No movies found.</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5"
    >
      {movies.map((movie) => (
        <MovieCard
          key={movie.id}
          movie={{
            id: movie.id,
            title: movie.title,
            poster_path: movie.poster_path,
            adult: movie.adult,
            vote_average: movie.vote_average,
            vote_count: movie.vote_count,
            release_date: movie.release_date,
            overview: movie.overview,
            genres: movie.genres,
            backdrop_path: movie.backdrop_path,
            popularity: movie.popularity,
            original_language: movie.original_language,
            original_title: movie.original_title,
            title_translations: movie.title_translations,
            overview_translations: movie.overview_translations,
            trailerUrl: movie.trailerUrl,
          }}
        />
      ))}
    </motion.div>
  );
};

export default MovieGrid;
