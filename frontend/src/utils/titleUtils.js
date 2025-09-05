/**
 * Get localized movie title with comprehensive fallback
 * @param {Object} movie - Movie object
 * @param {string} language - Language preference ('vi' or 'en')
 * @returns {string} - Localized title with fallback
 */
export const getLocalizedTitle = (movie, language = 'en') => {
  if (!movie) return language === 'vi' ? 'Phim chưa có tên' : 'Untitled Movie';

  if (language === 'vi') {
    // Vietnamese priority: title_vi → title_en → title → original_title → fallback
    return (
      movie.title_vi || movie.title_en || movie.title || movie.original_title || 'Phim chưa có tên'
    );
  } else {
    // English priority: title_en → title → title_vi → original_title → fallback
    return (
      movie.title_en || movie.title || movie.title_vi || movie.original_title || 'Untitled Movie'
    );
  }
};

/**
 * Get title for search/filtering purposes (no language preference)
 * @param {Object} movie - Movie object
 * @returns {string} - Title for search purposes
 */
export const getSearchableTitle = movie => {
  if (!movie) return '';

  // For search, use any available title
  return movie.title || movie.title_en || movie.title_vi || movie.original_title || '';
};

/**
 * Get all available titles for a movie
 * @param {Object} movie - Movie object
 * @returns {Array} - Array of unique non-empty titles
 */
export const getAllTitles = movie => {
  if (!movie) return [];

  const titles = [movie.title, movie.title_en, movie.title_vi, movie.original_title].filter(
    Boolean
  ); // Remove empty/null/undefined values

  // Remove duplicates
  return [...new Set(titles)];
};

/**
 * Get display title based on current language with fallback
 * @param {Object} movie - Movie object
 * @param {string} language - Current language ('en' or 'vi')
 * @returns {string} - Display title
 */
export const getDisplayTitle = (movie, language = 'en') => {
  if (!movie) return '';

  if (language === 'vi') {
    return movie.title_vi || movie.original_title || movie.title_en || movie.title || '';
  } else {
    return movie.title_en || movie.original_title || movie.title_vi || movie.title || '';
  }
};

/**
 * Get display overview based on current language with fallback
 * @param {Object} movie - Movie object
 * @param {string} language - Current language ('en' or 'vi')
 * @returns {string} - Display overview
 */
export const getDisplayOverview = (movie, language = 'en') => {
  if (!movie) return '';

  if (language === 'vi') {
    return movie.overview_vi || movie.overview_en || movie.overview || '';
  } else {
    return movie.overview_en || movie.overview_vi || movie.overview || '';
  }
};
