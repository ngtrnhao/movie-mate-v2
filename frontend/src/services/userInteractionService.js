import axiosInstance from '../api/axios';

class UserInteractionService {
  constructor() {
    this.sessionId = this.generateSessionId();
    this.queue = [];
    this.isProcessing = false;
    this.batchSize = 10;
    this.flushInterval = 5000; // 5 seconds
    this.startAutoFlush();
  }

  generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  /**
   * Track user interaction with a movie
   * @param {number} movieId - Movie ID
   * @param {string} action - Action type (view, click, favorite, etc.)
   * @param {object} metadata - Additional metadata
   */
  trackInteraction(movieId, action, metadata = {}) {
    if (!movieId || !action) return;

    const interaction = {
      movie_id: movieId,
      action: action,
      session_id: this.sessionId,
      timestamp: new Date().toISOString(),
      metadata: {
        ...metadata,
        page_url: window.location.href,
        user_agent: navigator.userAgent,
        screen_resolution: `${window.screen.width}x${window.screen.height}`,
        viewport_size: `${window.innerWidth}x${window.innerHeight}`,
      },
    };

    // Add user ID if available
    const user = this.getCurrentUser();
    if (user && user.id) {
      interaction.user_id = user.id;
    }

    this.queue.push(interaction);

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
    this.trackInteraction(movieId, 'trailer_view', {
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
}

// Create singleton instance
const userInteractionService = new UserInteractionService();

// Auto-flush on page unload
window.addEventListener('beforeunload', () => {
  userInteractionService.forceFlush();
});

export default userInteractionService;
