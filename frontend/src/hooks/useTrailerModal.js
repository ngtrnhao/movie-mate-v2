import { useState, useCallback } from 'react';

/**
 * Custom hook to manage trailer modal state and functionality
 * @returns {Object} Modal state and handlers
 */
export const useTrailerModal = () => {
  const [isTrailerOpen, setIsTrailerOpen] = useState(false);
  const [modalMovie, setModalMovie] = useState(null);
  const [modalTrailerUrl, setModalTrailerUrl] = useState(null);

  /**
   * Open trailer modal with movie and trailer URL
   * @param {Object} movie - Movie object
   * @param {string} trailerUrl - Trailer URL (YouTube watch URL or embed URL)
   */
  const openTrailerModal = useCallback((movie, trailerUrl) => {
    if (!movie) {
      console.warn('useTrailerModal: No movie provided');
      return;
    }

    if (!trailerUrl) {
      console.warn('useTrailerModal: No trailer URL provided for movie:', movie.title);
      return;
    }

    setModalMovie(movie);
    setModalTrailerUrl(trailerUrl);
    setIsTrailerOpen(true);
  }, []);

  /**
   * Close trailer modal and reset state
   */
  const closeTrailerModal = useCallback(() => {
    setIsTrailerOpen(false);
    setModalMovie(null);
    setModalTrailerUrl(null);
  }, []);

  /**
   * Get trailer URL from movie object
   * @param {Object} movie - Movie object with trailers array
   * @returns {string|null} Trailer URL or null if not found
   */
  const getTrailerUrl = useCallback(movie => {
    if (!movie?.trailers || !Array.isArray(movie.trailers)) {
      return null;
    }

    // Find the first TRAILER type
    const trailerObj = movie.trailers.find(t => t.type === 'TRAILER');
    if (!trailerObj?.youtube_key) {
      return null;
    }

    return `https://www.youtube.com/watch?v=${trailerObj.youtube_key}`;
  }, []);

  /**
   * Handle trailer button click
   * @param {Object} movie - Movie object
   */
  const handleTrailerClick = useCallback(
    movie => {
      const trailerUrl = getTrailerUrl(movie);
      openTrailerModal(movie, trailerUrl);
    },
    [getTrailerUrl, openTrailerModal]
  );

  return {
    // State
    isTrailerOpen,
    modalMovie,
    modalTrailerUrl,

    // Handlers
    openTrailerModal,
    closeTrailerModal,
    getTrailerUrl,
    handleTrailerClick,
  };
};
