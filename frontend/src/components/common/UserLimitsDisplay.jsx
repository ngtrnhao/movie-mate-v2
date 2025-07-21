import { useUserLimits } from '../../hooks/useUserLimits';
import { Heart, List, MessageSquare, Zap } from 'lucide-react';

const UserLimitsDisplay = ({ showDetails = false, className = '' }) => {
  const { usageStats, loading, userLimits, getLimitDisplay, userType } = useUserLimits();

  if (loading) {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="flex items-center gap-4">
          <div className="h-4 w-20 rounded bg-gray-200"></div>
          <div className="h-4 w-16 rounded bg-gray-200"></div>
          <div className="h-4 w-24 rounded bg-gray-200"></div>
        </div>
      </div>
    );
  }

  if (!usageStats) {
    return null;
  }

  const limits = [
    {
      key: 'favorites',
      icon: Heart,
      label: 'Favorites',
      current: usageStats.favorites.current,
      max: usageStats.favorites.max,
      isUnlimited: usageStats.favorites.is_unlimited,
      color: 'text-pink-500',
    },
    {
      key: 'lists',
      icon: List,
      label: 'Lists',
      current: usageStats.lists.current,
      max: usageStats.lists.max,
      isUnlimited: usageStats.lists.is_unlimited,
      color: 'text-blue-500',
    },
    {
      key: 'reviews_today',
      icon: MessageSquare,
      label: 'Reviews Today',
      current: usageStats.reviews_today.current,
      max: usageStats.reviews_today.max,
      isUnlimited: usageStats.reviews_today.is_unlimited,
      color: 'text-green-500',
    },
    {
      key: 'moods',
      icon: Zap,
      label: 'Moods',
      current: usageStats.moods.current,
      max: usageStats.moods.max,
      isUnlimited: usageStats.moods.is_unlimited,
      color: 'text-purple-500',
    },
  ];

  return (
    <div className={`space-y-2 ${className}`}>
      {showDetails ? (
        // Detailed view
        <div className="grid grid-cols-2 gap-4">
          {limits.map(limit => {
            const Icon = limit.icon;
            const percentage = limit.isUnlimited ? 100 : (limit.current / limit.max) * 100;
            const isNearLimit = !limit.isUnlimited && percentage >= 80;
            const isAtLimit = !limit.isUnlimited && percentage >= 100;

            return (
              <div
                key={limit.key}
                className={`rounded-lg border p-3 ${
                  isAtLimit
                    ? 'border-red-200 bg-red-50'
                    : isNearLimit
                      ? 'border-yellow-200 bg-yellow-50'
                      : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="mb-2 flex items-center gap-2">
                  <Icon size={16} className={limit.color} />
                  <span className="text-sm font-medium text-gray-700">{limit.label}</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-lg font-semibold text-gray-900">
                    {limit.isUnlimited ? '∞' : limit.current}
                  </span>
                  {!limit.isUnlimited && (
                    <span className="text-sm text-gray-500">/ {limit.max}</span>
                  )}
                </div>

                {!limit.isUnlimited && (
                  <div className="mt-2">
                    <div className="h-2 w-full rounded-full bg-gray-200">
                      <div
                        className={`h-2 rounded-full transition-all duration-300 ${
                          isAtLimit ? 'bg-red-500' : isNearLimit ? 'bg-yellow-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${Math.min(percentage, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                )}

                {isAtLimit && <p className="mt-1 text-xs text-red-600">Limit reached</p>}
                {isNearLimit && !isAtLimit && (
                  <p className="mt-1 text-xs text-yellow-600">Near limit</p>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        // Compact view
        <div className="flex items-center gap-4 text-sm text-gray-600">
          {limits.map(limit => {
            const Icon = limit.icon;
            const isAtLimit = !limit.isUnlimited && limit.current >= limit.max;

            return (
              <div
                key={limit.key}
                className={`flex items-center gap-1 ${isAtLimit ? 'text-red-500' : limit.color}`}
                title={`${limit.label}: ${getLimitDisplay(limit.key)}`}
              >
                <Icon size={14} />
                <span className="font-medium">{limit.isUnlimited ? '∞' : limit.current}</span>
                {!limit.isUnlimited && <span className="text-gray-400">/{limit.max}</span>}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default UserLimitsDisplay;
