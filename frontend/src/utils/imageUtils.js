const TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/original';

// Fallback URLs
const FALLBACK_URLS = {
  poster: 'https://placehold.co/600x400',
  backdrop: '/images/placeholder-backdrop.jpg',
  profile: {
    male: '/images/avatar-male.png',
    female: '/images/avatar-female.png',
    default: '/images/avatar-default.png',
  },
};

/**
 * Get the full image URL from various possible formats
 * @param {string} path - The image path or URL
 * @param {string} [size='w342'] - The size for TMDB images (w342, w500, etc.)
 * @returns {string|null} The full image URL or null if no valid path
 */
export const getImageUrl = (path, size = 'w342') => {
  if (!path) return null;

  // Case 1: Already a full URL (including Amazon, IMDB, etc)
  if (path.startsWith('http') || path.startsWith('https')) {
    // Nếu là TMDB, thay /original/ bằng /w342/ hoặc size chỉ định
    if (path.includes('tmdb.org/t/p/')) {
      return path.replace('/original/', `/${size}/`);
    }
    return path;
  }

  // Case 2: TMDB path
  if (path.startsWith('/')) {
    return `${TMDB_IMAGE_BASE_URL.replace('original', size)}${path}`;
  }

  // Case 3: TMDB path without leading slash
  return `${TMDB_IMAGE_BASE_URL.replace('original', size)}/${path}`;
};

/**
 * Get the backdrop URL from movie object
 * @param {Object} movie - The movie object
 * @param {string} [size='w780'] - The size for TMDB images
 * @returns {string|null} The backdrop URL or null if not found
 */
export const getBackdropUrl = (movie, size = 'w780') => {
  if (!movie) return FALLBACK_URLS.backdrop;

  // Try all possible backdrop fields
  const backdropPath = movie.backdrop_url || movie.backdrop_path;
  if (backdropPath) {
    return getImageUrl(backdropPath, size);
  }

  // Fallback to poster if no backdrop
  const posterUrl = getPosterUrl(movie, size);
  return posterUrl || FALLBACK_URLS.backdrop;
};

/**
 * Get the poster URL from movie object
 * @param {Object} movie - The movie object
 * @param {string} [size='w342'] - The size for TMDB images
 * @returns {string|null} The poster URL or null if not found
 */
export const getPosterUrl = (movie, size = 'w342') => {
  if (!movie) return FALLBACK_URLS.poster;

  // Try all possible poster fields
  const posterPath = movie.poster_url || movie.poster_path;
  return posterPath ? getImageUrl(posterPath, size) : FALLBACK_URLS.poster;
};

/**
 * Get the profile image URL for cast/crew
 * @param {Object} person - The person object
 * @param {string} [size='original'] - The size for TMDB images
 * @returns {string} The profile URL or appropriate fallback avatar
 */
export const getProfileUrl = (person, size = 'original') => {
  if (!person) return FALLBACK_URLS.profile.default;

  const profilePath = person.profile_url || person.profile_path;
  if (profilePath) {
    return getImageUrl(profilePath, size);
  }

  // Use gender-specific fallback if available
  if (person.gender === 1) return FALLBACK_URLS.profile.female;
  if (person.gender === 2) return FALLBACK_URLS.profile.male;

  return FALLBACK_URLS.profile.default;
};

/**
 * Preload image for better UX
 * @param {string} imageUrl - Image URL to preload
 * @returns {Promise} - Promise that resolves when image is loaded
 */
export const preloadImage = imageUrl => {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = resolve;
    img.onerror = reject;
    img.src = imageUrl;
  });
};

/**
 * Get optimized image URL based on device pixel ratio
 * @param {string} imageUrl - Base image URL
 * @param {number} baseWidth - Base width for 1x displays
 * @returns {string} - Optimized image URL
 */
export const getResponsiveImageUrl = (imageUrl, baseWidth = 500) => {
  const dpr = window.devicePixelRatio || 1;

  if (dpr >= 2) {
    // High DPI display - use larger image
    if (baseWidth <= 300) return getImageUrl(imageUrl, 'w500');
    if (baseWidth <= 500) return getImageUrl(imageUrl, 'w780');
    return getImageUrl(imageUrl, 'original');
  } else {
    // Standard DPI display
    if (baseWidth <= 154) return getImageUrl(imageUrl, 'w154');
    if (baseWidth <= 300) return getImageUrl(imageUrl, 'w342');
    if (baseWidth <= 500) return getImageUrl(imageUrl, 'w500');
    return getImageUrl(imageUrl, 'w780');
  }
};
