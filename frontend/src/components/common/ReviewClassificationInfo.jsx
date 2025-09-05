import {
  CheckCircle,
  AlertTriangle,
  Clock,
  Shield,
  Flag,
  UserCheck,
  EyeOff,
  Zap,
} from 'lucide-react';

const ReviewClassificationInfo = ({
  classification,
  confidence,
  isAnalyzing = false,
  className = '',
}) => {
  if (!classification || isAnalyzing) {
    return null;
  }

  const getActionConfig = () => {
    switch (classification.action) {
      case 'auto_approve':
        return {
          icon: CheckCircle,
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          title: 'Tự động phê duyệt',
          description: classification.message,
        };

      case 'user_confirmation':
        return {
          icon: UserCheck,
          color: 'text-blue-600',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          title: 'Cần xác nhận',
          description: classification.message,
        };

      case 'moderation_required':
        return {
          icon: Shield,
          color: 'text-orange-600',
          bgColor: 'bg-orange-50',
          borderColor: 'border-orange-200',
          title: 'Cần kiểm tra thủ công',
          description: classification.message,
        };

      case 'auto_approve_with_flag':
        return {
          icon: Flag,
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          title: 'Phê duyệt với cảnh báo',
          description: classification.message,
        };

      default:
        return {
          icon: Clock,
          color: 'text-gray-600',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          title: 'Đang xử lý',
          description: 'Đang phân tích review...',
        };
    }
  };

  const getPriorityConfig = () => {
    if (!classification.priority) return null;

    switch (classification.priority) {
      case 'high':
        return {
          icon: Zap,
          color: 'text-red-600',
          label: 'Ưu tiên cao',
        };
      case 'medium':
        return {
          icon: AlertTriangle,
          color: 'text-orange-600',
          label: 'Ưu tiên trung bình',
        };
      case 'low':
        return {
          icon: Clock,
          color: 'text-yellow-600',
          label: 'Ưu tiên thấp',
        };
      default:
        return null;
    }
  };

  const config = getActionConfig();
  const priorityConfig = getPriorityConfig();
  const IconComponent = config.icon;

  return (
    <div className={`${config.bgColor} border ${config.borderColor} rounded-lg p-4 ${className}`}>
      <div className="flex items-start space-x-3">
        <IconComponent className={`size-5 ${config.color} mt-0.5 shrink-0`} />

        <div className="min-w-0 flex-1">
          <div className="mb-2 flex items-center justify-between">
            <h4 className={`text-sm font-medium ${config.color}`}>{config.title}</h4>

            {/* Confidence indicator */}
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
              <span className="text-xs text-gray-600">{Math.round(confidence * 100)}%</span>
            </div>
          </div>

          <p className="mb-3 text-sm text-gray-700">{config.description}</p>

          {/* Classification details */}
          <div className="space-y-2">
            {/* Reason */}
            <div className="flex items-center space-x-2">
              <span className="text-xs font-medium text-gray-600">Lý do:</span>
              <span className="text-xs capitalize text-gray-800">
                {classification.reason?.replace(/_/g, ' ')}
              </span>
            </div>

            {/* Priority */}
            {priorityConfig && (
              <div className="flex items-center space-x-2">
                <span className="text-xs font-medium text-gray-600">Ưu tiên:</span>
                <div className="flex items-center space-x-1">
                  <priorityConfig.icon className={`size-3 ${priorityConfig.color}`} />
                  <span className={`text-xs ${priorityConfig.color} font-medium`}>
                    {priorityConfig.label}
                  </span>
                </div>
              </div>
            )}

            {/* Auto actions */}
            {classification.autoMarkAsSpoiler && (
              <div className="flex items-center space-x-2">
                <EyeOff className="size-3 text-orange-600" />
                <span className="text-xs font-medium text-orange-600">
                  Tự động đánh dấu là spoiler
                </span>
              </div>
            )}

            {classification.flagForReview && (
              <div className="flex items-center space-x-2">
                <Flag className="size-3 text-yellow-600" />
                <span className="text-xs font-medium text-yellow-600">
                  Được đánh dấu để kiểm tra sau
                </span>
              </div>
            )}

            {/* Suggested action */}
            {classification.suggestedAction && (
              <div className="flex items-center space-x-2">
                <UserCheck className="size-3 text-blue-600" />
                <span className="text-xs font-medium text-blue-600">
                  Gợi ý:{' '}
                  {classification.suggestedAction === 'mark_as_spoiler'
                    ? 'Đánh dấu là spoiler'
                    : classification.suggestedAction}
                </span>
              </div>
            )}
          </div>

          {/* Action buttons based on classification */}
          <div className="mt-4 flex items-center space-x-2">
            {classification.action === 'user_confirmation' && (
              <>
                <button className="rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-blue-700">
                  Xác nhận là spoiler
                </button>
                <button className="rounded-md bg-gray-200 px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-300">
                  Không phải spoiler
                </button>
              </>
            )}

            {classification.action === 'moderation_required' && (
              <div className="flex items-center space-x-2 text-xs text-orange-600">
                <Shield className="size-3" />
                <span>Review sẽ được gửi đến Moderator để kiểm tra</span>
              </div>
            )}

            {classification.action === 'auto_approve' && (
              <div className="flex items-center space-x-2 text-xs text-green-600">
                <CheckCircle className="size-3" />
                <span>Review sẽ được tự động phê duyệt</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReviewClassificationInfo;
