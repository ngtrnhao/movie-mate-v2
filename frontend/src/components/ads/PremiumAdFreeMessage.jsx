import { memo } from 'react';
import { useSelector } from 'react-redux';
import useAdDisplay from '../../hooks/useAdDisplay';

/**
 * Component hiển thị thông báo cho premium users
 * Chỉ hiển thị khi user đã đăng nhập và không phải member
 */
const PremiumAdFreeMessage = memo(() => {
  const isAuthenticated = useSelector(state => state.auth.isAuthenticated);
  const userType = useSelector(state => state.auth.user?.user_type);
  const shouldShowAds = useAdDisplay();

  // Chỉ hiển thị cho premium users (đã đăng nhập và không phải member)
  if (!isAuthenticated || shouldShowAds) {
    return null;
  }

  return (
    <div className="bg-gradient-to-r from-green-600/10 to-blue-600/10 border border-green-500/20 rounded-lg p-4 mb-4">
      <div className="flex items-center gap-3">
        <div className="flex-shrink-0">
          <svg
            className="w-6 h-6 text-green-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <div className="flex-1">
          <h4 className="text-sm font-semibold text-green-400">Ad-Free Experience</h4>
          <p className="text-xs text-gray-400 mt-1">
            Enjoy an ad-free experience with your {userType?.replace('prenium_', 'Premium ')}{' '}
            subscription!
          </p>
        </div>
      </div>
    </div>
  );
});

PremiumAdFreeMessage.displayName = 'PremiumAdFreeMessage';

export default PremiumAdFreeMessage;
