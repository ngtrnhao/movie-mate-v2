import { TrendingUp, AlertTriangle, CheckCircle, Clock, Zap } from 'lucide-react';

const SpoilerAnalysisStats = ({
  analysisProgress = 0,
  intermediateResults = null,
  detectionResult = null,
  isAnalyzing = false,
  className = '',
}) => {
  if (!isAnalyzing && !intermediateResults && !detectionResult) {
    return null;
  }

  const getCurrentResult = () => {
    return detectionResult || intermediateResults;
  };

  const result = getCurrentResult();
  const confidence = result?.confidence || 0;
  const detectedPatterns = result?.detected_patterns || [];
  const spoilerIndicators = result?.spoiler_indicators || [];

  const getAnalysisStage = () => {
    if (analysisProgress < 30) {
      return {
        stage: 'keyword',
        title: 'Phân tích từ khóa',
        description: 'Tìm kiếm các từ khóa spoiler cơ bản',
        icon: Zap,
        color: 'text-blue-500',
        bgColor: 'bg-blue-100',
      };
    }
    if (analysisProgress < 60) {
      return {
        stage: 'pattern',
        title: 'Phân tích mẫu câu',
        description: 'Kiểm tra các mẫu câu có thể chứa spoiler',
        icon: TrendingUp,
        color: 'text-orange-500',
        bgColor: 'bg-orange-100',
      };
    }
    if (analysisProgress < 85) {
      return {
        stage: 'context',
        title: 'Phân tích ngữ cảnh',
        description: 'Đánh giá ngữ cảnh và ý nghĩa',
        icon: AlertTriangle,
        color: 'text-yellow-500',
        bgColor: 'bg-yellow-100',
      };
    }
    return {
      stage: 'complete',
      title: 'Hoàn thành phân tích',
      description: 'Kết quả cuối cùng đã sẵn sàng',
      icon: CheckCircle,
      color: 'text-green-500',
      bgColor: 'bg-green-100',
    };
  };

  const stage = getAnalysisStage();
  const IconComponent = stage.icon;

  return (
    <div className={`rounded-lg border border-gray-200 bg-gray-50 p-4 ${className}`}>
      <div className="space-y-4">
        {/* Analysis Progress */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`rounded-full p-2 ${stage.bgColor}`}>
              <IconComponent className={`size-4 ${stage.color}`} />
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-900">{stage.title}</h4>
              <p className="text-xs text-gray-600">{stage.description}</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm font-medium text-gray-900">{analysisProgress}%</div>
            <div className="text-xs text-gray-500">Hoàn thành</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="h-2 w-full rounded-full bg-gray-200">
          <div
            className={`h-2 rounded-full transition-all duration-500 ease-out ${
              analysisProgress < 30
                ? 'bg-blue-500'
                : analysisProgress < 60
                  ? 'bg-orange-500'
                  : analysisProgress < 85
                    ? 'bg-yellow-500'
                    : 'bg-green-500'
            }`}
            style={{ width: `${analysisProgress}%` }}
          />
        </div>

        {/* Current Results */}
        {result && (
          <div className="space-y-3">
            {/* Confidence Score */}
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Độ tin cậy:</span>
              <div className="flex items-center space-x-2">
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
                <span className="text-sm font-medium text-gray-900">
                  {Math.round(confidence * 100)}%
                </span>
              </div>
            </div>

            {/* Detected Indicators */}
            {spoilerIndicators.length > 0 && (
              <div>
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Dấu hiệu phát hiện:</span>
                  <span className="text-xs text-gray-500">{spoilerIndicators.length} dấu hiệu</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {spoilerIndicators.slice(0, 5).map((indicator, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center rounded-full bg-red-100 px-2 py-1 text-xs text-red-700"
                    >
                      {indicator}
                    </span>
                  ))}
                  {spoilerIndicators.length > 5 && (
                    <span className="text-xs text-gray-500">
                      +{spoilerIndicators.length - 5} khác
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Analysis Status */}
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center space-x-1 text-gray-500">
                <Clock className="size-3" />
                <span>
                  {intermediateResults && !detectionResult
                    ? 'Kết quả tạm thời'
                    : 'Phân tích hoàn tất'}
                </span>
              </div>
              {result.is_spoiler && (
                <div className="flex items-center space-x-1 text-red-600">
                  <AlertTriangle className="size-3" />
                  <span>Nội dung có spoiler</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Analysis Tips */}
        {isAnalyzing && (
          <div className="rounded-md border border-blue-200 bg-blue-50 p-3">
            <div className="flex items-start space-x-2">
              <div className="shrink-0">
                <div className="size-2 animate-pulse rounded-full bg-blue-500"></div>
              </div>
              <div className="text-xs text-blue-700">
                <p className="mb-1 font-medium">Mẹo phân tích:</p>
                <ul className="space-y-1">
                  <li>• Hệ thống đang kiểm tra từ khóa, mẫu câu và ngữ cảnh</li>
                  <li>• Kết quả sẽ được cập nhật theo thời gian thực</li>
                  <li>• Bạn có thể tiếp tục viết trong khi phân tích</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SpoilerAnalysisStats;
