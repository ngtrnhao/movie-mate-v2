import { useSelector } from 'react-redux';
import useAdDisplay from '../../hooks/useAdDisplay';
import { AdWrapper, PremiumAdFreeMessage } from './index';

/**
 * Component test để kiểm tra logic hiển thị quảng cáo
 * Chỉ hiển thị trong development mode
 */
const AdDisplayTest = () => {
  const isAuthenticated = useSelector(state => state.auth.isAuthenticated);
  const userType = useSelector(state => state.auth.user?.user_type);
  const isRehydrated = useSelector(state => state.auth.isRehydrated);
  const shouldShowAds = useAdDisplay();

  // Chỉ hiển thị trong development
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-4 z-50 max-w-sm rounded-lg border border-gray-600 bg-black/90 p-4 text-white">
      <h3 className="mb-2 text-sm font-bold">🔧 Ad Display Test</h3>

      <div className="space-y-1 text-xs">
        <div>
          <span className="text-gray-400">Rehydrated:</span>{' '}
          <span className={isRehydrated ? 'text-green-400' : 'text-red-400'}>
            {isRehydrated ? 'Yes' : 'No'}
          </span>
        </div>
        <div>
          <span className="text-gray-400">Authenticated:</span>{' '}
          <span className={isAuthenticated ? 'text-green-400' : 'text-red-400'}>
            {isAuthenticated ? 'Yes' : 'No'}
          </span>
        </div>

        <div>
          <span className="text-gray-400">User Type:</span>{' '}
          <span className="text-yellow-400">{userType || 'None'}</span>
        </div>

        <div>
          <span className="text-gray-400">Should Show Ads:</span>{' '}
          <span className={shouldShowAds ? 'text-green-400' : 'text-red-400'}>
            {shouldShowAds ? 'Yes' : 'No'}
          </span>
        </div>
      </div>

      <div className="mt-3 border-t border-gray-600 pt-3">
        <h4 className="mb-2 text-xs font-semibold">Test Components:</h4>

        {/* Test AdWrapper */}
        <div className="mb-2">
          <div className="mb-1 text-xs text-gray-400">AdWrapper:</div>
          <AdWrapper>
            <div className="rounded border border-red-500/50 bg-red-600/20 p-2 text-xs">
              🎯 This ad should show for non-premium users
            </div>
          </AdWrapper>
        </div>

        {/* Test PremiumAdFreeMessage */}
        <div>
          <div className="mb-1 text-xs text-gray-400">PremiumAdFreeMessage:</div>
          <PremiumAdFreeMessage />
        </div>
      </div>
    </div>
  );
};

export default AdDisplayTest;
