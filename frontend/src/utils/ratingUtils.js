/**
 * Shared Rating Utilities for Movie Components
 * Ensures consistent rating logic across all movie cards
 * Updated for discrete 5-point rating scale (1.0, 2.0, 3.0, 4.0, 5.0)
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
      value: normalizeToDiscreteRating(ratingObj.imdb),
      source: 'IMDb',
      votes: ratingObj.imdb_votes,
    };
  }

  if (movie.cached_imdb_rating) {
    return {
      value: normalizeToDiscreteRating(parseFloat(movie.cached_imdb_rating)),
      source: 'IMDb',
      votes: movie.cached_imdb_votes || 0,
    };
  }

  if (movie.imdb_rating) {
    return {
      value: normalizeToDiscreteRating(parseFloat(movie.imdb_rating)),
      source: 'IMDb',
      votes: movie.imdb_votes || 0,
    };
  }

  // Priority 2: TMDB Rating
  if (ratingObj.tmdb && ratingObj.tmdb_votes > 0) {
    return {
      value: normalizeToDiscreteRating(ratingObj.tmdb),
      source: 'TMDB',
      votes: ratingObj.tmdb_votes,
    };
  }

  if (movie.cached_tmdb_rating) {
    return {
      value: normalizeToDiscreteRating(parseFloat(movie.cached_tmdb_rating)),
      source: 'TMDB',
      votes: movie.cached_tmdb_votes || 0,
    };
  }

  if (movie.tmdb_rating) {
    return {
      value: normalizeToDiscreteRating(parseFloat(movie.tmdb_rating)),
      source: 'TMDB',
      votes: movie.tmdb_votes || 0,
    };
  }

  // Priority 3: Fallback to vote_average
  if (movie.vote_average && movie.vote_count > 0) {
    return {
      value: normalizeToDiscreteRating(parseFloat(movie.vote_average)),
      source: 'TMDb',
      votes: movie.vote_count,
    };
  }

  return null;
};

/**
 * Normalize any rating to discrete 5-point scale (1, 2, 3, 4, 5)
 * @param {number} rating - Original rating value
 * @returns {number} - Normalized rating (1, 2, 3, 4, or 5)
 */
export const normalizeToDiscreteRating = rating => {
  if (!rating || isNaN(rating)) return 3;

  const ratingFloat = parseFloat(rating);

  // Handle different rating scales and convert to 1-5 discrete scale
  if (ratingFloat <= 0) return 1;
  else if (ratingFloat <= 2) return 1;
  else if (ratingFloat <= 4) return 2;
  else if (ratingFloat <= 6) return 3;
  else if (ratingFloat <= 8) return 4;
  else return 5; // > 8
};

/**
 * Convert rating to star scale (10-point to 5-point)
 * @param {number} rating - Rating value
 * @param {number} maxRating - Maximum rating value (default: 10)
 * @returns {number} - Rating in 5-star scale
 */
export const convertToStarRating = (rating, maxRating = 10) => {
  if (!rating || isNaN(rating)) return 0;

  // Convert to 5-star scale and then normalize to discrete
  const starRating = (rating / maxRating) * 5;
  return normalizeToDiscreteRating(starRating);
};

/**
 * Get star display for rating
 * @param {number} rating - Rating value (1-5)
 * @returns {string} - Star display string
 */
export const getStarDisplay = rating => {
  const normalizedRating = normalizeToDiscreteRating(rating);
  return '★'.repeat(normalizedRating) + '☆'.repeat(5 - normalizedRating);
};

/**
 * Get rating text description
 * @param {number} rating - Rating value (1-5)
 * @returns {string} - Rating description
 */
export const getRatingDescription = rating => {
  const normalizedRating = normalizeToDiscreteRating(rating);

  switch (normalizedRating) {
    case 1:
      return 'Rất tệ';
    case 2:
      return 'Tệ';
    case 3:
      return 'Trung bình';
    case 4:
      return 'Tốt';
    case 5:
      return 'Rất tốt';
    default:
      return 'Chưa đánh giá';
  }
};

/**
 * Check if rating is valid for discrete scale
 * @param {number} rating - Rating value
 * @returns {boolean} - Is valid discrete rating
 */
export const isValidDiscreteRating = rating => {
  if (!rating || isNaN(rating)) return false;
  const normalizedRating = normalizeToDiscreteRating(rating);
  return [1, 2, 3, 4, 5].includes(normalizedRating);
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
