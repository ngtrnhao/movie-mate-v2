import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  Filler,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  ArrowTrendingUpIcon,
  UsersIcon,
  EyeIcon,
  ChartBarIcon,
  ClockIcon,
  DevicePhoneMobileIcon,
  ComputerDesktopIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { useAdminData } from '../../../contexts/AdminDataContext';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  Filler
);

const RealTimeCharts = () => {
  const {
    userInteractionStats: userStats,
    trendingAnalytics: trendingData,
    productionMetrics,
    realTimeInteractions,
    loading,
    errors,
    loadDataOnDemand,
    refreshUserInteractionStats,
    refreshTrendingAnalytics,
    refreshProductionMetrics,
    refreshRealTimeInteractions,
  } = useAdminData();

  // Check what data we have and load missing data on demand (with debounce)
  useEffect(() => {
    // Debounce to avoid rapid successive calls
    const timer = setTimeout(() => {
      const missingData = [];

      // Prioritize production metrics as most important
      if (!productionMetrics && !loading.production && !errors.production) {
        missingData.push('production');
      }

      // Load real-time interactions for real-time chart
      if (!realTimeInteractions && !loading.realTimeInteractions && !errors.realTimeInteractions) {
        console.log('📊 [RealTimeCharts] Loading real-time interactions data');
        missingData.push('realTimeInteractions');
      }

      // Only load userInteraction and trending if really needed for charts
      // Skip if there are errors to avoid repeated failures
      if (!userStats && !loading.userInteraction && !errors.userInteraction) {
        // Only load if user explicitly wants real-time charts
        console.log('📊 [RealTimeCharts] UserInteraction data available on demand');
        // missingData.push('userInteraction'); // Commented out to avoid auto-loading
      }
      if (!trendingData && !loading.trending && !errors.trending) {
        // Only load if user explicitly wants trending charts
        console.log('📈 [RealTimeCharts] Trending data available on demand');
        // missingData.push('trending'); // Commented out to avoid auto-loading
      }

      if (missingData.length > 0) {
        console.log('🔄 [RealTimeCharts] Loading missing data (debounced):', missingData);
        loadDataOnDemand(missingData);
      }
    }, 500); // 500ms debounce

    return () => clearTimeout(timer);
  }, [
    userStats,
    trendingData,
    productionMetrics,
    realTimeInteractions,
    loading,
    errors,
    loadDataOnDemand,
  ]);

  // Derived loading states
  const userLoading = loading.userInteraction;
  const trendingLoading = loading.trending;
  const metricsLoading = loading.production;

  const [realTimeData, setRealTimeData] = useState({
    userActivity: [],
    viewCounts: [],
    deviceBreakdown: {},
    performanceMetrics: [],
    lastUpdated: new Date(),
  });

  // Manual data loading for heavy operations
  const loadAdditionalData = useCallback(() => {
    console.log('🔄 [RealTimeCharts] Manually loading additional data...');
    const additionalData = [];

    if (!userStats && !loading.userInteraction) {
      additionalData.push('userInteraction');
    }
    if (!trendingData && !loading.trending) {
      additionalData.push('trending');
    }
    if (!realTimeInteractions && !loading.realTimeInteractions) {
      additionalData.push('realTimeInteractions');
    }

    if (additionalData.length > 0) {
      loadDataOnDemand(additionalData);
    }
  }, [userStats, trendingData, realTimeInteractions, loading, loadDataOnDemand]);

  // Process real backend data
  const processRealTimeData = useCallback(
    (userInteractionStats, trendingAnalytics, productionMetrics, realTimeInteractionsData) => {
      // Generate time series from real interaction data
      const userActivity = generateTimeSeriesFromRealData(
        userInteractionStats,
        realTimeInteractionsData
      );

      // Process real action breakdown
      const viewCounts = processActionBreakdown(userInteractionStats.action_breakdown || []);

      // Process device breakdown (simulate from user data if not available)
      const deviceBreakdown = processDeviceBreakdown(userInteractionStats);

      // Process performance metrics from production data
      const performanceMetrics = processPerformanceMetrics(productionMetrics);

      return {
        userActivity,
        viewCounts,
        deviceBreakdown,
        performanceMetrics,
        lastUpdated: new Date(),
      };
    },
    [] // Empty dependency array since helper functions don't change
  );

  // Process real data when available
  useEffect(() => {
    console.log('Debug - userStats:', userStats);
    console.log('Debug - trendingData:', trendingData);
    console.log('Debug - productionMetrics:', productionMetrics);
    console.log('Debug - realTimeInteractions:', realTimeInteractions);

    // Check different possible data structures
    const userData = userStats?.data || userStats || {};
    const trendingDataRes = trendingData?.data || trendingData || {};
    const productionData = productionMetrics?.data || productionMetrics || {};
    const realTimeData = realTimeInteractions?.data || realTimeInteractions || null;

    console.log('Debug - processed userData:', userData);
    console.log('Debug - processed trendingDataRes:', trendingDataRes);
    console.log('Debug - processed productionData:', productionData);
    console.log('Debug - processed realTimeData:', realTimeData);

    // Update as long as we have at least real-time data or any of the supporting datasets
    if (realTimeData || userData || trendingDataRes || productionData) {
      const processedData = processRealTimeData(
        userData,
        trendingDataRes,
        productionData,
        realTimeData
      );
      console.log('Debug - processedData:', processedData);
      setRealTimeData(processedData);
    }
  }, [userStats, trendingData, productionMetrics, realTimeInteractions, processRealTimeData]);

  // Remove separate interval - rely on AdminDataContext for auto-refresh
  // useEffect(() => {
  //   const refreshData = () => {
  //     refetchUserStats();
  //     refetchTrending();
  //     refetchMetrics();
  //   };

  //   // Refresh every 30 seconds for real-time feel
  //   intervalRef.current = setInterval(refreshData, 30000);

  //   return () => {
  //     if (intervalRef.current) {
  //       clearInterval(intervalRef.current);
  //     }
  //   };
  // }, [refetchUserStats, refetchTrending, refetchMetrics]);

  // Generate time series data from real API only
  const generateTimeSeriesFromRealData = (stats, realTimeApiData = null) => {
    console.log('🔍 [DEBUG] generateTimeSeriesFromRealData input:', { stats, realTimeApiData });

    // Hỗ trợ cả hai định dạng: {real_time_activity: [...]} hoặc {data: {real_time_activity: [...]}}
    const activity =
      realTimeApiData?.real_time_activity || realTimeApiData?.data?.real_time_activity || [];

    if (Array.isArray(activity) && activity.length) {
      console.log('✅ [DEBUG] Sử dụng dữ liệu thực từ real-time interactions API');
      return activity.map(item => {
        // Ưu tiên dùng time_iso (UTC) nếu có và format theo local timezone
        const label = item.time_iso
          ? new Date(item.time_iso).toLocaleTimeString('vi-VN', {
              hour: '2-digit',
              minute: '2-digit',
              hour12: false,
            })
          : item.time;
        return {
          time: label,
          value: item.interactions ?? item.value ?? 0,
        };
      });
    }

    // Nếu không có dữ liệu thực, trả về mảng rỗng
    console.log('⚠️ [DEBUG] Không có dữ liệu thực, trả về mảng rỗng');
    return [];
  };

  // Process action breakdown from real data
  const processActionBreakdown = actionBreakdown => {
    console.log('Debug - processActionBreakdown input:', actionBreakdown);

    if (!Array.isArray(actionBreakdown)) {
      console.log('Debug - actionBreakdown is not array, returning empty');
      return [];
    }

    const result = actionBreakdown.map(action => ({
      action: action.action?.replace(/_/g, ' ').toUpperCase() || 'UNKNOWN',
      count: action.count || 0,
      uniqueUsers: action.unique_users || 0,
      uniqueSessions: action.unique_sessions || 0,
    }));

    console.log('Debug - processActionBreakdown result:', result);
    return result;
  };

  // Process device breakdown (simulate realistic distribution)
  const processDeviceBreakdown = stats => {
    const totalSessions = stats.overview?.total_sessions || 100;

    // Realistic device distribution based on web analytics
    return {
      desktop: Math.floor(totalSessions * 0.6), // 60% desktop
      mobile: Math.floor(totalSessions * 0.35), // 35% mobile
      tablet: Math.floor(totalSessions * 0.05), // 5% tablet
    };
  };

  // Process performance metrics from production data
  const processPerformanceMetrics = productionData => {
    console.log('Debug - processPerformanceMetrics input:', productionData);

    // New mapping: API returns engagement_stats at top level
    const engagementStats =
      productionData?.engagement_stats || productionData?.data?.engagement_stats || {};

    const performanceScore = Number(
      engagementStats?.avg_performance_score ?? productionData?.avg_performance_score ?? 0
    );
    const homepageViews = Number(
      engagementStats?.total_homepage_views ?? productionData?.total_homepage_views ?? 0
    );
    const detailViews = Number(
      engagementStats?.total_detail_views ?? productionData?.total_detail_views ?? 0
    );
    const trendingScore = Number(
      engagementStats?.avg_trending_score ?? productionData?.avg_trending_score ?? 0
    );
    const userEngagement = Number(
      engagementStats?.avg_engagement_rate ?? productionData?.avg_engagement_rate ?? 0
    );

    const result = [
      {
        metric: 'Performance Score',
        value: performanceScore,
        status: performanceScore > 70 ? 'good' : 'warning',
      },
      {
        metric: 'Homepage Views',
        value: homepageViews,
        status: 'neutral',
      },
      {
        metric: 'Detail Views',
        value: detailViews,
        status: 'neutral',
      },
      {
        metric: 'Trending Score',
        value: trendingScore,
        status: trendingScore > 60 ? 'good' : 'warning',
      },
      {
        metric: 'User Engagement',
        value: userEngagement,
        status: userEngagement > 50 ? 'good' : 'warning',
      },
    ];

    console.log('Debug - processPerformanceMetrics result:', result);
    return result;
  };

  // Update performance metrics as soon as production data arrives
  useEffect(() => {
    const productionData = productionMetrics?.data || productionMetrics;
    if (productionData) {
      const metrics = processPerformanceMetrics(productionData);
      setRealTimeData(prev => ({ ...prev, performanceMetrics: metrics, lastUpdated: new Date() }));
    }
  }, [productionMetrics]);

  // Chart configurations
  const lineChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'User Interactions (Real-time)',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
      },
      x: {
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
      },
    },
    animation: {
      duration: 750,
    },
  };

  const barChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'User Actions Breakdown (Real Data)',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
      },
      title: {
        display: true,
        text: 'Device Distribution',
      },
    },
  };

  // Chart data using real data
  const lineChartData = {
    labels: realTimeData.userActivity.map(item => item.time),
    datasets: [
      {
        label: 'User Interactions',
        data: realTimeData.userActivity.map(item => item.value),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const barChartData = {
    labels: realTimeData.viewCounts.map(item => item.action),
    datasets: [
      {
        label: 'Action Count',
        data: realTimeData.viewCounts.map(item => item.count),
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(139, 92, 246, 0.8)',
        ],
        borderColor: [
          'rgb(59, 130, 246)',
          'rgb(16, 185, 129)',
          'rgb(245, 158, 11)',
          'rgb(239, 68, 68)',
          'rgb(139, 92, 246)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const doughnutData = {
    labels: Object.keys(realTimeData.deviceBreakdown).map(
      device => device.charAt(0).toUpperCase() + device.slice(1)
    ),
    datasets: [
      {
        data: Object.values(realTimeData.deviceBreakdown),
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
        ],
        borderColor: ['rgb(59, 130, 246)', 'rgb(16, 185, 129)', 'rgb(245, 158, 11)'],
        borderWidth: 2,
      },
    ],
  };

  if (userLoading || trendingLoading || metricsLoading) {
    return (
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <div className="animate-pulse">
              <div className="mb-4 h-4 w-1/3 rounded bg-gray-200"></div>
              <div className="h-64 rounded bg-gray-200"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Real-time Stats Overview */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <div className="rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-100">Total Users</p>
              <p className="text-2xl font-bold">
                {userStats?.data?.overview?.total_users || userStats?.overview?.total_users || 0}
              </p>
            </div>
            <UsersIcon className="size-8 text-blue-200" />
          </div>
          <div className="mt-2 flex items-center">
            <ArrowTrendingUpIcon className="mr-1 size-4 text-green-300" />
            <span className="text-sm text-blue-100">
              {userStats?.data?.trends?.daily_growth > 0 ? '+' : ''}
              {userStats?.data?.trends?.daily_growth || 0}% hôm nay
            </span>
          </div>
        </div>

        <div className="rounded-lg bg-gradient-to-r from-green-500 to-green-600 p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-green-100">Total Interactions</p>
              <p className="text-2xl font-bold">
                {userStats?.data?.overview?.total_interactions ||
                  userStats?.overview?.total_interactions ||
                  0}
              </p>
            </div>
            <EyeIcon className="size-8 text-green-200" />
          </div>
          <div className="mt-2 flex items-center">
            <ArrowTrendingUpIcon className="mr-1 size-4 text-green-300" />
            <span className="text-sm text-green-100">
              {userStats?.data?.trends?.weekly_growth > 0 ? '+' : ''}
              {userStats?.data?.trends?.weekly_growth || 0}% tuần này
            </span>
          </div>
        </div>

        <div className="rounded-lg bg-gradient-to-r from-purple-500 to-purple-600 p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-purple-100">Avg Performance</p>
              <p className="text-2xl font-bold">
                {productionMetrics?.data?.summary?.avg_performance_score?.toFixed(1) || '0.0'}
              </p>
            </div>
            <ChartBarIcon className="size-8 text-purple-200" />
          </div>
          <div className="mt-2 flex items-center">
            {(productionMetrics?.data?.summary?.avg_performance_score || 0) > 70 ? (
              <CheckCircleIcon className="mr-1 size-4 text-green-300" />
            ) : (
              <ExclamationTriangleIcon className="mr-1 size-4 text-yellow-300" />
            )}
            <span className="text-sm text-purple-100">
              {(productionMetrics?.data?.summary?.avg_performance_score || 0) > 70
                ? 'Tốt'
                : 'Cần cải thiện'}
            </span>
          </div>
        </div>

        <div className="rounded-lg bg-gradient-to-r from-orange-500 to-orange-600 p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-orange-100">Session Duration</p>
              <p className="text-2xl font-bold">
                {userStats?.data?.session_stats?.avg_duration_seconds
                  ? Math.round(userStats.data.session_stats.avg_duration_seconds / 60)
                  : 0}
                <span className="text-sm">min</span>
              </p>
            </div>
            <ClockIcon className="size-8 text-orange-200" />
          </div>
          <div className="mt-2 flex items-center">
            <ArrowTrendingUpIcon className="mr-1 size-4 text-green-300" />
            <span className="text-sm text-orange-100">Từ dữ liệu thực tế</span>
          </div>
        </div>
      </div>

      {/* Data freshness indicator */}
      <div className="flex items-center justify-between rounded-lg border border-blue-200 bg-blue-50 p-3">
        <div className="flex items-center">
          <div className="mr-2 size-2 animate-pulse rounded-full bg-green-400"></div>
          <span className="text-sm text-blue-800">
            Dữ liệu được cập nhật lúc: {realTimeData.lastUpdated.toLocaleTimeString('vi-VN')}
          </span>
        </div>
        <div className="flex items-center space-x-3">
          {(!userStats || !trendingData) && (
            <button
              onClick={loadAdditionalData}
              disabled={userLoading || trendingLoading}
              className="text-sm font-medium text-green-600 hover:text-green-800 disabled:text-gray-400"
            >
              {userLoading || trendingLoading ? 'Đang tải...' : 'Tải thêm dữ liệu'}
            </button>
          )}
          <button
            onClick={() => {
              refreshUserInteractionStats(true);
              refreshTrendingAnalytics(true);
              refreshProductionMetrics(true);
              refreshRealTimeInteractions(true);
            }}
            className="text-sm font-medium text-blue-600 hover:text-blue-800"
          >
            Làm mới ngay
          </button>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Real-time User Activity */}
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">Real-time User Activity</h3>
            <div className="flex items-center space-x-2">
              <div className="size-2 animate-pulse rounded-full bg-green-400"></div>
              <span className="text-sm text-gray-500">Live Data</span>
            </div>
          </div>
          <div style={{ height: '300px' }}>
            <Line data={lineChartData} options={lineChartOptions} />
          </div>
        </div>

        {/* User Actions Breakdown */}
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-medium text-gray-900">
            User Actions Breakdown (Real Data)
          </h3>
          <div style={{ height: '300px' }}>
            <Bar data={barChartData} options={barChartOptions} />
          </div>
        </div>

        {/* Device Breakdown */}
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-medium text-gray-900">Device Usage Distribution</h3>
          <div style={{ height: '300px' }}>
            <Doughnut data={doughnutData} options={doughnutOptions} />
          </div>
          <div className="mt-4 grid grid-cols-3 gap-4 text-center">
            <div className="flex flex-col items-center">
              <ComputerDesktopIcon className="mb-1 size-6 text-blue-500" />
              <span className="text-sm text-gray-600">Desktop</span>
              <span className="font-semibold text-gray-600">
                {realTimeData.deviceBreakdown.desktop || 0}
              </span>
            </div>
            <div className="flex flex-col items-center">
              <DevicePhoneMobileIcon className="mb-1 size-6 text-green-500" />
              <span className="text-sm text-gray-600">Mobile</span>
              <span className="font-semibold  text-gray-600">
                {realTimeData.deviceBreakdown.mobile || 0}
              </span>
            </div>
            <div className="flex flex-col items-center">
              <ChartBarIcon className="mb-1 size-6 text-yellow-500" />
              <span className="text-sm text-gray-600">Tablet</span>
              <span className="font-semibold  text-gray-600">
                {realTimeData.deviceBreakdown.tablet || 0}
              </span>
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-medium text-gray-900">Production Metrics (Real Data)</h3>
          <div className="space-y-4">
            {realTimeData.performanceMetrics.map((metric, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-gray-600">{metric.metric}</span>
                  {metric.status === 'good' && (
                    <CheckCircleIcon className="size-4 text-green-500" />
                  )}
                  {metric.status === 'warning' && (
                    <ExclamationTriangleIcon className="size-4 text-yellow-500" />
                  )}
                </div>
                <div className="flex items-center space-x-3">
                  <div className="h-2 w-32 rounded-full bg-gray-200">
                    <div
                      className={`h-2 rounded-full transition-all duration-500 ${
                        metric.status === 'good'
                          ? 'bg-green-600'
                          : metric.status === 'warning'
                            ? 'bg-yellow-600'
                            : 'bg-blue-600'
                      }`}
                      style={{
                        width: `${Math.min(100, Math.max(0, (metric.value / Math.max(...realTimeData.performanceMetrics.map(m => m.value), 1)) * 100))}%`,
                      }}
                    ></div>
                  </div>
                  <span className="min-w-12 text-right text-sm font-semibold text-gray-900">
                    {typeof metric.value === 'number' ? metric.value.toFixed(1) : metric.value}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RealTimeCharts;
