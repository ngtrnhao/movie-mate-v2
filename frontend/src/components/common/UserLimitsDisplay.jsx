import React from 'react';
import { useUserLimits } from '../../hooks/useUserLimits';
import { Heart, List, MessageSquare, Zap } from 'lucide-react';

const UserLimitsDisplay = ({ showDetails = false, className = '' }) => {
  const { usageStats, loading, userLimits, getLimitDisplay, userType } = useUserLimits();

  if (loading) {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="flex items-center gap-4">
          <div className="h-4 bg-gray-200 rounded w-20"></div>
          <div className="h-4 bg-gray-200 rounded w-16"></div>
          <div className="h-4 bg-gray-200 rounded w-24"></div>
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
                className={`p-3 rounded-lg border ${
                  isAtLimit
                    ? 'bg-red-50 border-red-200'
                    : isNearLimit
                      ? 'bg-yellow-50 border-yellow-200'
                      : 'bg-gray-50 border-gray-200'
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
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
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-300 ${
                          isAtLimit ? 'bg-red-500' : isNearLimit ? 'bg-yellow-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${Math.min(percentage, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                )}

                {isAtLimit && <p className="text-xs text-red-600 mt-1">Limit reached</p>}
                {isNearLimit && !isAtLimit && (
                  <p className="text-xs text-yellow-600 mt-1">Near limit</p>
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
