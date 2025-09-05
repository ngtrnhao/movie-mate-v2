import { useSelector } from 'react-redux';
import { useQuery } from '@tanstack/react-query';
import { selectUser } from '../../store/slices/authSlice';
import { getPaymentTransactionAPI } from '../../api/profileService';
import { useTranslation } from 'react-i18next';

const SubscriptionStatus = () => {
  const user = useSelector(selectUser);
  const { t } = useTranslation('checkout');

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
        <p className="mt-2 text-sm text-gray-400">{t('subscriptionStatus.loading')}</p>
      </div>
    );
  }

  if (isError || !currentSubscription?.has_active_subscription) {
    return (
      <div className="rounded-lg bg-gray-800/50 p-4 text-center">
        <h3 className="mb-2 text-lg font-semibold text-gray-300">
          {t('subscriptionStatus.noActive')}
        </h3>
        <p className="text-sm text-gray-400">{t('subscriptionStatus.choosePlan')}</p>
      </div>
    );
  }

  const getStatusColor = () => {
    if (currentSubscription.days_remaining <= 7) return 'text-red-400';
    if (currentSubscription.days_remaining <= 30) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getStatusText = () => {
    if (currentSubscription.days_remaining <= 7) return t('subscriptionStatus.expiringSoon');
    if (currentSubscription.days_remaining <= 30) return t('subscriptionStatus.expiringMonth');
    return t('subscriptionStatus.active');
  };

  return (
    <div className="rounded-lg bg-gray-800/50 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">{t('subscriptionStatus.current')}</h3>
        <span className={`text-sm font-medium ${getStatusColor()}`}>{getStatusText()}</span>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">{t('subscriptionStatus.plan')}</span>
          <span className="font-medium capitalize text-white">{currentSubscription.plan}</span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-400">{t('subscriptionStatus.validUntil')}</span>
          <span className="text-white">
            {new Date(currentSubscription.subscription_end_date).toLocaleDateString()}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-400">{t('subscriptionStatus.daysRemaining')}</span>
          <span className={`font-medium ${getStatusColor()}`}>
            {currentSubscription.days_remaining} {t('subscriptionStatus.days')}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-400">{t('subscriptionStatus.amount')}</span>
          <span className="text-white">${currentSubscription.amount}</span>
        </div>
      </div>

      {/* Action buttons */}
      <div className="mt-4 space-y-2">
        {currentSubscription.can_renew && (
          <div className="rounded bg-blue-900/30 p-2 text-xs text-blue-300">
            {t('subscriptionStatus.renewWarning')}
          </div>
        )}

        {currentSubscription.can_downgrade && (
          <div className="rounded bg-yellow-900/30 p-2 text-xs text-yellow-300">
            {t('subscriptionStatus.downgradeWarning')}
          </div>
        )}
      </div>
    </div>
  );
};

export default SubscriptionStatus;
