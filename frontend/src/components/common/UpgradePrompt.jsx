import { useNavigate } from 'react-router-dom';
import { getUpgradeTarget, getUpgradeMessage, getUserBadge } from '../../utils/userPermissions';

const UpgradePrompt = ({
  user,
  feature,
  type = 'inline', // 'inline', 'modal', 'tooltip'
  size = 'sm',
  className = '',
}) => {
  const navigate = useNavigate();
  const target = getUpgradeTarget(user);
  const targetBadge = getUserBadge({ user_type: target });
  const message = getUpgradeMessage(user, feature);

  if (!target) return null;

  const handleUpgrade = () => {
    navigate('/pricing');
  };

  const sizeClasses = {
    xs: 'px-2 py-1 text-xs',
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-3 text-base',
    lg: 'px-6 py-4 text-lg',
  };

  if (type === 'inline') {
    return (
      <div className={`rounded-lg border border-gray-600 bg-gray-800/90 p-4 ${className}`}>
        <div className="flex items-center gap-3">
          <div className="shrink-0">
            <svg className="size-8 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="flex-1">
            <h4 className="font-semibold text-white">{feature} requires upgrade</h4>
            <p className="text-gray-300">{message}</p>
          </div>
          <button
            onClick={handleUpgrade}
            className={`rounded-lg bg-gradient-to-r ${targetBadge.gradientFrom} ${targetBadge.gradientTo} font-semibold text-white transition-all hover:scale-105 hover:shadow-lg ${sizeClasses[size]}`}
          >
            Upgrade Now
          </button>
        </div>
      </div>
    );
  }

  if (type === 'button') {
    return (
      <button
        onClick={handleUpgrade}
        className={`inline-flex items-center gap-2 rounded-lg bg-gradient-to-r ${targetBadge.gradientFrom} ${targetBadge.gradientTo} font-semibold text-white transition-all hover:scale-105 hover:shadow-lg ${sizeClasses[size]} ${className}`}
      >
        <svg className="size-4" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M12.395 2.553a1 1 0 00-1.45-.385c-.345.23-.614.558-.822.88-.214.33-.403.713-.57 1.116-.334.804-.614 1.768-.84 2.734a31.365 31.365 0 00-.613 3.58 2.64 2.64 0 01-.945-1.067c-.328-.68-.398-1.534-.398-2.654A1 1 0 005.05 6.05 6.981 6.981 0 003 11a7 7 0 1011.95-4.95c-.592-.591-.98-.985-1.348-1.467-.363-.476-.724-1.063-1.207-2.03zM12.12 15.12A3 3 0 017 13s.879.5 2.5.5c0-1 .5-4 1.25-4.5.5 1 .786 1.293 1.371 1.879A2.99 2.99 0 0113 13a2.99 2.99 0 01-.879 2.121z"
            clipRule="evenodd"
          />
        </svg>
        Upgrade to {targetBadge.label}
      </button>
    );
  }

  if (type === 'overlay') {
    return (
      <div
        className={`absolute inset-0 flex items-center justify-center rounded-lg bg-black/80 backdrop-blur-sm ${className}`}
      >
        <div className="rounded-lg bg-gray-800 p-6 text-center">
          <svg
            className="mx-auto mb-4 size-12 text-yellow-500"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
              clipRule="evenodd"
            />
          </svg>
          <h3 className="mb-2 text-lg font-semibold text-white">{feature}</h3>
          <p className="mb-4 text-gray-300">{message}</p>
          <button
            onClick={handleUpgrade}
            className={`rounded-lg bg-gradient-to-r ${targetBadge.gradientFrom} ${targetBadge.gradientTo} font-semibold text-white transition-all hover:scale-105 hover:shadow-lg ${sizeClasses[size]}`}
          >
            Upgrade Now
          </button>
        </div>
      </div>
    );
  }

  return null;
};

export default UpgradePrompt;
