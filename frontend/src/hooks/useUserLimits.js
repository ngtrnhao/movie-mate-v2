import { useState, useEffect, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { getUserLimits, getUserType, isUnlimited, formatLimit } from '../utils/userPermissions';
import axiosInstance from '../api/axios';

export const useUserLimits = () => {
  const { user, isAuthenticated } = useSelector(state => state.auth);
  const [usageStats, setUsageStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Get user limits from frontend config
  const userLimits = getUserLimits(user);
  const userType = getUserType(user);

  // Fetch usage statistics from backend
  const fetchUsageStats = useCallback(async () => {
    if (!isAuthenticated || !user?.id) {
      setUsageStats(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axiosInstance.get('/api/auth/usage-stats/');
      if (response.data.status === 'success') {
        setUsageStats(response.data.data);
      } else {
        setError('Failed to fetch usage statistics');
      }
    } catch (err) {
      console.error('Error fetching usage stats:', err);
      setError(err.response?.data?.message || 'Failed to fetch usage statistics');
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, user?.id]);

  // Load usage stats on mount and when user changes
  useEffect(() => {
    fetchUsageStats();
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
    canPerformAction,
    getLimitDisplay,
    getUpgradeMessage,
    shouldShowUpgrade,

    // Helper functions
    isUnlimited: limit => isUnlimited(limit),
    formatLimit: (current, max) => formatLimit(current, max),
  };
};
