import axiosInstance from './axios';

// =====================================================
// DASHBOARD STATISTICS API
// =====================================================

/**
 * Get real-time dashboard statistics for moderator
 * Replaces hardcoded stats in Dashboard.jsx getDashboardStats()
 */
export const getDashboardStatistics = async () => {
  try {
    const response = await axiosInstance.get('/api/admin/movies/dashboard_statistics/');
    return response.data;
  } catch (error) {
    console.error('Error fetching dashboard statistics:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch dashboard statistics',
      details: error.response?.data,
    };
  }
};

/**
 * Get navigation badge counts for all moderator sections
 * Replaces hardcoded badges in Dashboard.jsx getNavigationItems()
 */
export const getNavigationBadgeCounts = async () => {
  try {
    const response = await axiosInstance.get('/api/admin/movies/navigation_badge_counts/');
    return response.data;
  } catch (error) {
    console.error('Error fetching navigation badge counts:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch badge counts',
      details: error.response?.data,
    };
  }
};

/**
 * Get real-time moderation queue statistics
 * For view-specific stats in moderation queue section
 */
export const getModerationQueueStats = async () => {
  try {
    const response = await axiosInstance.get('/api/movies/reviews/moderation_stats/');
    return response.data;
  } catch (error) {
    console.error('Error fetching moderation queue stats:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch queue statistics',
      details: error.response?.data,
    };
  }
};

// =====================================================
// DASHBOARD OVERVIEW API
// =====================================================

/**
 * Get dashboard overview data
 * Replaces all hardcoded data in DashboardOverview.jsx
 */
export const getDashboardOverview = async () => {
  try {
    const response = await axiosInstance.get('/api/admin/movies/dashboard_overview_data/');
    return response.data;
  } catch (error) {
    console.error('Error fetching dashboard overview:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch dashboard overview',
      details: error.response?.data,
    };
  }
};

/**
 * Get recent moderation activities
 * Replaces hardcoded recentActivities in DashboardOverview.jsx
 */
export const getRecentModerationActivities = async (limit = 10) => {
  try {
    const response = await axiosInstance.get('/api/admin/movies/dashboard_overview_data/');
    return {
      data: response.data?.data?.recent_activities || [],
    };
  } catch (error) {
    console.error('Error fetching recent activities:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch recent activities',
      details: error.response?.data,
    };
  }
};

/**
 * Get moderation performance metrics
 * Replaces hardcoded performance metrics in DashboardOverview.jsx
 */
export const getModerationPerformanceMetrics = async () => {
  try {
    const response = await axiosInstance.get('/api/admin/movies/dashboard_overview_data/');
    return {
      data: response.data?.data?.performance_metrics || {},
    };
  } catch (error) {
    console.error('Error fetching performance metrics:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch performance metrics',
      details: error.response?.data,
    };
  }
};

// =====================================================
// USER MANAGEMENT API
// =====================================================

/**
 * Get flagged users for moderation
 * Replaces mock data in UserManagement.jsx
 */
export const getFlaggedUsers = async (params = {}) => {
  try {
    const { page = 1, pageSize = 20, status = 'all', sortBy = 'report_count' } = params;

    const response = await axiosInstance.get('/api/auth/moderator-dashboard/flagged_users/', {
      params: {
        page,
        page_size: pageSize,
        status,
        sort_by: sortBy,
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching flagged users:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch flagged users',
      details: error.response?.data,
    };
  }
};

/**
 * Take moderation action on a user
 * Handle warnings, bans, reactivation
 */
export const moderateUser = async (userId, action, reason = '', durationDays = 0) => {
  try {
    const response = await axiosInstance.post(
      `/api/users/moderator-dashboard/${userId}/moderate_user/`,
      {
        action,
        reason,
        duration_days: durationDays,
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error moderating user:', error);
    throw {
      error: error.response?.data?.message || 'Failed to moderate user',
      details: error.response?.data,
    };
  }
};

// =====================================================
// SYSTEM NOTIFICATIONS API
// =====================================================

/**
 * Get system notifications for moderator dashboard
 * Replaces hardcoded notifications in frontend
 */
export const getSystemNotifications = async () => {
  try {
    const response = await axiosInstance.get('/api/auth/moderator-dashboard/system_notifications/');
    return response.data;
  } catch (error) {
    console.error('Error fetching system notifications:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch notifications',
      details: error.response?.data,
    };
  }
};

/**
 * Mark notification as read
 * Update notification status
 */
export const markNotificationRead = async notificationId => {
  try {
    // For now, this is a placeholder since we don't have read status persistence
    const response = await axiosInstance.post(
      `/api/users/moderator-dashboard/notifications/${notificationId}/mark_read/`
    );
    return response.data;
  } catch (error) {
    console.error('Error marking notification as read:', error);
    throw {
      error: error.response?.data?.message || 'Failed to mark notification as read',
      details: error.response?.data,
    };
  }
};

// =====================================================
// SYSTEM SETTINGS API
// =====================================================

/**
 * Get comprehensive system settings
 * Replaces hardcoded settings in SystemSettings.jsx
 */
export const getSystemSettings = async () => {
  try {
    const response = await axiosInstance.get('/api/moderation-config/system_settings/');
    return response.data;
  } catch (error) {
    console.error('Error fetching system settings:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch system settings',
      details: error.response?.data,
    };
  }
};

/**
 * Update system settings
 * Handle configuration updates from admin interface
 */
export const updateSystemSettings = async settings => {
  try {
    const response = await axiosInstance.post(
      '/api/moderation-config/update_system_settings/',
      settings
    );
    return response.data;
  } catch (error) {
    console.error('Error updating system settings:', error);
    throw {
      error: error.response?.data?.message || 'Failed to update system settings',
      details: error.response?.data,
    };
  }
};

/**
 * Get performance analytics for admin dashboard
 * Detailed metrics and trends
 */
export const getPerformanceAnalytics = async () => {
  try {
    const response = await axiosInstance.get('/api/moderation-config/performance_analytics/');
    return response.data;
  } catch (error) {
    console.error('Error fetching performance analytics:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch performance analytics',
      details: error.response?.data,
    };
  }
};

// =====================================================
// MODERATION ACTIONS API
// =====================================================

/**
 * Get moderation queue items
 * Already exists in movieService but adding for completeness
 */
export const getModerationQueue = async (params = {}) => {
  try {
    const response = await axiosInstance.get('/api/movies/reviews/moderation_queue/', {
      params,
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching moderation queue:', error);
    throw {
      error: error.response?.data?.message || 'Failed to fetch moderation queue',
      details: error.response?.data,
    };
  }
};

/**
 * Moderate a review
 * Approve or reject content
 */
export const moderateReview = async (reviewId, action, reason = '') => {
  try {
    const response = await axiosInstance.post(`/api/movies/reviews/${reviewId}/moderate/`, {
      action,
      reason,
    });
    return response.data;
  } catch (error) {
    console.error('Error moderating review:', error);
    throw {
      error: error.response?.data?.message || 'Failed to moderate review',
      details: error.response?.data,
    };
  }
};

/**
 * Bulk moderate reviews
 * Handle multiple reviews at once
 */
export const bulkModerateReviews = async (reviewIds, action, reason = '') => {
  try {
    const response = await axiosInstance.post('/api/movies/reviews/bulk_moderate/', {
      review_ids: reviewIds,
      action,
      reason,
    });
    return response.data;
  } catch (error) {
    console.error('Error bulk moderating reviews:', error);
    throw {
      error: error.response?.data?.message || 'Failed to bulk moderate reviews',
      details: error.response?.data,
    };
  }
};

// =====================================================
// HELPER FUNCTIONS
// =====================================================

/**
 * Get all dashboard data in one call
 * Optimized for dashboard initialization
 */
export const getAllDashboardData = async () => {
  try {
    const [statistics, badges, overview, notifications] = await Promise.allSettled([
      getDashboardStatistics(),
      getNavigationBadgeCounts(),
      getDashboardOverview(),
      getSystemNotifications(),
    ]);

    return {
      statistics: statistics.status === 'fulfilled' ? statistics.value : null,
      badges: badges.status === 'fulfilled' ? badges.value : null,
      overview: overview.status === 'fulfilled' ? overview.value : null,
      notifications: notifications.status === 'fulfilled' ? notifications.value : null,
      errors: [
        statistics.status === 'rejected' ? statistics.reason : null,
        badges.status === 'rejected' ? badges.reason : null,
        overview.status === 'rejected' ? overview.reason : null,
        notifications.status === 'rejected' ? notifications.reason : null,
      ].filter(Boolean),
    };
  } catch (error) {
    console.error('Error fetching all dashboard data:', error);
    throw {
      error: 'Failed to fetch complete dashboard data',
      details: error,
    };
  }
};

/**
 * Refresh all cache and fetch latest data
 * Force refresh without cache
 */
export const refreshAllData = async () => {
  try {
    // Add cache busting parameter
    const timestamp = Date.now();

    const statistics = await axiosInstance.get('/api/admin/movies/dashboard_statistics/', {
      params: { _t: timestamp },
    });

    const badges = await axiosInstance.get('/api/admin/reviews/navigation_badge_counts/', {
      params: { _t: timestamp },
    });

    return {
      statistics: statistics.data,
      badges: badges.data,
      refreshed_at: new Date().toISOString(),
    };
  } catch (error) {
    console.error('Error refreshing data:', error);
    throw {
      error: 'Failed to refresh data',
      details: error.response?.data,
    };
  }
};
