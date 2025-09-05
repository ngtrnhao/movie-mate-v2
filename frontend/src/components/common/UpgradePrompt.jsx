import { useUserLimits } from '../../hooks/useUserLimits';
import { Crown, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

const UpgradePrompt = ({ feature, showIcon = true, variant = 'inline' }) => {
  const { shouldShowUpgrade, getUpgradeMessage, userType } = useUserLimits();

  if (!shouldShowUpgrade(feature)) {
    return null;
  }

  const message = getUpgradeMessage(feature);
  const isGuest = userType === 'guest';

  if (variant === 'modal') {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
        <div className="mx-4 max-w-md rounded-lg bg-white p-6">
          <div className="mb-4 flex items-center gap-3">
            {showIcon && <Crown className="text-yellow-500" size={24} />}
            <h3 className="text-lg font-semibold text-gray-900">
              {isGuest ? 'Upgrade Required' : 'Upgrade Your Plan'}
            </h3>
          </div>

          <p className="mb-6 text-gray-600">{message}</p>

          <div className="flex gap-3">
            <Link
              to="/pricing"
              className="flex-1 rounded-lg bg-gradient-to-r from-yellow-500 to-orange-500 px-4 py-2 text-center font-medium text-white transition-all duration-200 hover:from-yellow-600 hover:to-orange-600"
            >
              View Plans
            </Link>
            <button className="px-4 py-2 text-gray-500 transition-colors hover:text-gray-700">
              Maybe Later
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (variant === 'banner') {
    return (
      <div className="mb-4 rounded-lg border border-yellow-200 bg-gradient-to-r from-yellow-50 to-orange-50 p-4">
        <div className="flex items-center gap-3">
          {showIcon && <Crown className="text-yellow-500" size={20} />}
          <div className="flex-1">
            <p className="text-sm text-gray-700">{message}</p>
          </div>
          <Link
            to="/pricing"
            className="flex items-center gap-1 text-sm font-medium text-yellow-700 transition-colors hover:text-yellow-800"
          >
            Upgrade
            <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    );
  }

  // Default inline variant
  return (
    <div className="inline-flex items-center gap-2 rounded-full bg-yellow-50 px-3 py-1 text-sm text-yellow-700">
      {showIcon && <Crown size={14} />}
      <span>{message}</span>
      <Link to="/pricing" className="font-medium transition-colors hover:text-yellow-800">
        Upgrade
      </Link>
    </div>
  );
};

export default UpgradePrompt;
