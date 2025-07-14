import React, {
  createContext,
  useContext,
  useReducer,
  useCallback,
  useEffect,
  useRef,
} from 'react';
import {
  getDashboardOverview,
  getProductionMetrics,
  getTrendingAnalytics,
  getUserInteractionStats,
} from '../api/adminMovieService';

// Action types
const ACTIONS = {
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  SET_DASHBOARD_DATA: 'SET_DASHBOARD_DATA',
  SET_PRODUCTION_METRICS: 'SET_PRODUCTION_METRICS',
  SET_TRENDING_ANALYTICS: 'SET_TRENDING_ANALYTICS',
  SET_USER_INTERACTION_STATS: 'SET_USER_INTERACTION_STATS',
  SET_LAST_UPDATED: 'SET_LAST_UPDATED',
  CLEAR_ERROR: 'CLEAR_ERROR',
};

// Initial state
const initialState = {
  // Data
  dashboardData: null,
  productionMetrics: null,
  trendingAnalytics: null,
  userInteractionStats: null,

  // Loading states
  loading: {
    dashboard: false,
    production: false,
    trending: false,
    userInteraction: false,
  },

  // Error states
  errors: {
    dashboard: null,
    production: null,
    trending: null,
    userInteraction: null,
  },

  // Cache timestamps
  lastUpdated: {
    dashboard: null,
    production: null,
    trending: null,
    userInteraction: null,
  },

  // Settings
  autoRefresh: true,
  refreshInterval: 30000, // 30 seconds default
};

// Reducer
const adminDataReducer = (state, action) => {
  switch (action.type) {
    case ACTIONS.SET_LOADING:
      return {
        ...state,
        loading: {
          ...state.loading,
          [action.dataType]: action.loading,
        },
      };

    case ACTIONS.SET_ERROR:
      return {
        ...state,
        errors: {
          ...state.errors,
          [action.dataType]: action.error,
        },
        loading: {
          ...state.loading,
          [action.dataType]: false,
        },
      };

    case ACTIONS.SET_DASHBOARD_DATA:
      return {
        ...state,
        dashboardData: action.data,
        loading: { ...state.loading, dashboard: false },
        errors: { ...state.errors, dashboard: null },
        lastUpdated: { ...state.lastUpdated, dashboard: new Date() },
      };

    case ACTIONS.SET_PRODUCTION_METRICS:
      return {
        ...state,
        productionMetrics: action.data,
        loading: { ...state.loading, production: false },
        errors: { ...state.errors, production: null },
        lastUpdated: { ...state.lastUpdated, production: new Date() },
      };

    case ACTIONS.SET_TRENDING_ANALYTICS:
      return {
        ...state,
        trendingAnalytics: action.data,
        loading: { ...state.loading, trending: false },
        errors: { ...state.errors, trending: null },
        lastUpdated: { ...state.lastUpdated, trending: new Date() },
      };

    case ACTIONS.SET_USER_INTERACTION_STATS:
      return {
        ...state,
        userInteractionStats: action.data,
        loading: { ...state.loading, userInteraction: false },
        errors: { ...state.errors, userInteraction: null },
        lastUpdated: { ...state.lastUpdated, userInteraction: new Date() },
      };

    case ACTIONS.CLEAR_ERROR:
      return {
        ...state,
        errors: {
          ...state.errors,
          [action.dataType]: null,
        },
      };

    default:
      return state;
  }
};

// Context
const AdminDataContext = createContext(null);

// Provider component
export const AdminDataProvider = ({ children }) => {
  const [state, dispatch] = useReducer(adminDataReducer, initialState);
  const intervalsRef = useRef({});
  const abortControllersRef = useRef({});

  // Helper function to check if data is stale
  const isDataStale = useCallback(
    (dataType, customInterval = null) => {
      const lastUpdate = state.lastUpdated[dataType];
      if (!lastUpdate) return true;

      const interval = customInterval || state.refreshInterval;
      return Date.now() - lastUpdate.getTime() > interval;
    },
    [state.lastUpdated, state.refreshInterval]
  );

  // Generic fetch function with caching and deduplication
  const fetchData = useCallback(
    async (dataType, fetchFunction, force = false) => {
      // Check if already loading to prevent duplicate requests
      if (state.loading[dataType] && !force) {
        console.log(`⏳ [AdminDataContext] ${dataType} already loading, skipping...`);
        return;
      }

      // Check cache if not forcing refresh
      if (!force && !isDataStale(dataType)) {
        console.log(`💾 [AdminDataContext] ${dataType} cache hit, skipping fetch`);
        return;
      }

      // Cancel previous request if exists
      if (abortControllersRef.current[dataType]) {
        abortControllersRef.current[dataType].abort();
      }

      // Create new abort controller
      const abortController = new AbortController();
      abortControllersRef.current[dataType] = abortController;

      dispatch({ type: ACTIONS.SET_LOADING, dataType, loading: true });
      dispatch({ type: ACTIONS.CLEAR_ERROR, dataType });

      try {
        console.log(`🚀 [AdminDataContext] Fetching ${dataType}...`);
        const data = await fetchFunction(abortController.signal);

        // Check if request was aborted
        if (abortController.signal.aborted) {
          console.log(`❌ [AdminDataContext] ${dataType} request aborted`);
          return;
        }

        // Extract data based on response structure
        const extractedData = data?.data || data;

        // Dispatch appropriate action
        switch (dataType) {
          case 'dashboard':
            dispatch({ type: ACTIONS.SET_DASHBOARD_DATA, data: extractedData });
            break;
          case 'production':
            dispatch({ type: ACTIONS.SET_PRODUCTION_METRICS, data: extractedData });
            break;
          case 'trending':
            dispatch({ type: ACTIONS.SET_TRENDING_ANALYTICS, data: extractedData });
            break;
          case 'userInteraction':
            dispatch({ type: ACTIONS.SET_USER_INTERACTION_STATS, data: extractedData });
            break;
        }

        console.log(`✅ [AdminDataContext] ${dataType} fetched successfully`);
      } catch (error) {
        if (error.name === 'AbortError') {
          console.log(`🛑 [AdminDataContext] ${dataType} fetch aborted`);
          return;
        }

        console.error(`❌ [AdminDataContext] Error fetching ${dataType}:`, error);
        dispatch({
          type: ACTIONS.SET_ERROR,
          dataType,
          error: error.message || `Failed to fetch ${dataType}`,
        });
      } finally {
        // Clean up abort controller
        if (abortControllersRef.current[dataType] === abortController) {
          delete abortControllersRef.current[dataType];
        }
      }
    },
    [state.loading, isDataStale]
  );

  // API fetch functions
  const fetchDashboard = useCallback(signal => getDashboardOverview({ signal }), []);
  const fetchProduction = useCallback(signal => getProductionMetrics({ signal }), []);
  const fetchTrending = useCallback(signal => getTrendingAnalytics({ signal }), []);
  const fetchUserInteraction = useCallback(signal => getUserInteractionStats({ signal }), []);

  // Public API methods
  const refreshDashboard = useCallback(
    (force = false) => {
      return fetchData('dashboard', fetchDashboard, force);
    },
    [fetchData, fetchDashboard]
  );

  const refreshProductionMetrics = useCallback(
    (force = false) => {
      return fetchData('production', fetchProduction, force);
    },
    [fetchData, fetchProduction]
  );

  const refreshTrendingAnalytics = useCallback(
    (force = false) => {
      return fetchData('trending', fetchTrending, force);
    },
    [fetchData, fetchTrending]
  );

  const refreshUserInteractionStats = useCallback(
    (force = false) => {
      return fetchData('userInteraction', fetchUserInteraction, force);
    },
    [fetchData, fetchUserInteraction]
  );

  // Refresh all data
  const refreshAllData = useCallback(
    async (force = false) => {
      console.log('🔄 [AdminDataContext] Refreshing all data...', { force });
      await Promise.allSettled([
        refreshDashboard(force),
        refreshProductionMetrics(force),
        refreshTrendingAnalytics(force),
        refreshUserInteractionStats(force),
      ]);
    },
    [
      refreshDashboard,
      refreshProductionMetrics,
      refreshTrendingAnalytics,
      refreshUserInteractionStats,
    ]
  );

  // Setup auto-refresh intervals
  useEffect(() => {
    if (!state.autoRefresh) return;

    console.log('⏰ [AdminDataContext] Setting up auto-refresh intervals');

    // Different refresh intervals for different data types
    const intervals = {
      dashboard: 60000, // 1 minute
      production: 30000, // 30 seconds
      trending: 60000, // 1 minute
      userInteraction: 120000, // 2 minutes
    };

    // Set up intervals
    Object.entries(intervals).forEach(([dataType, interval]) => {
      intervalsRef.current[dataType] = setInterval(() => {
        console.log(`⏰ [AdminDataContext] Auto-refreshing ${dataType}`);
        switch (dataType) {
          case 'dashboard':
            refreshDashboard();
            break;
          case 'production':
            refreshProductionMetrics();
            break;
          case 'trending':
            refreshTrendingAnalytics();
            break;
          case 'userInteraction':
            refreshUserInteractionStats();
            break;
        }
      }, interval);
    });

    // Initial fetch for all data
    refreshAllData();

    // Cleanup intervals
    return () => {
      Object.values(intervalsRef.current).forEach(clearInterval);
      intervalsRef.current = {};
    };
  }, [
    state.autoRefresh,
    refreshDashboard,
    refreshProductionMetrics,
    refreshTrendingAnalytics,
    refreshUserInteractionStats,
    refreshAllData,
  ]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Cancel all pending requests
      Object.values(abortControllersRef.current).forEach(controller => controller.abort());
      abortControllersRef.current = {};

      // Clear all intervals
      Object.values(intervalsRef.current).forEach(clearInterval);
      intervalsRef.current = {};
    };
  }, []);

  // Context value
  const value = {
    // Data
    dashboardData: state.dashboardData,
    productionMetrics: state.productionMetrics,
    trendingAnalytics: state.trendingAnalytics,
    userInteractionStats: state.userInteractionStats,

    // Loading states
    loading: state.loading,

    // Error states
    errors: state.errors,

    // Last updated timestamps
    lastUpdated: state.lastUpdated,

    // Utility functions
    isDataStale,

    // Refresh functions
    refreshDashboard,
    refreshProductionMetrics,
    refreshTrendingAnalytics,
    refreshUserInteractionStats,
    refreshAllData,

    // Combined loading state
    isLoading: Object.values(state.loading).some(Boolean),

    // Combined error state
    hasErrors: Object.values(state.errors).some(Boolean),

    // Real-time metrics (optimized for frequent updates)
    realTimeMetrics: state.productionMetrics,

    // Comprehensive metrics (includes all data)
    comprehensiveMetrics: {
      ...state.productionMetrics,
      trending: state.trendingAnalytics,
      userInteraction: state.userInteractionStats,
    },
  };

  return <AdminDataContext.Provider value={value}>{children}</AdminDataContext.Provider>;
};

// Hook to use admin data context
export const useAdminData = () => {
  const context = useContext(AdminDataContext);
  if (!context) {
    throw new Error('useAdminData must be used within AdminDataProvider');
  }
  return context;
};

// Specialized hooks for backward compatibility and specific use cases
export const useAdminDashboard = () => {
  const { dashboardData, loading, errors, refreshDashboard } = useAdminData();
  return {
    data: dashboardData,
    loading: loading.dashboard,
    error: errors.dashboard,
    refreshDashboard,
  };
};

export const useAdminProductionMetrics = () => {
  const { productionMetrics, loading, errors, refreshProductionMetrics, lastUpdated, isDataStale } =
    useAdminData();
  return {
    data: productionMetrics,
    loading: loading.production,
    error: errors.production,
    refreshMetrics: refreshProductionMetrics,
    lastUpdated: lastUpdated.production,
    isStale: isDataStale('production'),
  };
};

export const useAdminTrendingAnalytics = () => {
  const { trendingAnalytics, loading, errors, refreshTrendingAnalytics } = useAdminData();
  return {
    data: trendingAnalytics,
    loading: loading.trending,
    error: errors.trending,
    refetch: refreshTrendingAnalytics,
  };
};

export const useAdminUserInteractionStats = () => {
  const { userInteractionStats, loading, errors, refreshUserInteractionStats } = useAdminData();
  return {
    data: userInteractionStats,
    loading: loading.userInteraction,
    error: errors.userInteraction,
    refetch: refreshUserInteractionStats,
  };
};

// Real-time metrics hook (optimized for frequent updates)
export const useAdminRealTimeMetrics = () => {
  const { realTimeMetrics, loading, errors, isDataStale } = useAdminData();
  return {
    data: realTimeMetrics,
    loading: loading.production,
    error: errors.production,
    isStale: isDataStale('production', 10000), // 10 second threshold for real-time
  };
};

// Comprehensive metrics hook (includes all related data)
export const useAdminComprehensiveMetrics = () => {
  const {
    productionMetrics,
    trendingAnalytics,
    userInteractionStats,
    loading,
    errors,
    lastUpdated,
    refreshProductionMetrics,
    isDataStale,
  } = useAdminData();

  return {
    data: {
      ...productionMetrics,
      trending: trendingAnalytics,
      userInteraction: userInteractionStats,
    },
    loading: loading.production || loading.trending || loading.userInteraction,
    error: errors.production || errors.trending || errors.userInteraction,
    lastUpdated: lastUpdated.production,
    refreshMetrics: refreshProductionMetrics,
    isStale: isDataStale('production', 60000), // 1 minute threshold for comprehensive
  };
};

export default AdminDataContext;
