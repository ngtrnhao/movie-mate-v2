import { useSearchParams, useNavigate } from 'react-router-dom';
import { PayPalScriptProvider, PayPalButtons } from '@paypal/react-paypal-js';
import { useTranslation } from '../i18n/hooks/useTranslation';
import { useSelector, useDispatch } from 'react-redux';
import { selectUser } from '../store/selectors/authSelectors';
import { useState, useEffect } from 'react';
import { format, addMonths } from 'date-fns';
import { fetchProfile } from '../store/slices/profileSlice';
import { getPaymentTransactionAPI } from '../api/profileService';

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

  // Chọn thời gian đăng ký
  const [duration, setDuration] = useState(1);
  const [paymentInfo, setPaymentInfo] = useState(null);

  // States for polling logic
  const [isProcessing, setIsProcessing] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState('idle');

  // Tính giá tiền theo thời gian và discount
  const basePrice = Number(plan?.price || 0);
  const discount = DURATION_OPTIONS.find(opt => opt.value === duration)?.discount || 0;
  const totalPrice = (basePrice * duration * (1 - discount)).toFixed(2);

  // Tính ngày bắt đầu và kết thúc dự kiến (local, chờ backend xác nhận thực tế)
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
          setPaymentStatus('success');
          setIsProcessing(false);
          clearInterval(interval);
        }
        // Alternative success condition: If user type is already premium and payment transaction is active
        else if (updatedUser?.user_type !== 'member' && hasActiveSubscription) {
          console.log(
            'Payment successful! User already premium with confirmed payment transaction.'
          );
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
  }, [isProcessing, dispatch, user]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-[#3a1c71] via-[#d76d77] to-[#2e1a47] px-2 py-10 text-white">
      <div className="flex w-full max-w-2xl flex-col gap-8 rounded-2xl bg-gray-900/95 p-8 shadow-2xl md:flex-row md:items-start md:gap-10">
        {/* Plan Summary */}
        <div className="flex-1">
          <h1 className="mb-4 text-center text-3xl font-bold md:text-left">
            {t('checkout.title', 'Checkout')}
          </h1>
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
              <PayPalScriptProvider
                options={{ 'client-id': process.env.REACT_APP_PAYPAL_CLIENT_ID }}
              >
                <PayPalButtons
                  style={{ layout: 'vertical', color: 'blue', shape: 'rect', label: 'paypal' }}
                  createOrder={(data, actions) => {
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
                />
              </PayPalScriptProvider>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CheckoutPage;
