import { useState, useEffect, useCallback } from 'react';
import { getDashboardOverview } from '../api/adminMovieService';

let isInitialFetchDone = false;
let refreshCallback = null;

export const useRefreshDashboard = () => {
  return refreshCallback;
};

export const useDashboardData = () => {
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchDashboard = useCallback(async () => {
    try {
      setLoading(true);
      const dashboardData = await getDashboardOverview();
      setData(dashboardData);
      setError(null);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Không thể tải dữ liệu dashboard. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isInitialFetchDone) {
      fetchDashboard();
      isInitialFetchDone = true;
    }
    refreshCallback = fetchDashboard;
    return () => {
      if (refreshCallback === fetchDashboard) {
        refreshCallback = null;
      }
    };
  }, [fetchDashboard]);

  return {
    data,
    loading,
    error,
    refreshDashboard: fetchDashboard,
  };
};
