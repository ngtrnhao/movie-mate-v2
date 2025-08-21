import axiosInstance from '../api/axios';

class UserInteractionService {
  constructor() {
    this.sessionId = this.generateSessionId();
    this.queue = [];
    this.isProcessing = false;
    this.batchSize = 10;
    this.flushInterval = 5000; // 5 seconds

    // Add deduplication tracking
    this.recentInteractions = new Map(); // action_movieId -> timestamp
    this.deduplicationWindow = 30000; // 30 seconds
    this.viewTrackingCooldown = new Map(); // movieId -> lastTrackedTime
    this.viewCooldownPeriod = 60000; // 1 minute for view actions

    this.startAutoFlush();
    this.startCleanupTimer();

    // Track page navigation for referrer detection
    this.trackPageNavigation();
  }

  generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  /**
   * Track page navigation for referrer detection
   */
  trackPageNavigation() {
    // Store current page as previous page when navigating
    const currentPage = window.location.href;
    const previousPage = sessionStorage.getItem('current_page');

    if (previousPage && previousPage !== currentPage) {
      sessionStorage.setItem('previous_page', previousPage);
    }

    sessionStorage.setItem('current_page', currentPage);

    // Listen for popstate events (back/forward navigation)
    window.addEventListener('popstate', () => {
      const newPage = window.location.href;
      sessionStorage.setItem('previous_page', currentPage);
      sessionStorage.setItem('current_page', newPage);
    });
  }

  /**
   * Track user interaction with a movie
   * @param {number} movieId - Movie ID
   * @param {string} action - Action type (view, click, favorite, etc.)
   * @param {object} metadata - Additional metadata
   */
  trackInteraction(movieId, action, metadata = {}) {
    if (!action) return;

    //  NEW: Check if user is authenticated before tracking
    const currentUser = this.getCurrentUser();
    if (!currentUser || !currentUser.id) {
      console.warn('User not authenticated, skipping interaction tracking:', action);
      return;
    }

    // Check for deduplication
    if (this.shouldDeduplicateInteraction(movieId, action)) {
      console.log(`🔄 Deduplicated interaction: ${action} for movie ${movieId}`);
      return;
    }

    // Enhanced referrer detection
    const getReferrer = () => {
      const referrer = document.referrer;
      if (referrer && referrer.length > 0) {
        return referrer;
      }

      // Fallback: Check if user came from internal navigation
      const previousPage = sessionStorage.getItem('previous_page');
      if (previousPage && previousPage !== window.location.href) {
        return previousPage;
      }

      // Fallback: Check if user came from search engine
      const searchEngines = ['google.com', 'bing.com', 'yahoo.com', 'duckduckgo.com'];
      const urlParams = new URLSearchParams(window.location.search);
      const utmSource = urlParams.get('utm_source');
      const utmMedium = urlParams.get('utm_medium');

      if (utmSource && searchEngines.some(engine => utmSource.includes(engine))) {
        return `https://${utmSource}`;
      }

      return 'direct_access';
    };

    const interaction = {
      movie_id: movieId,
      action: action,
      session_id: this.sessionId,
      timestamp: Date.now(),
      metadata: {
        ...metadata,
        page_url: window.location.href,
        referrer: getReferrer(),
        user_agent: navigator.userAgent,
        screen_resolution: `${window.screen.width}x${window.screen.height}`,
        viewport_size: `${window.innerWidth}x${window.innerHeight}`,
        duration_seconds: metadata.duration_seconds || null, // ✅ Move to metadata
      },
    };

    console.log('🔍 [trackInteraction] Debug:', {
      original_duration: metadata.duration_seconds,
      final_duration: interaction.metadata.duration_seconds,
      metadata_keys: Object.keys(metadata),
    });

    // Add user ID if available
    const user = this.getCurrentUser();
    if (user && user.id) {
      interaction.user_id = user.id;
    }

    // Record for deduplication
    this.recordInteractionForDeduplication(movieId, action);

    this.queue.push(interaction);
    console.log(`✅ Tracked interaction: ${action} for movie ${movieId}`, {
      duration_seconds: interaction.metadata.duration_seconds,
      has_duration: !!interaction.metadata.duration_seconds,
    });

    // Flush if queue is full
    if (this.queue.length >= this.batchSize) {
      this.flush();
    }
  }

  /**
   * Track homepage movie view
   * @param {number} movieId - Movie ID
   * @param {object} metadata - Additional metadata
   */
  trackHomepageView(movieId, metadata = {}) {
    this.trackInteraction(movieId, 'homepage_view', {
      ...metadata,
      page_type: 'homepage',
    });
  }

  /**
   * Track movie detail page view
   * @param {number} movieId - Movie ID
   * @param {object} metadata - Additional metadata
   */
  trackDetailView(movieId, metadata = {}) {
    this.trackInteraction(movieId, 'detail_view', {
      ...metadata,
      page_type: 'detail',
    });
  }

  /**
   * Track movie card click
   * @param {number} movieId - Movie ID
   * @param {object} metadata - Additional metadata
   */
  trackMovieClick(movieId, metadata = {}) {
    this.trackInteraction(movieId, 'click', {
      ...metadata,
      interaction_type: 'movie_card_click',
    });
  }

  /**
   * Track favorite action
   * @param {number} movieId - Movie ID
   * @param {boolean} isAdding - Whether adding or removing favorite
   */
  trackFavorite(movieId, isAdding = true) {
    this.trackInteraction(movieId, 'favorite', {
      action_type: isAdding ? 'add' : 'remove',
      interaction_type: 'favorite_button',
    });
  }

  /**
   * Track watchlist action
   * @param {number} movieId - Movie ID
   * @param {boolean} isAdding - Whether adding or removing from watchlist
   */
  trackWatchlist(movieId, isAdding = true) {
    this.trackInteraction(movieId, 'watchlist', {
      action_type: isAdding ? 'add' : 'remove',
      interaction_type: 'watchlist_button',
    });
  }

  /**
   * Track movie share
   * @param {number} movieId - Movie ID
   * @param {string} shareType - Share type (facebook, twitter, etc.)
   */
  trackShare(movieId, shareType = 'unknown') {
    this.trackInteraction(movieId, 'share', {
      share_type: shareType,
      interaction_type: 'share_button',
    });
  }

  /**
   * Track movie rating
   * @param {number} movieId - Movie ID
   * @param {number} rating - Rating value
   */
  trackRating(movieId, rating) {
    this.trackInteraction(movieId, 'rating', {
      rating_value: rating,
      interaction_type: 'rating_widget',
    });
  }

  /**
   * Track movie comment
   * @param {number} movieId - Movie ID
   * @param {string} commentType - Comment type (add, edit, delete)
   */
  trackComment(movieId, commentType = 'add') {
    this.trackInteraction(movieId, 'comment', {
      comment_type: commentType,
      interaction_type: 'comment_form',
    });
  }

  /**
   * Track movie trailer view
   * @param {number} movieId - Movie ID
   * @param {object} metadata - Additional metadata
   */
  trackTrailerView(movieId, metadata = {}) {
    // Use action from metadata if provided, otherwise default to 'trailer_view'
    const action = metadata.action || 'trailer_view';

    console.log('🔍 [trackTrailerView] Debug:', {
      movieId,
      action,
      metadata,
      duration_seconds: metadata.duration_seconds,
    });

    this.trackInteraction(movieId, action, {
      ...metadata,
      interaction_type: 'trailer_modal',
    });
  }

  /**
   * Track search interaction
   * @param {string} query - Search query
   * @param {array} resultIds - Array of movie IDs in results
   */
  trackSearch(query, resultIds = []) {
    // Track search query
    this.trackInteraction(null, 'search', {
      search_query: query,
      result_count: resultIds.length,
      interaction_type: 'search_form',
    });

    // Track search result views
    resultIds.forEach(movieId => {
      this.trackInteraction(movieId, 'search_result_view', {
        search_query: query,
        interaction_type: 'search_results',
      });
    });
  }

  /**
   * Get current user from localStorage or Redux store
   */
  getCurrentUser() {
    try {
      // Try to get from localStorage first
      const userStr = localStorage.getItem('user');
      if (userStr) {
        return JSON.parse(userStr);
      }

      // Try to get from Redux store if available
      if (window.__REDUX_STORE__) {
        const state = window.__REDUX_STORE__.getState();
        return state.auth?.user || null;
      }

      return null;
    } catch (error) {
      console.warn('Error getting current user:', error);
      return null;
    }
  }

  /**
   * Flush interactions to backend
   */
  async flush() {
    if (this.isProcessing || this.queue.length === 0) return;

    this.isProcessing = true;
    const batch = this.queue.splice(0, this.batchSize);

    try {
      const response = await axiosInstance.post('/api/auth/user-interactions/', {
        interactions: batch,
      });

      if (response.data.status === 'success') {
        console.log(`✅ Successfully sent ${response.data.data.processed} interactions`);
      } else {
        console.error('❌ Failed to send interactions:', response.data.message);
        // Put batch back at the beginning of queue on failure
        this.queue.unshift(...batch);
      }
    } catch (error) {
      console.error('❌ Error sending interactions:', error);
      // Put batch back at the beginning of queue on error
      this.queue.unshift(...batch);
    } finally {
      this.isProcessing = false;
    }
  }

  /**
   * Start automatic flushing
   */
  startAutoFlush() {
    setInterval(() => {
      if (this.queue.length > 0) {
        this.flush();
      }
    }, this.flushInterval);
  }

  /**
   * Force flush all pending interactions
   */
  async forceFlush() {
    while (this.queue.length > 0) {
      await this.flush();
    }
  }

  /**
   * Get interaction statistics
   */
  getStats() {
    return {
      sessionId: this.sessionId,
      pendingInteractions: this.queue.length,
      isProcessing: this.isProcessing,
      batchSize: this.batchSize,
      flushInterval: this.flushInterval,
    };
  }

  /**
   * Start cleanup timer for deduplication maps
   */
  startCleanupTimer() {
    setInterval(() => {
      this.cleanupDeduplicationMaps();
    }, 60000); // Clean every minute
  }

  /**
   * Clean up old entries from deduplication maps
   */
  cleanupDeduplicationMaps() {
    const now = Date.now();

    // Clean recent interactions
    for (const [key, timestamp] of this.recentInteractions.entries()) {
      if (now - timestamp > this.deduplicationWindow) {
        this.recentInteractions.delete(key);
      }
    }

    // Clean view tracking cooldown
    for (const [movieId, lastTracked] of this.viewTrackingCooldown.entries()) {
      if (now - lastTracked > this.viewCooldownPeriod) {
        this.viewTrackingCooldown.delete(movieId);
      }
    }
  }

  /**
   * Check if interaction should be deduplicated
   */
  shouldDeduplicateInteraction(movieId, action) {
    const key = `${action}_${movieId || 'null'}`;
    const now = Date.now();
    const lastTracked = this.recentInteractions.get(key);

    if (lastTracked && now - lastTracked < this.deduplicationWindow) {
      return true; // Should deduplicate
    }

    // Special handling for view actions
    if ((action === 'homepage_view' || action === 'detail_view') && movieId) {
      const lastViewTracked = this.viewTrackingCooldown.get(movieId);
      if (lastViewTracked && now - lastViewTracked < this.viewCooldownPeriod) {
        return true; // Should deduplicate
      }
    }

    return false; // Don't deduplicate
  }

  /**
   * Record interaction for deduplication
   */
  recordInteractionForDeduplication(movieId, action) {
    const key = `${action}_${movieId || 'null'}`;
    const now = Date.now();

    this.recentInteractions.set(key, now);

    // Special tracking for view actions
    if ((action === 'homepage_view' || action === 'detail_view') && movieId) {
      this.viewTrackingCooldown.set(movieId, now);
    }
  }
}

// Create singleton instance
const userInteractionService = new UserInteractionService();

// Auto-flush on page unload
window.addEventListener('beforeunload', () => {
  userInteractionService.forceFlush();
});

export default userInteractionService;
