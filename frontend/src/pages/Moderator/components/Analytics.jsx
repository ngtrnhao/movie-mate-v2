import { useState, useEffect, useCallback } from 'react';
import {
  getModerationAnalytics,
  getAccuracySummary,
  getModerationConfig,
} from '../../../api/movieService';
import moderationCacheService from '../../../services/moderationCacheService';

const Analytics = () => {
  const [timeRange, setTimeRange] = useState('week');
  const [analytics, setAnalytics] = useState(null);
  const [accuracyData, setAccuracyData] = useState(null);
  const [moderationConfig, setModerationConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const timeRangeToDays = range => {
    switch (range) {
      case 'week':
        return 7;
      case 'month':
        return 30;
      case 'quarter':
        return 90;
      case 'year':
        return 365;
      default:
        return 30;
    }
  };

  // Optimized fetch analytics with caching
  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      const days = timeRangeToDays(timeRange);

      // Use cache service for all three APIs
      const [analyticsData, accuracyDataRes, configDataRes] = await Promise.all([
        moderationCacheService.cachedApiCall(
          'moderation_analytics',
          async () => await getModerationAnalytics(days),
          { days }
        ),
        moderationCacheService.cachedApiCall(
          'accuracy_summary',
          async () => await getAccuracySummary(),
          {}
        ),
        moderationCacheService.cachedApiCall(
          'moderation_config',
          async () => await getModerationConfig(),
          {}
        ),
      ]);

      const analyticsObj = analyticsData.data || analyticsData;
      const accuracyObj = accuracyDataRes.data || accuracyDataRes;
      const configObj = configDataRes.data || configDataRes;

      setAnalytics(analyticsObj);
      setAccuracyData(accuracyObj);
      setModerationConfig(configObj);
      setError(null);

      console.log('✅ Analytics data loaded:', {
        analytics: analyticsObj?.summary?.total_feedback || 0,
        accuracy: accuracyObj?.['7d']?.accuracy || 0,
        config: configObj?.learning_enabled || false,
        fromCache: {
          analytics: analyticsData.__fromCache || false,
          accuracy: accuracyDataRes.__fromCache || false,
          config: configDataRes.__fromCache || false,
        },
      });
    } catch (err) {
      console.error('Error fetching analytics:', err);
      setError('Không thể tải dữ liệu analytics');
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="size-8 animate-spin rounded-full border-b-2 border-blue-600"></div>
        <span className="ml-2">Đang tải analytics...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4">
        <p className="text-red-800">{error}</p>
        <button
          onClick={() => {
            moderationCacheService.invalidateCache('moderation_analytics');
            moderationCacheService.invalidateCache('accuracy_summary');
            moderationCacheService.invalidateCache('moderation_config');
            fetchAnalytics();
          }}
          className="mt-2 text-sm text-red-600 underline hover:text-red-800"
        >
          Thử lại
        </button>
      </div>
    );
  }

  // Dynamic stats based on real data
  const stats = [
    {
      title: 'Tổng review đã xử lý',
      value: analytics?.volume_metrics?.total_reviews?.toLocaleString() || '0',
      change: analytics?.summary?.processing_change_percentage || '+0%',
      changeType: analytics?.summary?.processing_change_percentage?.includes('+')
        ? 'increase'
        : 'decrease',
      icon: '📊',
      color: 'blue',
    },
    {
      title: 'Tổng feedback',
      value: analytics?.summary?.total_feedback?.toLocaleString() || '0',
      change: analytics?.summary?.feedback_change_percentage || '+0%',
      changeType: analytics?.summary?.feedback_change_percentage?.includes('+')
        ? 'increase'
        : 'decrease',
      icon: '📝',
      color: 'gray',
    },
    {
      title: 'Độ chính xác AI',
      value:
        analytics?.summary?.overall_accuracy !== undefined
          ? `${(analytics.summary.overall_accuracy * 100).toFixed(1)}%`
          : '0%',
      change:
        analytics?.summary?.accuracy_vs_target !== undefined
          ? `${(analytics.summary.accuracy_vs_target * 100).toFixed(1)}%`
          : '+0%',
      changeType: analytics?.summary?.accuracy_vs_target > 0 ? 'increase' : 'decrease',
      icon: '🎯',
      color: 'purple',
    },
    {
      title: 'Auto-marked reviews',
      value: analytics?.volume_metrics?.auto_marked_reviews?.toLocaleString() || '0',
      change: '',
      changeType: 'increase',
      icon: '🚨',
      color: 'red',
    },
    {
      title: 'Pending moderation',
      value: analytics?.volume_metrics?.pending_moderation?.toLocaleString() || '0',
      change: '',
      changeType: 'decrease',
      icon: '⏳',
      color: 'indigo',
    },
  ];

  // Add learning system stats if enabled
  if (moderationConfig?.learning_enabled) {
    stats.push({
      title: 'Learning adjustments',
      value: analytics?.accuracy_metrics?.total_learning_adjustments?.toString() || '0',
      change: '',
      changeType: 'increase',
      icon: '🧠',
      color: 'indigo',
    });
  }

  const getColorClasses = color => {
    const colors = {
      blue: 'bg-blue-50 border-blue-200 text-blue-800',
      green: 'bg-green-50 border-green-200 text-green-800',
      purple: 'bg-purple-50 border-purple-200 text-purple-800',
      red: 'bg-red-50 border-red-200 text-red-800',
      indigo: 'bg-indigo-50 border-indigo-200 text-indigo-800',
    };
    return colors[color] || colors.blue;
  };

  return (
    <div className="space-y-6">
      {/* Time Range Selector */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">Phân tích hiệu suất</h2>
        <div className="flex items-center space-x-4">
          {moderationConfig?.learning_enabled && (
            <div className="flex items-center space-x-2">
              <div className="size-2 animate-pulse rounded-full bg-green-400"></div>
              <span className="text-sm font-medium text-green-600">Learning System Active</span>
            </div>
          )}
          <select
            value={timeRange}
            onChange={e => {
              setTimeRange(e.target.value);
              // Invalidate analytics cache when time range changes
              moderationCacheService.invalidateCache('moderation_analytics');
            }}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm text-black"
          >
            <option className="text-black" value="week">
              Tuần này
            </option>
            <option className="text-black" value="month">
              Tháng này
            </option>
            <option className="text-black" value="quarter">
              Quý này
            </option>
            <option className="text-black" value="year">
              Năm nay
            </option>
          </select>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5">
        {stats.map((stat, index) => (
          <div key={index} className={`rounded-xl border p-6 ${getColorClasses(stat.color)}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium opacity-75">{stat.title}</p>
                <p className="mt-2 text-3xl font-bold">{stat.value}</p>
              </div>
              <div className="text-3xl">{stat.icon}</div>
            </div>
            <div className="mt-4 flex items-center">
              <span
                className={`text-xs font-medium ${
                  stat.changeType === 'increase' ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {stat.change}
              </span>
              <span className="ml-1 text-xs opacity-75">so với kỳ trước</span>
            </div>
          </div>
        ))}
      </div>

      {/* Learning System Performance */}
      {moderationConfig?.learning_enabled && analytics?.accuracy_metrics && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h3 className="mb-4 text-lg font-semibold text-gray-900">Hiệu suất Learning System</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Precision</span>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-bold text-gray-900">
                    {analytics?.accuracy_metrics?.precision !== undefined
                      ? (analytics.accuracy_metrics.precision * 100).toFixed(1) + '%'
                      : '0%'}
                  </span>
                  <div className="h-2 w-24 rounded-full bg-gray-200">
                    <div
                      className="h-2 rounded-full bg-blue-600"
                      style={{ width: `${(analytics.accuracy_metrics.precision || 0) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Recall</span>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-bold text-gray-900">
                    {analytics?.accuracy_metrics?.recall !== undefined
                      ? (analytics.accuracy_metrics.recall * 100).toFixed(1) + '%'
                      : '0%'}
                  </span>
                  <div className="h-2 w-24 rounded-full bg-gray-200">
                    <div
                      className="h-2 rounded-full bg-green-600"
                      style={{ width: `${(analytics.accuracy_metrics.recall || 0) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">F1 Score</span>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-bold text-gray-900">
                    {analytics?.accuracy_metrics?.f1_score !== undefined
                      ? (analytics.accuracy_metrics.f1_score * 100).toFixed(1) + '%'
                      : '0%'}
                  </span>
                  <div className="h-2 w-24 rounded-full bg-gray-200">
                    <div
                      className="h-2 rounded-full bg-purple-600"
                      style={{ width: `${(analytics.accuracy_metrics.f1_score || 0) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Current Thresholds */}
            <div className="mt-6 border-t border-gray-200 pt-4">
              <h4 className="mb-3 text-sm font-semibold text-gray-700">Current Thresholds</h4>
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-xs text-gray-700">Auto Mark:</span>
                  <span className="font-mono text-gray-900">
                    {moderationConfig.auto_mark_threshold}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-xs text-gray-700">Flag Review:</span>
                  <span className="font-mono text-gray-900">
                    {moderationConfig.flag_for_review_threshold}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-xs text-gray-700">Suggest Warning:</span>
                  <span className="font-mono text-gray-900">
                    {moderationConfig.suggest_warning_threshold}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h3 className="mb-4 text-lg font-semibold text-gray-900">Learning Metrics</h3>
            <div className="space-y-4">
              <div className="rounded-lg bg-blue-50 p-4">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm font-medium text-blue-800">Total Feedback</span>
                  <span className="text-lg font-bold text-blue-900">
                    {analytics?.accuracy_metrics?.total_feedback || 0}
                  </span>
                </div>
                <div className="text-xs text-blue-600">
                  Minimum needed: {analytics?.configuration?.min_feedback_count || 0}
                </div>
              </div>
              <div className="rounded-lg bg-green-50 p-4">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm font-medium text-green-800">Successful Adjustments</span>
                  <span className="text-lg font-bold text-green-900">
                    {analytics?.learning_status?.effectiveness?.improvement !== undefined
                      ? (analytics.learning_status.effectiveness.improvement * 100).toFixed(1) + '%'
                      : '0%'}
                  </span>
                </div>
                <div className="text-xs text-green-600">
                  Learning rate: {analytics?.configuration?.learning_rate || 0}
                </div>
              </div>
              <div className="rounded-lg bg-yellow-50 p-4">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm font-medium text-yellow-800">False Positives</span>
                  <span className="text-lg font-bold text-yellow-900">
                    {analytics?.accuracy_metrics?.false_positives || 0}
                  </span>
                </div>
                <div className="text-xs text-yellow-600">
                  Target: &lt;
                  {(analytics?.configuration?.false_positive_limit * 100 || 0).toFixed(0)}%
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts and Analytics */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Processing Trend */}
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">Xu hướng xử lý</h3>
          <div className="space-y-4">
            {analytics?.accuracy_metrics?.trends?.weekly_accuracy?.length > 0 ? (
              analytics.accuracy_metrics.trends.weekly_accuracy.map((item, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Tuần {item.week}</span>
                  <span className="text-sm text-gray-900">
                    {(item.accuracy * 100).toFixed(1)}% ({item.total_feedback} feedback)
                  </span>
                </div>
              ))
            ) : (
              <div className="py-4 text-center text-gray-500">Chưa có dữ liệu trend</div>
            )}
          </div>
        </div>

        {/* Top Detection Categories */}
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">Loại phát hiện phổ biến</h3>
          <div className="space-y-4">
            {analytics?.detection_categories?.map((category, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="mb-1 flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">{category.type}</span>
                    <span className="text-sm text-gray-500">{category.count} trường hợp</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-gray-200">
                    <div
                      className="h-2 rounded-full bg-red-600"
                      style={{ width: `${category.percentage}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            )) || (
              <div className="py-4 text-center text-gray-500">
                Chưa có dữ liệu detection categories
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Moderator Performance */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Hiệu suất Moderator</h3>
        <div className="overflow-x-auto">
          {analytics?.accuracy_metrics?.moderator_performance?.length > 0 ? (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700">
                    Moderator
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700">
                    Đã xử lý
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700">
                    Độ chính xác
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700">
                    Thời gian TB
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {analytics.accuracy_metrics.moderator_performance.map((mod, idx) => (
                  <tr key={idx}>
                    <td className="whitespace-nowrap px-6 py-4 text-gray-900">{mod.moderator}</td>
                    <td className="whitespace-nowrap px-6 py-4 text-gray-900">
                      {mod.total_feedback}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-gray-900">
                      {(mod.accuracy * 100).toFixed(1)}%
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-gray-900">
                      {mod.avg_time_seconds}s
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="py-4 text-center text-gray-500">
              Chưa có dữ liệu moderator performance
            </div>
          )}
        </div>
      </div>

      {/* Export Options */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Xuất báo cáo</h3>
        <div className="flex space-x-4">
          <button className="rounded-md bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700">
            📊 Xuất PDF
          </button>
          <button className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">
            📈 Xuất Excel
          </button>
          <button className="rounded-md bg-purple-600 px-4 py-2 text-sm text-white hover:bg-purple-700">
            📋 Báo cáo chi tiết
          </button>
          {moderationConfig?.learning_enabled && (
            <button className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700">
              🧠 Learning Report
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Analytics;
