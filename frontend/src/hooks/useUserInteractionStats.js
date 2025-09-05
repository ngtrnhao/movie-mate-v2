import { useState, useEffect, useCallback } from 'react';
import { getUserInteractionStats } from '../api/adminMovieService';

export const useUserInteractionStats = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await getUserInteractionStats();
      setData(result.data || result);
    } catch (err) {
      console.error('Error fetching user interaction stats:', err);
      setError('Không thể tải dữ liệu thống kê tương tác. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return {
    data,
    loading,
    error,
    refetch: fetchStats,
  };
};
