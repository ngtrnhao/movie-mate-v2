import { useState, useEffect, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { getUserLimits, getUserType, isUnlimited, formatLimit } from '../utils/userPermissions';
import axiosInstance from '../api/axios';

// Global state manager để tránh nhiều component gọi API cùng lúc
class UsageStatsManager {
  constructor() {
    this.cache = null;
    this.lastFetchTime = 0;
    this.cacheDuration = 30000; // 30 giây
    this.pendingRequest = null;
    this.subscribers = new Set();
    this.abortController = null;
  }

  async fetchUsageStats(forceRefresh = false) {
    // Kiểm tra cache
    const now = Date.now();
    if (!forceRefresh && this.cache && now - this.lastFetchTime < this.cacheDuration) {
      return this.cache;
    }

    // Nếu đang có request pending, đợi request đó
    if (this.pendingRequest) {
      return this.pendingRequest;
    }

    // Hủy request trước đó nếu có
    if (this.abortController) {
      this.abortController.abort();
    }

    // Tạo abort controller mới
    this.abortController = new AbortController();

    // Tạo promise mới
    this.pendingRequest = this._makeRequest();

    try {
      const result = await this.pendingRequest;
      return result;
    } finally {
      this.pendingRequest = null;
    }
  }

  async _makeRequest() {
    try {
      const response = await axiosInstance.get('/api/auth/usage-stats/', {
        signal: this.abortController.signal,
      });

      if (response.data.status === 'success') {
        const newStats = response.data.data;

        // Cập nhật cache
        this.cache = newStats;
        this.lastFetchTime = Date.now();

        // Thông báo cho tất cả subscribers
        this.notifySubscribers(newStats);

        return newStats;
      } else {
        throw new Error('Failed to fetch usage statistics');
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        throw err;
      }
      console.error('Error fetching usage stats:', err);
      throw err;
    }
  }

  subscribe(callback) {
    this.subscribers.add(callback);
    // Trả về unsubscribe function
    return () => {
      this.subscribers.delete(callback);
    };
  }

  notifySubscribers(data) {
    this.subscribers.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error('Error in subscriber callback:', error);
      }
    });
  }

  getCachedData() {
    return this.cache;
  }

  clearCache() {
    this.cache = null;
    this.lastFetchTime = 0;
  }
}

// Singleton instance
const usageStatsManager = new UsageStatsManager();

export const useUserLimits = () => {
  const { user, isAuthenticated } = useSelector(state => state.auth);
  const [usageStats, setUsageStats] = useState(usageStatsManager.getCachedData());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Get user limits from frontend config
  const userLimits = getUserLimits(user);
  const userType = getUserType(user);

  // Fetch usage statistics from backend
  const fetchUsageStats = useCallback(
    async (forceRefresh = false) => {
      if (!isAuthenticated || !user?.id) {
        setUsageStats(null);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const result = await usageStatsManager.fetchUsageStats(forceRefresh);
        setUsageStats(result);
      } catch (err) {
        if (err.name === 'AbortError') {
          return;
        }
        console.error('Error fetching usage stats:', err);
        setError(err.response?.data?.message || 'Failed to fetch usage statistics');
      } finally {
        setLoading(false);
      }
    },
    [isAuthenticated, user?.id]
  );

  // Subscribe to global manager updates
  useEffect(() => {
    if (!isAuthenticated || !user?.id) {
      setUsageStats(null);
      return;
    }

    // Subscribe to global updates
    const unsubscribe = usageStatsManager.subscribe(setUsageStats);

    // Fetch initial data if not cached
    if (!usageStatsManager.getCachedData()) {
      fetchUsageStats();
    } else {
      setUsageStats(usageStatsManager.getCachedData());
    }

    return unsubscribe;
  }, [isAuthenticated, user?.id]);

  // Refresh usage stats (force refresh)
  const refreshUsageStats = useCallback(() => {
    fetchUsageStats(true);
  }, [fetchUsageStats]);

  // Check if user can perform an action
  const canPerformAction = useCallback(
    action => {
      if (!user) return false;

      switch (action) {
        case 'add_favorite':
          if (isUnlimited(userLimits.favorites)) return true;
          return usageStats?.favorites?.remaining > 0;

        case 'create_list':
          if (isUnlimited(userLimits.lists)) return true;
          return usageStats?.lists?.remaining > 0;

        case 'write_review':
          if (isUnlimited(userLimits.reviews_per_day)) return true;
          return usageStats?.reviews_today?.remaining > 0;

        case 'add_mood':
          if (isUnlimited(userLimits.moods)) return true;
          return usageStats?.moods?.remaining > 0;

        default:
          return false;
      }
    },
    [user, userLimits, usageStats]
  );

  // Get formatted limit display
  const getLimitDisplay = useCallback(
    feature => {
      if (!usageStats) return 'Loading...';

      switch (feature) {
        case 'favorites':
          return formatLimit(usageStats.favorites.current, usageStats.favorites.max);

        case 'lists':
          return formatLimit(usageStats.lists.current, usageStats.lists.max);

        case 'reviews_today':
          return formatLimit(usageStats.reviews_today.current, usageStats.reviews_today.max);

        case 'moods':
          return formatLimit(usageStats.moods.current, usageStats.moods.max);

        default:
          return 'N/A';
      }
    },
    [usageStats]
  );

  // Get upgrade message for a feature
  const getUpgradeMessage = useCallback(
    feature => {
      if (!user) return 'Please login to use this feature';

      const featureNames = {
        favorites: 'favorite movies',
        lists: 'watchlists',
        reviews_today: 'reviews per day',
        moods: 'mood preferences',
      };

      const featureName = featureNames[feature] || feature;

      if (userType === 'guest') {
        return `Please upgrade to add ${featureName}`;
      }

      return `Upgrade your plan to add more ${featureName}`;
    },
    [user, userType]
  );

  // Check if user should see upgrade prompt
  const shouldShowUpgrade = useCallback(
    feature => {
      if (!user) return false;

      switch (feature) {
        case 'add_favorite':
          return !isUnlimited(userLimits.favorites) && usageStats?.favorites?.remaining === 0;

        case 'create_list':
          return !isUnlimited(userLimits.lists) && usageStats?.lists?.remaining === 0;

        case 'write_review':
          return (
            !isUnlimited(userLimits.reviews_per_day) && usageStats?.reviews_today?.remaining === 0
          );

        case 'add_mood':
          return !isUnlimited(userLimits.moods) && usageStats?.moods?.remaining === 0;

        default:
          return false;
      }
    },
    [user, userLimits, usageStats]
  );

  return {
    // State
    usageStats,
    loading,
    error,

    // User info
    userLimits,
    userType,

    // Actions
    fetchUsageStats,
    refreshUsageStats, // Thêm refreshUsageStats vào trả về
    canPerformAction,
    getLimitDisplay,
    getUpgradeMessage,
    shouldShowUpgrade,

    // Helper functions
    isUnlimited: limit => isUnlimited(limit),
    formatLimit: (current, max) => formatLimit(current, max),
  };
};
