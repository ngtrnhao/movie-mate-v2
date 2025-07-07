import { useState, useEffect } from 'react';
import {
  getModerationConfig,
  updateModerationThresholds,
  toggleLearningSystem,
  getModerationAnalytics,
} from '../../../api/movieService';
import {
  CogIcon,
  AcademicCapIcon,
  ChartBarIcon,
  AdjustmentsHorizontalIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  BoltIcon,
  ShieldCheckIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

const AdminThresholdConfig = () => {
  const [config, setConfig] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [thresholds, setThresholds] = useState({
    autoMarkThreshold: 0.8,
    flagForReviewThreshold: 0.6,
    suggestWarningThreshold: 0.4,
  });
  const [originalThresholds, setOriginalThresholds] = useState({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [learningEnabled, setLearningEnabled] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Fetch current configuration
  const fetchConfig = async () => {
    setLoading(true);
    try {
      const response = await getModerationConfig();
      setConfig(response);

      const newThresholds = {
        autoMarkThreshold: response.auto_mark_threshold,
        flagForReviewThreshold: response.flag_for_review_threshold,
        suggestWarningThreshold: response.suggest_warning_threshold,
      };

      setThresholds(newThresholds);
      setOriginalThresholds(newThresholds);
      setLearningEnabled(response.learning_enabled);
    } catch (error) {
      console.error('Error fetching config:', error);
      setMessage({ type: 'error', text: 'Không thể tải cấu hình' });
    } finally {
      setLoading(false);
    }
  };

  // Fetch analytics
  const fetchAnalytics = async () => {
    try {
      const response = await getModerationAnalytics(30);
      setAnalytics(response);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  // Initial load
  useEffect(() => {
    fetchConfig();
    fetchAnalytics();
  }, []);

  // Check for changes
  useEffect(() => {
    const hasThresholdChanges =
      thresholds.autoMarkThreshold !== originalThresholds.autoMarkThreshold ||
      thresholds.flagForReviewThreshold !== originalThresholds.flagForReviewThreshold ||
      thresholds.suggestWarningThreshold !== originalThresholds.suggestWarningThreshold;

    const hasLearningChange = config && learningEnabled !== config.learning_enabled;

    setHasChanges(hasThresholdChanges || hasLearningChange);
  }, [thresholds, originalThresholds, learningEnabled, config]);

  // Handle threshold change
  const handleThresholdChange = (key, value) => {
    const numValue = parseFloat(value);
    if (numValue >= 0 && numValue <= 1) {
      setThresholds(prev => ({
        ...prev,
        [key]: numValue,
      }));
    }
  };

  // Validate thresholds
  const validateThresholds = () => {
    const { autoMarkThreshold, flagForReviewThreshold, suggestWarningThreshold } = thresholds;

    if (autoMarkThreshold <= flagForReviewThreshold) {
      return 'Auto-mark threshold phải lớn hơn flag-for-review threshold';
    }

    if (flagForReviewThreshold <= suggestWarningThreshold) {
      return 'Flag-for-review threshold phải lớn hơn suggest-warning threshold';
    }

    return null;
  };

  // Save thresholds
  const saveThresholds = async () => {
    const validationError = validateThresholds();
    if (validationError) {
      setMessage({ type: 'error', text: validationError });
      return;
    }

    setSaving(true);
    try {
      await updateModerationThresholds(thresholds);
      setOriginalThresholds({ ...thresholds });
      setMessage({ type: 'success', text: 'Cập nhật thresholds thành công' });

      // Refresh config
      await fetchConfig();
    } catch (error) {
      console.error('Error saving thresholds:', error);
      setMessage({ type: 'error', text: 'Không thể cập nhật thresholds' });
    } finally {
      setSaving(false);
    }
  };

  // Toggle learning system
  const handleToggleLearning = async () => {
    setSaving(true);
    try {
      const newValue = !learningEnabled;
      await toggleLearningSystem(newValue);
      setLearningEnabled(newValue);
      setMessage({
        type: 'success',
        text: `Hệ thống học ${newValue ? 'đã bật' : 'đã tắt'}`,
      });

      // Refresh config
      await fetchConfig();
    } catch (error) {
      console.error('Error toggling learning:', error);
      setMessage({ type: 'error', text: 'Không thể thay đổi trạng thái learning system' });
    } finally {
      setSaving(false);
    }
  };

  // Reset thresholds
  const resetThresholds = () => {
    setThresholds({ ...originalThresholds });
    setLearningEnabled(config?.learning_enabled || false);
    setMessage({ type: '', text: '' });
  };

  // Get threshold recommendation based on analytics
  const getThresholdRecommendation = () => {
    if (!analytics) return null;

    const accuracy = analytics.summary?.overall_accuracy || 0;
    const falsePositiveRate = analytics.accuracy_metrics?.false_positive_rate || 0;

    if (accuracy < 0.8) {
      return {
        type: 'warning',
        message: 'Độ chính xác thấp. Khuyến nghị giảm auto-mark threshold để giảm false positive.',
        suggestion: {
          autoMarkThreshold: Math.max(0.85, thresholds.autoMarkThreshold - 0.05),
        },
      };
    }

    if (falsePositiveRate > 0.15) {
      return {
        type: 'warning',
        message: 'Tỷ lệ false positive cao. Khuyến nghị tăng thresholds.',
        suggestion: {
          autoMarkThreshold: Math.min(0.95, thresholds.autoMarkThreshold + 0.05),
          flagForReviewThreshold: Math.min(0.8, thresholds.flagForReviewThreshold + 0.05),
        },
      };
    }

    if (accuracy > 0.9 && falsePositiveRate < 0.05) {
      return {
        type: 'success',
        message: 'Hiệu suất tốt! Có thể tinh chỉnh để tăng khả năng phát hiện.',
        suggestion: {
          autoMarkThreshold: Math.max(0.75, thresholds.autoMarkThreshold - 0.02),
        },
      };
    }

    return null;
  };

  // Apply suggested thresholds
  const applySuggestion = suggestion => {
    setThresholds(prev => ({
      ...prev,
      ...suggestion,
    }));
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

  const recommendation = getThresholdRecommendation();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <CogIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Cấu hình Thresholds</h1>
              <p className="text-gray-600">
                Quản lý ngưỡng phát hiện spoiler và cấu hình hệ thống học
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              fetchConfig();
              fetchAnalytics();
            }}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            <ArrowPathIcon className="h-4 w-4" />
            <span>Làm mới</span>
          </button>
        </div>
      </div>

      {/* Message */}
      {message.text && (
        <div
          className={`p-4 rounded-lg border ${
            message.type === 'success'
              ? 'bg-green-50 border-green-200 text-green-800'
              : 'bg-red-50 border-red-200 text-red-800'
          }`}
        >
          <div className="flex items-center space-x-2">
            {message.type === 'success' ? (
              <CheckCircleIcon className="h-5 w-5" />
            ) : (
              <ExclamationTriangleIcon className="h-5 w-5" />
            )}
            <span>{message.text}</span>
          </div>
        </div>
      )}

      {/* Current Performance */}
      {analytics && (
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-medium mb-4 flex items-center space-x-2">
            <ChartBarIcon className="h-5 w-5 text-gray-600" />
            <span>Hiệu suất hiện tại (30 ngày)</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-2xl font-bold text-blue-600">
                {(analytics.summary?.overall_accuracy * 100).toFixed(1)}%
              </p>
              <p className="text-sm text-gray-600">Độ chính xác</p>
            </div>

            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-2xl font-bold text-green-600">
                {analytics.accuracy_metrics?.precision?.toFixed(3) || '0.000'}
              </p>
              <p className="text-sm text-gray-600">Precision</p>
            </div>

            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <p className="text-2xl font-bold text-purple-600">
                {analytics.accuracy_metrics?.recall?.toFixed(3) || '0.000'}
              </p>
              <p className="text-sm text-gray-600">Recall</p>
            </div>

            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <p className="text-2xl font-bold text-yellow-600">
                {analytics.volume_metrics?.auto_marked_reviews || 0}
              </p>
              <p className="text-sm text-gray-600">Auto-marked</p>
            </div>
          </div>
        </div>
      )}

      {/* Recommendation */}
      {recommendation && (
        <div
          className={`p-4 rounded-lg border ${
            recommendation.type === 'success'
              ? 'bg-green-50 border-green-200'
              : 'bg-yellow-50 border-yellow-200'
          }`}
        >
          <div className="flex items-start space-x-3">
            <BoltIcon
              className={`h-5 w-5 mt-0.5 ${
                recommendation.type === 'success' ? 'text-green-600' : 'text-yellow-600'
              }`}
            />
            <div className="flex-1">
              <p
                className={`font-medium ${
                  recommendation.type === 'success' ? 'text-green-800' : 'text-yellow-800'
                }`}
              >
                Khuyến nghị từ AI
              </p>
              <p
                className={`text-sm mt-1 ${
                  recommendation.type === 'success' ? 'text-green-700' : 'text-yellow-700'
                }`}
              >
                {recommendation.message}
              </p>
              {recommendation.suggestion && (
                <button
                  onClick={() => applySuggestion(recommendation.suggestion)}
                  className={`mt-2 px-3 py-1 text-sm rounded ${
                    recommendation.type === 'success'
                      ? 'bg-green-600 text-white hover:bg-green-700'
                      : 'bg-yellow-600 text-white hover:bg-yellow-700'
                  } transition-colors`}
                >
                  Áp dụng khuyến nghị
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Threshold Configuration */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <div className="flex items-center space-x-3 mb-6">
          <AdjustmentsHorizontalIcon className="h-6 w-6 text-gray-600" />
          <h3 className="text-lg font-medium">Cấu hình Thresholds</h3>
        </div>

        <div className="space-y-6">
          {/* Auto Mark Threshold */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Auto-mark Threshold
              <span className="text-gray-500 ml-2">(≥ {thresholds.autoMarkThreshold})</span>
            </label>
            <div className="flex items-center space-x-4">
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={thresholds.autoMarkThreshold}
                onChange={e => handleThresholdChange('autoMarkThreshold', e.target.value)}
                className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              />
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={thresholds.autoMarkThreshold}
                onChange={e => handleThresholdChange('autoMarkThreshold', e.target.value)}
                className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
              />
            </div>
            <p className="text-xs text-gray-600 mt-1">
              Reviews với confidence ≥ {thresholds.autoMarkThreshold} sẽ được đánh dấu tự động
            </p>
          </div>

          {/* Flag for Review Threshold */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Flag for Review Threshold
              <span className="text-gray-500 ml-2">
                ({thresholds.flagForReviewThreshold} - {thresholds.autoMarkThreshold})
              </span>
            </label>
            <div className="flex items-center space-x-4">
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={thresholds.flagForReviewThreshold}
                onChange={e => handleThresholdChange('flagForReviewThreshold', e.target.value)}
                className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              />
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={thresholds.flagForReviewThreshold}
                onChange={e => handleThresholdChange('flagForReviewThreshold', e.target.value)}
                className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
              />
            </div>
            <p className="text-xs text-gray-600 mt-1">Reviews sẽ được gắn cờ để user xác nhận</p>
          </div>

          {/* Suggest Warning Threshold */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Suggest Warning Threshold
              <span className="text-gray-500 ml-2">
                ({thresholds.suggestWarningThreshold} - {thresholds.flagForReviewThreshold})
              </span>
            </label>
            <div className="flex items-center space-x-4">
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={thresholds.suggestWarningThreshold}
                onChange={e => handleThresholdChange('suggestWarningThreshold', e.target.value)}
                className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              />
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={thresholds.suggestWarningThreshold}
                onChange={e => handleThresholdChange('suggestWarningThreshold', e.target.value)}
                className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
              />
            </div>
            <p className="text-xs text-gray-600 mt-1">Reviews sẽ được gửi vào queue kiểm duyệt</p>
          </div>
        </div>

        {/* Visual Threshold Representation */}
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Minh họa Thresholds</h4>
          <div className="relative h-8 bg-gradient-to-r from-green-200 via-yellow-200 via-orange-200 to-red-200 rounded">
            {/* Threshold markers */}
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-red-600"
              style={{ left: `${thresholds.autoMarkThreshold * 100}%` }}
            >
              <div className="absolute -top-6 -left-8 text-xs font-medium text-red-600">
                Auto: {thresholds.autoMarkThreshold}
              </div>
            </div>
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-orange-600"
              style={{ left: `${thresholds.flagForReviewThreshold * 100}%` }}
            >
              <div className="absolute -bottom-6 -left-8 text-xs font-medium text-orange-600">
                Flag: {thresholds.flagForReviewThreshold}
              </div>
            </div>
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-yellow-600"
              style={{ left: `${thresholds.suggestWarningThreshold * 100}%` }}
            >
              <div className="absolute -top-6 -left-10 text-xs font-medium text-yellow-600">
                Warning: {thresholds.suggestWarningThreshold}
              </div>
            </div>
          </div>
          <div className="flex justify-between text-xs text-gray-600 mt-8">
            <span>0.0 (No Action)</span>
            <span>1.0 (Maximum Confidence)</span>
          </div>
        </div>
      </div>

      {/* Learning System Configuration */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <div className="flex items-center space-x-3 mb-6">
          <AcademicCapIcon className="h-6 w-6 text-gray-600" />
          <h3 className="text-lg font-medium">Hệ thống học (Learning System)</h3>
        </div>

        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div>
            <p className="font-medium text-gray-900">Tự động điều chỉnh thresholds</p>
            <p className="text-sm text-gray-600">
              Hệ thống sẽ học từ feedback của moderator để tự động cải thiện độ chính xác
            </p>
          </div>

          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={learningEnabled}
              onChange={handleToggleLearning}
              disabled={saving}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {config && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="p-3 bg-blue-50 rounded">
              <p className="font-medium text-blue-900">Learning Rate</p>
              <p className="text-blue-700">{config.learning_rate}</p>
            </div>
            <div className="p-3 bg-green-50 rounded">
              <p className="font-medium text-green-900">Min Feedback Count</p>
              <p className="text-green-700">{config.min_feedback_count}</p>
            </div>
            <div className="p-3 bg-purple-50 rounded">
              <p className="font-medium text-purple-900">Accuracy Target</p>
              <p className="text-purple-700">{(config.accuracy_target * 100).toFixed(1)}%</p>
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex space-x-3">
        <button
          onClick={saveThresholds}
          disabled={!hasChanges || saving || validateThresholds()}
          className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
        >
          {saving ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
          ) : (
            <ShieldCheckIcon className="h-5 w-5" />
          )}
          <span>{saving ? 'Đang lưu...' : 'Lưu cấu hình'}</span>
        </button>

        <button
          onClick={resetThresholds}
          disabled={!hasChanges || saving}
          className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Reset
        </button>
      </div>

      {/* Information Panel */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <InformationCircleIcon className="h-5 w-5 text-blue-600 mt-0.5" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-2">Hướng dẫn sử dụng:</p>
            <ul className="space-y-1 list-disc list-inside">
              <li>Thresholds cao hơn = ít false positive nhưng có thể bỏ sót spoiler</li>
              <li>Thresholds thấp hơn = phát hiện nhiều hơn nhưng có thể có false positive</li>
              <li>Learning system sẽ tự động điều chỉnh dựa trên feedback của moderator</li>
              <li>Khuyến nghị kiểm tra hiệu suất hàng tuần và điều chỉnh thích hợp</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminThresholdConfig;
