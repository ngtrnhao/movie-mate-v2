import { useSearchParams } from 'react-router-dom';
import { PayPalScriptProvider, PayPalButtons } from '@paypal/react-paypal-js';
import { useTranslation } from '../i18n/hooks/useTranslation';
import { useSelector } from 'react-redux';
import { selectUser } from '../store/selectors/authSelectors';

const getInitials = user => {
  if (user.firstName || user.lastName) {
    return `${user.firstName?.[0] || ''}${user.lastName?.[0] || ''}`.toUpperCase();
  }
  if (user.username) return user.username[0].toUpperCase();
  if (user.email) return user.email[0].toUpperCase();
  return 'U';
};

const CheckoutPage = () => {
  const { t } = useTranslation('landing');
  const [searchParams] = useSearchParams();
  const planId = searchParams.get('plan');
  // Get plan from i18n (like PlanList)
  let plan = t(`plans.${planId.replace('prenium_', '')}`, { returnObjects: true });
  // Fallback if not found
  if (!plan || typeof plan !== 'object' || !plan.name) plan = null;
  const user = useSelector(selectUser);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-[#3a1c71] via-[#d76d77] to-[#2e1a47] text-white py-10 px-2">
      <div className="w-full max-w-2xl bg-gray-900/95 rounded-2xl shadow-2xl p-8 flex flex-col gap-8 md:flex-row md:gap-10 md:items-start">
        {/* Plan Summary */}
        <div className="flex-1">
          <h1 className="text-3xl font-bold mb-4 text-center md:text-left">
            {t('checkout.title', 'Checkout')}
          </h1>
          {plan ? (
            <div className="rounded-xl bg-gray-800/90 p-6 shadow-lg mb-4">
              <div className="flex items-center gap-4 mb-2">
                <span className="text-2xl font-bold text-yellow-400">{plan.name}</span>
                <span className="ml-auto text-3xl font-extrabold">${plan.price}</span>
                <span className="text-base text-gray-400">/{t(`plans.period`, plan.period)}</span>
              </div>
              <p className="text-gray-300 mb-3">{plan.description}</p>
              <ul className="list-disc list-inside text-sm text-gray-300 space-y-1">
                {plan.features && plan.features.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
            </div>
          ) : (
            <div className="text-center text-red-400">
              {t('checkout.invalidPlan', 'Invalid plan selected.')}
            </div>
          )}
          {/* User Info */}
          <div className="mt-6 bg-gray-800/80 rounded-lg p-4 flex items-center gap-3">
            {user?.avatarUrl ? (
              <img
                src={user.avatarUrl}
                alt="avatar"
                className="rounded-full w-12 h-12 object-cover border-2 border-gray-700"
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
        </div>
        {/* PayPal Payment Section */}
        <div className="flex-1 flex flex-col items-center justify-center">
          {plan && (
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
                            value: plan.price.toString(),
                          },
                          description: plan.name,
                        },
                      ],
                    });
                  }}
                  onApprove={(data, actions) => {
                    return actions.order.capture().then(details => {
                      alert(
                        t('checkout.success', 'Payment completed by') +
                          ' ' +
                          details.payer.name.given_name
                      );
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
