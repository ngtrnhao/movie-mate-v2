import { AlertTriangle, CheckCircle, XCircle, Info } from 'lucide-react';

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
      <div className={`rounded-lg border border-blue-200 bg-blue-50 p-4 ${className}`}>
        <div className="flex items-center space-x-3">
          <div className="size-5 animate-spin rounded-full border-b-2 border-blue-600"></div>
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
        <IconComponent className={`size-5 ${config.textColor} mt-0.5 shrink-0`} />

        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between">
            <h4 className={`text-sm font-medium ${config.textColor}`}>{config.title}</h4>

            <div className="flex items-center space-x-2">
              {/* Confidence indicator */}
              <div className="flex items-center space-x-1">
                <div className="h-2 w-16 rounded-full bg-gray-200">
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
                  className="text-gray-400 transition-colors hover:text-gray-600"
                >
                  <XCircle className="size-4" />
                </button>
              )}
            </div>
          </div>

          <p className={`text-sm ${config.textColor} mt-1`}>{explanation}</p>

          {/* Show detected indicators if any */}
          {spoiler_indicators && spoiler_indicators.length > 0 && (
            <div className="mt-2">
              <p className="mb-1 text-xs text-gray-600">Dấu hiệu được phát hiện:</p>
              <div className="flex flex-wrap gap-1">
                {spoiler_indicators.slice(0, 3).map((indicator, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-700"
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
          <div className="mt-3 flex items-center space-x-2">
            {config.actionText && confidence > 0.6 && onMarkAsSpoiler && (
              <button
                onClick={onMarkAsSpoiler}
                className={`rounded-md px-3 py-1.5 text-xs font-medium text-white transition-colors ${config.actionColor}`}
              >
                {config.actionText}
              </button>
            )}

            {confidence > 0.4 && confidence <= 0.6 && onReviewContent && (
              <button
                onClick={onReviewContent}
                className="rounded-md bg-yellow-100 px-3 py-1.5 text-xs font-medium text-yellow-700 transition-colors hover:bg-yellow-200"
              >
                {config.actionText}
              </button>
            )}

            {confidence <= 0.4 && (
              <span className="text-xs font-medium text-green-600">✓ Nội dung an toàn</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SpoilerDetectionAlert;
