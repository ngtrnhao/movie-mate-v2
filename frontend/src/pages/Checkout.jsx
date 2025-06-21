import { useSearchParams, useNavigate } from 'react-router-dom';
import { PayPalScriptProvider, PayPalButtons } from '@paypal/react-paypal-js';
import { useTranslation } from '../i18n/hooks/useTranslation';
import { useSelector, useDispatch } from 'react-redux';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { selectUser } from '../store/selectors/authSelectors';
import { useState, useEffect } from 'react';
import { format, addMonths } from 'date-fns';
import { fetchProfile } from '../store/slices/profileSlice';
import { getPaymentTransactionAPI } from '../api/profileService';
import { toast } from 'react-hot-toast';
import { createPaymentAPI } from '../api/profileService';

const getInitials = user => {
  if (user.firstName || user.lastName) {
    return `${user.firstName?.[0] || ''}${user.lastName?.[0] || ''}`.toUpperCase();
  }
  if (user.username) return user.username[0].toUpperCase();
  if (user.email) return user.email[0].toUpperCase();
  return 'U';
};

const DURATION_OPTIONS = [
  { value: 1, label: '1 tháng', discount: 0 },
  { value: 3, label: '3 tháng (giảm 10%)', discount: 0.1 },
  { value: 12, label: '12 tháng (giảm 20%)', discount: 0.2 },
];

const CheckoutPage = () => {
  const { t } = useTranslation('landing');
  const [searchParams] = useSearchParams();
  const planName = searchParams.get('plan');
  let plan = t(`plans.${planName.replace('prenium_', '')}`, { returnObjects: true });
  if (!plan || typeof plan !== 'object' || !plan.name) plan = null;
  const user = useSelector(selectUser);
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: currentSubscription, isLoading: isLoadingSubscription } = useQuery({
    queryKey: ['subscription', user?.id],
    queryFn: () => getPaymentTransactionAPI(user.id),
    enabled: !!user?.id,
  });

  // Chọn thời gian đăng ký
  const [duration, setDuration] = useState(1);
  const [paymentInfo, setPaymentInfo] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState('idle');

  // Tính giá tiền theo thời gian và discount
  const basePrice = Number(plan?.price || 0);
  const discount = DURATION_OPTIONS.find(opt => opt.value === duration)?.discount || 0;
  const totalPrice = (basePrice * duration * (1 - discount)).toFixed(2);

  // Helper functions
  const getPlanLevel = planName => {
    if (planName === 'basic') return 1;
    if (planName === 'standard') return 2;
    if (planName === 'vip') return 3;
    return 0;
  };

  const isUpgrade = () => {
    if (!currentSubscription?.has_active_subscription || !planName) return false;
    const currentLevel = getPlanLevel(currentSubscription.plan);
    const newLevel = getPlanLevel(planName.replace('prenium_', ''));
    return newLevel > currentLevel;
  };

  const isDowngrade = () => {
    if (!currentSubscription?.has_active_subscription || !planName) return false;
    const currentLevel = getPlanLevel(currentSubscription.plan);
    const newLevel = getPlanLevel(planName.replace('prenium_', ''));
    return newLevel < currentLevel;
  };

  const isSamePlan = () => {
    if (!currentSubscription?.has_active_subscription || !planName) return false;
    return currentSubscription.plan === planName.replace('prenium_', '');
  };

  // Calculate subscription dates
  const now = new Date();
  const expectedEnd = addMonths(now, duration);

  // Polling effect
  useEffect(() => {
    if (!isProcessing) {
      return;
    }

    let retryCount = 0;
    const maxRetries = 3;

    const interval = setInterval(async () => {
      // Ensure we have a valid user ID before polling
      if (!user?.id) {
        console.warn('Polling skipped: user ID not available.');
        return;
      }
      console.log(`Polling for profile updates for user ${user.id}... (attempt ${retryCount + 1})`);

      try {
        // Fetch updated user profile
        const action = await dispatch(fetchProfile(user.id));
        const updatedUser = action.payload.user;

        // Fetch payment transaction data
        const paymentData = await getPaymentTransactionAPI(user.id);

        // Check if user type has been upgraded to premium
        const isUserTypeUpgraded =
          updatedUser?.user_type &&
          updatedUser.user_type !== 'member' &&
          updatedUser.user_type !== user.user_type;

        // Check if payment transaction shows active subscription
        const hasActiveSubscription = paymentData?.has_active_subscription;

        // Check if subscription dates are available (from PaymentTransaction)
        const hasSubscriptionDates =
          updatedUser?.subscription_start_date && updatedUser?.subscription_end_date;

        // Check if subscription end date is in the future
        const isSubscriptionActive =
          hasSubscriptionDates && new Date(updatedUser.subscription_end_date) > new Date();

        console.log('Polling check results:', {
          isUserTypeUpgraded,
          hasActiveSubscription,
          hasSubscriptionDates,
          isSubscriptionActive,
          oldUserType: user.user_type,
          newUserType: updatedUser?.user_type,
          subscriptionEndDate: updatedUser?.subscription_end_date,
          paymentTransactionData: paymentData,
          retryCount: retryCount + 1,
        });

        // Success condition: User type upgraded AND has active subscription from payment transaction
        if (isUserTypeUpgraded && hasActiveSubscription) {
          console.log('Payment successful! User upgraded and payment transaction confirmed.');
          // Invalidate the query to refetch subscription data across the app
          queryClient.invalidateQueries({ queryKey: ['subscription', user.id] });
          setPaymentStatus('success');
          setIsProcessing(false);
          clearInterval(interval);
        }
        // Alternative success condition: If user type is already premium and payment transaction is active
        else if (updatedUser?.user_type !== 'member' && hasActiveSubscription) {
          console.log(
            'Payment successful! User already premium with confirmed payment transaction.'
          );
          // Invalidate the query to refetch subscription data across the app
          queryClient.invalidateQueries({ queryKey: ['subscription', user.id] });
          setPaymentStatus('success');
          setIsProcessing(false);
          clearInterval(interval);
        }

        // Reset retry count on successful API calls
        retryCount = 0;
      } catch (error) {
        console.error('Error during polling:', error);
        retryCount++;

        // If too many retries, show error but don't stop polling
        if (retryCount >= maxRetries) {
          console.warn(`Max retries (${maxRetries}) reached, but continuing to poll...`);
          retryCount = 0; // Reset for next cycle
        }
      }
    }, 3000); // Poll every 3 seconds

    // Timeout after 2 minutes (120 seconds)
    const timeout = setTimeout(() => {
      if (isProcessing) {
        console.log('Polling timeout reached after 2 minutes. Payment processing may be delayed.');
        setPaymentStatus('failed');
        setIsProcessing(false);
        clearInterval(interval);
      }
    }, 120000); // 2 minutes = 120,000 milliseconds

    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [isProcessing, dispatch, user, queryClient]);

  const handlePayment = async () => {
    if (!user) {
      toast.error('Please login to continue');
      return;
    }

    // Check if user already has an active subscription and is trying to buy the same plan
    if (currentSubscription?.has_active_subscription && isSamePlan()) {
      const daysUntilExpiry = Math.ceil(
        (new Date(currentSubscription.subscription_end_date) - new Date()) / (1000 * 60 * 60 * 24)
      );

      if (daysUntilExpiry > 7) {
        toast.error(
          `You already have an active ${currentSubscription.plan} subscription valid until ${new Date(currentSubscription.subscription_end_date).toLocaleDateString()}. Please wait until it's closer to expiry to renew.`
        );
        return;
      }
    }

    // Check if user is trying to downgrade too early
    if (currentSubscription?.has_active_subscription && isDowngrade()) {
      const daysUntilExpiry = Math.ceil(
        (new Date(currentSubscription.subscription_end_date) - new Date()) / (1000 * 60 * 60 * 24)
      );

      if (daysUntilExpiry > 30) {
        toast.error(
          `You can only downgrade your plan when it's within 30 days of expiry. Your current plan expires on ${new Date(currentSubscription.subscription_end_date).toLocaleDateString()}.`
        );
        return;
      }
    }

    // If all validations pass, show PayPal buttons
    setPaymentStatus('ready');
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-[#3a1c71] via-[#d76d77] to-[#2e1a47] px-2 py-10 text-white">
      <div className="flex w-full max-w-2xl flex-col gap-8 rounded-2xl bg-gray-900/95 p-8 shadow-2xl md:flex-row md:items-start md:gap-10">
        {/* Plan Summary */}
        <div className="flex-1">
          <h1 className="mb-4 text-center text-3xl font-bold md:text-left">
            {t('checkout.title', 'Checkout')}
          </h1>

          {/* Loading state */}
          {isLoadingSubscription && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
              <p className="mt-2">Loading subscription information...</p>
            </div>
          )}

          {/* Current subscription info */}
          {!isLoadingSubscription && currentSubscription?.has_active_subscription && (
            <div className="mb-4 rounded-xl bg-blue-800/90 p-4 shadow-lg">
              <h3 className="font-semibold text-blue-200 mb-2">Current Subscription</h3>
              <div className="text-sm space-y-1">
                <p>
                  <span className="text-gray-300">Plan:</span> {currentSubscription.plan}
                </p>
                <p>
                  <span className="text-gray-300">Valid until:</span>{' '}
                  {new Date(currentSubscription.subscription_end_date).toLocaleDateString()}
                </p>
                <p>
                  <span className="text-gray-300">Amount:</span> ${currentSubscription.amount}
                </p>
              </div>
            </div>
          )}

          {/* Action type indicator */}
          {!isLoadingSubscription && currentSubscription?.has_active_subscription && (
            <div className="mb-4 p-3 rounded-lg text-center">
              {isUpgrade() && (
                <div className="bg-green-800/50 p-2 rounded">
                  <span className="text-green-300 font-semibold">⬆️ Upgrade Plan</span>
                  <p className="text-sm text-gray-300 mt-1">
                    You're upgrading to a higher tier plan
                  </p>
                </div>
              )}
              {isDowngrade() && (
                <div className="bg-yellow-800/50 p-2 rounded">
                  <span className="text-yellow-300 font-semibold">⬇️ Downgrade Plan</span>
                  <p className="text-sm text-gray-300 mt-1">
                    You're switching to a lower tier plan
                  </p>
                </div>
              )}
              {isSamePlan() && (
                <div className="bg-blue-800/50 p-2 rounded">
                  <span className="text-blue-300 font-semibold">🔄 Renew Plan</span>
                  <p className="text-sm text-gray-300 mt-1">You're renewing the same plan</p>
                </div>
              )}
            </div>
          )}

          {plan ? (
            <div className="mb-4 rounded-xl bg-gray-800/90 p-6 shadow-lg">
              <div className="mb-2 flex items-center gap-4">
                <span className="text-2xl font-bold text-yellow-400">{plan.name}</span>
                <span className="ml-auto text-3xl font-extrabold">${totalPrice}</span>
                <span className="text-base text-gray-400">
                  /{duration} {duration > 1 ? 'tháng' : 'tháng'}
                </span>
              </div>
              <div className="mb-3">
                <label className="mb-1 block font-semibold">Chọn thời gian đăng ký:</label>
                <select
                  className="w-full rounded-lg bg-gray-700 p-2 text-white"
                  value={duration}
                  onChange={e => setDuration(Number(e.target.value))}
                >
                  {DURATION_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <p className="mb-3 text-gray-300">{plan.description}</p>
              <ul className="list-inside list-disc space-y-1 text-sm text-gray-300">
                {plan.features && plan.features.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
            </div>
          ) : (
            <div className="text-center text-red-400">
              {t('checkout.invalidPlan', 'Invalid plan selected.')}
            </div>
          )}
          {/* User Info */}
          <div className="mt-6 flex items-center gap-3 rounded-lg bg-gray-800/80 p-4">
            {user?.avatarUrl ? (
              <img
                src={user.avatarUrl}
                alt="avatar"
                className="size-12 rounded-full border-2 border-gray-700 object-cover"
              />
            ) : (
              <div className="rounded-full bg-gray-700 w-12 h-12 flex items-center justify-center text-xl font-bold text-white">
                {getInitials(user)}
              </div>
            )}
            <div>
              <div className="font-semibold">
                {user?.firstName || user?.lastName
                  ? `${user.firstName || ''} ${user.lastName || ''}`.trim()
                  : user?.username || t('checkout.user', 'User')}
              </div>
              <div className="text-xs text-gray-400">{user?.email || ''}</div>
            </div>
          </div>
          {/* Hiển thị thời gian hiệu lực dự kiến sau thanh toán */}
          {paymentInfo && (
            <div className="mt-6 bg-green-800/80 rounded-lg p-4 text-center">
              <div className="mb-1 font-semibold">Đăng ký thành công!</div>
              <div>Hiệu lực từ: {format(now, 'dd/MM/yyyy')}</div>
              <div>Đến: {format(expectedEnd, 'dd/MM/yyyy')}</div>
            </div>
          )}
        </div>
        {/* PayPal Payment Section */}
        <div className="flex-1 flex flex-col items-center justify-center">
          {isProcessing && (
            <div className="text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
              <p className="mt-4 text-lg">
                {t('checkout.processing', 'Processing your payment, please wait...')}
              </p>
              <p className="mt-2 text-sm text-gray-400">
                This may take up to 2 minutes. Please don't close this page.
              </p>
            </div>
          )}

          {paymentStatus === 'success' && (
            <div className="text-center p-6 bg-green-800/50 rounded-lg">
              <h2 className="text-2xl font-bold text-green-300">
                {t('checkout.successTitle', 'Payment Successful!')}
              </h2>
              <p className="mt-2">
                {t('checkout.successMessage', 'Your account has been upgraded.')}
              </p>
              <button
                onClick={() => navigate('/profile')}
                className="mt-4 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
              >
                {t('checkout.goToProfile', 'Go to Profile')}
              </button>
            </div>
          )}

          {paymentStatus === 'failed' && (
            <div className="text-center p-6 bg-red-800/50 rounded-lg">
              <h2 className="text-2xl font-bold text-red-300">
                {t('checkout.failedTitle', 'Processing Delayed')}
              </h2>
              <p className="mt-2">
                {t(
                  'checkout.failedMessage',
                  'Your payment is being processed. Please check your profile in a few minutes.'
                )}
              </p>
              <p className="mt-2 text-sm text-gray-300">
                If you don't see the update in 5 minutes, please contact support.
              </p>
              <button
                onClick={() => navigate(`/profile/${user.id}`)}
                className="mt-4 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
              >
                {t('checkout.goToProfile', 'Go to Profile')}
              </button>
            </div>
          )}

          {plan && paymentStatus === 'idle' && (
            <div className="w-full max-w-xs bg-gray-800/90 rounded-xl p-6 shadow-lg flex flex-col items-center">
              <h2 className="text-xl font-semibold mb-4 text-center">
                {t('checkout.payWithPaypal', 'Pay securely with PayPal')}
              </h2>

              {/* Disable button if loading subscription */}
              {isLoadingSubscription ? (
                <div className="w-full">
                  <button
                    disabled
                    className="w-full bg-gray-600 text-gray-400 py-3 px-6 rounded-lg font-semibold cursor-not-allowed"
                  >
                    Loading subscription info...
                  </button>
                </div>
              ) : (
                <div className="w-full space-y-3">
                  <button
                    onClick={handlePayment}
                    disabled={isProcessing}
                    className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white py-3 px-6 rounded-lg font-semibold transition-colors"
                  >
                    {isProcessing ? (
                      <div className="flex items-center justify-center">
                        <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white mr-2"></div>
                        Processing...
                      </div>
                    ) : (
                      `Continue to PayPal - $${totalPrice}`
                    )}
                  </button>

                  {/* Show warning for same plan renewal */}
                  {currentSubscription?.has_active_subscription && isSamePlan() && (
                    <div className="text-xs text-yellow-300 bg-yellow-900/30 p-2 rounded">
                      ⚠️ You're renewing the same plan. This will extend your subscription.
                    </div>
                  )}

                  {/* Show warning for downgrade */}
                  {currentSubscription?.has_active_subscription && isDowngrade() && (
                    <div className="text-xs text-orange-300 bg-orange-900/30 p-2 rounded">
                      ⚠️ You're downgrading your plan. Changes will take effect at next billing
                      cycle.
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* PayPal Buttons - Show when ready */}
          {plan && paymentStatus === 'ready' && (
            <div className="w-full max-w-xs bg-gray-800/90 rounded-xl p-6 shadow-lg flex flex-col items-center">
              <h2 className="text-xl font-semibold mb-4 text-center">
                {t('checkout.payWithPaypal', 'Pay securely with PayPal')}
              </h2>

              <PayPalScriptProvider
                options={{ 'client-id': process.env.REACT_APP_PAYPAL_CLIENT_ID }}
              >
                <PayPalButtons
                  style={{ layout: 'vertical', color: 'blue', shape: 'rect', label: 'paypal' }}
                  createOrder={(data, actions) => {
                    console.log('Creating PayPal order with duration:', duration);
                    console.log('Total price:', totalPrice);
                    console.log('Plan:', planName.replace('prenium_', ''));

                    return actions.order.create({
                      purchase_units: [
                        {
                          amount: {
                            value: totalPrice,
                          },
                          description: planName.replace('prenium_', ''),
                          custom_id: user.id?.toString(),
                          custom: JSON.stringify({ duration }),
                        },
                      ],
                    });
                  }}
                  onApprove={(data, actions) => {
                    return actions.order.capture().then(details => {
                      setPaymentInfo(details);
                      setIsProcessing(true);
                      setPaymentStatus('processing');
                    });
                  }}
                  onError={err => {
                    console.error('PayPal error:', err);
                    toast.error('Payment failed. Please try again.');
                    setPaymentStatus('error');
                  }}
                  onCancel={() => {
                    setPaymentStatus('idle');
                  }}
                />
              </PayPalScriptProvider>

              <button
                onClick={() => setPaymentStatus('idle')}
                className="mt-4 text-sm text-gray-400 hover:text-white"
              >
                ← Back to payment options
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CheckoutPage;
