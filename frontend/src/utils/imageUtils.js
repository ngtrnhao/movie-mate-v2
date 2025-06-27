/**
 * Get optimized image URL with fallback handling
 * @param {string} imageUrl - The image URL from API
 * @param {string} size - Optional size parameter (w300, w500, w780, original)
 * @returns {string} - Processed image URL
 */
export const getImageUrl = (imageUrl, size = 'original') => {
  if (!imageUrl) {
    return '/images/placeholder-poster.jpg'; // Fallback placeholder
  }

  // If it's already a full URL, return as is
  if (imageUrl.startsWith('http')) {
    return imageUrl;
  }

  // If it's a relative path from TMDB, construct full URL
  if (imageUrl.startsWith('/')) {
    return `https://image.tmdb.org/t/p/${size}${imageUrl}`;
  }

  // Return the URL as is for other cases
  return imageUrl;
};

/**
 * Get poster image URL with appropriate size
 * @param {string} posterUrl - Poster URL from API
 * @param {string} size - Size (w154, w185, w342, w500, w780, original)
 * @returns {string} - Poster image URL
 */
export const getPosterUrl = (posterUrl, size = 'w500') => {
  return getImageUrl(posterUrl, size);
};

/**
 * Get backdrop image URL with appropriate size
 * @param {string} backdropUrl - Backdrop URL from API
 * @param {string} size - Size (w300, w780, w1280, original)
 * @returns {string} - Backdrop image URL
 */
export const getBackdropUrl = (backdropUrl, size = 'original') => {
  return getImageUrl(backdropUrl, size);
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
