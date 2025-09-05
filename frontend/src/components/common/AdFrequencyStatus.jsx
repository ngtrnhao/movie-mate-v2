import { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { selectUser } from '../../store/slices/authSlice';
import adFrequencyService from '../../services/adFrequencyService';
import { isPremiumUser } from '../../utils/userUtils';

const AdFrequencyStatus = () => {
  const user = useSelector(selectUser);
  const [showStatus, setShowStatus] = useState(false);
  const [status, setStatus] = useState(null);
  const [timeElapsed, setTimeElapsed] = useState(0);

  const isPremium = isPremiumUser(user?.user_type);
  const isEligibleUser = !isPremium && (user?.user_type === 'member' || !user);

  useEffect(() => {
    if (!isEligibleUser) {
      return;
    }

    // Cập nhật status mỗi giây
    const interval = setInterval(() => {
      const currentStatus = adFrequencyService.getStatus();
      setStatus(currentStatus);
      setTimeElapsed(currentStatus.timeElapsed);
    }, 1000);

    return () => clearInterval(interval);
  }, [isEligibleUser]);

  const formatTime = milliseconds => {
    const minutes = Math.floor(milliseconds / 1000 / 60);
    const seconds = Math.floor((milliseconds / 1000) % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const formatTimeRemaining = milliseconds => {
    const minutes = Math.ceil(milliseconds / 1000 / 60);
    return `${minutes} phút`;
  };

  // Chỉ hiển thị cho eligible users
  if (!isEligibleUser) {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-4 z-50">
      {/* Toggle button */}
      <button
        onClick={() => setShowStatus(!showStatus)}
        className="rounded-lg bg-green-600 px-3 py-2 text-white shadow-lg transition-colors duration-200 hover:bg-green-700"
        title="Ad Frequency Status"
      >
        ⏱️ {formatTime(timeElapsed)}
      </button>

      {/* Status panel */}
      {showStatus && status && (
        <div className="absolute bottom-full left-0 mb-2 min-w-80 rounded-lg border border-gray-200 bg-white p-4 shadow-xl dark:border-gray-700 dark:bg-gray-800">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Tần suất Quảng cáo
            </h3>
            <button
              onClick={() => setShowStatus(false)}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              ✕
            </button>
          </div>

          <div className="space-y-3">
            {/* Session Time */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-300">Thời gian session:</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {formatTime(status.timeElapsed)}
              </span>
            </div>

            {/* Initial Delay Status */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-300">Trạng thái 15 phút:</span>
              <span
                className={`rounded px-2 py-1 text-xs font-medium ${
                  status.hasInitialDelayPassed
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                    : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                }`}
              >
                {status.hasInitialDelayPassed ? 'ĐÃ QUA' : 'ĐANG CHỜ'}
              </span>
            </div>

            {/* Time Until Ads */}
            {!status.hasInitialDelayPassed && (
              <div className="rounded bg-yellow-50 p-3 dark:bg-yellow-900/20">
                <div className="text-sm text-yellow-800 dark:text-yellow-200">
                  Quảng cáo sẽ hiển thị sau: {formatTimeRemaining(status.timeUntilAds)}
                </div>
              </div>
            )}

            {/* Hourly Limit */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-300">Quảng cáo giờ này:</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {status.adsShownThisHour}/{status.maxAdsPerHour}
              </span>
            </div>

            {/* Progress Bar */}
            <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
              <div
                className="h-2 rounded-full bg-blue-600 transition-all duration-300"
                style={{ width: `${(status.adsShownThisHour / status.maxAdsPerHour) * 100}%` }}
              />
            </div>

            {/* Cooldown Status */}
            {status.hasInitialDelayPassed && (
              <div className="rounded bg-blue-50 p-3 dark:bg-blue-900/20">
                <div className="mb-2 text-sm font-medium text-blue-800 dark:text-blue-200">
                  Cooldown hiện tại:
                </div>
                <div className="space-y-1">
                  {Object.entries(status.adCooldowns).map(([adType, cooldown]) => {
                    const remaining = adFrequencyService.getCooldownRemaining(adType);
                    const isInCooldown = remaining > 0;

                    return (
                      <div key={adType} className="flex items-center justify-between text-xs">
                        <span className="capitalize text-blue-700 dark:text-blue-300">
                          {adType.replace('_', ' ')}:
                        </span>
                        <span
                          className={`rounded px-1 text-xs ${
                            isInCooldown
                              ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                              : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                          }`}
                        >
                          {isInCooldown ? `${Math.ceil(remaining / 1000 / 60)}m` : 'Sẵn sàng'}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex space-x-2 pt-2">
              <button
                onClick={() => {
                  adFrequencyService.resetSession();
                  setStatus(adFrequencyService.getStatus());
                }}
                className="flex-1 rounded bg-red-500 px-3 py-2 text-sm font-medium text-white transition-colors duration-200 hover:bg-red-600"
              >
                Reset Session
              </button>

              <button
                onClick={() => {
                  setStatus(adFrequencyService.getStatus());
                }}
                className="flex-1 rounded bg-blue-500 px-3 py-2 text-sm font-medium text-white transition-colors duration-200 hover:bg-blue-600"
              >
                Refresh
              </button>
            </div>

            {/* Info */}
            <div className="mt-3 border-t border-gray-200 pt-3 dark:border-gray-600">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Quảng cáo chỉ hiển thị sau 15 phút và tuân theo giới hạn tần suất để tránh spam.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdFrequencyStatus;
