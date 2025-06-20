import { useSearchParams } from 'react-router-dom';
import { PayPalScriptProvider, PayPalButtons } from '@paypal/react-paypal-js';
import { useTranslation } from '../i18n/hooks/useTranslation';
import { useSelector } from 'react-redux';
import { selectUser } from '../store/selectors/authSelectors';
import { useState } from 'react';
import { format, addMonths } from 'date-fns';

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
  const planId = searchParams.get('plan');
  let plan = t(`plans.${planId.replace('prenium_', '')}`, { returnObjects: true });
  if (!plan || typeof plan !== 'object' || !plan.name) plan = null;
  const user = useSelector(selectUser);

  // Chọn thời gian đăng ký
  const [duration, setDuration] = useState(1);
  const [paymentInfo, setPaymentInfo] = useState(null); // Lưu thông tin sau khi thanh toán thành công

  // Tính giá tiền theo thời gian và discount
  const basePrice = Number(plan?.price || 0);
  const discount = DURATION_OPTIONS.find(opt => opt.value === duration)?.discount || 0;
  const totalPrice = (basePrice * duration * (1 - discount)).toFixed(2);

  // Tính ngày bắt đầu và kết thúc dự kiến (local, chờ backend xác nhận thực tế)
  const now = new Date();
  const expectedEnd = addMonths(now, duration);

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
                <span className="ml-auto text-3xl font-extrabold">${totalPrice}</span>
                <span className="text-base text-gray-400">
                  /{duration} {duration > 1 ? 'tháng' : 'tháng'}
                </span>
              </div>
              <div className="mb-3">
                <label className="block mb-1 font-semibold">Chọn thời gian đăng ký:</label>
                <select
                  className="w-full rounded-lg bg-gray-700 text-white p-2"
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
          {/* Hiển thị thời gian hiệu lực dự kiến sau thanh toán */}
          {paymentInfo && (
            <div className="mt-6 bg-green-800/80 rounded-lg p-4 text-center">
              <div className="font-semibold mb-1">Đăng ký thành công!</div>
              <div>Hiệu lực từ: {format(now, 'dd/MM/yyyy')}</div>
              <div>Đến: {format(expectedEnd, 'dd/MM/yyyy')}</div>
            </div>
          )}
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
                            value: totalPrice,
                          },
                          description: plan.name,
                          custom_id: user.id?.toString(),
                          custom: JSON.stringify({ duration }),
                        },
                      ],
                    });
                  }}
                  onApprove={(data, actions) => {
                    return actions.order.capture().then(details => {
                      setPaymentInfo(details);
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
