import React, { useState, useEffect } from 'react';
import adminMovieService from '../../../api/adminMovieService';

const AutoProcessingStatus = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState({});
  const [lastRefresh, setLastRefresh] = useState(null);

  // Fetch automation status
  const fetchStatus = async () => {
    try {
      setLoading(true);
      const response = await adminMovieService.getAutoProcessingStatus();
      if (response.data?.status === 'success') {
        setStatus(response.data.data);
        setLastRefresh(new Date());
      }
    } catch (error) {
      console.error('Error fetching auto-processing status:', error);
    } finally {
      setLoading(false);
    }
  };

  // Trigger manual processing
  const triggerProcessing = async (type, options = {}) => {
    try {
      setTriggering(prev => ({ ...prev, [type]: true }));

      const response = await adminMovieService.triggerManualProcessing({
        type,
        ...options,
      });

      if (response.data?.status === 'success') {
        // Refresh status after a delay
        setTimeout(fetchStatus, 3000);
      }
    } catch (error) {
      console.error(`Error triggering ${type} processing:`, error);
    } finally {
      setTriggering(prev => ({ ...prev, [type]: false }));
    }
  };

  // Auto refresh every 30 seconds
  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !status) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded mb-4 w-1/3"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          </div>
        </div>
      </div>
    );
  }

  const getStatusColor = isHealthy => {
    if (isHealthy === null) return 'text-gray-500';
    return isHealthy ? 'text-green-600' : 'text-red-600';
  };

  const getStatusIcon = isHealthy => {
    if (isHealthy === null) return '⏳';
    return isHealthy ? '✅' : '❌';
  };

  const formatTimestamp = timestamp => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const automation = status?.automation_status || {};
  const health = status?.system_health || {};

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">🔄 Auto-Processing Status</h3>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-500">
              Last updated: {lastRefresh ? formatTimestamp(lastRefresh) : 'Loading...'}
            </span>
            <button
              onClick={fetchStatus}
              disabled={loading}
              className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 disabled:opacity-50"
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>
      </div>

      <div className="p-6">
        {/* System Health */}
        <div className="mb-6">
          <h4 className="text-md font-medium text-gray-900 mb-3">System Health</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center space-x-2">
              <span>{getStatusIcon(health.database_responsive)}</span>
              <span className={getStatusColor(health.database_responsive)}>Database</span>
            </div>
            <div className="flex items-center space-x-2">
              <span>{getStatusIcon(health.cache_responsive)}</span>
              <span className={getStatusColor(health.cache_responsive)}>Cache</span>
            </div>
            <div className="flex items-center space-x-2">
              <span>{getStatusIcon(status?.queue_status?.celery_available)}</span>
              <span className={getStatusColor(status?.queue_status?.celery_available)}>
                Celery Tasks
              </span>
            </div>
          </div>
        </div>

        {/* Task Status */}
        {status?.queue_status?.task_status && (
          <div className="mb-6">
            <h4 className="text-md font-medium text-gray-900 mb-3">Current Task Status</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(status.queue_status.task_status).map(([taskName, taskStatus]) => (
                <div key={taskName} className="bg-gray-50 p-3 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <span>
                      {taskStatus === 'running'
                        ? '🔄'
                        : taskStatus === 'completed'
                          ? '✅'
                          : taskStatus === 'error'
                            ? '❌'
                            : '⏳'}
                    </span>
                    <div>
                      <div className="font-medium text-sm capitalize">
                        {taskName.replace('_', ' ')}
                      </div>
                      <div
                        className={`text-xs ${
                          taskStatus === 'running'
                            ? 'text-blue-600'
                            : taskStatus === 'completed'
                              ? 'text-green-600'
                              : taskStatus === 'error'
                                ? 'text-red-600'
                                : 'text-gray-500'
                        }`}
                      >
                        {taskStatus === 'unknown' ? 'Not yet run' : taskStatus}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Current Activity */}
        <div className="mb-6">
          <h4 className="text-md font-medium text-gray-900 mb-3">Current Activity</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-sm text-blue-600 font-medium">Pending Interactions</div>
              <div className="text-2xl font-bold text-blue-900">
                {automation.pending_interactions?.toLocaleString() || '0'}
              </div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm text-green-600 font-medium">Recent Activity (1h)</div>
              <div className="text-2xl font-bold text-green-900">
                {automation.recent_interactions_1h?.toLocaleString() || '0'}
              </div>
            </div>
          </div>
        </div>

        {/* Last Processing Results */}
        <div className="mb-6">
          <h4 className="text-md font-medium text-gray-900 mb-3">Last Processing Results</h4>
          <div className="space-y-3">
            {/* Interaction Processing */}
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <div className="font-medium">User Interactions</div>
                <div className="text-sm text-gray-600">
                  {automation.last_processing_result ? (
                    <>
                      Processed: {automation.last_processing_result.processed_interactions}{' '}
                      interactions for {automation.last_processing_result.movies_processed} movies
                      <br />
                      <span className="text-xs text-gray-500">
                        {formatTimestamp(automation.last_processing_result.timestamp)}
                      </span>
                    </>
                  ) : (
                    'No recent processing'
                  )}
                </div>
              </div>
              <button
                onClick={() => triggerProcessing('interactions', { hours: 1 })}
                disabled={triggering.interactions}
                className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 disabled:opacity-50"
              >
                {triggering.interactions ? 'Triggering...' : 'Trigger Now'}
              </button>
            </div>

            {/* Metrics Calculation */}
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <div className="font-medium">Production Metrics</div>
                <div className="text-sm text-gray-600">
                  {automation.last_metrics_calculation ? (
                    <>
                      Calculated for {automation.last_metrics_calculation.processed_movies} movies (
                      {automation.last_metrics_calculation.errors} errors)
                      <br />
                      <span className="text-xs text-gray-500">
                        {formatTimestamp(automation.last_metrics_calculation.timestamp)}
                      </span>
                    </>
                  ) : (
                    'No recent calculation'
                  )}
                </div>
              </div>
              <button
                onClick={() => triggerProcessing('metrics')}
                disabled={triggering.metrics}
                className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded-md hover:bg-green-200 disabled:opacity-50"
              >
                {triggering.metrics ? 'Triggering...' : 'Trigger Now'}
              </button>
            </div>

            {/* Trending Sync */}
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <div className="font-medium">Trending Categories</div>
                <div className="text-sm text-gray-600">
                  {automation.last_trending_sync ? (
                    <>
                      Updated {automation.last_trending_sync.updated_count} of{' '}
                      {automation.last_trending_sync.total_checked} movies
                      <br />
                      <span className="text-xs text-gray-500">
                        {formatTimestamp(automation.last_trending_sync.timestamp)}
                      </span>
                    </>
                  ) : (
                    'No recent sync'
                  )}
                </div>
              </div>
              <button
                onClick={() => triggerProcessing('trending')}
                disabled={triggering.trending}
                className="px-3 py-1 text-sm bg-purple-100 text-purple-700 rounded-md hover:bg-purple-200 disabled:opacity-50"
              >
                {triggering.trending ? 'Triggering...' : 'Trigger Now'}
              </button>
            </div>
          </div>
        </div>

        {/* Automation Info */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-md font-medium text-blue-900 mb-2">🤖 Automation Schedule</h4>
          <div className="text-sm text-blue-800 space-y-1">
            <div>• User interactions: Every 15 minutes</div>
            <div>• Production metrics: Auto-triggered after interactions</div>
            <div>• Trending categories: Every 6 hours</div>
            <div>• Daily analytics: Every day at 1:00 AM</div>
            <div>• Data cleanup: Monthly on 1st day at 2:00 AM</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AutoProcessingStatus;
