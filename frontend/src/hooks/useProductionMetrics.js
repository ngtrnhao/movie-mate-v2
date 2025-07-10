import { useState, useEffect, useCallback } from 'react';
import { getProductionMetrics } from '../api/adminMovieService';

let isInitialFetchDone = false;

export const useProductionMetrics = () => {
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchMetrics = useCallback(async () => {
    try {
      setLoading(true);
      const metricsData = await getProductionMetrics();
      setData(metricsData);
      setError(null);
    } catch (err) {
      console.error('Error fetching production metrics:', err);
      setError('Không thể tải dữ liệu metrics. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isInitialFetchDone) {
      fetchMetrics();
      isInitialFetchDone = true;
    }
  }, [fetchMetrics]);

  return {
    data,
    loading,
    error,
    refreshMetrics: fetchMetrics,
  };
};
