import { useEffect, useRef } from 'react';
import userInteractionService from '../services/userInteractionService';

/**
 * Custom hook for tracking user interactions with improved spam prevention
 * @param {object} options - Configuration options
 * @returns {object} - Tracking functions
 */
const useUserTracking = (options = {}) => {
  const {
    enableAutoView = true,
    viewThreshold = 0.5,
    viewDelay = 1000,
    sessionTimeout = 30 * 60 * 1000, // 30 minutes
    maxViewsPerSession = 3, // Max views per movie per session
    cooldownPeriod = 5 * 60 * 1000, // 5 minutes cooldown between same movie views
  } = options;

  const viewTimeoutRef = useRef(null);
  const sessionStartTime = useRef(Date.now());
  const viewCounts = useRef(new Map()); // movieId -> { count, lastViewTime }
  const sentViews = useRef(new Set()); // NEW: Track sent movieIds in memory
  const sessionId = useRef(`session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

  // NEW: Load sentViews from sessionStorage on mount
  useEffect(() => {
    const stored = sessionStorage.getItem('sentHomepageViews');
    if (stored) {
      try {
        sentViews.current = new Set(JSON.parse(stored));
      } catch (e) {
        sentViews.current = new Set();
      }
    }
  }, []);

  // NEW: Save sentViews to sessionStorage when updated
  const saveSentViews = () => {
    sessionStorage.setItem('sentHomepageViews', JSON.stringify(Array.from(sentViews.current)));
  };

  /**
   * Check if session has expired
   */
  const isSessionExpired = () => {
    return Date.now() - sessionStartTime.current > sessionTimeout;
  };

  /**
   * Reset session data
   */
  const resetSession = () => {
    sessionStartTime.current = Date.now();
    viewCounts.current.clear();
    sessionId.current = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };

  /**
   * Check if movie view should be tracked based on session rules
   * @param {number} movieId - Movie ID
   * @returns {boolean} - Whether to track the view
   */
  const shouldTrackView = movieId => {
    if (!movieId) return false;

    // Reset session if expired
    if (isSessionExpired()) {
      resetSession();
      sentViews.current = new Set();
      saveSentViews();
    }

    // NEW: Check if already sent in this session
    if (sentViews.current.has(movieId)) {
      return false;
    }

    const now = Date.now();
    const movieData = viewCounts.current.get(movieId);

    if (!movieData) {
      // First view of this movie in session
      viewCounts.current.set(movieId, { count: 1, lastViewTime: now });
      sentViews.current.add(movieId); // Mark as sent
      saveSentViews();
      return true;
    }

    // Check cooldown period
    if (now - movieData.lastViewTime < cooldownPeriod) {
      return false;
    }

    // Check max views per session
    if (movieData.count >= maxViewsPerSession) {
      return false;
    }

    // Update view data
    movieData.count += 1;
    movieData.lastViewTime = now;
    sentViews.current.add(movieId); // Mark as sent
    saveSentViews();
    return true;
  };

  /**
   * Track homepage view with improved session management
   * @param {number} movieId - Movie ID
   * @param {object} metadata - Additional metadata
   */
  const trackHomepageView = (movieId, metadata = {}) => {
    if (!shouldTrackView(movieId)) return;

    // Add session info to metadata
    const enhancedMetadata = {
      ...metadata,
      sessionId: sessionId.current,
      sessionViewCount: viewCounts.current.get(movieId)?.count || 1,
      timestamp: Date.now(),
    };

    userInteractionService.trackHomepageView(movieId, enhancedMetadata);
  };

  /**
   * Track detail page view
   * @param {number} movieId - Movie ID
   * @param {object} metadata - Additional metadata
   */
  const trackDetailView = (movieId, metadata = {}) => {
    if (!movieId) return;

    // Add page duration tracking
    const pageStartTime = Date.now();
    const enhancedMetadata = {
      ...metadata,
      page_start_time: pageStartTime,
    };

    userInteractionService.trackDetailView(movieId, enhancedMetadata);

    // Track page duration when user leaves
    const handlePageLeave = () => {
      const duration = Date.now() - pageStartTime;
      if (duration > 5000) {
        // Chỉ track nếu ở lại ít nhất 5 giây
        userInteractionService.trackInteraction(movieId, 'page_duration', {
          duration_seconds: Math.floor(duration / 1000),
          page_type: 'detail',
        });
      }
      window.removeEventListener('beforeunload', handlePageLeave);
    };

    // Track page duration khi user navigate away
    const handleVisibilityChange = () => {
      if (document.hidden) {
        const duration = Date.now() - pageStartTime;
        if (duration > 5000) {
          // Chỉ track nếu ở lại ít nhất 5 giây
          userInteractionService.trackInteraction(movieId, 'page_duration', {
            duration_seconds: Math.floor(duration / 1000),
            page_type: 'detail',
            reason: 'visibility_change',
          });
        }
      }
    };

    window.addEventListener('beforeunload', handlePageLeave);
    document.addEventListener('visibilitychange', handleVisibilityChange);
  };

  /**
   * Track movie card click
   * @param {number} movieId - Movie ID
   * @param {object} metadata - Additional metadata
   */
  const trackMovieClick = (movieId, metadata = {}) => {
    if (!movieId) return;
    userInteractionService.trackMovieClick(movieId, metadata);
  };

  /**
   * Track favorite action
   * @param {number} movieId - Movie ID
   * @param {boolean} isAdding - Whether adding or removing favorite
   */
  const trackFavorite = (movieId, isAdding = true) => {
    if (!movieId) return;
    userInteractionService.trackFavorite(movieId, isAdding);
  };

  /**
   * Track watchlist action
   * @param {number} movieId - Movie ID
   * @param {boolean} isAdding - Whether adding or removing from watchlist
   */
  const trackWatchlist = (movieId, isAdding = true) => {
    if (!movieId) return;
    userInteractionService.trackWatchlist(movieId, isAdding);
  };

  /**
   * Track movie share
   * @param {number} movieId - Movie ID
   * @param {string} shareType - Share type
   */
  const trackShare = (movieId, shareType = 'unknown') => {
    if (!movieId) return;
    userInteractionService.trackShare(movieId, shareType);
  };

  /**
   * Track movie rating
   * @param {number} movieId - Movie ID
   * @param {number} rating - Rating value
   */
  const trackRating = (movieId, rating) => {
    if (!movieId || !rating) return;
    userInteractionService.trackRating(movieId, rating);
  };

  /**
   * Track movie comment
   * @param {number} movieId - Movie ID
   * @param {string} commentType - Comment type
   */
  const trackComment = (movieId, commentType = 'add') => {
    if (!movieId) return;
    userInteractionService.trackComment(movieId, commentType);
  };

  /**
   * Track trailer view
   * @param {number} movieId - Movie ID
   * @param {object} metadata - Additional metadata
   */
  const trackTrailerView = (movieId, metadata = {}) => {
    if (!movieId) return;
    userInteractionService.trackTrailerView(movieId, metadata);
  };

  /**
   * Track search interaction
   * @param {string} query - Search query
   * @param {array} resultIds - Array of movie IDs in results
   */
  const trackSearch = (query, resultIds = []) => {
    if (!query) return;
    userInteractionService.trackSearch(query, resultIds);
  };

  /**
   * Create intersection observer for automatic view tracking
   * @param {HTMLElement} element - Element to observe
   * @param {number} movieId - Movie ID
   * @param {object} metadata - Additional metadata
   */
  const createViewObserver = (element, movieId, metadata = {}) => {
    if (!element || !movieId || !enableAutoView) return null;

    let timeoutId = null;
    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting && entry.intersectionRatio >= viewThreshold) {
            timeoutId = setTimeout(() => {
              trackHomepageView(movieId, metadata);
            }, viewDelay);
          } else {
            if (timeoutId) {
              clearTimeout(timeoutId);
              timeoutId = null;
            }
          }
        });
      },
      {
        threshold: viewThreshold,
        rootMargin: '0px 0px -10% 0px',
      }
    );

    observer.observe(element);

    // Return cleanup function
    return () => {
      observer.disconnect();
      if (timeoutId) clearTimeout(timeoutId);
    };
  };

  /**
   * Get tracking statistics
   */
  const getTrackingStats = () => {
    return userInteractionService.getStats();
  };

  /**
   * Force flush pending interactions
   */
  const flushInteractions = async () => {
    await userInteractionService.forceFlush();
  };

  /**
   * Generic track interaction function
   * @param {object} params - Interaction parameters
   * @param {string} params.action - Action type
   * @param {number} params.movieId - Movie ID (optional)
   * @param {object} params.metadata - Additional metadata
   */
  const trackInteraction = ({ action, movieId, metadata = {} }) => {
    userInteractionService.trackInteraction(movieId, action, metadata);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (viewTimeoutRef.current) {
        clearTimeout(viewTimeoutRef.current);
      }
    };
  }, []);

  return {
    // Generic tracking function
    trackInteraction,

    // Tracking functions
    trackHomepageView,
    trackDetailView,
    trackMovieClick,
    trackFavorite,
    trackWatchlist,
    trackShare,
    trackRating,
    trackComment,
    trackTrailerView,
    trackSearch,

    // Utility functions
    createViewObserver,
    getTrackingStats,
    flushInteractions,

    // Service instance (for advanced usage)
    userInteractionService,
  };
};

export default useUserTracking;
