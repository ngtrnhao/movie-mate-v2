/**
 * Moderation Cache Service
 * Prevents duplicate API calls across all moderator dashboard components
 */

class ModerationCacheService {
  constructor() {
    this.cache = new Map();
    this.cacheTimestamps = new Map();
    this.ongoingRequests = new Map(); // Track ongoing requests to prevent duplicates
    this.defaultTTL = 30000; // 30 seconds default TTL
    this.apiTTLConfig = {
      // Different TTL for different APIs based on data freshness needs
      dashboard_overview_optimized: 120000, // 2min - Dashboard data can be cached longer
      dashboard_batch_data: 120000, // 2min - Batch dashboard data
      unified_moderation_queue: 45000, // 45s - Most dynamic
      moderation_queue_optimized: 60000, // 1min - Semi-dynamic
      ultra_optimized_moderation_queue: 45000, // 45s - Ultra-fast, shorter cache
      spoiler_statistics_optimized: 120000, // 2min - Stats change slowly
      auto_marked_reviews: 60000, // 1min - Semi-dynamic
      moderation_analytics: 300000, // 5min - Analytics data
      accuracy_summary: 300000, // 5min - Summary data
      moderation_config: 600000, // 10min - Config rarely changes
    };
    this.statsCallbacks = new Set();
    this.stats = {
      totalCalls: 0,
      cacheHits: 0,
      cacheMisses: 0,
      duplicatesPrevented: 0,
      apiCallHistory: [],
    };
    this.debugMode = false;
  }

  /**
   * Enable/disable debug logging
   */
  setDebugMode(enabled) {
    this.debugMode = enabled;
  }

  /**
   * Register a callback for stats updates
   */
  onStatsUpdate(callback) {
    this.statsCallbacks.add(callback);
    return () => this.statsCallbacks.delete(callback);
  }

  /**
   * Notify all registered callbacks about stats changes
   */
  notifyStatsUpdate() {
    this.statsCallbacks.forEach(callback => {
      try {
        callback(this.stats);
      } catch (error) {
        console.error('Error in stats callback:', error);
      }
    });
  }

  /**
   * Generate cache key from API endpoint and parameters
   */
  generateCacheKey(apiEndpoint, params = {}) {
    const sortedParams = Object.keys(params)
      .sort()
      .reduce((result, key) => {
        result[key] = params[key];
        return result;
      }, {});

    return `${apiEndpoint}:${JSON.stringify(sortedParams)}`;
  }

  /**
   * Get API name from endpoint for TTL configuration
   */
  getApiNameFromEndpoint(endpoint) {
    if (endpoint.includes('dashboard_overview_optimized')) return 'dashboard_overview_optimized';
    if (endpoint.includes('unified_moderation_queue')) return 'unified_moderation_queue';
    if (endpoint.includes('moderation_queue_optimized')) return 'moderation_queue_optimized';
    if (endpoint.includes('ultra_optimized_moderation_queue'))
      return 'ultra_optimized_moderation_queue';
    if (endpoint.includes('spoiler_statistics_optimized')) return 'spoiler_statistics_optimized';
    if (endpoint.includes('auto_marked_reviews')) return 'auto_marked_reviews';
    if (endpoint.includes('moderation_analytics')) return 'moderation_analytics';
    if (endpoint.includes('accuracy_summary')) return 'accuracy_summary';
    if (endpoint.includes('active_config')) return 'moderation_config';
    return 'default';
  }

  /**
   * Check if cache entry is still valid
   */
  isCacheValid(cacheKey) {
    if (!this.cache.has(cacheKey)) return false;

    const timestamp = this.cacheTimestamps.get(cacheKey);
    const apiName = this.getApiNameFromEndpoint(cacheKey);
    const ttl = this.apiTTLConfig[apiName] || this.defaultTTL;

    return Date.now() - timestamp < ttl;
  }

  /**
   * Get data from cache if valid
   */
  getCachedData(apiEndpoint, params = {}) {
    const cacheKey = this.generateCacheKey(apiEndpoint, params);

    if (this.isCacheValid(cacheKey)) {
      this.stats.cacheHits++;
      this.stats.duplicatesPrevented++;

      if (this.debugMode) {
        console.log(`🎯 Cache HIT for ${apiEndpoint}`, { params, cacheKey });
      }

      this.notifyStatsUpdate();
      return this.cache.get(cacheKey);
    }

    this.stats.cacheMisses++;
    this.notifyStatsUpdate();
    return null;
  }

  /**
   * Store data in cache
   */
  setCachedData(apiEndpoint, params = {}, data) {
    const cacheKey = this.generateCacheKey(apiEndpoint, params);
    this.cache.set(cacheKey, data);
    this.cacheTimestamps.set(cacheKey, Date.now());

    if (this.debugMode) {
      console.log(`💾 Cached data for ${apiEndpoint}`, { params, cacheKey });
    }
  }

  /**
   * Wrapper for API calls with caching and deduplication
   */
  async cachedApiCall(apiEndpoint, apiFunction, params = {}, options = {}) {
    // Generate cache key
    const cacheKey = this.generateCacheKey(apiEndpoint, params);

    // Check cache first
    const cachedData = this.getCachedData(apiEndpoint, params);
    if (cachedData && !options.bypassCache) {
      this.stats.cacheHits++;
      this.notifyStatsUpdate();
      return cachedData;
    }

    // Check if there's already an ongoing request for this exact call
    if (this.ongoingRequests.has(cacheKey)) {
      this.stats.duplicatesPrevented++;
      if (this.debugMode) {
        console.log(`🔄 Deduplicating API call: ${apiEndpoint}`, { params });
      }
      this.notifyStatsUpdate();
      return this.ongoingRequests.get(cacheKey);
    }

    // Track API call
    this.stats.totalCalls++;
    this.stats.cacheMisses++;
    const callInfo = {
      id: Date.now(),
      endpoint: apiEndpoint,
      params,
      timestamp: new Date().toISOString(),
      status: 'pending',
    };

    // Add to call history (keep last 20)
    this.stats.apiCallHistory.unshift(callInfo);
    if (this.stats.apiCallHistory.length > 20) {
      this.stats.apiCallHistory.pop();
    }

    if (this.debugMode) {
      console.log(`🔄 API call for ${apiEndpoint}`, { params });
    }

    // Create the request promise and store it
    const requestPromise = this._executeApiCall(apiEndpoint, apiFunction, params, callInfo);
    this.ongoingRequests.set(cacheKey, requestPromise);

    try {
      const data = await requestPromise;
      return data;
    } finally {
      // Clean up the ongoing request
      this.ongoingRequests.delete(cacheKey);
    }
  }

  /**
   * Execute the actual API call
   */
  async _executeApiCall(apiEndpoint, apiFunction, params, callInfo) {
    try {
      const startTime = Date.now();
      const data = await apiFunction(params);
      const responseTime = Date.now() - startTime;

      // Update call info
      const callIndex = this.stats.apiCallHistory.findIndex(call => call.id === callInfo.id);
      if (callIndex !== -1) {
        this.stats.apiCallHistory[callIndex] = {
          ...callInfo,
          status: 'success',
          responseTime,
        };
      }

      // Cache the result
      this.setCachedData(apiEndpoint, params, data);

      this.notifyStatsUpdate();
      return data;
    } catch (error) {
      // Update call info with error
      const callIndex = this.stats.apiCallHistory.findIndex(call => call.id === callInfo.id);
      if (callIndex !== -1) {
        this.stats.apiCallHistory[callIndex] = {
          ...callInfo,
          status: 'error',
          error: error.message,
        };
      }

      this.notifyStatsUpdate();
      throw error;
    }
  }

  /**
   * Invalidate cache for specific API or all
   */
  invalidateCache(apiEndpoint = null, params = {}) {
    if (apiEndpoint) {
      const cacheKey = this.generateCacheKey(apiEndpoint, params);
      this.cache.delete(cacheKey);
      this.cacheTimestamps.delete(cacheKey);

      if (this.debugMode) {
        console.log(`🗑️ Invalidated cache for ${apiEndpoint}`, { params });
      }
    } else {
      // Clear all cache
      this.cache.clear();
      this.cacheTimestamps.clear();

      if (this.debugMode) {
        console.log('🗑️ Cleared all cache');
      }
    }
  }

  /**
   * Get cache statistics
   */
  getStats() {
    const totalRequests = this.stats.cacheHits + this.stats.cacheMisses;
    const cacheHitRatio = totalRequests > 0 ? (this.stats.cacheHits / totalRequests) * 100 : 0;

    return {
      ...this.stats,
      cacheHitRatio: Math.round(cacheHitRatio * 100) / 100,
      totalRequests,
      cacheSize: this.cache.size,
      duplicatesPrevented: this.stats.duplicatesPrevented,
    };
  }

  /**
   * Get cache status for debug panel
   */
  getCacheStatus() {
    const now = Date.now();
    const entries = [];

    for (const [cacheKey, timestamp] of this.cacheTimestamps.entries()) {
      const apiName = this.getApiNameFromEndpoint(cacheKey);
      const ttl = this.apiTTLConfig[apiName] || this.defaultTTL;
      const age = now - timestamp;
      const isValid = age < ttl;

      entries.push({
        key: cacheKey,
        apiName,
        age: Math.round(age / 1000), // in seconds
        ttl: Math.round(ttl / 1000), // in seconds
        isValid,
        remainingTime: isValid ? Math.round((ttl - age) / 1000) : 0,
      });
    }

    return entries.sort((a, b) => b.age - a.age); // Sort by age, newest first
  }

  /**
   * Reset all statistics
   */
  resetStats() {
    this.stats = {
      totalCalls: 0,
      cacheHits: 0,
      cacheMisses: 0,
      duplicatesPrevented: 0,
      apiCallHistory: [],
    };
    this.notifyStatsUpdate();
  }

  /**
   * Get performance metrics
   */
  getPerformanceMetrics() {
    const total = this.stats.totalCalls;
    const cacheHitRate = total > 0 ? (this.stats.cacheHits / total) * 100 : 0;
    const duplicatePreventionRate = total > 0 ? (this.stats.duplicatesPrevented / total) * 100 : 0;

    return {
      totalCalls: total,
      cacheHitRate: Math.round(cacheHitRate * 100) / 100,
      duplicatePreventionRate: Math.round(duplicatePreventionRate * 100) / 100,
      cacheHits: this.stats.cacheHits,
      cacheMisses: this.stats.cacheMisses,
      duplicatesPrevented: this.stats.duplicatesPrevented,
      ongoingRequests: this.ongoingRequests.size,
      cacheSize: this.cache.size,
    };
  }

  /**
   * Preload cache with data
   */
  preloadCache(apiEndpoint, params = {}, data) {
    this.setCachedData(apiEndpoint, params, data);
  }
}

// Create singleton instance
const moderationCacheService = new ModerationCacheService();

// Enable debug mode in development
if (process.env.NODE_ENV === 'development') {
  moderationCacheService.setDebugMode(true);
}

export default moderationCacheService;

// Export specific methods for convenience
export const {
  cachedApiCall,
  invalidateCache,
  getStats,
  getCacheStatus,
  onStatsUpdate,
  setDebugMode,
  resetStats,
  preloadCache,
} = moderationCacheService;
