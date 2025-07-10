import { useState, useEffect, useCallback } from 'react';
import {
  getModerationConfig,
  updateModerationThresholds,
  toggleLearningSystem,
  getModerationAnalytics,
} from '../../../api/movieService';
import moderationCacheService from '../../../services/moderationCacheService';
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
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [hasChanges, setHasChanges] = useState(false);

  const [thresholds, setThresholds] = useState({
    autoMarkThreshold: 0.85,
    flagForReviewThreshold: 0.7,
    suggestWarningThreshold: 0.6,
  });
  const [originalThresholds, setOriginalThresholds] = useState({});
  const [learningEnabled, setLearningEnabled] = useState(false);

  // Optimized fetch config with caching
  const fetchConfig = useCallback(async () => {
    try {
      // Use cache service for moderation config API
      const response = await moderationCacheService.cachedApiCall(
        'moderation_config',
        async () => await getModerationConfig(),
        {}
      );

      setConfig(response);

      if (response) {
        const newThresholds = {
          autoMarkThreshold: response.auto_mark_threshold || 0.85,
          flagForReviewThreshold: response.flag_for_review_threshold || 0.7,
          suggestWarningThreshold: response.suggest_warning_threshold || 0.6,
        };
        setThresholds(newThresholds);
        setOriginalThresholds(newThresholds);
        setLearningEnabled(response.learning_enabled || false);
      }

      console.log('✅ Moderation config loaded:', {
        learningEnabled: response?.learning_enabled || false,
        autoMarkThreshold: response?.auto_mark_threshold || 0,
        fromCache: response.__fromCache || false,
      });
    } catch (error) {
      console.error('Error fetching config:', error);
      setMessage({ type: 'error', text: 'Không thể tải cấu hình' });
    } finally {
      setLoading(false);
    }
  }, []);

  // Optimized fetch analytics with caching
  const fetchAnalytics = useCallback(async () => {
    try {
      // Use cache service for moderation analytics API
      const response = await moderationCacheService.cachedApiCall(
        'moderation_analytics',
        async () => await getModerationAnalytics(30),
        { days: 30 }
      );

      setAnalytics(response);

      console.log('✅ Moderation analytics loaded:', {
        totalFeedback: response?.summary?.total_feedback || 0,
        fromCache: response.__fromCache || false,
      });
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchConfig();
    fetchAnalytics();
  }, [fetchConfig, fetchAnalytics]);

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

      // Invalidate cache and refresh config
      moderationCacheService.invalidateCache('moderation_config');
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

      // Invalidate cache and refresh config
      moderationCacheService.invalidateCache('moderation_config');
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
        <div className="rounded-lg border bg-white p-6 shadow-sm">
          <div className="animate-pulse">
            <div className="mb-4 h-8 w-1/3 rounded bg-gray-200"></div>
            <div className="space-y-3">
              <div className="h-4 w-1/2 rounded bg-gray-200"></div>
              <div className="h-4 w-2/3 rounded bg-gray-200"></div>
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
      <div className="rounded-lg border bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="rounded-lg bg-blue-100 p-2">
              <CogIcon className="size-6 text-blue-600" />
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
              moderationCacheService.invalidateCache('moderation_config');
              moderationCacheService.invalidateCache('moderation_analytics');
              fetchConfig();
              fetchAnalytics();
            }}
            className="flex items-center space-x-2 rounded-lg bg-gray-600 px-4 py-2 text-white transition-colors hover:bg-gray-700"
          >
            <ArrowPathIcon className="size-4" />
            <span>Làm mới</span>
          </button>
        </div>
      </div>

      {/* Message */}
      {message.text && (
        <div
          className={`rounded-lg border p-4 ${
            message.type === 'success'
              ? 'border-green-200 bg-green-50 text-green-800'
              : 'border-red-200 bg-red-50 text-red-800'
          }`}
        >
          <div className="flex items-center space-x-2">
            {message.type === 'success' ? (
              <CheckCircleIcon className="size-5" />
            ) : (
              <ExclamationTriangleIcon className="size-5" />
            )}
            <span>{message.text}</span>
          </div>
        </div>
      )}

      {/* Current Performance */}
      {analytics && (
        <div className="rounded-lg border bg-white p-6 shadow-sm">
          <h3 className="mb-4 flex items-center space-x-2 text-lg font-medium">
            <ChartBarIcon className="size-5 text-gray-600" />
            <span>Hiệu suất hiện tại (30 ngày)</span>
          </h3>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <div className="rounded-lg bg-blue-50 p-4 text-center">
              <p className="text-2xl font-bold text-blue-600">
                {(analytics.summary?.overall_accuracy * 100).toFixed(1)}%
              </p>
              <p className="text-sm text-gray-600">Độ chính xác</p>
            </div>

            <div className="rounded-lg bg-green-50 p-4 text-center">
              <p className="text-2xl font-bold text-green-600">
                {analytics.accuracy_metrics?.precision?.toFixed(3) || '0.000'}
              </p>
              <p className="text-sm text-gray-600">Precision</p>
            </div>

            <div className="rounded-lg bg-purple-50 p-4 text-center">
              <p className="text-2xl font-bold text-purple-600">
                {analytics.accuracy_metrics?.recall?.toFixed(3) || '0.000'}
              </p>
              <p className="text-sm text-gray-600">Recall</p>
            </div>

            <div className="rounded-lg bg-yellow-50 p-4 text-center">
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
          className={`rounded-lg border p-4 ${
            recommendation.type === 'success'
              ? 'border-green-200 bg-green-50'
              : 'border-yellow-200 bg-yellow-50'
          }`}
        >
          <div className="flex items-start space-x-3">
            <BoltIcon
              className={`mt-0.5 size-5 ${
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
                className={`mt-1 text-sm ${
                  recommendation.type === 'success' ? 'text-green-700' : 'text-yellow-700'
                }`}
              >
                {recommendation.message}
              </p>
              {recommendation.suggestion && (
                <button
                  onClick={() => applySuggestion(recommendation.suggestion)}
                  className={`mt-2 rounded px-3 py-1 text-sm ${
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
      <div className="rounded-lg border bg-white p-6 shadow-sm">
        <div className="mb-6 flex items-center space-x-3">
          <AdjustmentsHorizontalIcon className="size-6 text-gray-600" />
          <h3 className="text-lg font-medium">Cấu hình Thresholds</h3>
        </div>

        <div className="space-y-6">
          {/* Auto Mark Threshold */}
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              Auto-mark Threshold
              <span className="ml-2 text-gray-500">(≥ {thresholds.autoMarkThreshold})</span>
            </label>
            <div className="flex items-center space-x-4">
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={thresholds.autoMarkThreshold}
                onChange={e => handleThresholdChange('autoMarkThreshold', e.target.value)}
                className="slider h-2 flex-1 cursor-pointer appearance-none rounded-lg bg-gray-200"
              />
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={thresholds.autoMarkThreshold}
                onChange={e => handleThresholdChange('autoMarkThreshold', e.target.value)}
                className="w-20 rounded border border-gray-300 px-2 py-1 text-sm"
              />
            </div>
            <p className="mt-1 text-xs text-gray-600">
              Reviews với confidence ≥ {thresholds.autoMarkThreshold} sẽ được đánh dấu tự động
            </p>
          </div>

          {/* Flag for Review Threshold */}
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              Flag for Review Threshold
              <span className="ml-2 text-gray-500">
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
                className="slider h-2 flex-1 cursor-pointer appearance-none rounded-lg bg-gray-200"
              />
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={thresholds.flagForReviewThreshold}
                onChange={e => handleThresholdChange('flagForReviewThreshold', e.target.value)}
                className="w-20 rounded border border-gray-300 px-2 py-1 text-sm"
              />
            </div>
            <p className="mt-1 text-xs text-gray-600">Reviews sẽ được gắn cờ để user xác nhận</p>
          </div>

          {/* Suggest Warning Threshold */}
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              Suggest Warning Threshold
              <span className="ml-2 text-gray-500">
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
                className="slider h-2 flex-1 cursor-pointer appearance-none rounded-lg bg-gray-200"
              />
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={thresholds.suggestWarningThreshold}
                onChange={e => handleThresholdChange('suggestWarningThreshold', e.target.value)}
                className="w-20 rounded border border-gray-300 px-2 py-1 text-sm"
              />
            </div>
            <p className="mt-1 text-xs text-gray-600">Reviews sẽ được gửi vào queue kiểm duyệt</p>
          </div>
        </div>

        {/* Visual Threshold Representation */}
        <div className="mt-6 rounded-lg bg-gray-50 p-4">
          <h4 className="mb-3 text-sm font-medium text-gray-700">Minh họa Thresholds</h4>
          <div className="relative h-8 rounded bg-gradient-to-r from-green-200 via-orange-200 via-yellow-200 to-red-200">
            {/* Threshold markers */}
            <div
              className="absolute inset-y-0 w-0.5 bg-red-600"
              style={{ left: `${thresholds.autoMarkThreshold * 100}%` }}
            >
              <div className="absolute -left-8 -top-6 text-xs font-medium text-red-600">
                Auto: {thresholds.autoMarkThreshold}
              </div>
            </div>
            <div
              className="absolute inset-y-0 w-0.5 bg-orange-600"
              style={{ left: `${thresholds.flagForReviewThreshold * 100}%` }}
            >
              <div className="absolute -bottom-6 -left-8 text-xs font-medium text-orange-600">
                Flag: {thresholds.flagForReviewThreshold}
              </div>
            </div>
            <div
              className="absolute inset-y-0 w-0.5 bg-yellow-600"
              style={{ left: `${thresholds.suggestWarningThreshold * 100}%` }}
            >
              <div className="absolute -left-10 -top-6 text-xs font-medium text-yellow-600">
                Warning: {thresholds.suggestWarningThreshold}
              </div>
            </div>
          </div>
          <div className="mt-8 flex justify-between text-xs text-gray-600">
            <span>0.0 (No Action)</span>
            <span>1.0 (Maximum Confidence)</span>
          </div>
        </div>
      </div>

      {/* Learning System Configuration */}
      <div className="rounded-lg border bg-white p-6 shadow-sm">
        <div className="mb-6 flex items-center space-x-3">
          <AcademicCapIcon className="size-6 text-gray-600" />
          <h3 className="text-lg font-medium">Hệ thống học (Learning System)</h3>
        </div>

        <div className="flex items-center justify-between rounded-lg bg-gray-50 p-4">
          <div>
            <p className="font-medium text-gray-900">Tự động điều chỉnh thresholds</p>
            <p className="text-sm text-gray-600">
              Hệ thống sẽ học từ feedback của moderator để tự động cải thiện độ chính xác
            </p>
          </div>

          <label className="relative inline-flex cursor-pointer items-center">
            <input
              type="checkbox"
              checked={learningEnabled}
              onChange={handleToggleLearning}
              disabled={saving}
              className="peer sr-only"
            />
            <div className="peer h-6 w-11 rounded-full bg-gray-200 after:absolute after:left-[2px] after:top-[2px] after:size-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-blue-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300"></div>
          </label>
        </div>

        {config && (
          <div className="mt-4 grid grid-cols-1 gap-4 text-sm md:grid-cols-3">
            <div className="rounded bg-blue-50 p-3">
              <p className="font-medium text-blue-900">Learning Rate</p>
              <p className="text-blue-700">{config.learning_rate}</p>
            </div>
            <div className="rounded bg-green-50 p-3">
              <p className="font-medium text-green-900">Min Feedback Count</p>
              <p className="text-green-700">{config.min_feedback_count}</p>
            </div>
            <div className="rounded bg-purple-50 p-3">
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
          className="flex flex-1 items-center justify-center space-x-2 rounded-lg bg-blue-600 px-6 py-3 text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {saving ? (
            <div className="size-4 animate-spin rounded-full border-b-2 border-white"></div>
          ) : (
            <ShieldCheckIcon className="size-5" />
          )}
          <span>{saving ? 'Đang lưu...' : 'Lưu cấu hình'}</span>
        </button>

        <button
          onClick={resetThresholds}
          disabled={!hasChanges || saving}
          className="rounded-lg bg-gray-600 px-6 py-3 text-white transition-colors hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Reset
        </button>
      </div>

      {/* Information Panel */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
        <div className="flex items-start space-x-3">
          <InformationCircleIcon className="mt-0.5 size-5 text-blue-600" />
          <div className="text-sm text-blue-800">
            <p className="mb-2 font-medium">Hướng dẫn sử dụng:</p>
            <ul className="list-inside list-disc space-y-1">
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
