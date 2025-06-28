/**
 * Shared Rating Utilities for Movie Components
 * Ensures consistent rating logic across all movie cards
 */

/**
 * Get the primary rating with source information
 * @param {Object} movie - Movie object with various rating fields
 * @returns {Object|null} - {value, source, votes} or null
 */
export const getPrimaryRating = movie => {
  // Handle different movie object structures
  const ratingObj = movie.rating || {};

  // Priority 1: IMDb Rating
  if (ratingObj.imdb && ratingObj.imdb_votes > 0) {
    return {
      value: ratingObj.imdb,
      source: 'IMDb',
      votes: ratingObj.imdb_votes,
    };
  }

  if (movie.cached_imdb_rating) {
    return {
      value: parseFloat(movie.cached_imdb_rating),
      source: 'IMDb',
      votes: movie.cached_imdb_votes || 0,
    };
  }

  if (movie.imdb_rating) {
    return {
      value: parseFloat(movie.imdb_rating),
      source: 'IMDb',
      votes: movie.imdb_votes || 0,
    };
  }

  // Priority 2: TMDB Rating
  if (ratingObj.tmdb && ratingObj.tmdb_votes > 0) {
    return {
      value: ratingObj.tmdb,
      source: 'TMDB',
      votes: ratingObj.tmdb_votes,
    };
  }

  if (movie.cached_tmdb_rating) {
    return {
      value: parseFloat(movie.cached_tmdb_rating),
      source: 'TMDB',
      votes: movie.cached_tmdb_votes || 0,
    };
  }

  if (movie.tmdb_rating) {
    return {
      value: parseFloat(movie.tmdb_rating),
      source: 'TMDB',
      votes: movie.tmdb_votes || 0,
    };
  }

  // Priority 3: Fallback to vote_average
  if (movie.vote_average && movie.vote_count > 0) {
    return {
      value: parseFloat(movie.vote_average),
      source: 'TMDb',
      votes: movie.vote_count,
    };
  }

  // Handle complex rating object structures
  if (movie.rating && typeof movie.rating === 'object') {
    if (movie.rating.imdb) {
      return {
        value: parseFloat(movie.rating.imdb),
        source: 'IMDb',
        votes: movie.rating.imdb_votes || 0,
      };
    }
    if (movie.rating.tmdb) {
      return {
        value: parseFloat(movie.rating.tmdb),
        source: 'TMDB',
        votes: movie.rating.tmdb_votes || 0,
      };
    }
    if (movie.rating.combined_score) {
      return {
        value: parseFloat(movie.rating.combined_score),
        source: 'Combined',
        votes: 0,
      };
    }
  }

  // Handle simple number rating
  if (typeof movie.rating === 'number' && movie.rating > 0) {
    return {
      value: movie.rating,
      source: 'Rating',
      votes: 0,
    };
  }

  return null;
};

/**
 * Convert rating to star scale (10-point to 5-point)
 * @param {number} rating - Rating value (0-10)
 * @returns {number} - Star rating (0-5)
 */
export const getStarRating = rating => {
  if (!rating || rating <= 0) return 0;
  return Math.round(rating / 2);
};

/**
 * Format vote count for display
 * @param {number} votes - Vote count
 * @returns {string} - Formatted vote count (e.g., "1.2K", "1.5M")
 */
export const formatVoteCount = votes => {
  if (!votes || votes === 0) return '0';
  if (votes >= 1_000_000) return `${(votes / 1_000_000).toFixed(1)}M`;
  if (votes >= 1000) return `${(votes / 1000).toFixed(1)}K`;
  return votes.toString();
};

/**
 * Get rating badge colors based on source
 * @param {string} source - Rating source ('IMDb', 'TMDB', 'TMDb', etc.)
 * @returns {Object} - {bg, text} classes
 */
export const getRatingBadgeColors = source => {
  if (source === 'IMDb') {
    return {
      bg: 'bg-yellow-500',
      text: 'text-black',
    };
  }
  // TMDB, TMDb, or any other source
  return {
    bg: 'bg-blue-500',
    text: 'text-white',
  };
};

/**
 * Create a unified rating component props
 * @param {Object} movie - Movie object
 * @returns {Object} - Props for Rating component
 */
export const createRatingProps = movie => {
  const primaryRating = getPrimaryRating(movie);

  if (!primaryRating) {
    return {
      rating: null,
      voteAverage: null,
      voteCount: 0,
    };
  }

  return {
    rating: {
      [primaryRating.source.toLowerCase()]: primaryRating.value,
      [`${primaryRating.source.toLowerCase()}_votes`]: primaryRating.votes,
    },
    voteAverage: primaryRating.value,
    voteCount: primaryRating.votes,
  };
};
