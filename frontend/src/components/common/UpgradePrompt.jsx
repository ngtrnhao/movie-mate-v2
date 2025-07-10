import React from 'react';
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
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-md mx-4">
          <div className="flex items-center gap-3 mb-4">
            {showIcon && <Crown className="text-yellow-500" size={24} />}
            <h3 className="text-lg font-semibold text-gray-900">
              {isGuest ? 'Upgrade Required' : 'Upgrade Your Plan'}
            </h3>
          </div>

          <p className="text-gray-600 mb-6">{message}</p>

          <div className="flex gap-3">
            <Link
              to="/pricing"
              className="flex-1 bg-gradient-to-r from-yellow-500 to-orange-500 text-white px-4 py-2 rounded-lg font-medium text-center hover:from-yellow-600 hover:to-orange-600 transition-all duration-200"
            >
              View Plans
            </Link>
            <button className="px-4 py-2 text-gray-500 hover:text-gray-700 transition-colors">
              Maybe Later
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (variant === 'banner') {
    return (
      <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-lg p-4 mb-4">
        <div className="flex items-center gap-3">
          {showIcon && <Crown className="text-yellow-500" size={20} />}
          <div className="flex-1">
            <p className="text-sm text-gray-700">{message}</p>
          </div>
          <Link
            to="/pricing"
            className="flex items-center gap-1 text-sm font-medium text-yellow-700 hover:text-yellow-800 transition-colors"
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
    <div className="inline-flex items-center gap-2 text-sm text-yellow-700 bg-yellow-50 px-3 py-1 rounded-full">
      {showIcon && <Crown size={14} />}
      <span>{message}</span>
      <Link to="/pricing" className="font-medium hover:text-yellow-800 transition-colors">
        Upgrade
      </Link>
    </div>
  );
};

export default UpgradePrompt;
