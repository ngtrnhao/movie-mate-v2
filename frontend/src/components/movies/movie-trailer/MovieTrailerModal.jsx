import { X, Play, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState, useRef } from 'react';
import ReactDOM from 'react-dom';
import useUserTracking from '../../../hooks/useUserTracking';

const MovieTrailerModal = ({ isOpen, onClose, movie, trailerUrl }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [embedUrl, setEmbedUrl] = useState(null);
  const iframeRef = useRef(null);
  const [startTime, setStartTime] = useState(null);
  const [watchedDuration, setWatchedDuration] = useState(0);
  const watchTimer = useRef(null);

  const { trackTrailerView } = useUserTracking();

  // Track trailer viewing duration
  useEffect(() => {
    if (isOpen && movie && !startTime) {
      // Only track once when modal opens
      const start = Date.now();
      setStartTime(start);

      // Start timer to track viewing duration
      watchTimer.current = setInterval(() => {
        const elapsed = Date.now() - start;
        setWatchedDuration(elapsed);
      }, 1000);

      // Track trailer view start - only once when modal opens
      trackTrailerView(movie.id, {
        action: 'trailer_start',
        timestamp: start,
        url: trailerUrl,
      });

      return () => {
        if (watchTimer.current) {
          clearInterval(watchTimer.current);
        }
      };
    }
  }, [isOpen, movie, trailerUrl, trackTrailerView, startTime]); // Added startTime to deps

  // Track trailer completion on close
  useEffect(() => {
    return () => {
      if (startTime && watchedDuration > 0 && movie) {
        const completionPercentage = Math.min((watchedDuration / 1000 / 120) * 100, 100); // Assuming 2min average trailer

        // Track completion if watched more than 80%
        if (completionPercentage >= 80) {
          trackTrailerView(movie.id, {
            action: 'trailer_completion',
            duration: watchedDuration,
            completion_percentage: completionPercentage,
          });
        }

        // Always track end event
        trackTrailerView(movie.id, {
          action: 'trailer_end',
          duration: watchedDuration,
          completion_percentage: completionPercentage,
        });
      }
    };
  }, [movie, startTime, watchedDuration, trackTrailerView]);

  useEffect(() => {
    if (isOpen) {
      // Reset states when modal opens
      setIsLoading(true);
      setError(null);
      console.log('MovieTrailerModal - Opening with URL:', trailerUrl);

      // Convert YouTube watch URL to embed URL if needed
      if (trailerUrl && !trailerUrl.includes('embed')) {
        const convertedUrl = trailerUrl.replace('watch?v=', 'embed/');
        console.log('MovieTrailerModal - Converting to embed URL:', convertedUrl);
        setEmbedUrl(convertedUrl);
      } else if (trailerUrl) {
        console.log('MovieTrailerModal - Using existing embed URL:', trailerUrl);
        setEmbedUrl(trailerUrl);
      } else {
        console.error('MovieTrailerModal - No trailer URL provided');
        setError('No trailer URL available');
        setIsLoading(false);
      }
    } else {
      // Reset iframe src when modal closes to stop video
      if (iframeRef.current) {
        iframeRef.current.src = '';
      }
      setEmbedUrl(null);
    }
  }, [isOpen, trailerUrl]);

  // Set iframe src when embedUrl changes
  useEffect(() => {
    if (embedUrl && iframeRef.current) {
      console.log('MovieTrailerModal - Setting iframe src to:', embedUrl);
      iframeRef.current.src = embedUrl;
    }
  }, [embedUrl]);

  const handleClose = () => {
    console.log('MovieTrailerModal - Closing modal');

    // Clear watch timer
    if (watchTimer.current) {
      clearInterval(watchTimer.current);
      watchTimer.current = null;
    }

    // Reset tracking states
    setStartTime(null);
    setWatchedDuration(0);

    onClose();
  };

  const handleIframeLoad = () => {
    console.log('MovieTrailerModal - Iframe loaded successfully');
    setIsLoading(false);
  };

  const handleIframeError = () => {
    console.error('MovieTrailerModal - Failed to load trailer iframe');
    setError('Failed to load trailer');
    setIsLoading(false);
  };

  // Suppress console errors from ad blockers and tracking
  useEffect(() => {
    if (isOpen) {
      const originalError = console.error;
      const originalWarn = console.warn;

      // Temporarily suppress tracking-related errors
      console.error = (...args) => {
        const message = args[0]?.toString() || '';
        if (
          message.includes('ERR_BLOCKED_BY_CLIENT') ||
          message.includes('play.google.com/log') ||
          message.includes('youtube.com/youtubei/v1/log_event')
        ) {
          // Suppress these specific errors
          return;
        }
        originalError.apply(console, args);
      };

      console.warn = (...args) => {
        const message = args[0]?.toString() || '';
        if (
          message.includes('ERR_BLOCKED_BY_CLIENT') ||
          message.includes('play.google.com/log') ||
          message.includes('youtube.com/youtubei/v1/log_event')
        ) {
          // Suppress these specific warnings
          return;
        }
        originalWarn.apply(console, args);
      };

      return () => {
        console.error = originalError;
        console.warn = originalWarn;
      };
    }
  }, [isOpen]);

  // Handle keyboard events
  useEffect(() => {
    const handleKeyDown = e => {
      if (e.key === 'Escape') {
        handleClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      // Restore body scroll when modal is closed
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return ReactDOM.createPortal(
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 p-2 backdrop-blur-sm sm:p-4"
          onClick={handleClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ type: 'spring', duration: 0.5 }}
            className="relative w-full max-w-4xl rounded-lg bg-gray-900 shadow-2xl"
            onClick={e => e.stopPropagation()}
          >
            {/* Header - Responsive */}
            <div className="flex items-center justify-between border-b border-gray-800 p-3 sm:p-4">
              <div className="flex items-center gap-2 sm:gap-3">
                <Play className="size-4 text-red-600 sm:size-5" />
                <h2 className="text-sm font-semibold text-white sm:text-xl">
                  {movie?.title} - Trailer
                </h2>
              </div>
              <button
                onClick={handleClose}
                className="rounded-full p-1 text-gray-400 transition-colors hover:bg-gray-800 hover:text-white"
              >
                <X className="size-5 sm:size-6" />
              </button>
            </div>

            {/* Content - Responsive aspect ratio */}
            <div className="relative aspect-video w-full">
              {isLoading && (
                <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                  <Loader2 className="size-6 animate-spin text-red-600 sm:size-8" />
                </div>
              )}

              {error ? (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-gray-900 p-4 text-white">
                  <p className="text-base font-medium text-red-500 sm:text-lg">{error}</p>
                  <button
                    onClick={handleClose}
                    className="rounded-md bg-red-600 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700 sm:px-4"
                  >
                    Close
                  </button>
                </div>
              ) : (
                <iframe
                  ref={iframeRef}
                  src={embedUrl}
                  style={{ border: 'none', minHeight: 200, minWidth: 300 }}
                  className="size-full rounded-b-lg"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  allowFullScreen
                  onLoad={handleIframeLoad}
                  onError={handleIframeError}
                  title={`${movie?.title} - Trailer`}
                />
              )}
            </div>

            {/* Footer - Responsive */}
            <div className="border-t border-gray-800 p-3 sm:p-4">
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-gray-400 sm:gap-4 sm:text-sm">
                <div className="flex items-center gap-2 sm:gap-4">
                  <span>{movie?.release_date?.split('-')[0]}</span>
                  {movie?.runtime && (
                    <span>
                      {Math.floor(movie.runtime / 60)}h {movie.runtime % 60}m
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1 sm:gap-2">
                  <span className="text-yellow-500">★</span>
                  <span>{movie?.vote_average?.toFixed(1)}</span>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body
  );
};

export default MovieTrailerModal;
