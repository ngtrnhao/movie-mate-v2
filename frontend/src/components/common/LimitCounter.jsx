import { formatLimit, getRemainingLimit, isUnlimited } from '../../utils/userPermissions';

const LimitCounter = ({
  current = 0,
  max = 0,
  label = '',
  type = 'inline', // 'inline', 'badge', 'progress'
  size = 'sm',
  showProgress = false,
  className = '',
}) => {
  const remaining = getRemainingLimit(current, max);
  const isUnlimitedPlan = isUnlimited(max);
  const percentage = !isUnlimitedPlan ? (current / max) * 100 : 100;
  const isNearLimit = !isUnlimitedPlan && remaining <= max * 0.1; // 10% warning
  const isOverLimit = !isUnlimitedPlan && remaining <= 0;

  const sizeClasses = {
    xs: 'text-xs px-1.5 py-0.5',
    sm: 'text-sm px-2 py-1',
    md: 'text-base px-3 py-1.5',
    lg: 'text-lg px-4 py-2',
  };

  const getColorClasses = () => {
    if (isOverLimit) return 'bg-red-100 text-red-800 border-red-200';
    if (isNearLimit) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    if (isUnlimitedPlan) return 'bg-purple-100 text-purple-800 border-purple-200';
    return 'bg-green-100 text-green-800 border-green-200';
  };

  const getProgressColor = () => {
    if (isOverLimit) return 'bg-red-500';
    if (isNearLimit) return 'bg-yellow-500';
    if (isUnlimitedPlan) return 'bg-purple-500';
    return 'bg-green-500';
  };

  if (type === 'badge') {
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-full border font-medium ${getColorClasses()} ${sizeClasses[size]} ${className}`}
      >
        {label && <span>{label}:</span>}
        <span className="font-bold">{formatLimit(current, max)}</span>
        {!isUnlimitedPlan && remaining > 0 && (
          <span className="text-xs opacity-75">({remaining} left)</span>
        )}
      </span>
    );
  }

  if (type === 'progress') {
    return (
      <div className={`space-y-2 ${className}`}>
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-300">{label}</span>
          <span
            className={`text-sm font-bold ${isOverLimit ? 'text-red-400' : isNearLimit ? 'text-yellow-400' : isUnlimitedPlan ? 'text-purple-400' : 'text-green-400'}`}
          >
            {formatLimit(current, max)}
          </span>
        </div>
        {!isUnlimitedPlan && (
          <div className="h-2 w-full rounded-full bg-gray-700">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${getProgressColor()}`}
              style={{ width: `${Math.min(percentage, 100)}%` }}
            />
          </div>
        )}
        {isUnlimitedPlan && (
          <div className="h-2 w-full rounded-full bg-gradient-to-r from-purple-500 to-purple-600">
            <div className="h-2 animate-pulse rounded-full bg-gradient-to-r from-purple-400 to-purple-500" />
          </div>
        )}
      </div>
    );
  }

  // Default inline type
  return (
    <div className={`inline-flex items-center gap-2 ${className}`}>
      {label && <span className="text-gray-300">{label}:</span>}
      <span
        className={`font-semibold ${isOverLimit ? 'text-red-400' : isNearLimit ? 'text-yellow-400' : isUnlimitedPlan ? 'text-purple-400' : 'text-green-400'}`}
      >
        {formatLimit(current, max)}
      </span>
      {showProgress && !isUnlimitedPlan && (
        <div className="h-1.5 w-16 rounded-full bg-gray-700">
          <div
            className={`h-1.5 rounded-full transition-all duration-300 ${getProgressColor()}`}
            style={{ width: `${Math.min(percentage, 100)}%` }}
          />
        </div>
      )}
    </div>
  );
};

export default LimitCounter;
