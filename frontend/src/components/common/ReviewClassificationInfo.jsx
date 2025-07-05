import React from 'react';
import {
  CheckCircle,
  AlertTriangle,
  Clock,
  Shield,
  Flag,
  UserCheck,
  Eye,
  EyeOff,
  Zap,
  Star,
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
        <IconComponent className={`h-5 w-5 ${config.color} flex-shrink-0 mt-0.5`} />

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-2">
            <h4 className={`text-sm font-medium ${config.color}`}>{config.title}</h4>

            {/* Confidence indicator */}
            <div className="flex items-center space-x-2">
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
          </div>

          <p className="text-sm text-gray-700 mb-3">{config.description}</p>

          {/* Classification details */}
          <div className="space-y-2">
            {/* Reason */}
            <div className="flex items-center space-x-2">
              <span className="text-xs font-medium text-gray-600">Lý do:</span>
              <span className="text-xs text-gray-800 capitalize">
                {classification.reason?.replace(/_/g, ' ')}
              </span>
            </div>

            {/* Priority */}
            {priorityConfig && (
              <div className="flex items-center space-x-2">
                <span className="text-xs font-medium text-gray-600">Ưu tiên:</span>
                <div className="flex items-center space-x-1">
                  <priorityConfig.icon className={`h-3 w-3 ${priorityConfig.color}`} />
                  <span className={`text-xs ${priorityConfig.color} font-medium`}>
                    {priorityConfig.label}
                  </span>
                </div>
              </div>
            )}

            {/* Auto actions */}
            {classification.autoMarkAsSpoiler && (
              <div className="flex items-center space-x-2">
                <EyeOff className="h-3 w-3 text-orange-600" />
                <span className="text-xs text-orange-600 font-medium">
                  Tự động đánh dấu là spoiler
                </span>
              </div>
            )}

            {classification.flagForReview && (
              <div className="flex items-center space-x-2">
                <Flag className="h-3 w-3 text-yellow-600" />
                <span className="text-xs text-yellow-600 font-medium">
                  Được đánh dấu để kiểm tra sau
                </span>
              </div>
            )}

            {/* Suggested action */}
            {classification.suggestedAction && (
              <div className="flex items-center space-x-2">
                <UserCheck className="h-3 w-3 text-blue-600" />
                <span className="text-xs text-blue-600 font-medium">
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
                <button className="px-3 py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors">
                  Xác nhận là spoiler
                </button>
                <button className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-md transition-colors">
                  Không phải spoiler
                </button>
              </>
            )}

            {classification.action === 'moderation_required' && (
              <div className="flex items-center space-x-2 text-xs text-orange-600">
                <Shield className="h-3 w-3" />
                <span>Review sẽ được gửi đến Moderator để kiểm tra</span>
              </div>
            )}

            {classification.action === 'auto_approve' && (
              <div className="flex items-center space-x-2 text-xs text-green-600">
                <CheckCircle className="h-3 w-3" />
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
