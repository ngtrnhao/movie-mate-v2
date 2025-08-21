import { createContext, useContext, useReducer, useCallback, useEffect, useRef } from 'react';
import {
  getDashboardOverview,
  getProductionMetrics,
  getTrendingAnalytics,
  getUserInteractionStats,
  getRealTimeInteractions,
} from '../api/adminMovieService';

// Action types
const ACTIONS = {
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  SET_DASHBOARD_DATA: 'SET_DASHBOARD_DATA',
  SET_PRODUCTION_METRICS: 'SET_PRODUCTION_METRICS',
  SET_TRENDING_ANALYTICS: 'SET_TRENDING_ANALYTICS',
  SET_USER_INTERACTION_STATS: 'SET_USER_INTERACTION_STATS',
  SET_REAL_TIME_INTERACTIONS: 'SET_REAL_TIME_INTERACTIONS',
  SET_LAST_UPDATED: 'SET_LAST_UPDATED',
  CLEAR_ERROR: 'CLEAR_ERROR',
  SET_ACTIVE_TAB: 'SET_ACTIVE_TAB',
  UPDATE_TAB_REFRESH_MAP: 'UPDATE_TAB_REFRESH_MAP',
};

// Initial state
const initialState = {
  // Data
  dashboardData: null,
  productionMetrics: null,
  trendingAnalytics: null,
  userInteractionStats: null,
  realTimeInteractions: null,

  // Loading states
  loading: {
    dashboard: false,
    production: false,
    trending: false,
    userInteraction: false,
    realTimeInteractions: false,
  },

  // Error states
  errors: {
    dashboard: null,
    production: null,
    trending: null,
    userInteraction: null,
    realTimeInteractions: null,
  },

  // Cache timestamps
  lastUpdated: {
    dashboard: null,
    production: null,
    trending: null,
    userInteraction: null,
    realTimeInteractions: null,
  },

  // Settings
  autoRefresh: true,
  refreshInterval: 60000,

  activeTab: null,
  tabRefreshMap: {
    overview: ['dashboard'],
    realtime_analytics: ['production', 'trending', 'userInteraction', 'realTimeInteractions'],
    auto_processing: ['dashboard'],
    movies: ['dashboard', 'production'],
    visibility: ['production'],
    user_interactions: ['userInteraction', 'realTimeInteractions'],
    trending_analytics: ['trending'],
    content: ['dashboard', 'production'],
  },
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

    case ACTIONS.SET_REAL_TIME_INTERACTIONS:
      return {
        ...state,
        realTimeInteractions: action.data,
        loading: { ...state.loading, realTimeInteractions: false },
        errors: { ...state.errors, realTimeInteractions: null },
        lastUpdated: { ...state.lastUpdated, realTimeInteractions: new Date() },
      };

    case ACTIONS.CLEAR_ERROR:
      return {
        ...state,
        errors: {
          ...state.errors,
          [action.dataType]: null,
        },
      };

    case ACTIONS.SET_ACTIVE_TAB:
      return {
        ...state,
        activeTab: action.tab,
      };

    case ACTIONS.UPDATE_TAB_REFRESH_MAP:
      return {
        ...state,
        tabRefreshMap: action.map,
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
  const refreshFunctionsRef = useRef({});

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

      // Check cache if not forcing refresh (with extended cache time for heavy operations)
      const extendedCacheTime = {
        dashboard: 180000, // 3 minutes
        production: 300000, // 5 minutes
        trending: 600000, // 10 minutes
        userInteraction: 60000, // 1 minute for charts on real-time tab
        realTimeInteractions: 60000, // 1 minute for real-time
      };

      if (!force && !isDataStale(dataType, extendedCacheTime[dataType])) {
        console.log(`💾 [AdminDataContext] ${dataType} cache hit (extended), skipping fetch`);
        return;
      }

      // Cancel previous request if exists
      if (abortControllersRef.current[dataType]) {
        abortControllersRef.current[dataType].abort();
      }

      // Create new abort controller with timeout
      const abortController = new AbortController();
      abortControllersRef.current[dataType] = abortController;

      // Set timeout based on data type (more time for complex data)
      const timeouts = {
        dashboard: 15000, // 15 seconds for basic stats
        production: 45000, // 45 seconds for complex production metrics (increased)
        trending: 35000, // 35 seconds for trending analytics (increased)
        userInteraction: 30000, // 30 seconds for user stats (increased)
        realTimeInteractions: 20000, // 20 seconds for real-time API
      };

      const timeout = setTimeout(() => {
        abortController.abort();
      }, timeouts[dataType] || 20000);

      dispatch({ type: ACTIONS.SET_LOADING, dataType, loading: true });
      dispatch({ type: ACTIONS.CLEAR_ERROR, dataType });

      try {
        console.log(
          ` [AdminDataContext] Fetching ${dataType} with ${timeouts[dataType] || 20000}ms timeout...`
        );
        const data = await fetchFunction(abortController.signal);

        // Check if request was aborted
        if (abortController.signal.aborted) {
          console.log(` [AdminDataContext] ${dataType} request aborted`);
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
          case 'realTimeInteractions':
            dispatch({ type: ACTIONS.SET_REAL_TIME_INTERACTIONS, data: extractedData });
            break;
        }

        console.log(`[AdminDataContext] ${dataType} fetched successfully`);
      } catch (error) {
        if (error.name === 'AbortError' || error.name === 'CanceledError') {
          console.log(` [AdminDataContext] ${dataType} fetch aborted (timeout or canceled)`);
          dispatch({
            type: ACTIONS.SET_ERROR,
            dataType,
            error: `Request canceled or timeout - ${dataType}`,
          });
          return;
        }

        console.error(` [AdminDataContext] Error fetching ${dataType}:`, error);
        dispatch({
          type: ACTIONS.SET_ERROR,
          dataType,
          error: error.error || error.message || `Failed to fetch ${dataType}`,
        });
      } finally {
        // Clear timeout
        clearTimeout(timeout);

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
  const fetchRealTimeInteractions = useCallback(signal => getRealTimeInteractions({ signal }), []);

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

  const refreshRealTimeInteractions = useCallback(
    (force = false) => {
      return fetchData('realTimeInteractions', fetchRealTimeInteractions, force);
    },
    [fetchData, fetchRealTimeInteractions]
  );

  // Store refresh functions in ref to prevent infinite loops
  useEffect(() => {
    refreshFunctionsRef.current = {
      dashboard: refreshDashboard,
      production: refreshProductionMetrics,
      trending: refreshTrendingAnalytics,
      userInteraction: refreshUserInteractionStats,
      realTimeInteractions: refreshRealTimeInteractions,
    };
  }, [
    refreshDashboard,
    refreshProductionMetrics,
    refreshTrendingAnalytics,
    refreshUserInteractionStats,
    refreshRealTimeInteractions,
  ]);

  // Clear error function
  const clearError = useCallback(
    dataType => {
      dispatch({ type: ACTIONS.CLEAR_ERROR, dataType });
    },
    [dispatch]
  );

  // Tab control functions
  const setActiveTab = useCallback(
    tab => {
      console.log(' [AdminDataContext] Setting active tab to:', tab);
      dispatch({ type: ACTIONS.SET_ACTIVE_TAB, tab });
    },
    [dispatch]
  );

  const updateTabRefreshMap = useCallback(
    map => {
      dispatch({ type: ACTIONS.UPDATE_TAB_REFRESH_MAP, map });
    },
    [dispatch]
  );

  // Refresh all data
  const refreshAllData = useCallback(async (force = false) => {
    console.log(' [AdminDataContext] Refreshing all data...', { force });
    await Promise.allSettled([
      refreshFunctionsRef.current.dashboard(force),
      refreshFunctionsRef.current.production(force),
      refreshFunctionsRef.current.trending(force),
      refreshFunctionsRef.current.userInteraction(force),
      refreshFunctionsRef.current.realTimeInteractions(force),
    ]);
  }, []);

  // Load specific data types on demand (for lazy loading with throttling)
  const loadDataOnDemand = useCallback(
    async (dataTypes, force = false) => {
      console.log(' [AdminDataContext] Loading data on demand:', dataTypes);

      // Filter out data types that are already loading to prevent duplicates
      const filteredDataTypes = dataTypes.filter(dataType => {
        const isLoading = state.loading[dataType];
        if (isLoading && !force) {
          console.log(
            ` [AdminDataContext] ${dataType} already loading, skipping duplicate request`
          );
          return false;
        }
        return true;
      });

      if (filteredDataTypes.length === 0) {
        console.log(' [AdminDataContext] No new data types to load');
        return;
      }

      const promises = filteredDataTypes.map(dataType => {
        switch (dataType) {
          case 'dashboard':
            return refreshFunctionsRef.current.dashboard(force);
          case 'production':
            return refreshFunctionsRef.current.production(force);
          case 'trending':
            return refreshFunctionsRef.current.trending(force);
          case 'userInteraction':
            return refreshFunctionsRef.current.userInteraction(force);
          case 'realTimeInteractions':
            return refreshFunctionsRef.current.realTimeInteractions(force);
          default:
            return Promise.resolve();
        }
      });

      await Promise.allSettled(promises);
    },
    [state.loading]
  );

  // Setup auto-refresh intervals
  useEffect(() => {
    if (!state.autoRefresh) return;

    console.log(
      '⏰ [AdminDataContext] Setting up auto-refresh intervals for tab:',
      state.activeTab
    );

    // Clear existing intervals first
    Object.values(intervalsRef.current).forEach(clearInterval);
    intervalsRef.current = {};

    // Get data types that should be refreshed for current tab
    const activeTabDataTypes = state.activeTab ? state.tabRefreshMap[state.activeTab] || [] : [];

    if (activeTabDataTypes.length === 0) {
      console.log('⏰ [AdminDataContext] No data types to refresh for current tab');
      return;
    }

    // Different refresh intervals for different data types (optimized for performance)
    const intervals = {
      dashboard: 120000, // 2 minutes (less frequent for basic stats)
      production: 90000, // 1.5 minutes (slightly reduced)
      trending: 300000, // 5 minutes (trends don't change quickly)
      userInteraction: 60000, // 1 minute to sync with real-time charts
      realTimeInteractions: 60000, // 1 minute for real-time feed
    };

    // Set up intervals ONLY for data types relevant to current tab
    activeTabDataTypes.forEach(dataType => {
      const interval = intervals[dataType];

      // Skip auto-refresh for heavy operations unless specifically needed
      if (dataType === 'trending') {
        console.log(`⏸️ [AdminDataContext] Skipping auto-refresh for ${dataType} (manual only)`);
        return;
      }

      if (interval) {
        intervalsRef.current[dataType] = setInterval(() => {
          console.log(
            `⏰ [AdminDataContext] Auto-refreshing ${dataType} for tab: ${state.activeTab}`
          );
          switch (dataType) {
            case 'dashboard':
              refreshFunctionsRef.current.dashboard();
              break;
            case 'production':
              refreshFunctionsRef.current.production();
              break;
            case 'trending':
              refreshFunctionsRef.current.trending();
              break;
            case 'userInteraction':
              refreshFunctionsRef.current.userInteraction();
              break;
            case 'realTimeInteractions':
              refreshFunctionsRef.current.realTimeInteractions();
              break;
          }
        }, interval);
      }
    });

    // Initial fetch for relevant data only (prioritize essential data)
    const initialFetchPromises = activeTabDataTypes
      .filter(dataType => {
        // Always fetch dashboard and production
        if (dataType === 'dashboard' || dataType === 'production') {
          return true;
        }
        // Only fetch trending if specifically requested (keep manual)
        if (dataType === 'trending') {
          console.log(`📋 [AdminDataContext] Deferring ${dataType} to manual load`);
          return false;
        }
        return true;
      })
      .map(dataType => {
        switch (dataType) {
          case 'dashboard':
            return refreshFunctionsRef.current.dashboard();
          case 'production':
            return refreshFunctionsRef.current.production();
          case 'trending':
            return refreshFunctionsRef.current.trending();
          case 'userInteraction':
            return refreshFunctionsRef.current.userInteraction();
          case 'realTimeInteractions':
            return refreshFunctionsRef.current.realTimeInteractions();
          default:
            return Promise.resolve();
        }
      });

    if (initialFetchPromises.length > 0) {
      Promise.allSettled(initialFetchPromises);
    }

    // Cleanup intervals
    return () => {
      Object.values(intervalsRef.current).forEach(clearInterval);
      intervalsRef.current = {};
    };
  }, [state.autoRefresh, state.activeTab, state.tabRefreshMap]);

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
    realTimeInteractions: state.realTimeInteractions,

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
    refreshRealTimeInteractions,
    refreshAllData,
    loadDataOnDemand,

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

    // Tab control
    activeTab: state.activeTab,
    setActiveTab: setActiveTab,
    updateTabRefreshMap: updateTabRefreshMap,
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
