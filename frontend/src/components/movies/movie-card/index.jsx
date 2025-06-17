import { memo, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import Actions from './Actions';
import Badge from './Badge';
import Info from './Info';
import Poster from './Poster';
import Rating from './Rating';
import RecommendedInfo from './RecommendedInfo';

const MovieCard = memo(({ movie }) => {
  // Memoize movie data
  const movieData = useMemo(
    () => ({
      id: movie.id,
      title: movie.title,
      original_title: movie.original_title,
      poster_path: movie.poster_path,
      overview_en: movie.overview_en,
      release_date: movie.release_date,
      genres: movie.genres,
      rating: movie.rating,
      vote_average: movie.vote_average,
      vote_count: movie.vote_count,
      is_popular: movie.is_popular,
      is_top_rated: movie.is_top_rated,
      is_upcoming: movie.is_upcoming,
      adult: movie.adult,
      match: movie.match,
      recommendReason: movie.recommendReason,
    }),
    [movie]
  );

  // Memoize handlers
  // const handleClick = useCallback(() => {
  //   // Handle click if needed
  // }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
      layout={false}
      className="relative flex flex-col h-full overflow-hidden rounded-lg group bg-gray-800 shadow-md transition-all duration-300 will-change-transform hover:shadow-lg"
    >
      {/* Adult Content Badge */}
      {movieData.adult && <Badge />}

      {/* Movie Poster with Link */}
      <Link to={`/movies/${movieData.id}`} className="block">
        <Poster posterPath={movieData.poster_path} title={movieData.title} />
      </Link>

      {/* Movie Info Section */}
      <div className="flex min-h-[180px] flex-1 flex-col justify-between p-4">
        <Link to={`/movies/${movieData.id}`} className="block">
          <div>
            <Info
              title={movieData.title}
              originalTitle={movieData.original_title}
              releaseDate={movieData.release_date}
              overview={movieData.overview_en}
              genres={movieData.genres}
              isPopular={movieData.is_popular}
              isTopRated={movieData.is_top_rated}
              isUpcoming={movieData.is_upcoming}
            />
            <RecommendedInfo match={movieData.match} recommendReason={movieData.recommendReason} />
            <Rating
              rating={movieData.rating}
              voteAverage={movieData.vote_average}
              voteCount={movieData.vote_count}
            />
          </div>
        </Link>
        <div className="mt-3 flex items-center gap-2">
          <div className="flex flex-1 gap-2">
            <Actions moviesId={movieData.id} onlyMainButton />
            {movieData.match && (
              <button
                className="rounded bg-white/10 px-3 py-2 text-xs font-semibold text-white shadow transition hover:bg-white/20"
                type="button"
              >
                Why Recommend?
              </button>
            )}
          </div>
          <Actions moviesId={movieData.id} onlyBookmark />
        </div>
      </div>
    </motion.div>
  );
});

MovieCard.displayName = 'MovieCard';

export default MovieCard;
