import { useSelector } from 'react-redux';
import { useQuery } from '@tanstack/react-query';
import { selectUser } from '../../store/slices/authSlice';
import { getPaymentTransactionAPI } from '../../api/profileService';

const SubscriptionStatus = () => {
  const user = useSelector(selectUser);

  const {
    data: currentSubscription,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['subscription', user?.id],
    queryFn: () => getPaymentTransactionAPI(user.id),
    enabled: !!user?.id, // Chỉ fetch khi user đã đăng nhập
  });

  if (isLoading) {
    return (
      <div className="py-4 text-center">
        <div className="mx-auto size-6 animate-spin rounded-full border-y-2 border-blue-500"></div>
        <p className="mt-2 text-sm text-gray-400">Loading subscription...</p>
      </div>
    );
  }

  if (isError || !currentSubscription?.has_active_subscription) {
    return (
      <div className="rounded-lg bg-gray-800/50 p-4 text-center">
        <h3 className="mb-2 text-lg font-semibold text-gray-300">No Active Subscription</h3>
        <p className="text-sm text-gray-400">Choose a plan to get started</p>
      </div>
    );
  }

  const getStatusColor = () => {
    if (currentSubscription.days_remaining <= 7) return 'text-red-400';
    if (currentSubscription.days_remaining <= 30) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getStatusText = () => {
    if (currentSubscription.days_remaining <= 7) return 'Expiring Soon';
    if (currentSubscription.days_remaining <= 30) return 'Expiring This Month';
    return 'Active';
  };

  return (
    <div className="rounded-lg bg-gray-800/50 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Current Subscription</h3>
        <span className={`text-sm font-medium ${getStatusColor()}`}>{getStatusText()}</span>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">Plan:</span>
          <span className="font-medium capitalize text-white">{currentSubscription.plan}</span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-400">Valid Until:</span>
          <span className="text-white">
            {new Date(currentSubscription.subscription_end_date).toLocaleDateString()}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-400">Days Remaining:</span>
          <span className={`font-medium ${getStatusColor()}`}>
            {currentSubscription.days_remaining} days
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-400">Amount:</span>
          <span className="text-white">${currentSubscription.amount}</span>
        </div>
      </div>

      {/* Action buttons */}
      <div className="mt-4 space-y-2">
        {currentSubscription.can_renew && (
          <div className="rounded bg-blue-900/30 p-2 text-xs text-blue-300">
            ⚠️ Your subscription expires soon. You can renew now.
          </div>
        )}

        {currentSubscription.can_downgrade && (
          <div className="rounded bg-yellow-900/30 p-2 text-xs text-yellow-300">
            ⚠️ You can downgrade your plan within 30 days of expiry.
          </div>
        )}
      </div>
    </div>
  );
};

export default SubscriptionStatus;
