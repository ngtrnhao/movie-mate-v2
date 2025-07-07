import { useState, useEffect } from 'react';
import {
  getModerationAnalytics,
  getAccuracySummary,
  getModerationConfig,
} from '../../../api/movieService';
import {
  AcademicCapIcon,
  ChartBarIcon,
  CogIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  BoltIcon,
  ClockIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

const LearningDashboard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [accuracySummary, setAccuracySummary] = useState(null);
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState('30d');

  // Fetch data
  const fetchData = async () => {
    setLoading(true);
    try {
      const [analyticsResponse, accuracyResponse, configResponse] = await Promise.all([
        getModerationAnalytics(30),
        getAccuracySummary(),
        getModerationConfig(),
      ]);

      setAnalytics(analyticsResponse);
      setAccuracySummary(accuracyResponse);
      setConfig(configResponse);
    } catch (error) {
      console.error('Error fetching learning data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Calculate learning trends
  const calculateTrends = () => {
    if (!accuracySummary) return null;

    const periods = ['7d', '30d', '90d'];
    const trends = {};

    for (let i = 1; i < periods.length; i++) {
      const current = accuracySummary[periods[i]];
      const previous = accuracySummary[periods[i - 1]];

      if (current && previous) {
        trends[periods[i]] = {
          accuracy: current.accuracy - previous.accuracy,
          precision: current.precision - previous.precision,
          recall: current.recall - previous.recall,
        };
      }
    }

    return trends;
  };

  // Get learning status
  const getLearningStatus = () => {
    if (!config) return { status: 'unknown', message: 'Đang tải...', color: 'gray' };

    if (!config.learning_enabled) {
      return {
        status: 'disabled',
        message: 'Hệ thống học đã tắt',
        color: 'gray',
      };
    }

    const accuracy = analytics?.summary?.overall_accuracy || 0;
    const target = config.accuracy_target || 0.85;

    if (accuracy >= target) {
      return {
        status: 'optimal',
        message: 'Hoạt động tối ưu',
        color: 'green',
      };
    } else if (accuracy >= target - 0.1) {
      return {
        status: 'good',
        message: 'Hoạt động tốt',
        color: 'blue',
      };
    } else {
      return {
        status: 'learning',
        message: 'Đang học và cải thiện',
        color: 'yellow',
      };
    }
  };

  // Get threshold suggestions from analytics
  const getThresholdSuggestions = () => {
    if (!analytics?.threshold_analysis) return [];

    const suggestions = analytics.threshold_analysis.suggestions;
    const confidence = analytics.threshold_analysis.confidence;

    if (!suggestions || Object.keys(suggestions).length === 0) {
      return [];
    }

    return Object.entries(suggestions).map(([key, value]) => ({
      threshold: key,
      currentValue: getCurrentThresholdValue(key),
      suggestedValue: value,
      confidence: confidence,
      change: value - getCurrentThresholdValue(key),
    }));
  };

  const getCurrentThresholdValue = thresholdKey => {
    if (!config) return 0;

    switch (thresholdKey) {
      case 'auto_mark_threshold':
        return config.auto_mark_threshold;
      case 'flag_for_review_threshold':
        return config.flag_for_review_threshold;
      case 'suggest_warning_threshold':
        return config.suggest_warning_threshold;
      default:
        return 0;
    }
  };

  const formatThresholdName = key => {
    switch (key) {
      case 'auto_mark_threshold':
        return 'Auto-mark Threshold';
      case 'flag_for_review_threshold':
        return 'Flag for Review Threshold';
      case 'suggest_warning_threshold':
        return 'Suggest Warning Threshold';
      default:
        return key;
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="space-y-3">
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              <div className="h-4 bg-gray-200 rounded w-2/3"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const learningStatus = getLearningStatus();
  const trends = calculateTrends();
  const thresholdSuggestions = getThresholdSuggestions();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <AcademicCapIcon className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Learning Dashboard</h1>
              <p className="text-gray-600">Theo dõi hiệu suất và trạng thái hệ thống học máy</p>
            </div>
          </div>
          <button
            onClick={fetchData}
            className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            <ArrowPathIcon className="h-4 w-4" />
            <span>Làm mới</span>
          </button>
        </div>
      </div>

      {/* Learning Status */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h3 className="text-lg font-medium mb-4 flex items-center space-x-2">
          <BoltIcon className="h-5 w-5 text-gray-600" />
          <span>Trạng thái Learning System</span>
        </h3>

        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-4">
            <div
              className={`p-3 rounded-full ${
                learningStatus.color === 'green'
                  ? 'bg-green-100'
                  : learningStatus.color === 'blue'
                    ? 'bg-blue-100'
                    : learningStatus.color === 'yellow'
                      ? 'bg-yellow-100'
                      : 'bg-gray-100'
              }`}
            >
              {learningStatus.status === 'optimal' ? (
                <CheckCircleIcon
                  className={`h-6 w-6 ${
                    learningStatus.color === 'green' ? 'text-green-600' : 'text-gray-600'
                  }`}
                />
              ) : learningStatus.status === 'learning' ? (
                <ClockIcon
                  className={`h-6 w-6 ${
                    learningStatus.color === 'yellow' ? 'text-yellow-600' : 'text-gray-600'
                  }`}
                />
              ) : (
                <CogIcon
                  className={`h-6 w-6 ${
                    learningStatus.color === 'blue' ? 'text-blue-600' : 'text-gray-600'
                  }`}
                />
              )}
            </div>

            <div>
              <p className="font-medium text-gray-900">{learningStatus.message}</p>
              <p className="text-sm text-gray-600">
                Learning: {config?.learning_enabled ? 'Bật' : 'Tắt'} • Rate:{' '}
                {config?.learning_rate || 'N/A'} • Min Feedback:{' '}
                {config?.min_feedback_count || 'N/A'}
              </p>
            </div>
          </div>

          {config && (
            <div className="text-right">
              <p className="text-2xl font-bold text-gray-900">
                {(analytics?.summary?.overall_accuracy * 100).toFixed(1)}%
              </p>
              <p className="text-sm text-gray-600">Độ chính xác hiện tại</p>
            </div>
          )}
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Accuracy Trends</h4>
          {accuracySummary && (
            <div className="space-y-3">
              {Object.entries(accuracySummary).map(([period, data]) => (
                <div key={period} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">{period}</span>
                  <div className="flex items-center space-x-2">
                    <span className="font-medium">{(data.accuracy * 100).toFixed(1)}%</span>
                    {trends && trends[period] && (
                      <div className="flex items-center">
                        {trends[period].accuracy > 0 ? (
                          <ArrowTrendingUpIcon className="h-4 w-4 text-green-500" />
                        ) : trends[period].accuracy < 0 ? (
                          <ArrowTrendingDownIcon className="h-4 w-4 text-red-500" />
                        ) : null}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Precision & Recall</h4>
          {accuracySummary && (
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Precision (30d)</span>
                <span className="font-medium">
                  {(accuracySummary['30d']?.precision * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Recall (30d)</span>
                <span className="font-medium">
                  {(accuracySummary['30d']?.recall * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">F1-Score (30d)</span>
                <span className="font-medium">
                  {(accuracySummary['30d']?.f1_score * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Learning Stats</h4>
          {analytics && (
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Total Feedback</span>
                <span className="font-medium">{analytics.summary?.total_feedback || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Auto-marked Reviews</span>
                <span className="font-medium">
                  {analytics.volume_metrics?.auto_marked_reviews || 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Learning Enabled</span>
                <span
                  className={`font-medium ${
                    analytics.learning_status?.learning_enabled ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {analytics.learning_status?.learning_enabled ? 'Yes' : 'No'}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Threshold Suggestions */}
      {thresholdSuggestions.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-medium mb-4 flex items-center space-x-2">
            <ChartBarIcon className="h-5 w-5 text-gray-600" />
            <span>AI Threshold Suggestions</span>
          </h3>

          <div className="space-y-4">
            {thresholdSuggestions.map((suggestion, index) => (
              <div key={index} className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-blue-900">
                      {formatThresholdName(suggestion.threshold)}
                    </h4>
                    <p className="text-sm text-blue-700">
                      Current: {suggestion.currentValue.toFixed(3)} → Suggested:{' '}
                      {suggestion.suggestedValue.toFixed(3)}
                    </p>
                  </div>

                  <div className="text-right">
                    <div
                      className={`flex items-center space-x-1 ${
                        suggestion.change > 0 ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {suggestion.change > 0 ? (
                        <ArrowTrendingUpIcon className="h-4 w-4" />
                      ) : (
                        <ArrowTrendingDownIcon className="h-4 w-4" />
                      )}
                      <span className="text-sm font-medium">
                        {Math.abs(suggestion.change).toFixed(3)}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600">
                      Confidence: {(suggestion.confidence * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <InformationCircleIcon className="h-5 w-5 text-yellow-600 mt-0.5" />
              <div className="text-sm text-yellow-800">
                <p className="font-medium">Lưu ý:</p>
                <p>
                  Các đề xuất này được tạo tự động dựa trên phân tích hiệu suất. Vui lòng xem xét
                  cẩn thận trước khi áp dụng.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Learning Configuration */}
      {config && (
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-medium mb-4 flex items-center space-x-2">
            <CogIcon className="h-5 w-5 text-gray-600" />
            <span>Learning Configuration</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-700">Learning Rate</p>
              <p className="text-lg font-bold text-gray-900">{config.learning_rate}</p>
              <p className="text-xs text-gray-600">Tốc độ học của hệ thống</p>
            </div>

            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-700">Min Feedback Count</p>
              <p className="text-lg font-bold text-gray-900">{config.min_feedback_count}</p>
              <p className="text-xs text-gray-600">Số feedback tối thiểu để học</p>
            </div>

            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-700">Accuracy Target</p>
              <p className="text-lg font-bold text-gray-900">
                {(config.accuracy_target * 100).toFixed(1)}%
              </p>
              <p className="text-xs text-gray-600">Mục tiêu độ chính xác</p>
            </div>

            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-700">False Positive Limit</p>
              <p className="text-lg font-bold text-gray-900">
                {(config.false_positive_limit * 100).toFixed(1)}%
              </p>
              <p className="text-xs text-gray-600">Giới hạn false positive</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LearningDashboard;
