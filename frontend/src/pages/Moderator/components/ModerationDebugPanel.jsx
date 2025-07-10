import { useState, useEffect } from 'react';
import {
  ClockIcon,
  CheckCircleIcon,
  XMarkIcon,
  CpuChipIcon,
  ClockIcon as ClockIconOutline,
  ChartPieIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import moderationCacheService from '../../../services/moderationCacheService';

const ModerationDebugPanel = ({ showDebug = false, onToggleDebug = () => {} }) => {
  const [cacheStats, setCacheStats] = useState(null);
  const [cacheEntries, setCacheEntries] = useState([]);
  const [apiCallHistory, setApiCallHistory] = useState([]);
  const [performanceMetrics, setPerformanceMetrics] = useState({
    totalCalls: 0,
    duplicatesPrevented: 0,
    cacheHits: 0,
    cacheMisses: 0,
    averageResponseTime: 0,
    errorRate: 0,
  });

  // Update stats from cache service
  useEffect(() => {
    if (!showDebug) return;

    const updateStats = () => {
      const stats = moderationCacheService.getStats();
      const entries = moderationCacheService.getCacheStatus();

      setCacheStats(stats);
      setCacheEntries(entries);
      setApiCallHistory(stats.apiCallHistory || []);

      // Calculate performance metrics
      const successfulCalls = stats.apiCallHistory?.filter(call => call.status === 'success') || [];
      const errorCalls = stats.apiCallHistory?.filter(call => call.status === 'error') || [];
      const avgResponseTime =
        successfulCalls.length > 0
          ? successfulCalls.reduce((sum, call) => sum + (call.responseTime || 0), 0) /
            successfulCalls.length
          : 0;

      setPerformanceMetrics({
        totalCalls: stats.totalCalls || 0,
        duplicatesPrevented: stats.duplicatesPrevented || 0,
        cacheHits: stats.cacheHits || 0,
        cacheMisses: stats.cacheMisses || 0,
        averageResponseTime: Math.round(avgResponseTime),
        errorRate:
          stats.totalCalls > 0 ? Math.round((errorCalls.length / stats.totalCalls) * 100) : 0,
      });
    };

    // Update immediately
    updateStats();

    // Register for real-time updates
    const unsubscribe = moderationCacheService.onStatsUpdate(updateStats);

    // Auto-refresh every 2 seconds
    const interval = setInterval(updateStats, 2000);

    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, [showDebug]);

  const getApiStatusColor = apiName => {
    const recentCalls = apiCallHistory.filter(call => call.endpoint.includes(apiName)).slice(0, 3);

    if (recentCalls.length === 0) return 'bg-gray-100 text-gray-600';

    const hasErrors = recentCalls.some(call => call.status === 'error');
    const allSuccess = recentCalls.every(call => call.status === 'success');

    if (hasErrors) return 'bg-red-100 text-red-600';
    if (allSuccess) return 'bg-green-100 text-green-600';
    return 'bg-yellow-100 text-yellow-600';
  };

  const clearCache = () => {
    moderationCacheService.invalidateCache();
    moderationCacheService.resetStats();
  };

  const formatTimestamp = timestamp => {
    return new Date(timestamp).toLocaleTimeString('vi-VN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const getEndpointName = endpoint => {
    if (endpoint.includes('unified_moderation_queue')) return 'Unified Queue';
    if (endpoint.includes('moderation_queue_optimized')) return 'Optimized Queue';
    if (endpoint.includes('spoiler_statistics_optimized')) return 'Spoiler Stats';
    if (endpoint.includes('auto_marked_reviews')) return 'Auto-marked';
    if (endpoint.includes('moderation_analytics')) return 'Analytics';
    if (endpoint.includes('accuracy_summary')) return 'Accuracy';
    if (endpoint.includes('active_config')) return 'Config';
    return 'Unknown';
  };

  if (!showDebug) {
    return (
      <div className="fixed bottom-4 left-4 z-50">
        <button
          onClick={() => onToggleDebug(true)}
          className="rounded-full bg-blue-600 p-3 text-white shadow-lg transition-colors hover:bg-blue-700"
          title="Show API Debug Panel"
        >
          <CpuChipIcon className="size-5" />
        </button>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="max-h-[90vh] w-full max-w-6xl overflow-hidden rounded-lg bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between bg-blue-600 p-4 text-white">
          <div className="flex items-center space-x-3">
            <CpuChipIcon className="size-6" />
            <div>
              <h3 className="text-lg font-semibold">Moderation API Debug Panel</h3>
              <p className="text-sm text-blue-100">Real-time monitoring and cache statistics</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={clearCache}
              className="flex items-center space-x-1 rounded bg-red-500 px-3 py-1 text-sm text-white hover:bg-red-600"
            >
              <ArrowPathIcon className="size-4" />
              <span>Clear Cache</span>
            </button>
            <button
              onClick={() => onToggleDebug(false)}
              className="rounded bg-blue-700 p-2 text-white hover:bg-blue-800"
            >
              <XMarkIcon className="size-5" />
            </button>
          </div>
        </div>

        <div className="max-h-[calc(90vh-80px)] overflow-y-auto p-6">
          {/* Performance Metrics Grid */}
          <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
            <div className="rounded-lg border border-blue-200 bg-blue-50 p-3">
              <div className="text-sm font-medium text-blue-700">Total Calls</div>
              <div className="text-2xl font-bold text-blue-900">
                {performanceMetrics.totalCalls}
              </div>
            </div>

            <div className="rounded-lg border border-green-200 bg-green-50 p-3">
              <div className="text-sm font-medium text-green-700">Cache Hits</div>
              <div className="text-2xl font-bold text-green-900">
                {performanceMetrics.cacheHits}
              </div>
            </div>

            <div className="rounded-lg border border-orange-200 bg-orange-50 p-3">
              <div className="text-sm font-medium text-orange-700">Cache Misses</div>
              <div className="text-2xl font-bold text-orange-900">
                {performanceMetrics.cacheMisses}
              </div>
            </div>

            <div className="rounded-lg border border-purple-200 bg-purple-50 p-3">
              <div className="text-sm font-medium text-purple-700">Duplicates Prevented</div>
              <div className="text-2xl font-bold text-purple-900">
                {performanceMetrics.duplicatesPrevented}
              </div>
            </div>

            <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-3">
              <div className="text-sm font-medium text-indigo-700">Avg Response</div>
              <div className="text-2xl font-bold text-indigo-900">
                {performanceMetrics.averageResponseTime}ms
              </div>
            </div>

            <div
              className={`rounded-lg border p-3 ${
                performanceMetrics.errorRate > 5
                  ? 'border-red-200 bg-red-50'
                  : 'border-green-200 bg-green-50'
              }`}
            >
              <div
                className={`text-sm font-medium ${
                  performanceMetrics.errorRate > 5 ? 'text-red-700' : 'text-green-700'
                }`}
              >
                Error Rate
              </div>
              <div
                className={`text-2xl font-bold ${
                  performanceMetrics.errorRate > 5 ? 'text-red-900' : 'text-green-900'
                }`}
              >
                {performanceMetrics.errorRate}%
              </div>
            </div>
          </div>

          {/* Cache Hit Ratio */}
          {cacheStats && (
            <div className="mb-6 rounded-lg border border-gray-200 bg-gray-50 p-4">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Cache Hit Ratio</span>
                <span className="text-lg font-bold text-gray-900">{cacheStats.cacheHitRatio}%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-gray-200">
                <div
                  className="h-2 rounded-full bg-green-500 transition-all duration-300"
                  style={{ width: `${cacheStats.cacheHitRatio}%` }}
                ></div>
              </div>
              <div className="mt-1 text-xs text-gray-600">
                {cacheStats.cacheHits} hits out of {cacheStats.totalRequests} total requests
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Cache Entries */}
            <div className="rounded-lg border border-gray-200 bg-white">
              <div className="border-b border-gray-200 bg-gray-50 px-4 py-3">
                <h4 className="flex items-center space-x-2 text-lg font-medium text-gray-900">
                  <ChartPieIcon className="size-5" />
                  <span>Cache Entries ({cacheEntries.length})</span>
                </h4>
              </div>
              <div className="max-h-80 overflow-y-auto p-4">
                {cacheEntries.length === 0 ? (
                  <p className="py-4 text-center text-gray-500">No cache entries</p>
                ) : (
                  <div className="space-y-2">
                    {cacheEntries.map((entry, index) => (
                      <div
                        key={index}
                        className={`rounded border p-3 ${
                          entry.isValid
                            ? 'border-green-200 bg-green-50'
                            : 'border-red-200 bg-red-50'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <span
                              className={`inline-block size-2 rounded-full ${
                                entry.isValid ? 'bg-green-500' : 'bg-red-500'
                              }`}
                            ></span>
                            <span className="text-sm font-medium">
                              {getEndpointName(entry.key)}
                            </span>
                          </div>
                          <div className="text-xs text-gray-600">
                            {entry.isValid ? `${entry.remainingTime}s left` : 'Expired'}
                          </div>
                        </div>
                        <div className="mt-1 text-xs text-gray-500">
                          Age: {entry.age}s / TTL: {entry.ttl}s
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* API Call History */}
            <div className="rounded-lg border border-gray-200 bg-white">
              <div className="border-b border-gray-200 bg-gray-50 px-4 py-3">
                <h4 className="flex items-center space-x-2 text-lg font-medium text-gray-900">
                  <ClockIconOutline className="size-5" />
                  <span>Recent API Calls</span>
                </h4>
              </div>
              <div className="max-h-80 overflow-y-auto p-4">
                {apiCallHistory.length === 0 ? (
                  <p className="py-4 text-center text-gray-500">No API calls recorded</p>
                ) : (
                  <div className="space-y-2">
                    {apiCallHistory.slice(0, 10).map((call, index) => (
                      <div
                        key={call.id || index}
                        className={`rounded border p-3 ${
                          call.status === 'success'
                            ? 'border-green-200 bg-green-50'
                            : call.status === 'error'
                              ? 'border-red-200 bg-red-50'
                              : 'border-yellow-200 bg-yellow-50'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            {call.status === 'success' ? (
                              <CheckCircleIcon className="size-4 text-green-600" />
                            ) : call.status === 'error' ? (
                              <XMarkIcon className="size-4 text-red-600" />
                            ) : (
                              <ClockIcon className="size-4 text-yellow-600" />
                            )}
                            <span className="text-sm font-medium">
                              {getEndpointName(call.endpoint)}
                            </span>
                          </div>
                          <div className="text-xs text-gray-600">
                            {formatTimestamp(call.timestamp)}
                          </div>
                        </div>
                        <div className="mt-1 flex justify-between text-xs text-gray-500">
                          <span>Status: {call.status}</span>
                          {call.responseTime && <span>Response: {call.responseTime}ms</span>}
                        </div>
                        {call.error && (
                          <div className="mt-1 font-mono text-xs text-red-600">
                            Error: {call.error}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* API Status Overview */}
          <div className="mt-6 rounded-lg border border-gray-200 bg-white">
            <div className="border-b border-gray-200 bg-gray-50 px-4 py-3">
              <h4 className="text-lg font-medium text-gray-900">API Endpoints Status</h4>
            </div>
            <div className="p-4">
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-7">
                {[
                  'unified_moderation_queue',
                  'moderation_queue_optimized',
                  'spoiler_statistics_optimized',
                  'auto_marked_reviews',
                  'moderation_analytics',
                  'accuracy_summary',
                  'active_config',
                ].map(apiName => {
                  const calls = apiCallHistory.filter(call => call.endpoint.includes(apiName));
                  const lastCall = calls[0];
                  const totalCalls = calls.length;

                  return (
                    <div
                      key={apiName}
                      className={`rounded border p-3 ${getApiStatusColor(apiName)}`}
                    >
                      <div className="text-xs font-medium">{getEndpointName(apiName)}</div>
                      <div className="text-lg font-bold">{totalCalls}</div>
                      <div className="text-xs">
                        {lastCall ? formatTimestamp(lastCall.timestamp) : 'No calls'}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModerationDebugPanel;
