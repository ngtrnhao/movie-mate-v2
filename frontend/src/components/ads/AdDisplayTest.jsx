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
    <div className="fixed bottom-4 left-4 z-50 rounded-lg border border-gray-600 bg-black/90 p-4 text-white max-w-sm">
      <h3 className="text-sm font-bold mb-2">🔧 Ad Display Test</h3>

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

      <div className="mt-3 pt-3 border-t border-gray-600">
        <h4 className="text-xs font-semibold mb-2">Test Components:</h4>

        {/* Test AdWrapper */}
        <div className="mb-2">
          <div className="text-xs text-gray-400 mb-1">AdWrapper:</div>
          <AdWrapper>
            <div className="rounded border border-red-500/50 bg-red-600/20 p-2 text-xs">
              🎯 This ad should show for non-premium users
            </div>
          </AdWrapper>
        </div>

        {/* Test PremiumAdFreeMessage */}
        <div>
          <div className="text-xs text-gray-400 mb-1">PremiumAdFreeMessage:</div>
          <PremiumAdFreeMessage />
        </div>
      </div>
    </div>
  );
};

export default AdDisplayTest;
