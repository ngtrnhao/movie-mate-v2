import { useState, useEffect, useCallback } from 'react';
import { getTrendingAnalytics } from '../api/adminMovieService';

export const useTrendingAnalytics = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await getTrendingAnalytics();
      setData(result.data || result);
    } catch (err) {
      console.error('Error fetching trending analytics:', err);
      setError('Không thể tải dữ liệu phân tích xu hướng. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  return {
    data,
    loading,
    error,
    refetch: fetchAnalytics,
  };
};
