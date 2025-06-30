import { memo, useMemo, useCallback, useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import Actions from './Actions';
import Badge from './Badge';
import Info from './Info';
import Poster from './Poster';
import Rating from './Rating';
import RecommendedInfo from './RecommendedInfo';
import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { getDisplayTitle, getDisplayOverview } from '../../../utils/titleUtils';
import animationCache from '../../../utils/animationCache';

// Slide up animation variants
const posterVariants = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' } },
};

const MovieCard = memo(
  ({ movie, index = 0, onClick, onTrailerClick, priority = false, minimal = false, style }) => {
    const { i18n } = useTranslation();
    const [posterLoaded, setPosterLoaded] = useState(false);
    const [hasAnimated, setHasAnimated] = useState(animationCache.isMovieAnimated(movie.id));

    // Memoize stable movie data to prevent re-calculations
    const movieData = useMemo(
      () => ({
        id: movie.id,
        title: movie.title,
        title_en: movie.title_en,
        title_vi: movie.title_vi,
        original_title: movie.original_title,
        poster_path: movie.poster_path,
        overview_en: movie.overview_en,
        overview_vi: movie.overview_vi,
        release_date: movie.release_date,
        runtime: movie.runtime,
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
        trailers: movie.trailers,
      }),
      [
        movie.id,
        movie.title,
        movie.title_en,
        movie.title_vi,
        movie.original_title,
        movie.poster_path,
        movie.overview_en,
        movie.overview_vi,
        movie.release_date,
        movie.runtime,
        movie.genres,
        movie.rating,
        movie.vote_average,
        movie.vote_count,
        movie.is_popular,
        movie.is_top_rated,
        movie.is_upcoming,
        movie.adult,
        movie.match,
        movie.recommendReason,
        movie.trailers,
      ]
    );

    // Memoize display values để tránh re-computation
    const displayValues = useMemo(() => {
      const displayTitle = getDisplayTitle(movieData, i18n.language);
      const displayOverview = getDisplayOverview(movieData, i18n.language);
      const displayGenres = movieData.genres?.filter(g => g.language === i18n.language) || [];

      return {
        title: displayTitle,
        overview: displayOverview,
        genres: displayGenres,
      };
    }, [movieData, i18n.language]);

    const isPriority = index < 8;

    const handleClick = useCallback(() => {
      // Remove sessionStorage handling - let the global hook handle it
      if (onClick) {
        onClick(movieData);
      }
    }, [movieData, onClick]);

    const handleTrailerClick = useCallback(
      e => {
        if (e && e.preventDefault) {
          e.preventDefault();
        }
        if (e && e.stopPropagation) {
          e.stopPropagation();
        }
        if (onTrailerClick) {
          onTrailerClick(movieData);
        }
      },
      [movieData, onTrailerClick]
    );

    // Mark movie as animated when it comes into view
    const handleAnimationComplete = useCallback(() => {
      if (!hasAnimated && movie.id) {
        animationCache.markMovieAnimated(movie.id);
        setHasAnimated(true);
      }
    }, [hasAnimated, movie.id]);

    // Minimal rendering cho fast scroll - chỉ hiển thị poster và title
    if (minimal) {
      if (posterLoaded) {
        return (
          <motion.div
            variants={hasAnimated ? {} : posterVariants}
            initial={hasAnimated ? 'visible' : 'hidden'}
            whileInView={hasAnimated ? undefined : 'visible'}
            viewport={hasAnimated ? undefined : { once: true, amount: 0.2 }}
            onAnimationComplete={handleAnimationComplete}
            className="movie-card focus-ring group relative rounded-lg bg-gray-800 shadow-lg transition-transform will-change-transform hover:scale-105"
            style={style}
          >
            <Link
              to={`/movies/${movieData.id}`}
              state={{ preserveScroll: true }}
              onClick={handleClick}
            >
              <Poster
                movie={movieData}
                title={movieData.title}
                priority={priority}
                onLoadDone={() => setPosterLoaded(true)}
              />
              {/* Simplified title overlay */}
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-3">
                <h3 className="line-clamp-1 text-sm font-medium text-white">{movieData.title}</h3>
              </div>
            </Link>
          </motion.div>
        );
      }
      return (
        <div
          className="movie-card focus-ring group relative rounded-lg bg-gray-800 shadow-lg transition-transform will-change-transform hover:scale-105"
          style={style}
        >
          <Poster
            movie={movieData}
            title={movieData.title}
            priority={priority}
            onLoadDone={() => setPosterLoaded(true)}
          />
        </div>
      );
    }

    // Full rendering với all features
    if (posterLoaded) {
      return (
        <motion.div
          variants={hasAnimated ? {} : posterVariants}
          initial={hasAnimated ? 'visible' : 'hidden'}
          whileInView={hasAnimated ? undefined : 'visible'}
          viewport={hasAnimated ? undefined : { once: true, amount: 0.2 }}
          onAnimationComplete={handleAnimationComplete}
          className="movie-card focus-ring group relative flex h-full flex-col overflow-hidden rounded-lg bg-gray-800 shadow-md"
        >
          {/* Adult Content Badge */}
          {movieData.adult && <Badge />}

          {/* Movie Poster with Link */}
          <Link
            to={`/movies/${movieData.id}`}
            state={{ preserveScroll: true }}
            className="block"
            onClick={handleClick}
          >
            <div className="movie-poster">
              <Poster
                movie={movieData}
                title={displayValues.title}
                priority={isPriority}
                onLoadDone={() => setPosterLoaded(true)}
              />
            </div>
          </Link>

          {/* Movie Info Section */}
          <div className="flex min-h-[180px] flex-1 flex-col justify-between p-4">
            <Link
              to={`/movies/${movieData.id}`}
              state={{ preserveScroll: true }}
              className="focus-ring block rounded"
              onClick={handleClick}
            >
              <div>
                <Info
                  title={displayValues.title}
                  originalTitle={movieData.original_title}
                  releaseDate={movieData.release_date}
                  runtime={movieData.runtime}
                  overview={displayValues.overview}
                  genres={displayValues.genres}
                  isPopular={movieData.is_popular}
                  isTopRated={movieData.is_top_rated}
                  isUpcoming={movieData.is_upcoming}
                />
                <RecommendedInfo
                  match={movieData.match}
                  recommendReason={movieData.recommendReason}
                />
                <Rating
                  rating={movieData.rating}
                  voteAverage={movieData.vote_average}
                  voteCount={movieData.vote_count}
                />
              </div>
            </Link>
            <div className="mt-3 flex items-center gap-2">
              <div className="flex flex-1 gap-2">
                <Actions movie={movieData} onlyMainButton onTrailerClick={handleTrailerClick} />
                {movieData.match && (
                  <button
                    className="focus-ring rounded bg-white/10 px-3 py-2 text-xs font-semibold text-white shadow transition hover:bg-white/20"
                    type="button"
                  >
                    Why Recommend?
                  </button>
                )}
              </div>
              <Actions movie={movieData} onlyBookmark />
            </div>
          </div>
        </motion.div>
      );
    }
    return (
      <div className="movie-card focus-ring group relative flex h-full flex-col overflow-hidden rounded-lg bg-gray-800 shadow-md">
        <div className="movie-poster">
          <Poster
            movie={movieData}
            title={displayValues.title}
            priority={isPriority}
            onLoadDone={() => setPosterLoaded(true)}
          />
        </div>
      </div>
    );
  },
  (prevProps, nextProps) => {
    // Custom comparison function để tránh unnecessary re-renders
    return (
      prevProps.movie?.id === nextProps.movie?.id &&
      prevProps.movie?.poster_path === nextProps.movie?.poster_path &&
      prevProps.movie?.title === nextProps.movie?.title &&
      prevProps.movie?.vote_average === nextProps.movie?.vote_average &&
      prevProps.movie?.vote_count === nextProps.movie?.vote_count
    );
  }
);

MovieCard.displayName = 'MovieCard';

export default MovieCard;
