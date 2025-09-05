import { Shield, CheckCircle } from 'lucide-react';

const ModerationNotification = ({ classification, onDismiss, className = '' }) => {
  if (!classification || classification.action !== 'moderation_required') {
    return null;
  }

  const getNotificationConfig = () => {
    const { priority = 'medium', reason } = classification;

    if (priority === 'high') {
      return {
        icon: Shield,
        bgColor: 'bg-orange-50',
        borderColor: 'border-orange-200',
        textColor: 'text-orange-800',
        title: 'Review đã được gửi để kiểm duyệt',
        message: 'Review của bạn sẽ được kiểm tra bởi đội ngũ Moderator.',
      };
    }

    return {
      icon: CheckCircle,
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      textColor: 'text-blue-800',
      title: 'Review đã được gửi',
      message: 'Review của bạn sẽ được kiểm tra trong thời gian sớm nhất.',
    };
  };

  const config = getNotificationConfig();
  const IconComponent = config.icon;

  return (
    <div className={`${config.bgColor} border ${config.borderColor} rounded-lg p-3 ${className}`}>
      <div className="flex items-center space-x-2">
        <IconComponent className={`size-4 ${config.textColor} shrink-0`} />
        <div className="min-w-0 flex-1">
          <p className={`text-sm font-medium ${config.textColor}`}>{config.title}</p>
          <p className={`text-xs ${config.textColor} opacity-80`}>{config.message}</p>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className={`text-xs ${config.textColor} opacity-60 transition-opacity hover:opacity-100`}
          >
            Đóng
          </button>
        )}
      </div>
    </div>
  );
};

export default ModerationNotification;
