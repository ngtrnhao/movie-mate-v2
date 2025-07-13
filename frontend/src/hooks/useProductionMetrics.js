import { useState, useEffect, useCallback } from 'react';
import { getProductionMetrics, getTrendingAnalytics } from '../api/adminMovieService';

export const useProductionMetrics = (options = {}) => {
  const {
    autoRefresh = true,
    refreshInterval = 30000, // 30 seconds
    includeMovieDetails = true,
    includeTrendingData = true,
  } = options;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch production metrics
      const metricsResponse = await getProductionMetrics();

      // Fetch trending analytics if enabled
      let trendingResponse = null;
      if (includeTrendingData) {
        try {
          trendingResponse = await getTrendingAnalytics();
        } catch (trendingError) {
          console.warn('Trending analytics not available:', trendingError);
        }
      }

      // Process and combine data
      const processedData = {
        summary: {
          total_movies: metricsResponse.total_movies || 0,
          avg_performance_score: metricsResponse.avg_performance_score || 0,
          avg_trending_score: metricsResponse.avg_trending_score || 0,
          total_homepage_views: metricsResponse.total_homepage_views || 0,
          total_detail_views: metricsResponse.total_detail_views || 0,
          total_search_appearances: metricsResponse.total_search_appearances || 0,
          avg_user_favorites: metricsResponse.avg_user_favorites || 0,
          avg_session_duration: metricsResponse.avg_session_duration || 0,
          bounce_rate: metricsResponse.bounce_rate || 0,
          total_trailer_views: metricsResponse.total_trailer_views || 0,
        },

        // Performance breakdown by categories
        performance_breakdown: {
          excellent: metricsResponse.performance_categories?.excellent || 0,
          good: metricsResponse.performance_categories?.good || 0,
          average: metricsResponse.performance_categories?.average || 0,
          poor: metricsResponse.performance_categories?.poor || 0,
        },

        // Trending categories
        trending_breakdown: {
          viral: metricsResponse.trending_categories?.viral || 0,
          hot: metricsResponse.trending_categories?.hot || 0,
          rising: metricsResponse.trending_categories?.rising || 0,
          stable: metricsResponse.trending_categories?.stable || 0,
        },

        // Top performing movies
        top_performers: metricsResponse.top_performers || [],

        // User engagement metrics
        engagement_metrics: {
          avg_session_duration: metricsResponse.avg_session_duration || 0,
          bounce_rate: metricsResponse.bounce_rate || 0,
          page_views_per_session: metricsResponse.page_views_per_session || 0,
          return_visitor_rate: metricsResponse.return_visitor_rate || 0,
          user_favorites_count: metricsResponse.user_favorites_count || 0,
        },

        // Real-time metrics
        real_time_metrics: {
          current_active_users: metricsResponse.current_active_users || 0,
          last_hour_views: metricsResponse.last_hour_views || 0,
          last_hour_interactions: metricsResponse.last_hour_interactions || 0,
          peak_concurrent_users: metricsResponse.peak_concurrent_users || 0,
        },

        // Trending analytics (if available)
        trending_analytics: trendingResponse
          ? {
              summary: trendingResponse.summary || {},
              categories: trendingResponse.categories || {},
              top_performers: trendingResponse.top_performers || {},
              trends: trendingResponse.trends || [],
            }
          : null,

        // Growth metrics
        growth_metrics: {
          daily_growth: metricsResponse.daily_growth || 0,
          weekly_growth: metricsResponse.weekly_growth || 0,
          monthly_growth: metricsResponse.monthly_growth || 0,
          user_retention_rate: metricsResponse.user_retention_rate || 0,
        },

        // Quality metrics
        quality_metrics: {
          avg_quality_score: metricsResponse.avg_quality_score || 0,
          content_completeness: metricsResponse.avg_content_completeness || 0,
          quality_issues_count: metricsResponse.quality_issues_count || 0,
          approved_content_ratio: metricsResponse.approved_content_ratio || 0,
        },

        // Raw data for detailed analysis
        raw_data: includeMovieDetails ? metricsResponse : null,
      };

      setData(processedData);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err.message || 'Failed to fetch production metrics');
      console.error('Production metrics error:', err);
    } finally {
      setLoading(false);
    }
  }, [includeMovieDetails, includeTrendingData]);

  // Refresh data function
  const refreshMetrics = useCallback(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refresh setup
  useEffect(() => {
    fetchData(); // Initial fetch

    if (autoRefresh) {
      const interval = setInterval(fetchData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchData, autoRefresh, refreshInterval]);

  return {
    data,
    loading,
    error,
    lastUpdated,
    refreshMetrics,
    isStale: lastUpdated && Date.now() - lastUpdated.getTime() > refreshInterval * 2,
  };
};

// Specialized hook for real-time metrics only
export const useRealTimeMetrics = () => {
  return useProductionMetrics({
    autoRefresh: true,
    refreshInterval: 10000, // 10 seconds for real-time
    includeMovieDetails: false,
    includeTrendingData: true,
  });
};

// Hook for comprehensive analytics
export const useComprehensiveMetrics = () => {
  return useProductionMetrics({
    autoRefresh: true,
    refreshInterval: 60000, // 1 minute for comprehensive data
    includeMovieDetails: true,
    includeTrendingData: true,
  });
};

export default useProductionMetrics;
