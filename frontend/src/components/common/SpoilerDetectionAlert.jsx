import React from 'react';
import { AlertTriangle, CheckCircle, XCircle, Info, Search, Zap, Brain } from 'lucide-react';

const SpoilerDetectionAlert = ({
  detectionResult,
  isAnalyzing = false,
  onMarkAsSpoiler,
  onDismiss,
  onReviewContent,
  className = '',
}) => {
  if (!detectionResult && !isAnalyzing) {
    return null;
  }

  // Show simple loading state
  if (isAnalyzing) {
    return (
      <div className={`bg-blue-50 border border-blue-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
          <div>
            <p className="text-sm font-medium text-blue-800">Đang phân tích nội dung...</p>
            <p className="text-xs text-blue-600">Kiểm tra spoiler trong nội dung của bạn</p>
          </div>
        </div>
      </div>
    );
  }

  // Use detection result
  const { confidence, is_spoiler, explanation, spoiler_indicators } = detectionResult || {};

  // Determine alert type based on confidence
  const getAlertConfig = () => {
    if (confidence > 0.8) {
      return {
        type: 'error',
        icon: AlertTriangle,
        bgColor: 'bg-red-50',
        borderColor: 'border-red-200',
        textColor: 'text-red-800',
        title: 'Cảnh báo Spoiler Cao',
        actionText: 'Đánh dấu là Spoiler',
        actionColor: 'bg-red-600 hover:bg-red-700',
      };
    } else if (confidence > 0.6) {
      return {
        type: 'warning',
        icon: AlertTriangle,
        bgColor: 'bg-orange-50',
        borderColor: 'border-orange-200',
        textColor: 'text-orange-800',
        title: 'Có thể chứa Spoiler',
        actionText: 'Đánh dấu là Spoiler',
        actionColor: 'bg-orange-600 hover:bg-orange-700',
      };
    } else if (confidence > 0.4) {
      return {
        type: 'info',
        icon: Info,
        bgColor: 'bg-yellow-50',
        borderColor: 'border-yellow-200',
        textColor: 'text-yellow-800',
        title: 'Kiểm tra Nội dung',
        actionText: 'Xem lại nội dung',
        actionColor: 'bg-yellow-600 hover:bg-yellow-700',
      };
    } else {
      return {
        type: 'success',
        icon: CheckCircle,
        bgColor: 'bg-green-50',
        borderColor: 'border-green-200',
        textColor: 'text-green-800',
        title: 'Không có Spoiler',
        actionText: null,
        actionColor: null,
      };
    }
  };

  const config = getAlertConfig();
  const IconComponent = config.icon;

  return (
    <div className={`${config.bgColor} border ${config.borderColor} rounded-lg p-4 ${className}`}>
      <div className="flex items-start space-x-3">
        <IconComponent className={`h-5 w-5 ${config.textColor} flex-shrink-0 mt-0.5`} />

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h4 className={`text-sm font-medium ${config.textColor}`}>{config.title}</h4>

            <div className="flex items-center space-x-2">
              {/* Confidence indicator */}
              <div className="flex items-center space-x-1">
                <div className="w-16 bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      confidence > 0.8
                        ? 'bg-red-500'
                        : confidence > 0.6
                          ? 'bg-orange-500'
                          : confidence > 0.4
                            ? 'bg-yellow-500'
                            : 'bg-green-500'
                    }`}
                    style={{ width: `${confidence * 100}%` }}
                  />
                </div>
                <span className="text-xs text-gray-600">{Math.round(confidence * 100)}%</span>
              </div>

              {/* Dismiss button */}
              {onDismiss && (
                <button
                  onClick={onDismiss}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <XCircle className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>

          <p className={`text-sm ${config.textColor} mt-1`}>{explanation}</p>

          {/* Show detected indicators if any */}
          {spoiler_indicators && spoiler_indicators.length > 0 && (
            <div className="mt-2">
              <p className="text-xs text-gray-600 mb-1">Dấu hiệu được phát hiện:</p>
              <div className="flex flex-wrap gap-1">
                {spoiler_indicators.slice(0, 3).map((indicator, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-700"
                  >
                    {indicator}
                  </span>
                ))}
                {spoiler_indicators.length > 3 && (
                  <span className="text-xs text-gray-500">
                    +{spoiler_indicators.length - 3} khác
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex items-center space-x-2 mt-3">
            {config.actionText && confidence > 0.6 && onMarkAsSpoiler && (
              <button
                onClick={onMarkAsSpoiler}
                className={`px-3 py-1.5 text-xs font-medium text-white rounded-md transition-colors ${config.actionColor}`}
              >
                {config.actionText}
              </button>
            )}

            {confidence > 0.4 && confidence <= 0.6 && onReviewContent && (
              <button
                onClick={onReviewContent}
                className="px-3 py-1.5 text-xs font-medium text-yellow-700 bg-yellow-100 hover:bg-yellow-200 rounded-md transition-colors"
              >
                {config.actionText}
              </button>
            )}

            {confidence <= 0.4 && (
              <span className="text-xs text-green-600 font-medium">✓ Nội dung an toàn</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SpoilerDetectionAlert;
